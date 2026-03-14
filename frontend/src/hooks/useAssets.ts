import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export function useAssets(projectId?: string) {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/projects/${projectId}/assets/`);
      setAssets(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch assets');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void fetchAssets();
  }, [fetchAssets]);

  return { assets, loading, error, refresh: fetchAssets };
}
