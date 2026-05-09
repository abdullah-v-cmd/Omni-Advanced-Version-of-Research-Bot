/**
 * OmniSynth - Global TypeScript Types
 */

export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  role: 'admin' | 'researcher' | 'collaborator' | 'viewer'
  status: string
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  created_at: string
  last_login?: string
  profile?: UserProfile
}

export interface UserProfile {
  id: string
  bio?: string
  institution?: string
  department?: string
  research_interests?: string
  website?: string
  linkedin_url?: string
  orcid_id?: string
  google_scholar_id?: string
  total_research_hours?: number
  total_documents?: number
  total_citations?: number
}

export interface ResearchSession {
  id: string
  title: string
  description?: string
  topic?: string
  status: 'active' | 'completed' | 'archived' | 'paused'
  tags?: string[]
  version: number
  created_at: string
  updated_at?: string
}

export interface Document {
  id: string
  title: string
  filename?: string
  doc_type: string
  status: string
  word_count?: number
  page_count?: number
  is_indexed: boolean
  summary?: string
  keywords?: string[]
  extracted_text?: string
  created_at: string
}

export interface Draft {
  id: string
  title: string
  content?: string
  draft_type?: string
  version: number
  word_count: number
  is_ai_generated: boolean
  created_at: string
  updated_at?: string
}

export interface Citation {
  id: string
  style: string
  formatted_text: string
  bibtex?: string
  is_validated: boolean
  created_at: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  agent?: string
  sources?: any[]
}

export interface Conversation {
  id: string
  title: string
  model_used?: string
  message_count: number
  created_at: string
  updated_at?: string
}

export interface Workspace {
  id: string
  name: string
  description?: string
  owner_id: string
  is_public: boolean
  member_count?: number
  created_at: string
}

export interface PlagiarismReport {
  id: string
  overall_score: number
  plagiarism_percentage: number
  originality_percentage: number
  matches?: Match[]
  risk_level: 'low' | 'medium' | 'high'
  status: string
  created_at: string
}

export interface Match {
  text: string
  similarity: number
  source?: string
  type: string
}

export interface AnalyticsDashboard {
  summary: {
    total_sessions: number
    total_documents: number
    total_drafts: number
    total_citations: number
    total_ai_conversations: number
    total_plagiarism_checks: number
    productivity_score: number
  }
  recent_activity: {
    sessions_last_7_days: number
    documents_last_7_days: number
  }
  recent_sessions: ResearchSession[]
  charts: any
}

export interface ApiResponse<T> {
  data: T
  message?: string
  status: string
}
