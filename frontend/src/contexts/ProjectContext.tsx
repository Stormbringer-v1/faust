import { useState, useEffect, createContext, useContext, type ReactNode } from 'react';
import api from '../services/api';

export interface Project {
  id: string;
  name: string;
  description: string;
  allowed_targets: string[] | null;
  created_at: string;
}

interface ProjectContextType {
  projects: Project[];
  selectedProject: Project | null;
  setSelectedProject: (p: Project) => void;
  createProject: (name: string, description: string, allowedTargets: string[]) => Promise<Project>;
  loading: boolean;
  refresh: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProjectState] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProjects = async () => {
    try {
      const res = await api.get('/projects/');
      const data: Project[] = res.data;
      setProjects(data);
      if (data.length > 0) {
        const savedId = localStorage.getItem('selected_project_id');
        const saved = savedId ? data.find((p) => p.id === savedId) : null;
        setSelectedProjectState(saved ?? data[0]);
      } else {
        setSelectedProjectState(null);
      }
    } catch {
      // Not authenticated yet — ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void fetchProjects(); }, []);

  const setSelectedProject = (p: Project) => {
    setSelectedProjectState(p);
    localStorage.setItem('selected_project_id', p.id);
  };

  const createProject = async (name: string, description: string, allowedTargets: string[]) => {
    const res = await api.post('/projects/', {
      name,
      description,
      allowed_targets: allowedTargets.length > 0 ? allowedTargets : null,
    });
    const created: Project = res.data;
    setProjects((prev) => [...prev, created]);
    setSelectedProject(created);
    return created;
  };

  return (
    <ProjectContext.Provider value={{ projects, selectedProject, setSelectedProject, createProject, loading, refresh: fetchProjects }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error('useProject must be used within ProjectProvider');
  return ctx;
}
