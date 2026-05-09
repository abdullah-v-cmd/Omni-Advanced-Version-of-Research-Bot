'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { BarChart3, TrendingUp, BookOpen, FileText, Quote, MessageSquare, FileSearch, Zap, Award, RefreshCw, Loader2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null)
  const [productivity, setProductivity] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState(30)

  const load = async () => {
    setLoading(true)
    try {
      const [dash, prod] = await Promise.all([
        fetch(`${API}/api/v1/analytics/dashboard`, { headers: { Authorization: `Bearer ${getToken()}` } }).then(r => r.json()),
        fetch(`${API}/api/v1/analytics/productivity?days=${period}`, { headers: { Authorization: `Bearer ${getToken()}` } }).then(r => r.json()),
      ])
      setData(dash)
      setProductivity(prod)
    } catch {} finally { setLoading(false) }
  }

  useEffect(() => { load() }, [period])

  const stats = data?.summary ? [
    { label: 'Research Sessions', value: data.summary.total_sessions, icon: BookOpen, color: 'text-sky-400', bg: 'bg-sky-500/10' },
    { label: 'Documents Processed', value: data.summary.total_documents, icon: FileText, color: 'text-violet-400', bg: 'bg-violet-500/10' },
    { label: 'AI Conversations', value: data.summary.total_ai_conversations, icon: MessageSquare, color: 'text-pink-400', bg: 'bg-pink-500/10' },
    { label: 'Citations Generated', value: data.summary.total_citations, icon: Quote, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'Plagiarism Checks', value: data.summary.total_plagiarism_checks, icon: FileSearch, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Drafts Created', value: data.summary.total_drafts, icon: FileText, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  ] : []

  const COLORS = ['#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']

  const pieData = data?.summary ? [
    { name: 'Sessions', value: data.summary.total_sessions || 1 },
    { name: 'Documents', value: data.summary.total_documents || 0 },
    { name: 'Citations', value: data.summary.total_citations || 0 },
    { name: 'Chats', value: data.summary.total_ai_conversations || 0 },
    { name: 'Drafts', value: data.summary.total_drafts || 0 },
  ] : []

  return (
    <DashboardLayout title="Analytics">
      <div className="max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <p className="text-slate-400">Track your research productivity and AI usage</p>
          <div className="flex gap-2">
            {[7, 30, 90].map(d => (
              <button key={d} onClick={() => setPeriod(d)}
                className={`px-3 py-1.5 rounded-lg text-sm transition-all ${period === d ? 'bg-sky-500 text-white' : 'glass text-slate-400 hover:text-white'}`}>
                {d}d
              </button>
            ))}
            <button onClick={load} className="p-2 glass rounded-lg text-slate-400 hover:text-white">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="animate-spin text-sky-400" size={32} /></div>
        ) : (
          <>
            {/* Productivity Score */}
            {data?.summary?.productivity_score !== undefined && (
              <div className="glass-card p-6 bg-gradient-to-r from-sky-500/10 via-violet-500/10 to-pink-500/10 border border-sky-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Overall Productivity Score</p>
                    <div className="flex items-end gap-3">
                      <span className="text-5xl font-black gradient-text">{data.summary.productivity_score}</span>
                      <span className="text-slate-400 mb-1">/100</span>
                    </div>
                  </div>
                  <Award size={48} className="text-amber-400 opacity-60" />
                </div>
                <div className="mt-4 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${data.summary.productivity_score}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                    className="h-full bg-gradient-to-r from-sky-500 via-violet-500 to-pink-500 rounded-full" />
                </div>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {stats.map((s, i) => {
                const Icon = s.icon
                return (
                  <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                    className="glass-card p-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-lg ${s.bg} flex items-center justify-center`}>
                        <Icon size={16} className={s.color} />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-slate-100">{s.value}</p>
                        <p className="text-xs text-slate-500">{s.label}</p>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Weekly Activity Chart */}
              {data?.charts?.weekly_activity && (
                <div className="glass-card p-6">
                  <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <BarChart3 size={16} className="text-sky-400" /> Weekly Activity
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={data.charts.weekly_activity}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }} />
                      <Bar dataKey="sessions" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="documents" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Pie Chart */}
              {pieData.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <TrendingUp size={16} className="text-violet-400" /> Activity Breakdown
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                        {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-3 justify-center mt-2">
                    {pieData.map((d, i) => (
                      <div key={i} className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                        <span className="text-xs text-slate-400">{d.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Insights */}
            {productivity?.insights && (
              <div className="glass-card p-6">
                <h3 className="font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <Zap size={16} className="text-amber-400" /> AI Insights
                </h3>
                <div className="space-y-3">
                  {productivity.insights.map((insight: string, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-amber-500/5 border border-amber-500/10 rounded-lg">
                      <Zap size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-slate-300">{insight}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Sessions */}
            {data?.recent_sessions && data.recent_sessions.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="font-semibold text-slate-200 mb-4">Recent Research Sessions</h3>
                <div className="space-y-2">
                  {data.recent_sessions.map((s: any) => (
                    <div key={s.id} className="flex items-center justify-between p-3 glass rounded-lg">
                      <div className="flex items-center gap-3">
                        <BookOpen size={14} className="text-sky-400" />
                        <span className="text-sm text-slate-300">{s.title}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          s.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'}`}>
                          {s.status}
                        </span>
                        <span className="text-xs text-slate-600">{new Date(s.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
