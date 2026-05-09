'use client'
import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { plagiarismApi } from '@/lib/api'
import { useDropzone } from 'react-dropzone'
import { FileSearch, Upload, CheckCircle, AlertTriangle, XCircle, BarChart3 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function PlagiarismPage() {
  const [text, setText] = useState('')
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'text' | 'file'>('text')

  const onDrop = useCallback(async (files: File[]) => {
    if (!files[0]) return
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('file', files[0])
      const res = await plagiarismApi.checkFile(fd)
      setReport(res.data)
      toast.success('File analyzed successfully!')
    } catch { toast.error('File analysis failed') } finally { setLoading(false) }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'] }, multiple: false })

  const checkText = async () => {
    if (text.split(' ').length < 20) { toast.error('Please enter at least 20 words'); return }
    setLoading(true)
    try {
      const res = await plagiarismApi.check({ text })
      setReport(res.data)
      toast.success('Analysis complete!')
    } catch { toast.error('Check failed') } finally { setLoading(false) }
  }

  const getRiskIcon = (level: string) => {
    if (level === 'LOW') return <CheckCircle size={24} className="text-emerald-400" />
    if (level === 'MEDIUM') return <AlertTriangle size={24} className="text-amber-400" />
    return <XCircle size={24} className="text-red-400" />
  }

  const getRiskColor = (level: string) => {
    if (level === 'LOW') return 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30'
    if (level === 'MEDIUM') return 'from-amber-500/20 to-amber-600/10 border-amber-500/30'
    return 'from-red-500/20 to-red-600/10 border-red-500/30'
  }

  return (
    <DashboardLayout title="Plagiarism Detector">
      <div className="max-w-5xl space-y-6">
        <div className="flex gap-2">
          {['text', 'file'].map(t => (
            <button key={t} onClick={() => setTab(t as any)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t ? 'bg-sky-500/20 border border-sky-500/30 text-sky-400' : 'text-slate-400 hover:text-slate-200'}`}>
              {t === 'text' ? 'Paste Text' : 'Upload File'}
            </button>
          ))}
        </div>

        <div className="glass-card p-6">
          {tab === 'text' ? (
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Paste your text for plagiarism analysis (min. 20 words)</label>
              <textarea value={text} onChange={e => setText(e.target.value)} rows={8} placeholder="Paste your research text here..." className="w-full bg-slate-800/50 border border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none" />
              <div className="flex items-center justify-between mt-3">
                <span className="text-xs text-slate-500">{text.split(' ').filter(Boolean).length} words</span>
                <button onClick={checkText} disabled={loading || text.split(' ').filter(Boolean).length < 20}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-pink-500 to-rose-600 text-white text-sm font-semibold hover:opacity-90 transition-all disabled:opacity-50">
                  {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <FileSearch size={16} />}
                  {loading ? 'Analyzing...' : 'Check Plagiarism'}
                </button>
              </div>
            </div>
          ) : (
            <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${isDragActive ? 'border-sky-500 bg-sky-500/10' : 'border-slate-700 hover:border-sky-500/50 hover:bg-slate-800/30'}`}>
              <input {...getInputProps()} />
              <Upload size={40} className={`mx-auto mb-4 ${isDragActive ? 'text-sky-400' : 'text-slate-600'}`} />
              <p className="text-slate-300 font-medium">{isDragActive ? 'Drop your file here' : 'Drag & drop PDF or TXT file'}</p>
              <p className="text-slate-500 text-sm mt-1">or click to browse</p>
              {loading && <div className="mt-4 w-6 h-6 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin mx-auto" />}
            </div>
          )}
        </div>

        {report && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {/* Score Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className={`glass-card p-5 bg-gradient-to-br ${getRiskColor(report.risk_level)}`}>
                <div className="flex items-center gap-3 mb-2">
                  {getRiskIcon(report.risk_level)}
                  <span className="font-semibold text-slate-100">Risk Level</span>
                </div>
                <div className="text-3xl font-black text-slate-100">{report.risk_level}</div>
                <div className="text-sm text-slate-400 mt-1">Academic Integrity</div>
              </div>
              <div className="glass-card p-5">
                <div className="text-sm text-slate-400 mb-1">Originality Score</div>
                <div className="text-4xl font-black text-emerald-400">{report.originality_score}%</div>
                <div className="mt-2 h-2 bg-slate-800 rounded-full">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${report.originality_score}%` }} />
                </div>
              </div>
              <div className="glass-card p-5">
                <div className="text-sm text-slate-400 mb-1">Plagiarism Found</div>
                <div className="text-4xl font-black text-red-400">{report.plagiarism_percentage}%</div>
                <div className="text-sm text-slate-500 mt-2">{report.flagged_matches || 0} matches found</div>
              </div>
            </div>

            {/* Summary */}
            <div className="glass-card p-5">
              <h3 className="font-semibold text-slate-100 mb-2 flex items-center gap-2"><BarChart3 size={16} className="text-sky-400" />Analysis Summary</h3>
              <p className="text-slate-300 text-sm">{report.report_summary}</p>
              {report.ai_insights && <div className="mt-3 p-3 bg-sky-500/10 border border-sky-500/20 rounded-lg"><p className="text-sky-300 text-sm">{report.ai_insights}</p></div>}
            </div>

            {/* Recommendations */}
            {report.recommendations?.length > 0 && (
              <div className="glass-card p-5">
                <h3 className="font-semibold text-slate-100 mb-3">Recommendations</h3>
                <ul className="space-y-2">
                  {report.recommendations.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                      <CheckCircle size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" /> {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  )
}
