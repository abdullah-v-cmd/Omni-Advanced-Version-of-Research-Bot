'use client'
import { Bell, Search, Moon, Sun } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useState } from 'react'

interface HeaderProps { title?: string }

export function Header({ title }: HeaderProps) {
  const { user } = useAuthStore()
  const [searching, setSearching] = useState(false)

  return (
    <header className="h-16 border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl flex items-center px-6 gap-4 flex-shrink-0">
      <div className="flex-1">
        {title && <h1 className="text-lg font-semibold text-slate-100">{title}</h1>}
      </div>
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className={`flex items-center gap-2 transition-all ${searching ? 'w-64' : 'w-8'}`}>
          <button onClick={() => setSearching(!searching)} className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-all">
            <Search size={16} />
          </button>
          {searching && (
            <input autoFocus onBlur={() => setSearching(false)}
              placeholder="Search..." className="flex-1 bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-600" />
          )}
        </div>
        {/* Notifications */}
        <button className="relative p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-all">
          <Bell size={16} />
          <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-sky-400" />
        </button>
        {/* User Avatar */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 via-violet-500 to-pink-500 flex items-center justify-center text-xs font-bold">
            {(user?.full_name || user?.username || 'U')[0].toUpperCase()}
          </div>
          <div className="hidden md:block">
            <p className="text-xs font-medium text-slate-200 leading-tight">{user?.full_name || user?.username}</p>
            <p className="text-xs text-slate-500 capitalize leading-tight">{user?.role}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
