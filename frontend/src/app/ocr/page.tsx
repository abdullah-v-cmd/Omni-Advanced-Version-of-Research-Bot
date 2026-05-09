'use client'
import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { useDropzone } from 'react-dropzone'
import { Cpu, Upload, FileText, Trash2, Eye, Download, CheckCircle, Clock, XCircle, Loader2, Copy } from 'lucide-react'
import toast from 'react-hot-toast'
import ReactMarkdown from 'react-markdown'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

interface DocResult {
  id: string; title: string; filename: string; doc_type: string; status: string
  word_count: number; page_count: number; summary?: string; keywords?: string[]
  extracted_text_preview?: string; created_at: string; is_indexed: boolean
}

export default function OcrPage() {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<DocResult | null>(null)
  const [documents, setDocuments] = useState<DocResult[]>([])
  const [selectedDoc, setSelectedDoc] = useState<any>(null)
  const [viewModal, setViewModal] = useState(false)
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [generateSummary, setGenerateSummary] = useState(true)
  const [tab, setTab] = useState<'upload' | 'library'>('upload')

  const loadDocuments = useCallback(async () => {
    setLoadingDocs(true)
    try {
      const res = await fetch(`${API}/api/v1/ocr/documents`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      })
      if (res.ok) setDocuments(await res.json())
    } catch {} finally { setLoadingDocs(false) }
  }, [])

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles[0]) return
    const file = acceptedFiles[0]
    setUploading(true)
    setResult(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('generate_summary', String(generateSummary))
    try {
      const res = await fetch(`${API}/api/v1/ocr/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
        body: fd
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      const data = await res.json()
      setResult(data)
      toast.success('Document processed successfully!')
    } catch (e: any) {
      toast.error(e.message || 'Upload failed')
    } finally { setUploading(false) }
  }, [generateSummary])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024,
  })

  const viewDoc = async (id: string) => {
    try {
      const res = await fetch(`${API}/api/v1/ocr/documents/${id}`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      })
      if (res.ok) { setSelectedDoc(await res.json()); setViewModal(true) }
    } catch { toast.error('Failed to load document') }
  }

  const deleteDoc = async (id: string) => {
    if (!confirm('Delete this document?')) return
    try {
      await fetch(`${API}/api/v1/ocr/documents/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` }
      })
      setDocuments(prev => prev.filter(d => d.id !== id))
      toast.success('Deleted')
    } catch { toast.error('Failed to delete') }
  }

  const statusIcon = (s: string) => {
    if (s === 'processed') return <CheckCircle className="text-emerald-400" size={14} />
    if (s === 'processing') return <Loader2 className="text-sky-400 animate-spin" size={14} />
    if (s === 'failed') return <XCircle className="text-red-400" size={14} />
    return <Clock className="text-slate-400" size={14} />
  }

  return (
    <DashboardLayout title="OCR & Document Processing">
      <div className="max-w-6xl space-y-6">
        {/* Tabs */}
        <div className="flex gap-2">
          {(['upload', 'library'] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); if (t === 'library') loadDocuments() }}
              className={`px-5 py-2 rounded-lg font-medium capitalize transition-all ${tab === t ? 'bg-sky-500 text-white' : 'glass text-slate-400 hover:text-white'}`}>
              {t === 'library' ? 'Document Library' : 'Upload & Extract'}
            </button>
          ))}
        </div>

        {tab === 'upload' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Upload Zone */}
            <div className="space-y-4">
              <div className="glass-card p-6">
                <h2 className="font-semibold text-slate-100 mb-4 flex items-center gap-2">
                  <Cpu size={18} className="text-sky-400" /> Upload Document
                </h2>
                <div className="flex items-center gap-3 mb-4">
                  <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                    <input type="checkbox" checked={generateSummary} onChange={e => setGenerateSummary(e.target.checked)} className="rounded" />
                    Generate AI Summary
                  </label>
                </div>
                <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${isDragActive ? 'border-sky-400 bg-sky-500/10' : 'border-slate-600 hover:border-slate-400 hover:bg-white/5'}`}>
                  <input {...getInputProps()} />
                  {uploading ? (
                    <div className="flex flex-col items-center gap-3">
                      <Loader2 size={40} className="text-sky-400 animate-spin" />
                      <p className="text-slate-300">Processing with multi-engine OCR...</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-3">
                      <Upload size={40} className={isDragActive ? 'text-sky-400' : 'text-slate-500'} />
                      <p className="text-slate-300 font-medium">{isDragActive ? 'Drop it here!' : 'Drag & drop or click to upload'}</p>
                      <p className="text-xs text-slate-500">PDF, PNG, JPG, DOCX, TXT — Max 50MB</p>
                    </div>
                  )}
                </div>
                <div className="mt-4 p-3 glass rounded-lg">
                  <p className="text-xs text-slate-500 font-medium mb-1">OCR Engines Available:</p>
                  <div className="flex flex-wrap gap-1">
                    {['PyMuPDF', 'EasyOCR', 'pytesseract', 'pdfplumber'].map(e => (
                      <span key={e} className="text-xs bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded">{e}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Result Panel */}
            <div className="space-y-4">
              {result ? (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-100 flex items-center gap-2">
                      <CheckCircle size={16} className="text-emerald-400" /> Extraction Complete
                    </h3>
                    <span className={`text-xs px-2 py-1 rounded-full ${result.is_indexed ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'}`}>
                      {result.is_indexed ? 'Indexed' : 'Not indexed'}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Words', value: result.word_count?.toLocaleString() || 0 },
                      { label: 'Pages', value: result.page_count || 1 },
                      { label: 'Type', value: result.doc_type?.toUpperCase() },
                    ].map(s => (
                      <div key={s.label} className="glass rounded-lg p-3 text-center">
                        <div className="text-xl font-bold gradient-text">{s.value}</div>
                        <div className="text-xs text-slate-500">{s.label}</div>
                      </div>
                    ))}
                  </div>
                  {result.summary && (
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-1">AI Summary:</p>
                      <p className="text-sm text-slate-300 leading-relaxed bg-slate-800/50 p-3 rounded-lg">{result.summary}</p>
                    </div>
                  )}
                  {result.keywords && result.keywords.length > 0 && (
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-2">Keywords:</p>
                      <div className="flex flex-wrap gap-1">
                        {result.keywords.map((k, i) => (
                          <span key={i} className="text-xs bg-violet-500/10 text-violet-400 px-2 py-1 rounded-full">{k}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  {result.extracted_text_preview && (
                    <div>
                      <p className="text-xs text-slate-500 font-medium mb-1">Text Preview:</p>
                      <div className="text-xs text-slate-400 bg-slate-900 p-3 rounded-lg font-mono leading-relaxed max-h-32 overflow-y-auto">
                        {result.extracted_text_preview}
                      </div>
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="glass-card p-8 text-center">
                  <FileText size={48} className="text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-500">Upload a document to see extraction results</p>
                  <p className="text-xs text-slate-600 mt-1">Supports multi-engine OCR with AI summarization</p>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === 'library' && (
          <div className="glass-card p-6">
            <h2 className="font-semibold text-slate-100 mb-4">Document Library</h2>
            {loadingDocs ? (
              <div className="flex justify-center py-10"><Loader2 className="animate-spin text-sky-400" size={28} /></div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <FileText size={48} className="mx-auto mb-3 opacity-30" />
                <p>No documents yet. Upload some documents first.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {documents.map(doc => (
                  <div key={doc.id} className="flex items-center gap-4 p-4 glass rounded-xl hover:bg-white/5 transition-all">
                    <FileText size={20} className="text-sky-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-200 truncate">{doc.title}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="flex items-center gap-1 text-xs text-slate-500">{statusIcon(doc.status)} {doc.status}</span>
                        <span className="text-xs text-slate-600">{doc.word_count?.toLocaleString()} words</span>
                        <span className="text-xs text-slate-600">{doc.doc_type?.toUpperCase()}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => viewDoc(doc.id)} className="p-2 rounded-lg glass hover:bg-sky-500/10 text-slate-400 hover:text-sky-400 transition-all">
                        <Eye size={14} />
                      </button>
                      <button onClick={() => deleteDoc(doc.id)} className="p-2 rounded-lg glass hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-all">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* View Modal */}
        <AnimatePresence>
          {viewModal && selectedDoc && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setViewModal(false)}>
              <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }}
                className="glass-card w-full max-w-3xl max-h-[80vh] overflow-hidden flex flex-col"
                onClick={e => e.stopPropagation()}>
                <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
                  <h3 className="font-semibold truncate">{selectedDoc.title}</h3>
                  <div className="flex gap-2">
                    <button onClick={() => { navigator.clipboard.writeText(selectedDoc.extracted_text || ''); toast.success('Copied!') }}
                      className="p-2 rounded-lg glass hover:bg-white/10"><Copy size={14} /></button>
                    <button onClick={() => setViewModal(false)} className="p-2 rounded-lg glass hover:bg-white/10 text-slate-400">✕</button>
                  </div>
                </div>
                <div className="overflow-y-auto p-4 space-y-4">
                  {selectedDoc.summary && (
                    <div className="p-3 bg-sky-500/5 border border-sky-500/20 rounded-lg">
                      <p className="text-xs text-sky-400 font-medium mb-1">AI Summary</p>
                      <p className="text-sm text-slate-300">{selectedDoc.summary}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-slate-500 font-medium mb-2">Extracted Text</p>
                    <pre className="text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap bg-slate-900 p-4 rounded-lg">
                      {selectedDoc.extracted_text || 'No text extracted'}
                    </pre>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </DashboardLayout>
  )
}
