'use client'
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { chatApi } from '@/lib/api'
import { Send, Bot, User, Plus, Trash2, BookOpen, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'

interface Message { role: 'user' | 'assistant'; content: string; timestamp: string; agent?: string }
interface Conversation { id: string; title: string; message_count: number; updated_at: string }

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConvId, setCurrentConvId] = useState<string | null>(null)
  const [useHyde, setUseHyde] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversations = async () => {
    try {
      const res = await chatApi.getConversations()
      setConversations(res.data)
    } catch {}
  }

  const loadConversation = async (id: string) => {
    try {
      const res = await chatApi.getConversation(id)
      setMessages(res.data.messages || [])
      setCurrentConvId(id)
    } catch {}
  }

  const newConversation = () => {
    setMessages([])
    setCurrentConvId(null)
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg: Message = { role: 'user', content: input, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    const query = input
    setInput('')
    setLoading(true)
    try {
      const res = await chatApi.send({ message: query, conversation_id: currentConvId || undefined, use_hyde: useHyde })
      const aiMsg: Message = {
        role: 'assistant',
        content: res.data.message,
        timestamp: new Date().toISOString(),
        agent: res.data.agent_used,
      }
      setMessages(prev => [...prev, aiMsg])
      if (res.data.conversation_id && !currentConvId) {
        setCurrentConvId(res.data.conversation_id)
        loadConversations()
      }
    } catch (err: any) {
      toast.error('Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <DashboardLayout title="OmniChat AI">
      <div className="flex h-[calc(100vh-8rem)] gap-4 max-w-7xl">
        {/* Sidebar - Conversations */}
        <div className="w-64 flex flex-col gap-3">
          <button onClick={newConversation} className="flex items-center gap-2 w-full px-4 py-2.5 rounded-lg bg-gradient-to-r from-sky-500 to-violet-500 text-sm font-semibold hover:opacity-90 transition-all">
            <Plus size={16} /> New Conversation
          </button>
          <div className="glass-card flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-xs">No conversations yet</div>
            ) : (
              conversations.map((conv) => (
                <button key={conv.id} onClick={() => loadConversation(conv.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all hover:bg-slate-700/50 ${currentConvId === conv.id ? 'bg-sky-500/20 border border-sky-500/30 text-sky-300' : 'text-slate-300'}`}>
                  <div className="truncate font-medium">{conv.title}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{conv.message_count} messages</div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col glass-card overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-100">OmniSynth AI</div>
                <div className="text-xs text-emerald-400">● Online • Multi-Agent System</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <span className="text-xs text-slate-400">HyDE RAG</span>
                <div onClick={() => setUseHyde(!useHyde)} className={`w-9 h-5 rounded-full transition-colors ${useHyde ? 'bg-sky-500' : 'bg-slate-600'} relative cursor-pointer`}>
                  <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${useHyde ? 'translate-x-4' : 'translate-x-0.5'}`} />
                </div>
              </label>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-sky-500/20 to-violet-500/20 border border-sky-500/20 flex items-center justify-center mb-4">
                  <Bot size={32} className="text-sky-400" />
                </div>
                <h3 className="text-xl font-bold text-slate-100 mb-2">OmniSynth AI Assistant</h3>
                <p className="text-slate-400 max-w-md text-sm">Ask me anything about your research. I can help with literature reviews, summarization, citation generation, content writing, and more.</p>
                <div className="grid grid-cols-2 gap-2 mt-6 max-w-md">
                  {['Summarize this research paper for me', 'Help me write an introduction about AI ethics', 'Find papers on deep learning for NLP', 'Generate an APA citation for this source'].map((s, i) => (
                    <button key={i} onClick={() => setInput(s)} className="text-left px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-all">{s}</button>
                  ))}
                </div>
              </div>
            )}
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center flex-shrink-0">
                      <Bot size={14} className="text-white" />
                    </div>
                  )}
                  <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${msg.role === 'user' ? 'bg-gradient-to-r from-sky-500 to-violet-500 text-white rounded-tr-md' : 'bg-slate-800/80 text-slate-100 rounded-tl-md border border-slate-700/30'}`}>
                    {msg.agent && msg.role === 'assistant' && (
                      <div className="flex items-center gap-1 text-xs text-sky-400 mb-2 font-medium">
                        <Zap size={10} /> {msg.agent}
                      </div>
                    )}
                    {msg.role === 'assistant' ? (
                      <div className="ai-response-container text-sm prose prose-invert max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    )}
                    <div className="text-xs opacity-50 mt-1 text-right">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center flex-shrink-0">
                      <User size={14} className="text-slate-300" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-violet-500 flex items-center justify-center">
                  <Bot size={14} className="text-white" />
                </div>
                <div className="bg-slate-800/80 border border-slate-700/30 rounded-2xl rounded-tl-md px-4 py-3">
                  <div className="flex gap-1 items-center">
                    {[0, 1, 2].map(i => <div key={i} className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />)}
                    <span className="text-xs text-slate-400 ml-2">AI is thinking...</span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-slate-700/50">
            <div className="flex gap-3 items-end">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask OmniSynth AI anything about your research..."
                rows={1}
                className="flex-1 bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 resize-none transition-colors"
                style={{ maxHeight: '120px', overflowY: 'auto' }}
              />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="w-10 h-10 rounded-xl bg-gradient-to-r from-sky-500 to-violet-500 flex items-center justify-center hover:opacity-90 transition-all disabled:opacity-40"
              >
                <Send size={16} className="text-white" />
              </motion.button>
            </div>
            <p className="text-xs text-slate-600 mt-2 text-center">Press Enter to send • Shift+Enter for new line • HyDE RAG {useHyde ? 'enabled' : 'disabled'}</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
