import { useEffect, useState } from 'react';
import api from '../services/api';

export function useReports(projectId?: string) {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/projects/${projectId}/reports/`);
      setReports(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchReports();
  }, [projectId]);

  return { reports, loading, error, refresh: fetchReports };
}
