'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, Mail, Lock, User, Brain } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import toast from 'react-hot-toast'

const schema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  username: z.string().min(3, 'Username must be at least 3 characters').regex(/^[a-zA-Z0-9_]+$/, 'Only letters, numbers, underscores'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})
type FormData = z.infer<typeof schema>

export default function RegisterPage() {
  const [showPass, setShowPass] = useState(false)
  const { register: registerUser, isLoading } = useAuthStore()
  const router = useRouter()

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    try {
      await registerUser(data.email, data.username, data.password, data.full_name)
      toast.success('Account created! Please sign in.')
      router.push('/auth/login')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen bg-mesh flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500 via-violet-500 to-pink-500 flex items-center justify-center mx-auto mb-4 neon-glow">
            <Brain size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-black gradient-text">OmniSynth</h1>
          <p className="text-slate-400 mt-1">Create Your Research Account</p>
        </div>

        <div className="glass-card p-8">
          <h2 className="text-xl font-bold text-slate-100 mb-6">Get Started Free</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Full Name</label>
              <div className="relative">
                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input {...register('full_name')} placeholder="Dr. Jane Smith" className="w-full bg-slate-800/50 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors" />
              </div>
              {errors.full_name && <p className="text-red-400 text-xs mt-1">{errors.full_name.message}</p>}
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Username</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-sm">@</span>
                <input {...register('username')} placeholder="researcher123" className="w-full bg-slate-800/50 border border-slate-700 rounded-lg pl-8 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors" />
              </div>
              {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Email Address</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input {...register('email')} type="email" placeholder="you@university.edu" className="w-full bg-slate-800/50 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors" />
              </div>
              {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input {...register('password')} type={showPass ? 'text' : 'password'} placeholder="Min 8 characters" className="w-full bg-slate-800/50 border border-slate-700 rounded-lg pl-9 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors" />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{errors.password.message}</p>}
            </div>
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} type="submit" disabled={isLoading} className="w-full py-3 rounded-lg bg-gradient-to-r from-sky-500 to-violet-500 text-white font-semibold text-sm hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
              {isLoading ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Creating Account...</> : 'Create Free Account'}
            </motion.button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">Already have an account?{' '}<Link href="/auth/login" className="text-sky-400 hover:text-sky-300 font-medium">Sign in</Link></p>
          </div>
        </div>
        <div className="text-center mt-4"><Link href="/" className="text-slate-500 text-sm hover:text-slate-300 transition-colors">← Back to Home</Link></div>
      </motion.div>
    </div>
  )
}
