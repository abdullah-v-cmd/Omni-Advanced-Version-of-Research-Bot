'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Shield, Users, BarChart3, FileText, Trash2, Edit3, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
const apiFetch = async (path: string, opts: RequestInit = {}) => {
  const res = await fetch(`${API}/api/v1${path}`, {
    headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) throw new Error((await res.json()).detail || 'Error')
  return res.json()
}

export default function AdminPage() {
  const { user } = useAuthStore()
  const [tab, setTab] = useState<'users' | 'stats' | 'logs'>('users')
  const [users, setUsers] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  if (!user?.is_superuser && user?.role !== 'admin') {
    return (
      <DashboardLayout title="Admin">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Shield size={48} className="text-red-400 mx-auto mb-3" />
            <h2 className="text-xl font-bold text-red-400">Access Denied</h2>
            <p className="text-slate-500 mt-2">You need admin privileges to access this page.</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  const loadData = async (t = tab) => {
    setLoading(true)
    try {
      if (t === 'users') setUsers(await apiFetch('/admin/users'))
      else if (t === 'stats') setStats(await apiFetch('/admin/stats'))
      else if (t === 'logs') setLogs(await apiFetch('/admin/logs'))
    } catch (e: any) { toast.error(e.message) } finally { setLoading(false) }
  }

  useEffect(() => { loadData(tab) }, [tab])

  const deleteUser = async (id: string) => {
    if (!confirm('Delete this user? This is irreversible.')) return
    try {
      await apiFetch(`/admin/users/${id}`, { method: 'DELETE' })
      setUsers(prev => prev.filter(u => u.id !== id))
      toast.success('User deleted')
    } catch (e: any) { toast.error(e.message) }
  }

  const updateRole = async (id: string, role: string) => {
    try {
      await apiFetch(`/admin/users/${id}`, { method: 'PUT', body: JSON.stringify({ role }) })
      setUsers(prev => prev.map(u => u.id === id ? { ...u, role } : u))
      toast.success('Role updated')
    } catch (e: any) { toast.error(e.message) }
  }

  const roleColor: Record<string, string> = {
    admin: 'text-red-400 bg-red-500/10',
    researcher: 'text-sky-400 bg-sky-500/10',
    collaborator: 'text-emerald-400 bg-emerald-500/10',
    viewer: 'text-slate-400 bg-slate-500/10',
  }

  return (
    <DashboardLayout title="Admin Panel">
      <div className="max-w-6xl space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <Shield size={16} className="text-red-400" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-100">System Administration</h2>
            <p className="text-xs text-slate-500">Full system control and user management</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          {(['users', 'stats', 'logs'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-lg font-medium capitalize transition-all ${tab === t ? 'bg-sky-500 text-white' : 'glass text-slate-400 hover:text-white'}`}>
              {t === 'stats' ? 'System Stats' : t === 'logs' ? 'System Logs' : 'Users'}
            </button>
          ))}
          <button onClick={() => loadData(tab)} className="ml-auto p-2 glass rounded-lg text-slate-400 hover:text-white transition-all">
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {/* Users Tab */}
        {tab === 'users' && (
          <div className="glass-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">User</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Role</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Status</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Joined</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td colSpan={5} className="text-center py-10"><Loader2 className="animate-spin text-sky-400 mx-auto" size={24} /></td></tr>
                  ) : users.length === 0 ? (
                    <tr><td colSpan={5} className="text-center py-10 text-slate-500">No users found</td></tr>
                  ) : users.map(u => (
                    <tr key={u.id} className="border-b border-slate-800/50 hover:bg-white/2 transition-all">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center text-xs font-bold">
                            {(u.full_name || u.username || 'U')[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-slate-200">{u.full_name || u.username}</p>
                            <p className="text-xs text-slate-500">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <select value={u.role} onChange={e => updateRole(u.id, e.target.value)}
                          className={`text-xs px-2 py-1 rounded-full border-0 cursor-pointer ${roleColor[u.role] || roleColor.viewer}`}
                          style={{ background: 'transparent' }}>
                          {['admin', 'researcher', 'collaborator', 'viewer'].map(r => (
                            <option key={r} value={r} style={{ background: '#1e293b' }}>{r}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1 text-xs ${u.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                          {u.is_active ? <CheckCircle size={12} /> : <XCircle size={12} />}
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => deleteUser(u.id)}
                          className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all">
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stats Tab */}
        {tab === 'stats' && (
          <div>
            {loading ? (
              <div className="flex justify-center py-16"><Loader2 className="animate-spin text-sky-400" size={28} /></div>
            ) : stats ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(stats).map(([key, val]) => (
                  <div key={key} className="glass-card p-5">
                    <p className="text-xs text-slate-500 uppercase font-medium">{key.replace(/_/g, ' ')}</p>
                    <p className="text-3xl font-bold gradient-text mt-1">{String(val)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">No stats available</div>
            )}
          </div>
        )}

        {/* Logs Tab */}
        {tab === 'logs' && (
          <div className="glass-card overflow-hidden">
            {loading ? (
              <div className="flex justify-center py-10"><Loader2 className="animate-spin text-sky-400" size={24} /></div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-700/50">
                      <th className="text-left px-4 py-3 text-slate-500 uppercase">Level</th>
                      <th className="text-left px-4 py-3 text-slate-500 uppercase">Message</th>
                      <th className="text-left px-4 py-3 text-slate-500 uppercase">Service</th>
                      <th className="text-left px-4 py-3 text-slate-500 uppercase">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 ? (
                      <tr><td colSpan={4} className="text-center py-8 text-slate-500">No logs</td></tr>
                    ) : logs.map((log, i) => (
                      <tr key={i} className="border-b border-slate-800/30 hover:bg-white/2">
                        <td className="px-4 py-2">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                            log.level === 'ERROR' ? 'bg-red-500/10 text-red-400' :
                            log.level === 'WARNING' ? 'bg-amber-500/10 text-amber-400' :
                            'bg-emerald-500/10 text-emerald-400'}`}>
                            {log.level}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-slate-300 max-w-sm truncate">{log.message}</td>
                        <td className="px-4 py-2 text-slate-500">{log.service || '-'}</td>
                        <td className="px-4 py-2 text-slate-500">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
