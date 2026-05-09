'use client'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { ArrowRight, Brain, Zap, Shield, BarChart3, FileSearch, Quote, BookOpen, Users, Cpu } from 'lucide-react'

const features = [
  { icon: Brain, title: 'HyDE-Enhanced RAG', desc: 'Hypothetical Document Embedding for superior semantic retrieval accuracy', color: 'from-sky-500 to-blue-600' },
  { icon: Zap, title: 'Multi-Agent AI', desc: 'LangGraph-orchestrated specialized agents for every research task', color: 'from-violet-500 to-purple-600' },
  { icon: FileSearch, title: 'Plagiarism Detection', desc: 'Free AI-powered semantic plagiarism detection with detailed reports', color: 'from-pink-500 to-rose-600' },
  { icon: Cpu, title: 'OCR Analysis', desc: 'Multi-engine OCR with PDF extraction and table detection', color: 'from-emerald-500 to-green-600' },
  { icon: Quote, title: 'Citation Generator', desc: 'Auto-generate APA, MLA, IEEE, Chicago, Harvard citations with BibTeX', color: 'from-amber-500 to-orange-600' },
  { icon: BarChart3, title: 'Analytics Dashboard', desc: 'AI-generated productivity insights and research progress tracking', color: 'from-cyan-500 to-teal-600' },
  { icon: Users, title: 'Collaboration', desc: 'Real-time workspace collaboration with WebSocket presence indicators', color: 'from-indigo-500 to-blue-600' },
  { icon: BookOpen, title: 'Content Composer', desc: 'AI drafting for abstracts, introductions, literature reviews and more', color: 'from-red-500 to-pink-600' },
]

const stats = [
  { value: '70B', label: 'LLM Parameters (Llama3)' },
  { value: '9', label: 'Specialized AI Agents' },
  { value: '5', label: 'Citation Formats' },
  { value: '100%', label: 'Free AI Stack' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-mesh text-white overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 via-violet-500 to-pink-500 flex items-center justify-center neon-glow">
              <span className="text-white font-bold text-xs">OS</span>
            </div>
            <span className="font-bold text-lg gradient-text">OmniSynth</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm text-slate-400 hover:text-white transition-colors">Sign In</Link>
            <Link href="/auth/register" className="px-4 py-2 rounded-lg bg-gradient-to-r from-sky-500 to-violet-500 text-sm font-semibold hover:opacity-90 transition-opacity">
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 bg-sky-500/10 border border-sky-500/20 rounded-full px-4 py-1.5 mb-6">
              <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
              <span className="text-sky-400 text-sm font-medium">Powered by Groq + Llama3-70B + Free Models</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-black mb-6 leading-tight">
              The Future of{' '}
              <span className="gradient-text">AI Research</span>
              <br />is Here
            </h1>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-10 leading-relaxed">
              OmniSynth is an enterprise-grade AI research platform that automates your entire academic workflow — 
              from literature discovery to plagiarism detection, citation generation, and collaborative writing.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link href="/auth/register">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-sky-500 via-violet-500 to-pink-500 font-semibold text-lg neon-glow hover:opacity-90 transition-all"
                >
                  Start Research Free <ArrowRight size={20} />
                </motion.button>
              </Link>
              <Link href="/docs">
                <button className="flex items-center gap-2 px-8 py-4 rounded-xl glass border border-white/10 font-semibold text-lg hover:bg-white/10 transition-all">
                  View Documentation
                </button>
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-3xl mx-auto"
          >
            {stats.map((stat, i) => (
              <div key={i} className="glass-card p-5 text-center">
                <div className="text-3xl font-black gradient-text">{stat.value}</div>
                <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-14"
          >
            <h2 className="text-4xl font-bold mb-4">Everything You Need to Research Smarter</h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">9 specialized AI agents working in harmony to automate your entire research workflow</p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  whileHover={{ y: -4 }}
                  className="glass-card p-6 hover:border-white/15 transition-all cursor-pointer group"
                >
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    <Icon size={22} className="text-white" />
                  </div>
                  <h3 className="font-semibold text-slate-100 mb-2">{feature.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{feature.desc}</p>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section className="py-20 px-6 bg-slate-900/50">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">Enterprise-Grade Architecture</h2>
          <p className="text-slate-400 mb-12 text-lg">Built with production-ready, scalable, modular design</p>
          <div className="glass-card p-8">
            <div className="flex flex-col gap-3 text-sm">
              {[
                { label: 'Frontend Layer', tech: 'Next.js 14 + TypeScript + TailwindCSS + Framer Motion', color: 'text-sky-400' },
                { label: 'API Gateway', tech: 'FastAPI + JWT Auth + Rate Limiting + CORS', color: 'text-violet-400' },
                { label: 'AI Orchestrator', tech: 'LangChain + LangGraph Multi-Agent System', color: 'text-pink-400' },
                { label: 'HyDE Retrieval Engine', tech: 'FAISS + Sentence Transformers + Reranking', color: 'text-emerald-400' },
                { label: 'LLM Layer', tech: 'Groq API (Llama3-70B, Mixtral-8x7B) + HuggingFace', color: 'text-amber-400' },
                { label: 'Data Layer', tech: 'PostgreSQL + Redis + FAISS Vector DB', color: 'text-cyan-400' },
              ].map((layer, i) => (
                <div key={i} className="flex items-center gap-4 py-3 border-b border-white/5 last:border-0">
                  <div className="w-2 h-2 rounded-full bg-current flex-shrink-0" style={{ color: layer.color.replace('text-', '#') }} />
                  <span className={`font-semibold w-48 text-left flex-shrink-0 ${layer.color}`}>{layer.label}</span>
                  <span className="text-slate-400 text-left">{layer.tech}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div whileInView={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 20 }} viewport={{ once: true }}>
            <h2 className="text-4xl font-bold mb-4">Ready to Transform Your Research?</h2>
            <p className="text-slate-400 mb-8 text-lg">Join researchers using OmniSynth to accelerate their work with AI</p>
            <Link href="/auth/register">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-10 py-4 rounded-xl bg-gradient-to-r from-sky-500 via-violet-500 to-pink-500 font-bold text-lg neon-glow"
              >
                Start Free — No Credit Card Required
              </motion.button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6 text-center text-slate-500 text-sm">
        <p>© 2024 OmniSynth AI Research Platform. Built with ❤️ using Groq + Llama3 + HuggingFace.</p>
      </footer>
    </div>
  )
}
