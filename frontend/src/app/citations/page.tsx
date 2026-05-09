'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { citationsApi } from '@/lib/api'
import { Quote, Plus, Copy, Download, Trash2, Search } from 'lucide-react'
import toast from 'react-hot-toast'

const STYLES = ['APA', 'MLA', 'IEEE', 'Chicago', 'Harvard']

export default function CitationsPage() {
  const [citations, setCitations] = useState<any[]>([])
  const [form, setForm] = useState({ style: 'APA', title: '', authors: '', year: '', journal: '', volume: '', issue: '', pages: '', doi: '', publisher: '', url: '' })
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [doiInput, setDoiInput] = useState('')
  const [doiLoading, setDoiLoading] = useState(false)
  const [tab, setTab] = useState<'manual' | 'doi' | 'saved'>('manual')

  useEffect(() => { loadCitations() }, [])

  const loadCitations = async () => {
    try { const res = await citationsApi.list(); setCitations(res.data) } catch {}
  }

  const generate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = { ...form, authors: form.authors ? form.authors.split(',').map((a: string) => a.trim()) : [], year: form.year ? parseInt(form.year) : undefined }
      const res = await citationsApi.generate(data)
      setResult(res.data)
      toast.success('Citation generated!')
      loadCitations()
    } catch { toast.error('Generation failed') } finally { setLoading(false) }
  }

  const doiLookup = async () => {
    if (!doiInput.trim()) return
    setDoiLoading(true)
    try {
      const res = await citationsApi.doiLookup(doiInput, form.style)
      setResult({ formatted: res.data.formatted, bibtex: res.data.bibtex, style: res.data.style })
      toast.success('DOI found and citation generated!')
    } catch { toast.error('DOI lookup failed. Try manual entry.') } finally { setDoiLoading(false) }
  }

  const copy = (text: string) => { navigator.clipboard.writeText(text); toast.success('Copied!') }
  const deleteCitation = async (id: string) => {
    try { await citationsApi.delete(id); setCitations(prev => prev.filter(c => c.id !== id)); toast.success('Deleted') } catch {}
  }

  return (
    <DashboardLayout title="Citation Generator">
      <div className="max-w-5xl space-y-6">
        {/* Tabs */}
        <div className="flex gap-2 flex-wrap">
          {[['manual', 'Manual Entry'], ['doi', 'DOI Lookup'], ['saved', 'Saved Citations']].map(([t, l]) => (
            <button key={t} onClick={() => setTab(t as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t ? 'bg-sky-500/20 border border-sky-500/30 text-sky-400' : 'text-slate-400 hover:text-slate-200 glass'}`}>
              {l}
            </button>
          ))}
        </div>

        {/* Style Selector */}
        <div className="flex gap-2 flex-wrap">
          {STYLES.map(s => (
            <button key={s} onClick={() => setForm(f => ({ ...f, style: s }))}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${form.style === s ? 'bg-violet-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
              {s}
            </button>
          ))}
        </div>

        {tab === 'manual' && (
          <div className="glass-card p-6">
            <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2"><Quote size={16} className="text-violet-400" />Manual Citation Entry</h3>
            <form onSubmit={generate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { key: 'title', label: 'Title *', placeholder: 'Paper/Book Title', required: true, full: true },
                { key: 'authors', label: 'Authors', placeholder: 'Smith J, Doe A (comma separated)' },
                { key: 'year', label: 'Year', placeholder: '2024', type: 'number' },
                { key: 'journal', label: 'Journal/Book', placeholder: 'Nature, Science...' },
                { key: 'volume', label: 'Volume', placeholder: '12' },
                { key: 'issue', label: 'Issue', placeholder: '3' },
                { key: 'pages', label: 'Pages', placeholder: '123-145' },
                { key: 'doi', label: 'DOI', placeholder: '10.1000/xyz123' },
                { key: 'publisher', label: 'Publisher', placeholder: 'Springer' },
                { key: 'url', label: 'URL', placeholder: 'https://...' },
              ].map(field => (
                <div key={field.key} className={field.full ? 'md:col-span-2' : ''}>
                  <label className="text-xs text-slate-400 mb-1 block">{field.label}</label>
                  <input value={(form as any)[field.key]} onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
                    type={field.type || 'text'} required={field.required} placeholder={field.placeholder}
                    className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500" />
                </div>
              ))}
              <div className="md:col-span-2">
                <button type="submit" disabled={loading || !form.title}
                  className="w-full py-2.5 rounded-lg bg-gradient-to-r from-violet-500 to-purple-600 text-white text-sm font-semibold hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                  {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Quote size={16} />}
                  Generate {form.style} Citation
                </button>
              </div>
            </form>
          </div>
        )}

        {tab === 'doi' && (
          <div className="glass-card p-6">
            <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2"><Search size={16} className="text-sky-400" />DOI Lookup</h3>
            <p className="text-slate-400 text-sm mb-4">Enter a DOI to automatically fetch metadata and generate a citation</p>
            <div className="flex gap-3">
              <input value={doiInput} onChange={e => setDoiInput(e.target.value)} placeholder="10.1000/xyz123" className="flex-1 bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500" />
              <button onClick={doiLookup} disabled={doiLoading || !doiInput}
                className="px-5 py-2.5 rounded-lg bg-sky-500/20 border border-sky-500/30 text-sky-400 text-sm font-medium hover:bg-sky-500/30 transition-all disabled:opacity-50">
                {doiLoading ? <div className="w-4 h-4 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin" /> : 'Lookup'}
              </button>
            </div>
          </div>
        )}

        {/* Generated Result */}
        {result && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 border-violet-500/30">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-slate-100">Generated Citation ({result.style})</h3>
              <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">✓ Valid</span>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-4 mb-4 border border-slate-700/30">
              <p className="text-sm text-slate-200 leading-relaxed font-mono">{result.formatted}</p>
              <button onClick={() => copy(result.formatted)} className="mt-2 flex items-center gap-1 text-xs text-slate-500 hover:text-sky-400 transition-colors"><Copy size={12} />Copy Citation</button>
            </div>
            {result.bibtex && (
              <div>
                <h4 className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wider">BibTeX</h4>
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700/30">
                  <pre className="text-xs text-emerald-300 overflow-x-auto">{result.bibtex}</pre>
                  <button onClick={() => copy(result.bibtex)} className="mt-2 flex items-center gap-1 text-xs text-slate-500 hover:text-sky-400 transition-colors"><Copy size={12} />Copy BibTeX</button>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Saved Citations */}
        {tab === 'saved' && (
          <div className="space-y-3">
            {citations.length === 0 ? (
              <div className="glass-card p-12 text-center"><Quote size={40} className="text-slate-600 mx-auto mb-3" /><p className="text-slate-400">No saved citations yet</p></div>
            ) : citations.map((c, i) => (
              <motion.div key={c.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="glass-card p-4 flex items-start justify-between gap-4 group">
                <div className="flex-1 min-w-0">
                  <span className="text-xs bg-violet-500/20 text-violet-400 px-2 py-0.5 rounded-full border border-violet-500/30 mr-2">{c.style}</span>
                  <p className="text-sm text-slate-300 mt-2 font-mono leading-relaxed">{c.formatted_text}</p>
                  <p className="text-xs text-slate-500 mt-1">{new Date(c.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => copy(c.formatted_text)} className="p-2 rounded-lg hover:bg-slate-700 text-slate-500 hover:text-sky-400 transition-all"><Copy size={14} /></button>
                  <button onClick={() => deleteCitation(c.id)} className="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all"><Trash2 size={14} /></button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
