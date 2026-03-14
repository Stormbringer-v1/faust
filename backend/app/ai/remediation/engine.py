"""
AI Remediation Engine — orchestrates LLM calls for vulnerability remediation.

Architecture:
- Provider selection based on config (DEFAULT_AI_PROVIDER) or per-request override
- Prompt construction with full CVE context from Vulnerability reference table
- Redis caching to avoid redundant LLM calls for same CVE
- Automatic fallback: if preferred provider fails, try next available
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.finding import Finding
from app.models.vulnerability import Vulnerability
from app.ai.remediation.prompts import REMEDIATION_SYSTEM_PROMPT, build_remediation_user_prompt
from app.ai.remediation.providers import (
    AnthropicProvider,
    BaseLLMProvider,
    GoogleProvider,
    OllamaProvider,
    OpenAIProvider,
    ProviderError,
)

logger = logging.getLogger(__name__)
settings = get_settings()
_CACHE_PREFIX = "remediation:"
_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


class RemediationEngine:
    """
    Orchestrates AI-powered vulnerability remediation guidance.

    Usage:
        engine = RemediationEngine()
        result = await engine.generate(db, finding, provider_override="anthropic")
        # result is Markdown string or None on failure

    Provider priority (if no override):
        1. settings.DEFAULT_AI_PROVIDER
        2. Fallback chain: anthropic → openai → google → ollama
    """

    # Provider registry — maps name → class
    PROVIDERS: dict[str, type[BaseLLMProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "ollama": OllamaProvider,
    }

    # Fallback order when primary provider fails
    FALLBACK_ORDER: list[str] = ["anthropic", "openai", "google", "ollama"]

    def __init__(self) -> None:
        self._provider_cache: dict[str, BaseLLMProvider] = {}
        self._redis: Redis | None = None

    def _get_provider(self, name: str) -> BaseLLMProvider:
        """Get or create a provider instance by name."""
        if name not in self._provider_cache:
            provider_cls = self.PROVIDERS.get(name)
            if provider_cls is None:
                raise ValueError(f"Unknown AI provider: {name}")
            self._provider_cache[name] = provider_cls()
        return self._provider_cache[name]

    def _get_available_providers(self) -> list[str]:
        """Return list of providers that have credentials configured."""
        available = []
        if settings.ANTHROPIC_API_KEY:
            available.append("anthropic")
        if settings.OPENAI_API_KEY:
            available.append("openai")
        if settings.GOOGLE_AI_API_KEY:
            available.append("google")
        # Ollama is always "available" (local, no API key)
        available.append("ollama")
        return available

    def _cache_key(self, cve_id: str) -> str:
        return f"{_CACHE_PREFIX}{cve_id}"

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def _get_cached(self, cve_id: str) -> tuple[str, str | None] | None:
        key = self._cache_key(cve_id)
        try:
            redis_client = await self._get_redis()
            cached = await redis_client.get(key)
        except RedisError as exc:
            logger.warning("Redis cache read failed for %s: %s", key, exc)
            return None

        if not cached:
            return None

        try:
            payload = json.loads(cached)
        except json.JSONDecodeError:
            return cached, None

        if isinstance(payload, dict) and "text" in payload:
            return payload["text"], payload.get("provider")
        return cached, None

    async def _set_cached(self, cve_id: str, text: str, provider: str | None) -> None:
        key = self._cache_key(cve_id)
        payload = json.dumps({"text": text, "provider": provider})
        try:
            redis_client = await self._get_redis()
            await redis_client.set(key, payload, ex=_CACHE_TTL_SECONDS)
        except RedisError as exc:
            logger.warning("Redis cache write failed for %s: %s", key, exc)

    async def generate(
        self,
        db: AsyncSession,
        finding: Finding,
        provider_override: str | None = None,
    ) -> str | None:
        """
        Generate AI remediation for a finding.

        Steps:
        1. Check Redis cache for existing remediation (by CVE ID if present)
        2. Enrich finding context from Vulnerability reference table
        3. Build prompt with full context
        4. Call LLM provider (with fallback on failure)
        5. Cache result in Redis
        6. Update finding record with remediation text

        Args:
            db: Database session.
            finding: The Finding ORM object to remediate.
            provider_override: Force a specific provider (e.g. "anthropic").

        Returns:
            Markdown remediation text, or None if all providers fail.

        """
        # Step 1: Check cache
        if finding.cve_id:
            cached = await self._get_cached(finding.cve_id)
            if cached:
                cached_text, cached_provider = cached
                finding.ai_remediation = cached_text
                finding.ai_provider = cached_provider or "cache"
                finding.ai_generated_at = datetime.now(timezone.utc)
                logger.info(
                    "Remediation cache hit for CVE %s (finding %s)",
                    finding.cve_id,
                    finding.id,
                )
                return cached_text

        # Step 2: Enrich context from vulnerability reference table
        vuln_context = await self._get_vuln_context(db, finding.cve_id)

        # Step 3: Build prompt
        user_prompt = build_remediation_user_prompt(finding, vuln_context)

        # Step 4: Call provider with fallback
        provider_name = provider_override or settings.DEFAULT_AI_PROVIDER
        available = self._get_available_providers()

        # Build try-order: requested provider first, then fallbacks
        try_order = [provider_name] if provider_name in available else []
        for fb in self.FALLBACK_ORDER:
            if fb not in try_order and fb in available:
                try_order.append(fb)

        remediation_text: str | None = None
        used_provider: str | None = None

        for pname in try_order:
            try:
                provider = self._get_provider(pname)
                remediation_text = await provider.generate_remediation(
                    REMEDIATION_SYSTEM_PROMPT, user_prompt
                )
                used_provider = pname
                logger.info(
                    "Remediation generated via %s for finding %s",
                    pname,
                    finding.id,
                )
                break
            except (ProviderError, NotImplementedError) as e:
                logger.warning(
                    "Provider %s failed for finding %s: %s — trying fallback",
                    pname,
                    finding.id,
                    e,
                )
                continue

        if remediation_text is None:
            logger.error("All AI providers failed for finding %s", finding.id)
            return None

        # Step 5: Cache (BUILDER: implement Redis set)
        if finding.cve_id:
            await self._set_cached(finding.cve_id, remediation_text, used_provider)

        # Step 6: Update finding record
        finding.ai_remediation = remediation_text
        finding.ai_provider = used_provider
        finding.ai_generated_at = datetime.now(timezone.utc)

        return remediation_text

    async def _get_vuln_context(
        self, db: AsyncSession, cve_id: str | None
    ) -> dict[str, Any] | None:
        """
        Look up CVE in the Vulnerability reference table for context enrichment.

        Returns dict with CVSS details, EPSS, KEV status, CWE, references,
        or None if CVE not found in our catalog.
        """
        if not cve_id:
            return None

        result = await db.execute(
            select(Vulnerability).where(Vulnerability.cve_id == cve_id)
        )
        vuln = result.scalar_one_or_none()

        if vuln is None:
            return None

        return {
            "cve_id": vuln.cve_id,
            "description": vuln.description,
            "cvss_v31_score": vuln.cvss_v31_score,
            "cvss_v31_vector": vuln.cvss_v31_vector,
            "cvss_v31_severity": vuln.cvss_v31_severity,
            "cwe_ids": vuln.cwe_ids,
            "epss_score": vuln.epss_score,
            "epss_percentile": vuln.epss_percentile,
            "is_cisa_kev": vuln.is_cisa_kev,
            "kev_ransomware_use": vuln.kev_ransomware_use,
            "kev_due_date": str(vuln.kev_due_date) if vuln.kev_due_date else None,
            "vendor": vuln.vendor,
            "product": vuln.product,
            "references": vuln.references,
        }
