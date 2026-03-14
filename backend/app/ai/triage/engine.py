"""
AI-assisted triage engine.

Uses the same LLM provider infrastructure as remediation to help
analysts assess whether a finding is a true/false positive and
recommend triage priority.

"""

import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.remediation.engine import RemediationEngine
from app.ai.remediation.prompts import TRIAGE_SYSTEM_PROMPT, build_triage_user_prompt
from app.ai.remediation.providers import ProviderError
from app.core.config import get_settings
from app.models.finding import Finding

logger = logging.getLogger(__name__)
settings = get_settings()
_CACHE_PREFIX = "triage:"
_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


class TriageEngine:
    """
    AI-powered vulnerability triage assistant.

    Usage:
        engine = TriageEngine()
        assessment = await engine.generate_triage(db, finding)
        # assessment is a Markdown string with true/false positive analysis

    Uses the same provider selection and fallback logic as RemediationEngine.
    """

    def __init__(self) -> None:
        # Reuse RemediationEngine's provider infrastructure
        self._remediation_engine = RemediationEngine()
        self._redis: Redis | None = None

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

    async def generate_triage(
        self,
        db: AsyncSession,
        finding: Finding,
        provider_override: str | None = None,
    ) -> str | None:
        """
        Generate AI triage assessment for a finding.

        Pattern is identical to RemediationEngine.generate() — use the
        same provider selection, fallback, and error handling logic.
        """
        if finding.cve_id:
            cached = await self._get_cached(finding.cve_id)
            if cached:
                cached_text, _cached_provider = cached
                logger.info(
                    "Triage cache hit for CVE %s (finding %s)",
                    finding.cve_id,
                    finding.id,
                )
                return cached_text

        vuln_context = await self._remediation_engine._get_vuln_context(
            db, finding.cve_id
        )
        user_prompt = build_triage_user_prompt(finding, vuln_context)

        provider_name = provider_override or settings.DEFAULT_AI_PROVIDER
        available = self._remediation_engine._get_available_providers()

        try_order = [provider_name] if provider_name in available else []
        for fb in self._remediation_engine.FALLBACK_ORDER:
            if fb not in try_order and fb in available:
                try_order.append(fb)

        assessment_text: str | None = None
        used_provider: str | None = None

        for pname in try_order:
            try:
                provider = self._remediation_engine._get_provider(pname)
                assessment_text = await provider.generate_remediation(
                    TRIAGE_SYSTEM_PROMPT, user_prompt
                )
                used_provider = pname
                logger.info(
                    "Triage assessment generated via %s for finding %s",
                    pname,
                    finding.id,
                )
                break
            except (ProviderError, NotImplementedError) as exc:
                logger.warning(
                    "Provider %s failed for triage %s: %s — trying fallback",
                    pname,
                    finding.id,
                    exc,
                )
                continue

        if assessment_text is None:
            logger.error("All AI providers failed triage for finding %s", finding.id)
            return None

        if finding.cve_id:
            await self._set_cached(finding.cve_id, assessment_text, used_provider)

        return assessment_text
