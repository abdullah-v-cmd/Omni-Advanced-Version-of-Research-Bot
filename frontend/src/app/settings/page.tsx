'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Settings, Bell, Shield, Cpu, Database, Palette, Globe, Save, Loader2, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const sections = [
  { id: 'ai', label: 'AI Settings', icon: Cpu },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'privacy', label: 'Privacy & Security', icon: Shield },
  { id: 'appearance', label: 'Appearance', icon: Palette },
]

export default function SettingsPage() {
  const [active, setActive] = useState('ai')
  const [saving, setSaving] = useState(false)
  const [settings, setSettings] = useState({
    ai_model: 'llama3-70b-8192',
    use_hyde: true,
    temperature: 0.7,
    max_tokens: 4096,
    auto_citation: true,
    auto_summarize: true,
    stream_responses: true,
    email_notifications: true,
    research_alerts: true,
    collaboration_notifications: true,
    weekly_digest: false,
    share_analytics: false,
    store_conversations: true,
    theme: 'dark',
    language: 'en',
    citation_style: 'APA',
  })

  const save = async () => {
    setSaving(true)
    await new Promise(r => setTimeout(r, 800))
    setSaving(false)
    toast.success('Settings saved!')
  }

  const toggle = (key: string) => setSettings(p => ({ ...p, [key]: !(p as any)[key] }))

  const Toggle = ({ k, label, desc }: { k: string; label: string; desc?: string }) => (
    <div className="flex items-center justify-between py-3 border-b border-slate-800/50 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-200">{label}</p>
        {desc && <p className="text-xs text-slate-500 mt-0.5">{desc}</p>}
      </div>
      <button onClick={() => toggle(k)}
        className={`relative w-11 h-6 rounded-full transition-all ${(settings as any)[k] ? 'bg-sky-500' : 'bg-slate-700'}`}>
        <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${(settings as any)[k] ? 'left-6' : 'left-1'}`} />
      </button>
    </div>
  )

  const models = ['llama3-70b-8192', 'mixtral-8x7b-32768', 'llama3-8b-8192', 'gemma-7b-it']

  return (
    <DashboardLayout title="Settings">
      <div className="max-w-4xl">
        <div className="flex gap-6">
          {/* Sidebar */}
          <div className="w-48 space-y-1 flex-shrink-0">
            {sections.map(s => {
              const Icon = s.icon
              return (
                <button key={s.id} onClick={() => setActive(s.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all text-left ${active === s.id ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
                  <Icon size={15} />
                  {s.label}
                </button>
              )
            })}
          </div>

          {/* Content */}
          <div className="flex-1">
            <motion.div key={active} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="glass-card p-6 space-y-4">

              {active === 'ai' && (
                <>
                  <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2"><Cpu size={16} className="text-sky-400" /> AI Model Settings</h3>
                  <div>
                    <label className="text-xs text-slate-400 font-medium mb-2 block">Default LLM Model</label>
                    <select value={settings.ai_model} onChange={e => setSettings(p => ({ ...p, ai_model: e.target.value }))}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none text-sm">
                      {models.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 font-medium mb-2 block">Temperature: {settings.temperature}</label>
                    <input type="range" min="0" max="1" step="0.1" value={settings.temperature}
                      onChange={e => setSettings(p => ({ ...p, temperature: parseFloat(e.target.value) }))}
                      className="w-full accent-sky-500" />
                    <div className="flex justify-between text-xs text-slate-600 mt-1"><span>Precise</span><span>Creative</span></div>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 font-medium mb-2 block">Max Tokens: {settings.max_tokens}</label>
                    <input type="range" min="512" max="8192" step="512" value={settings.max_tokens}
                      onChange={e => setSettings(p => ({ ...p, max_tokens: parseInt(e.target.value) }))}
                      className="w-full accent-sky-500" />
                  </div>
                  <Toggle k="use_hyde" label="HyDE-Enhanced RAG" desc="Hypothetical Document Embedding for better search" />
                  <Toggle k="auto_summarize" label="Auto-Summarize Documents" desc="Generate AI summaries on document upload" />
                  <Toggle k="auto_citation" label="Auto-Detect Citations" desc="Automatically detect citation opportunities" />
                  <Toggle k="stream_responses" label="Stream Responses" desc="Show AI responses as they're generated" />
                  <div>
                    <label className="text-xs text-slate-400 font-medium mb-2 block">Default Citation Style</label>
                    <select value={settings.citation_style} onChange={e => setSettings(p => ({ ...p, citation_style: e.target.value }))}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none text-sm">
                      {['APA', 'MLA', 'IEEE', 'Chicago', 'Harvard', 'Vancouver'].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </>
              )}

              {active === 'notifications' && (
                <>
                  <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2"><Bell size={16} className="text-sky-400" /> Notification Preferences</h3>
                  <Toggle k="email_notifications" label="Email Notifications" desc="Receive notifications via email" />
                  <Toggle k="research_alerts" label="Research Alerts" desc="Get notified about new relevant research" />
                  <Toggle k="collaboration_notifications" label="Collaboration Updates" desc="Workspace activity and comments" />
                  <Toggle k="weekly_digest" label="Weekly Digest" desc="Weekly summary of your research activity" />
                </>
              )}

              {active === 'privacy' && (
                <>
                  <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2"><Shield size={16} className="text-sky-400" /> Privacy & Security</h3>
                  <Toggle k="share_analytics" label="Share Analytics" desc="Help improve OmniSynth with anonymized usage data" />
                  <Toggle k="store_conversations" label="Store Conversations" desc="Save AI conversations for context and history" />
                  <div className="mt-4 p-4 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                    <p className="text-xs text-amber-400 font-medium">Data Processing Notice</p>
                    <p className="text-xs text-slate-400 mt-1">Your documents and research data are processed securely. AI queries are sent to Groq's inference API. We do not sell or share your data with third parties.</p>
                  </div>
                </>
              )}

              {active === 'appearance' && (
                <>
                  <h3 className="font-semibold text-slate-100 mb-4 flex items-center gap-2"><Palette size={16} className="text-sky-400" /> Appearance</h3>
                  <div>
                    <label className="text-xs text-slate-400 font-medium mb-2 block">Theme</label>
                    <div className="flex gap-3">
                      {['dark', 'darker', 'midnight'].map(t => (
                        <button key={t} onClick={() => setSettings(p => ({ ...p, theme: t }))}
                          className={`px-4 py-2 rounded-lg text-sm capitalize transition-all border ${settings.theme === t ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-700 glass text-slate-400 hover:text-white'}`}>
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 font-medium mb-2 block">Language</label>
                    <select value={settings.language} onChange={e => setSettings(p => ({ ...p, language: e.target.value }))}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-sky-500 focus:outline-none text-sm">
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="zh">Chinese</option>
                    </select>
                  </div>
                </>
              )}

              <div className="pt-4 border-t border-slate-700/50">
                <button onClick={save} disabled={saving}
                  className="flex items-center gap-2 px-6 py-2.5 bg-sky-500 hover:bg-sky-600 rounded-lg font-medium text-white transition-all disabled:opacity-50">
                  {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save Settings
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
