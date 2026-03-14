import { useState, useEffect } from 'react';
import api from '../services/api';

export function useFindings(projectId?: string) {
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const fetchFindings = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(`/projects/${projectId}/findings/`);
        setFindings(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch findings');
      } finally {
        setLoading(false);
      }
    };

    fetchFindings();
  }, [projectId]);

  return { findings, loading, error };
}
