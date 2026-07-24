export interface AnalyzeRequest {
  user_name: string;
  phone: string;
  email: string;
  description: string;
}

export interface AnalyzeResponse {
  analysis_id: string;
  status: 'running' | 'done' | 'failed';
}

export interface RoadmapNode {
  id: string;
  name: string;
  type: string;
  category: string;
  level: string;
  importance: number;
  description?: string;
  aliases: string[];
  content_guidance: Record<string, unknown>;
}

export interface LevelResume {
  summary: string;
  strong_points: string[];
  weak_points: string[];
  estimated_level: string;
}

export interface AgentProgressEvent {
  node: string;
  status: 'started' | 'completed' | 'failed';
  message?: string;
  payload?: Record<string, unknown>;
}

export interface AnalyzeResult {
  level_resume: LevelResume;
  compatibility_score: number;
  personalized_roadmap: RoadmapNode[];
}
