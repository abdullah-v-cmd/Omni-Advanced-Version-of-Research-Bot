'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, MessageSquare, BookOpen, BarChart3,
  Quote, FileSearch, Users, Settings, User, Shield,
  Cpu, ChevronLeft, ChevronRight, LogOut
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/chat', label: 'OmniChat', icon: MessageSquare },
  { href: '/research', label: 'Research', icon: BookOpen },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/citations', label: 'Citations', icon: Quote },
  { href: '/plagiarism', label: 'Plagiarism', icon: FileSearch },
  { href: '/ocr', label: 'OCR Upload', icon: Cpu },
  { href: '/collaboration', label: 'Collaboration', icon: Users },
  { href: '/profile', label: 'Profile', icon: User },
  { href: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, clearAuth } = useAuthStore()
  const router = useRouter()
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = () => {
    clearAuth()
    toast.success('Logged out successfully')
    router.push('/auth/login')
  }

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/')

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="relative flex flex-col h-screen bg-slate-900/95 border-r border-slate-700/50 backdrop-blur-xl z-50 flex-shrink-0"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700/50">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 via-violet-500 to-pink-500 flex items-center justify-center flex-shrink-0 neon-glow">
          <span className="text-white font-bold text-sm">OS</span>
        </div>
        {!collapsed && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
            <span className="font-bold text-lg gradient-text">OmniSynth</span>
            <p className="text-xs text-slate-500">AI Research Platform</p>
          </motion.div>
        )}
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center hover:bg-slate-600 transition-all z-10"
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto scrollbar-hide">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 2 }}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer group ${
                  active
                    ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-white/5'
                }`}
              >
                <Icon size={18} className={`flex-shrink-0 ${active ? 'text-sky-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.05 }}
                    className="text-sm font-medium"
                  >
                    {item.label}
                  </motion.span>
                )}
                {!collapsed && active && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-sky-400" />
                )}
              </motion.div>
            </Link>
          )
        })}

        {/* Admin link */}
        {(user?.is_superuser || user?.role === 'admin') && (
          <Link href="/admin">
            <motion.div
              whileHover={{ x: 2 }}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer group mt-2 ${
                isActive('/admin')
                  ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                  : 'text-slate-400 hover:text-red-400 hover:bg-red-500/5'
              }`}
            >
              <Shield size={18} className="flex-shrink-0" />
              {!collapsed && <span className="text-sm font-medium">Admin Panel</span>}
            </motion.div>
          </Link>
        )}
      </nav>

      {/* User section */}
      <div className="border-t border-slate-700/50 p-3">
        <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center text-xs font-bold flex-shrink-0">
            {(user?.full_name || user?.username || 'U')[0].toUpperCase()}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">{user?.full_name || user?.username}</p>
              <p className="text-xs text-slate-500 capitalize truncate">{user?.role}</p>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all flex-shrink-0"
            title="Logout"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </motion.aside>
  )
}
