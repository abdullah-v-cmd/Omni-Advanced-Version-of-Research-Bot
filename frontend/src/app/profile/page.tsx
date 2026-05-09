'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { User, Mail, Building, BookOpen, Globe, Linkedin, Award, Save, Loader2, Camera, Lock } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
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

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'profile' | 'password'>('profile')
  const [profile, setProfile] = useState({
    full_name: user?.full_name || '',
    bio: '', institution: '', department: '', research_interests: '',
    website: '', linkedin_url: '', orcid_id: '', google_scholar_id: '',
  })
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm: '' })
  const [savingPass, setSavingPass] = useState(false)

  useEffect(() => {
    apiFetch('/auth/me').then(data => {
      setProfile(p => ({
        ...p,
        full_name: data.full_name || '',
        bio: data.profile?.bio || '',
        institution: data.profile?.institution || '',
        department: data.profile?.department || '',
        research_interests: data.profile?.research_interests || '',
        website: data.profile?.website || '',
        linkedin_url: data.profile?.linkedin_url || '',
        orcid_id: data.profile?.orcid_id || '',
        google_scholar_id: data.profile?.google_scholar_id || '',
      }))
    }).catch(() => {})
  }, [])

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await apiFetch('/auth/me', { method: 'PUT', body: JSON.stringify({ full_name: profile.full_name }) })
      await apiFetch('/auth/me/profile', {
        method: 'PUT',
        body: JSON.stringify({
          bio: profile.bio, institution: profile.institution,
          department: profile.department, research_interests: profile.research_interests,
          website: profile.website, linkedin_url: profile.linkedin_url,
          orcid_id: profile.orcid_id, google_scholar_id: profile.google_scholar_id,
        })
      })
      updateUser({ full_name: profile.full_name })
      toast.success('Profile updated successfully!')
    } catch (err: any) { toast.error(err.message) } finally { setLoading(false) }
  }

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (passwords.new_password !== passwords.confirm) { toast.error('Passwords do not match'); return }
    if (passwords.new_password.length < 8) { toast.error('Password must be at least 8 characters'); return }
    setSavingPass(true)
    try {
      await apiFetch('/auth/change-password', {
        method: 'PUT',
        body: JSON.stringify({ current_password: passwords.current_password, new_password: passwords.new_password })
      })
      toast.success('Password changed successfully!')
      setPasswords({ current_password: '', new_password: '', confirm: '' })
    } catch (err: any) { toast.error(err.message) } finally { setSavingPass(false) }
  }

  const inputClass = "w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none text-sm"

  return (
    <DashboardLayout title="Profile">
      <div className="max-w-3xl space-y-6">
        {/* Avatar Banner */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-5">
            <div className="relative">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-sky-500 via-violet-500 to-pink-500 flex items-center justify-center text-3xl font-bold">
                {(user?.full_name || user?.username || 'U')[0].toUpperCase()}
              </div>
              <div className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-slate-800 border border-slate-600 flex items-center justify-center cursor-pointer hover:bg-slate-700">
                <Camera size={12} className="text-slate-400" />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">{user?.full_name || user?.username}</h2>
              <p className="text-slate-400 text-sm">{user?.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${user?.role === 'admin' ? 'bg-red-500/10 text-red-400' : 'bg-sky-500/10 text-sky-400'}`}>
                  {user?.role}
                </span>
                {user?.is_superuser && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400">Superuser</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          {(['profile', 'password'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-5 py-2 rounded-lg font-medium capitalize transition-all ${tab === t ? 'bg-sky-500 text-white' : 'glass text-slate-400 hover:text-white'}`}>
              {t === 'password' ? 'Change Password' : 'Edit Profile'}
            </button>
          ))}
        </div>

        {tab === 'profile' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-6">
            <form onSubmit={saveProfile} className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">Full Name</label>
                  <div className="relative">
                    <User size={14} className="absolute left-3 top-3 text-slate-500" />
                    <input value={profile.full_name} onChange={e => setProfile(p => ({ ...p, full_name: e.target.value }))}
                      placeholder="Your full name" className={`${inputClass} pl-9`} />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">Institution</label>
                  <div className="relative">
                    <Building size={14} className="absolute left-3 top-3 text-slate-500" />
                    <input value={profile.institution} onChange={e => setProfile(p => ({ ...p, institution: e.target.value }))}
                      placeholder="University / Organization" className={`${inputClass} pl-9`} />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">Department</label>
                  <input value={profile.department} onChange={e => setProfile(p => ({ ...p, department: e.target.value }))}
                    placeholder="Department / Faculty" className={inputClass} />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">Website</label>
                  <div className="relative">
                    <Globe size={14} className="absolute left-3 top-3 text-slate-500" />
                    <input value={profile.website} onChange={e => setProfile(p => ({ ...p, website: e.target.value }))}
                      placeholder="https://yoursite.com" className={`${inputClass} pl-9`} />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">ORCID ID</label>
                  <div className="relative">
                    <Award size={14} className="absolute left-3 top-3 text-slate-500" />
                    <input value={profile.orcid_id} onChange={e => setProfile(p => ({ ...p, orcid_id: e.target.value }))}
                      placeholder="0000-0000-0000-0000" className={`${inputClass} pl-9`} />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">LinkedIn URL</label>
                  <div className="relative">
                    <Linkedin size={14} className="absolute left-3 top-3 text-slate-500" />
                    <input value={profile.linkedin_url} onChange={e => setProfile(p => ({ ...p, linkedin_url: e.target.value }))}
                      placeholder="linkedin.com/in/username" className={`${inputClass} pl-9`} />
                  </div>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-400 font-medium mb-1 block">Bio</label>
                <textarea value={profile.bio} onChange={e => setProfile(p => ({ ...p, bio: e.target.value }))}
                  placeholder="Tell us about your research..." rows={3}
                  className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none text-sm resize-none" />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-medium mb-1 block">Research Interests</label>
                <input value={profile.research_interests} onChange={e => setProfile(p => ({ ...p, research_interests: e.target.value }))}
                  placeholder="Machine Learning, NLP, Bioinformatics..." className={inputClass} />
              </div>
              <button type="submit" disabled={loading}
                className="flex items-center gap-2 px-6 py-2.5 bg-sky-500 hover:bg-sky-600 rounded-lg font-medium text-white transition-all disabled:opacity-50">
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save Profile
              </button>
            </form>
          </motion.div>
        )}

        {tab === 'password' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card p-6">
            <form onSubmit={changePassword} className="space-y-4 max-w-md">
              {[
                { label: 'Current Password', key: 'current_password' },
                { label: 'New Password', key: 'new_password' },
                { label: 'Confirm New Password', key: 'confirm' },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-xs text-slate-400 font-medium mb-1 block">{f.label}</label>
                  <div className="relative">
                    <Lock size={14} className="absolute left-3 top-3 text-slate-500" />
                    <input type="password" value={(passwords as any)[f.key]}
                      onChange={e => setPasswords(p => ({ ...p, [f.key]: e.target.value }))}
                      className={`${inputClass} pl-9`} required />
                  </div>
                </div>
              ))}
              <button type="submit" disabled={savingPass}
                className="flex items-center gap-2 px-6 py-2.5 bg-sky-500 hover:bg-sky-600 rounded-lg font-medium text-white transition-all disabled:opacity-50">
                {savingPass ? <Loader2 size={14} className="animate-spin" /> : <Lock size={14} />} Change Password
              </button>
            </form>
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  )
}
