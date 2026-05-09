'use client'
import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Users, Plus, Globe, Lock, MessageSquare, Trash2, Settings, Bell, Loader2, Send } from 'lucide-react'
import toast from 'react-hot-toast'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

const apiFetch = async (path: string, opts: RequestInit = {}) => {
  const res = await fetch(`${API}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json', ...((opts.headers as any) || {}) },
    ...opts,
  })
  if (!res.ok) throw new Error((await res.json()).detail || 'Error')
  return res.json()
}

export default function CollaborationPage() {
  const [workspaces, setWorkspaces] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', is_public: false })
  const [creating, setCreating] = useState(false)
  const [selected, setSelected] = useState<any>(null)
  const [comments, setComments] = useState<any[]>([])
  const [newComment, setNewComment] = useState('')
  const [sendingComment, setSendingComment] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => { loadWorkspaces() }, [])

  const loadWorkspaces = async () => {
    try { setWorkspaces(await apiFetch('/collaboration/workspaces')) } catch {} finally { setLoading(false) }
  }

  const createWorkspace = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      const ws = await apiFetch('/collaboration/workspaces', { method: 'POST', body: JSON.stringify(form) })
      setWorkspaces(prev => [ws, ...prev])
      setShowCreate(false)
      setForm({ name: '', description: '', is_public: false })
      toast.success('Workspace created!')
    } catch (err: any) { toast.error(err.message) } finally { setCreating(false) }
  }

  const selectWorkspace = async (ws: any) => {
    setSelected(ws)
    try {
      const comms = await apiFetch(`/collaboration/workspaces/${ws.id}/comments`)
      setComments(comms)
    } catch {}
    // Connect WebSocket
    if (wsRef.current) wsRef.current.close()
    const token = getToken()
    const wsUrl = `${API.replace('http', 'ws')}/api/v1/collaboration/ws/${ws.id}?token=${token}`
    try {
      wsRef.current = new WebSocket(wsUrl)
      wsRef.current.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.type === 'comment') {
          setComments(prev => [...prev, msg.data])
        }
      }
    } catch {}
  }

  const sendComment = async () => {
    if (!newComment.trim() || !selected) return
    setSendingComment(true)
    try {
      const comment = await apiFetch(`/collaboration/workspaces/${selected.id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ content: newComment })
      })
      setComments(prev => [...prev, comment])
      setNewComment('')
    } catch { toast.error('Failed to send') } finally { setSendingComment(false) }
  }

  const deleteWorkspace = async (id: string) => {
    if (!confirm('Delete this workspace?')) return
    try {
      await apiFetch(`/collaboration/workspaces/${id}`, { method: 'DELETE' })
      setWorkspaces(prev => prev.filter(w => w.id !== id))
      if (selected?.id === id) setSelected(null)
      toast.success('Deleted')
    } catch { toast.error('Failed to delete') }
  }

  return (
    <DashboardLayout title="Collaboration Workspaces">
      <div className="max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-slate-400">Real-time collaborative research workspaces</p>
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white font-medium transition-all">
            <Plus size={16} /> New Workspace
          </button>
        </div>

        {showCreate && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6">
            <h3 className="font-semibold mb-4">Create Workspace</h3>
            <form onSubmit={createWorkspace} className="space-y-4">
              <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                placeholder="Workspace name" required
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none" />
              <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                placeholder="Description (optional)" rows={2}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none resize-none" />
              <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                <input type="checkbox" checked={form.is_public} onChange={e => setForm(p => ({ ...p, is_public: e.target.checked }))} />
                Public workspace
              </label>
              <div className="flex gap-3">
                <button type="submit" disabled={creating}
                  className="flex items-center gap-2 px-5 py-2 bg-sky-500 hover:bg-sky-600 rounded-lg font-medium text-white">
                  {creating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Create
                </button>
                <button type="button" onClick={() => setShowCreate(false)} className="px-5 py-2 glass rounded-lg text-slate-400 hover:text-white">Cancel</button>
              </div>
            </form>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Workspace List */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">Your Workspaces</h3>
            {loading ? (
              <div className="flex justify-center py-8"><Loader2 className="animate-spin text-sky-400" size={24} /></div>
            ) : workspaces.length === 0 ? (
              <div className="text-center py-10 text-slate-500 glass-card">
                <Users size={32} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">No workspaces yet</p>
              </div>
            ) : (
              workspaces.map(ws => (
                <motion.div key={ws.id} whileHover={{ x: 2 }}
                  className={`glass-card p-4 cursor-pointer transition-all ${selected?.id === ws.id ? 'border-sky-500/50 bg-sky-500/5' : 'hover:border-white/15'}`}
                  onClick={() => selectWorkspace(ws)}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {ws.is_public ? <Globe size={13} className="text-emerald-400" /> : <Lock size={13} className="text-slate-500" />}
                        <p className="font-medium text-slate-200 truncate">{ws.name}</p>
                      </div>
                      {ws.description && <p className="text-xs text-slate-500 mt-1 truncate">{ws.description}</p>}
                    </div>
                    <button onClick={e => { e.stopPropagation(); deleteWorkspace(ws.id) }}
                      className="p-1 rounded hover:bg-red-500/10 hover:text-red-400 text-slate-600 transition-all">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </div>

          {/* Workspace Chat / Detail */}
          <div className="lg:col-span-2">
            {selected ? (
              <div className="glass-card h-[500px] flex flex-col">
                <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
                  <div>
                    <h3 className="font-semibold">{selected.name}</h3>
                    <p className="text-xs text-slate-500">Real-time collaboration</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-xs text-emerald-400">Live</span>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {comments.length === 0 ? (
                    <div className="text-center py-8 text-slate-600">
                      <MessageSquare size={32} className="mx-auto mb-2 opacity-30" />
                      <p className="text-sm">No messages yet. Start the conversation!</p>
                    </div>
                  ) : (
                    comments.map((c, i) => (
                      <div key={i} className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {(c.author || 'U')[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-baseline gap-2">
                            <span className="text-xs font-medium text-sky-400">{c.author || 'User'}</span>
                            <span className="text-xs text-slate-600">{c.created_at ? new Date(c.created_at).toLocaleTimeString() : ''}</span>
                          </div>
                          <p className="text-sm text-slate-300 mt-0.5">{c.content}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <div className="p-4 border-t border-slate-700/50 flex gap-3">
                  <input value={newComment} onChange={e => setNewComment(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendComment()}
                    placeholder="Type a message..."
                    className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-slate-100 text-sm focus:border-sky-500 focus:outline-none" />
                  <button onClick={sendComment} disabled={sendingComment || !newComment.trim()}
                    className="p-2 rounded-lg bg-sky-500 hover:bg-sky-600 disabled:opacity-50 transition-all">
                    {sendingComment ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  </button>
                </div>
              </div>
            ) : (
              <div className="glass-card h-[500px] flex items-center justify-center text-center text-slate-500">
                <div>
                  <Users size={48} className="mx-auto mb-3 opacity-20" />
                  <p>Select a workspace to start collaborating</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
