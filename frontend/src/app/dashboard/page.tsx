'use client'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { analyticsApi } from '@/lib/api'
import { BookOpen, FileText, Quote, MessageSquare, FileSearch, TrendingUp, Zap, Users, Award } from 'lucide-react'
import Link from 'next/link'
import { useAuthStore } from '@/store/authStore'

interface DashboardData {
  overview: any
  productivity: any
  recent_logs: any[]
}

const quickActions = [
  { href: '/chat', label: 'Start AI Chat', icon: MessageSquare, color: 'from-sky-500 to-blue-600', desc: 'Ask research questions' },
  { href: '/research', label: 'New Research', icon: BookOpen, color: 'from-violet-500 to-purple-600', desc: 'Start a research session' },
  { href: '/plagiarism', label: 'Check Plagiarism', icon: FileSearch, color: 'from-pink-500 to-rose-600', desc: 'AI originality check' },
  { href: '/citations', label: 'Generate Citation', icon: Quote, color: 'from-amber-500 to-orange-600', desc: 'APA, MLA, IEEE & more' },
]

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const { user } = useAuthStore()

  useEffect(() => {
    analyticsApi.getDashboard()
      .then(res => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const stats = data ? [
    { label: 'Research Sessions', value: data.overview?.total_sessions || 0, icon: BookOpen, color: 'text-sky-400', bg: 'bg-sky-500/10' },
    { label: 'Documents Processed', value: data.overview?.total_documents || 0, icon: FileText, color: 'text-violet-400', bg: 'bg-violet-500/10' },
    { label: 'Citations Generated', value: data.overview?.total_citations || 0, icon: Quote, color: 'text-pink-400', bg: 'bg-pink-500/10' },
    { label: 'AI Conversations', value: data.overview?.total_conversations || 0, icon: MessageSquare, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ] : []

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-6 max-w-7xl">
        {/* Welcome Banner */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 bg-gradient-to-r from-sky-500/10 via-violet-500/10 to-pink-500/10 border border-sky-500/20"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-100">
                Welcome back, {user?.full_name?.split(' ')[0] || user?.username || 'Researcher'}! 👋
              </h2>
              <p className="text-slate-400 mt-1">Your AI research platform is ready. What are we discovering today?</p>
            </div>
            <div className="hidden md:flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 text-sm font-medium">AI Systems Online</span>
            </div>
          </div>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {loading ? (
            Array(4).fill(0).map((_, i) => (
              <div key={i} className="glass-card p-5 shimmer h-24" />
            ))
          ) : (
            stats.map((stat, i) => {
              const Icon = stat.icon
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="glass-card p-5 hover:border-white/15 transition-all"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-9 h-9 rounded-lg ${stat.bg} flex items-center justify-center`}>
                      <Icon size={18} className={stat.color} />
                    </div>
                  </div>
                  <div className={`text-3xl font-black ${stat.color}`}>{stat.value}</div>
                  <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
                </motion.div>
              )
            })
          )}
        </div>

        {/* Productivity Score */}
        {data && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Award size={20} className="text-amber-400" />
                <h3 className="font-semibold text-slate-100">Productivity Score</h3>
              </div>
              <span className="text-amber-400 font-bold text-lg">{data.productivity?.score || 0}/100</span>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${data.productivity?.score || 0}%` }}
                transition={{ duration: 1, delay: 0.5 }}
                className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
              />
            </div>
            <div className="flex justify-between mt-2 text-xs text-slate-500">
              <span>Level: {data.productivity?.level || 'Beginner'}</span>
              <span>Keep researching to level up!</span>
            </div>
          </motion.div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Actions */}
          <div className="lg:col-span-2">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Actions</h3>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((action, i) => {
                const Icon = action.icon
                return (
                  <Link key={i} href={action.href}>
                    <motion.div
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      className="glass-card p-4 cursor-pointer hover:border-white/15 transition-all group"
                    >
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                        <Icon size={18} className="text-white" />
                      </div>
                      <div className="font-semibold text-slate-100 text-sm">{action.label}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{action.desc}</div>
                    </motion.div>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Recent Activity */}
          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Recent Activity</h3>
            <div className="glass-card p-4 space-y-3">
              {data?.recent_logs?.length ? (
                data.recent_logs.slice(0, 5).map((log: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 py-2 border-b border-slate-700/30 last:border-0">
                    <div className="w-2 h-2 rounded-full bg-sky-400 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-slate-300 capitalize">{log.action?.replace(/_/g, ' ')}</p>
                      <p className="text-xs text-slate-500">{new Date(log.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Zap size={24} className="mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No recent activity</p>
                  <p className="text-xs">Start a research session!</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
