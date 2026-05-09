'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { researchApi } from '@/lib/api'
import { Plus, BookOpen, Trash2, Edit3, Clock, Tag, Search, Zap, FileText } from 'lucide-react'
import toast from 'react-hot-toast'

interface Session { id: string; title: string; description?: string; topic?: string; status: string; tags?: string[]; version: number; created_at: string }

export default function ResearchPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', topic: '', tags: '' })
  const [aiQuery, setAiQuery] = useState('')
  const [aiResult, setAiResult] = useState('')
  const [querying, setQuerying] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [contentType, setContentType] = useState('abstract')
  const [genTopic, setGenTopic] = useState('')

  useEffect(() => { loadSessions() }, [])

  const loadSessions = async () => {
    try {
      const res = await researchApi.getSessions()
      setSessions(res.data)
    } catch {} finally { setLoading(false) }
  }

  const createSession = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await researchApi.createSession({ ...form, tags: form.tags ? form.tags.split(',').map(t => t.trim()) : [] })
      toast.success('Research session created!')
      setShowCreate(false)
      setForm({ title: '', description: '', topic: '', tags: '' })
      loadSessions()
    } catch { toast.error('Failed to create session') }
  }

  const deleteSession = async (id: string) => {
    if (!confirm('Delete this session?')) return
    try {
      await researchApi.deleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
      toast.success('Session deleted')
    } catch { toast.error('Failed to delete') }
  }

  const runQuery = async () => {
    if (!aiQuery.trim()) return
    setQuerying(true)
    try {
      const res = await researchApi.query({ query: aiQuery, use_hyde: true })
      setAiResult(res.data.answer)
    } catch { toast.error('Query failed') } finally { setQuerying(false) }
  }

  const generateContent = async () => {
    if (!genTopic.trim()) return
    setGenerating(true)
    try {
      const res = await researchApi.generateContent({ content_type: contentType, topic: genTopic })
      setAiResult(res.data.content)
    } catch { toast.error('Generation failed') } finally { setGenerating(false) }
  }

  const statusColor = (s: string) => ({ active: 'text-emerald-400 bg-emerald-500/10', completed: 'text-sky-400 bg-sky-500/10', paused: 'text-amber-400 bg-amber-500/10', archived: 'text-slate-400 bg-slate-500/10' }[s] || 'text-slate-400 bg-slate-500/10')

  return (
    <DashboardLayout title="Research Workspace">
      <div className="max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-100">Research Sessions</h2>
            <p className="text-slate-400 text-sm">{sessions.length} sessions • AI-powered research workspace</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-violet-500 text-sm font-semibold hover:opacity-90 transition-all">
            <Plus size={16} /> New Session
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Query */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Search size={16} className="text-sky-400" />
              <h3 className="font-semibold text-slate-100">HyDE Research Query</h3>
              <span className="text-xs bg-sky-500/20 text-sky-400 px-2 py-0.5 rounded-full">RAG Powered</span>
            </div>
            <textarea value={aiQuery} onChange={e => setAiQuery(e.target.value)} placeholder="Ask a research question... e.g. 'What are the latest advances in transformer architectures?'" rows={3} className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none" />
            <button onClick={runQuery} disabled={querying || !aiQuery.trim()} className="mt-3 w-full py-2 rounded-lg bg-sky-500/20 border border-sky-500/30 text-sky-400 text-sm font-medium hover:bg-sky-500/30 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
              {querying ? <><div className="w-4 h-4 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" />Searching...</> : <><Zap size={14} />Search with HyDE RAG</>}
            </button>
          </div>

          {/* AI Content Generator */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <FileText size={16} className="text-violet-400" />
              <h3 className="font-semibold text-slate-100">AI Content Composer</h3>
            </div>
            <select value={contentType} onChange={e => setContentType(e.target.value)} className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:outline-none focus:border-violet-500 mb-3">
              {['abstract', 'introduction', 'literature review', 'methodology', 'results', 'conclusion'].map(t => <option key={t} value={t} className="bg-slate-800">{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
            <input value={genTopic} onChange={e => setGenTopic(e.target.value)} placeholder="Research topic..." className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500 mb-3" />
            <button onClick={generateContent} disabled={generating || !genTopic.trim()} className="w-full py-2 rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-400 text-sm font-medium hover:bg-violet-500/30 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
              {generating ? <><div className="w-4 h-4 border-2 border-violet-400/30 border-t-violet-400 rounded-full animate-spin" />Generating...</> : <><Zap size={14} />Generate {contentType}</>}
            </button>
          </div>
        </div>

        {/* AI Result */}
        {aiResult && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-100 flex items-center gap-2"><Zap size={16} className="text-sky-400" />AI Response</h3>
              <button onClick={() => { navigator.clipboard.writeText(aiResult); toast.success('Copied!') }} className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 rounded bg-slate-800/50">Copy</button>
            </div>
            <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed bg-slate-800/30 rounded-lg p-4 max-h-64 overflow-y-auto">{aiResult}</div>
          </motion.div>
        )}

        {/* Sessions Grid */}
        <div>
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Your Research Sessions</h3>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array(3).fill(0).map((_, i) => <div key={i} className="glass-card h-40 shimmer" />)}
            </div>
          ) : sessions.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <BookOpen size={40} className="text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 font-medium">No research sessions yet</p>
              <p className="text-slate-500 text-sm mt-1">Create your first session to get started</p>
              <button onClick={() => setShowCreate(true)} className="mt-4 px-4 py-2 rounded-lg bg-sky-500/20 text-sky-400 text-sm border border-sky-500/30 hover:bg-sky-500/30 transition-all">Create Session</button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sessions.map((session, i) => (
                <motion.div key={session.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="glass-card p-5 hover:border-white/15 transition-all group">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-100 truncate">{session.title}</h4>
                      {session.topic && <p className="text-xs text-slate-400 mt-0.5">{session.topic}</p>}
                    </div>
                    <button onClick={() => deleteSession(session.id)} className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-all">
                      <Trash2 size={14} />
                    </button>
                  </div>
                  {session.description && <p className="text-xs text-slate-400 mb-3 line-clamp-2">{session.description}</p>}
                  {session.tags && session.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {session.tags.slice(0, 3).map(tag => <span key={tag} className="text-xs bg-slate-700/50 text-slate-400 px-2 py-0.5 rounded-full">{tag}</span>)}
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(session.status)}`}>{session.status}</span>
                    <span className="text-xs text-slate-500 flex items-center gap-1"><Clock size={10} />{new Date(session.created_at).toLocaleDateString()}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Create Session Modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card p-6 w-full max-w-md">
              <h3 className="text-lg font-bold text-slate-100 mb-4">New Research Session</h3>
              <form onSubmit={createSession} className="space-y-4">
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Session Title *</label>
                  <input value={form.title} onChange={e => setForm({...form, title: e.target.value})} required placeholder="e.g. Deep Learning Survey 2024" className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500" />
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Research Topic</label>
                  <input value={form.topic} onChange={e => setForm({...form, topic: e.target.value})} placeholder="e.g. Machine Learning, NLP..." className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500" />
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Description</label>
                  <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={2} placeholder="Brief description..." className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none" />
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">Tags (comma separated)</label>
                  <input value={form.tags} onChange={e => setForm({...form, tags: e.target.value})} placeholder="AI, NLP, transformers..." className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500" />
                </div>
                <div className="flex gap-3">
                  <button type="button" onClick={() => setShowCreate(false)} className="flex-1 py-2.5 rounded-lg border border-slate-700 text-slate-400 text-sm hover:bg-slate-800 transition-all">Cancel</button>
                  <button type="submit" className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-violet-500 text-white text-sm font-semibold hover:opacity-90 transition-all">Create Session</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
