import { useEffect, useState } from 'react';
import api from '../services/api';

export function useScans(projectId?: string) {
  const [scans, setScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchScans = async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/projects/${projectId}/scans/`);
      setScans(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch scans');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchScans();
  }, [projectId]);

  return { scans, loading, error, refresh: fetchScans };
}
