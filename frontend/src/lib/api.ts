/**
 * OmniSynth - Complete API Client
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 60000,
      headers: { 'Content-Type': 'application/json' },
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (typeof window !== 'undefined') {
          const token = localStorage.getItem('access_token')
          if (token && config.headers) config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
          const refreshToken = localStorage.getItem('refresh_token')
          if (refreshToken) {
            try {
              const { data } = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, { refresh_token: refreshToken })
              localStorage.setItem('access_token', data.access_token)
              localStorage.setItem('refresh_token', data.refresh_token)
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${data.access_token}`
                return this.client.request(error.config)
              }
            } catch {
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              window.location.href = '/auth/login'
            }
          }
        }
        return Promise.reject(error)
      }
    )
  }

  get http() { return this.client }
}

const apiClient = new ApiClient()
const http = apiClient.http

// ─── Auth ───────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    http.post('/auth/login', { email, password }),
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    http.post('/auth/register', data),
  me: () => http.get('/auth/me'),
  updateMe: (data: any) => http.put('/auth/me', data),
  updateProfile: (data: any) => http.put('/auth/me/profile', data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    http.put('/auth/change-password', data),
  refresh: (refresh_token: string) => http.post('/auth/refresh', { refresh_token }),
  logout: () => http.post('/auth/logout'),
}

// ─── Chat ───────────────────────────────────────────────────────────
export const chatApi = {
  send: (data: { message: string; conversation_id?: string; use_hyde?: boolean; agent_type?: string }) =>
    http.post('/chat/send', data),
  getConversations: (skip = 0, limit = 20) =>
    http.get(`/chat/conversations?skip=${skip}&limit=${limit}`),
  getConversation: (id: string) => http.get(`/chat/conversations/${id}`),
  deleteConversation: (id: string) => http.delete(`/chat/conversations/${id}`),
  getAgents: () => http.get('/chat/agents'),
  stream: (message: string, conversation_id?: string) =>
    `${API_BASE_URL}/api/v1/chat/stream?message=${encodeURIComponent(message)}${conversation_id ? `&conversation_id=${conversation_id}` : ''}`,
}

// ─── Research ───────────────────────────────────────────────────────
export const researchApi = {
  getSessions: (skip = 0, limit = 20) =>
    http.get(`/research/sessions?skip=${skip}&limit=${limit}`),
  createSession: (data: any) => http.post('/research/sessions', data),
  getSession: (id: string) => http.get(`/research/sessions/${id}`),
  updateSession: (id: string, data: any) => http.put(`/research/sessions/${id}`, data),
  deleteSession: (id: string) => http.delete(`/research/sessions/${id}`),
  query: (data: { query: string; session_id?: string; use_hyde?: boolean; top_k?: number }) =>
    http.post('/research/query', data),
  uploadDocument: (sessionId: string, formData: FormData) =>
    http.post(`/research/sessions/${sessionId}/documents`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getDocuments: (sessionId: string) => http.get(`/research/sessions/${sessionId}/documents`),
  getDrafts: (sessionId: string) => http.get(`/research/sessions/${sessionId}/drafts`),
  createDraft: (sessionId: string, data: any) => http.post(`/research/sessions/${sessionId}/drafts`, data),
  updateDraft: (sessionId: string, draftId: string, data: any) =>
    http.put(`/research/sessions/${sessionId}/drafts/${draftId}`, data),
  generateContent: (data: { content_type: string; topic: string; context?: string; word_limit?: number }) =>
    http.post('/research/generate-content', data),
}

// ─── Citations ──────────────────────────────────────────────────────
export const citationsApi = {
  generate: (data: any) => http.post('/citations/generate', data),
  generateAll: (data: any) => http.post('/citations/generate-all', data),
  extractFromText: (data: { text: string }) => http.post('/citations/extract-from-text', data),
  list: (skip = 0, limit = 50) => http.get(`/citations/?skip=${skip}&limit=${limit}`),
  delete: (id: string) => http.delete(`/citations/${id}`),
  styles: () => http.get('/citations/styles'),
}

// ─── Plagiarism ─────────────────────────────────────────────────────
export const plagiarismApi = {
  check: (data: { text: string }) => http.post('/plagiarism/check', data),
  checkFile: (formData: FormData) =>
    http.post('/plagiarism/check-file', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getReport: (id: string) => http.get(`/plagiarism/reports/${id}`),
  getReports: (skip = 0, limit = 20) => http.get(`/plagiarism/reports?skip=${skip}&limit=${limit}`),
}

// ─── OCR ────────────────────────────────────────────────────────────
export const ocrApi = {
  upload: (formData: FormData) =>
    http.post('/ocr/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  extractText: (formData: FormData) =>
    http.post('/ocr/extract-text', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getDocuments: (skip = 0, limit = 20) => http.get(`/ocr/documents?skip=${skip}&limit=${limit}`),
  getDocument: (id: string) => http.get(`/ocr/documents/${id}`),
  deleteDocument: (id: string) => http.delete(`/ocr/documents/${id}`),
}

// ─── Analytics ──────────────────────────────────────────────────────
export const analyticsApi = {
  getDashboard: () => http.get('/analytics/dashboard'),
  getActivity: (skip = 0, limit = 50) => http.get(`/analytics/activity?skip=${skip}&limit=${limit}`),
  getProductivity: (days = 30) => http.get(`/analytics/productivity?days=${days}`),
  getRecommendations: () => http.get('/analytics/recommendations'),
}

// ─── Collaboration ───────────────────────────────────────────────────
export const collaborationApi = {
  getWorkspaces: () => http.get('/collaboration/workspaces'),
  createWorkspace: (data: { name: string; description?: string; is_public?: boolean }) =>
    http.post('/collaboration/workspaces', data),
  getWorkspace: (id: string) => http.get(`/collaboration/workspaces/${id}`),
  deleteWorkspace: (id: string) => http.delete(`/collaboration/workspaces/${id}`),
  addMember: (workspaceId: string, userId: string, role?: string) =>
    http.post(`/collaboration/workspaces/${workspaceId}/members`, { user_id: userId, role }),
  removeMember: (workspaceId: string, userId: string) =>
    http.delete(`/collaboration/workspaces/${workspaceId}/members/${userId}`),
  getComments: (workspaceId: string) =>
    http.get(`/collaboration/workspaces/${workspaceId}/comments`),
  addComment: (workspaceId: string, content: string) =>
    http.post(`/collaboration/workspaces/${workspaceId}/comments`, { content }),
  getNotifications: () => http.get('/collaboration/notifications'),
  markNotificationRead: (id: string) =>
    http.patch(`/collaboration/notifications/${id}/read`),
}

// ─── Admin ──────────────────────────────────────────────────────────
export const adminApi = {
  getUsers: (skip = 0, limit = 50) => http.get(`/admin/users?skip=${skip}&limit=${limit}`),
  updateUser: (id: string, data: any) => http.patch(`/admin/users/${id}`, data),
  deleteUser: (id: string) => http.delete(`/admin/users/${id}`),
  getStats: () => http.get('/admin/stats'),
  getLogs: (level?: string) => http.get(`/admin/logs${level ? `?level=${level}` : ''}`),
}

export default apiClient
