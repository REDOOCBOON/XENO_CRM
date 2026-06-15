'use client'

import { useEffect, useState } from 'react'
import { getCampaigns, getSegments, createCampaign, sendCampaign, generateCampaignContent } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Megaphone, Sparkles, Send, Plus, X } from 'lucide-react'
import Link from 'next/link'

type Campaign = {
  id: string
  name: string
  segment_id: string | null
  message_template: string
  channel: string
  status: string
  goal: string | null
  readiness_score: number
  predicted_metrics: {
    open_rate?: number
    click_rate?: number
    conversion_rate?: number
    revenue_impact?: number
    spam_risk?: string
  }
  created_at: string
}

type Segment = {
  id: string
  name: string
}

const CHANNELS = ['WhatsApp', 'SMS', 'Email', 'RCS']
const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  sending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  completed: 'bg-green-500/10 text-green-400 border-green-500/20',
  failed: 'bg-red-500/10 text-red-400 border-red-500/20',
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [segments, setSegments] = useState<Segment[]>([])
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  
  const [name, setName] = useState('')
  const [segmentId, setSegmentId] = useState('')
  const [channel, setChannel] = useState('WhatsApp')
  const [template, setTemplate] = useState('')
  const [aiGoal, setAiGoal] = useState('')
  const [aiSuggestion, setAiSuggestion] = useState<any>(null)

  useEffect(() => {
    Promise.all([getCampaigns(), getSegments()])
      .then(([camps, segs]) => {
        setCampaigns(camps || [])
        setSegments(segs || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleGenerateAI = async () => {
    if (!aiGoal.trim() || !name.trim()) {
      setError('Enter campaign name and goal first')
      return
    }
    setGenerating(true)
    setError('')
    try {
      const result = await generateCampaignContent(name, 'Target audience based on goal', aiGoal)
      setAiSuggestion(result)
      setTemplate(result.message_template || '')
      setChannel(result.channel || 'WhatsApp')
    } catch(e: any) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleCreate = async () => {
    if (!name.trim() || !template.trim()) {
      setError('Name and message template are required')
      return
    }
    try {
      const newCamp = await createCampaign({
        name,
        segment_id: segmentId || null,
        message_template: template,
        channel,
        goal: aiGoal || null
      })
      setCampaigns(prev => [newCamp, ...prev])
      setShowForm(false)
      
      setName('')
      setTemplate('')
      setAiGoal('')
      setSegmentId('')
      setAiSuggestion(null)
      setError('')
    } catch(e: any) {
      setError(e.message)
    }
  }

  const handleSend = async (id: string) => {
    setSending(id)
    try {
      await sendCampaign(id)
      
      setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'sending' } : c))
    } catch(e: any) {
      setError(e.message)
    } finally {
      setSending(null)
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaign Studio</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create and manage your marketing campaigns
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Campaign
        </button>
      </div>

      
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={() => setShowForm(false)} />
          <div className="relative bg-card border border-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <h2 className="font-bold text-foreground">Create Campaign</h2>
              <button onClick={() => setShowForm(false)}>
                <X className="w-5 h-5 text-muted-foreground hover:text-foreground" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">Campaign Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. VIP Winback June"
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/50"
                />
              </div>

              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">Segment (optional)</label>
                <select
                  value={segmentId}
                  onChange={(e) => setSegmentId(e.target.value)}
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/50 text-foreground"
                >
                  <option value="">All customers</option>
                  {segments.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">Channel</label>
                <div className="flex gap-2">
                  {CHANNELS.map((ch) => (
                    <button
                      key={ch}
                      onClick={() => setChannel(ch)}
                      className={`flex-1 text-xs py-2 rounded-lg border transition-colors ${
                        channel === ch
                          ? 'bg-primary/15 border-primary/40 text-primary'
                          : 'border-border text-muted-foreground hover:bg-accent'
                      }`}
                    >
                      {ch}
                    </button>
                  ))}
                </div>
              </div>

              
              <div className="border border-primary/20 rounded-xl p-4 bg-primary/5 space-y-3">
                <p className="text-xs font-medium text-primary">AI Message Generator</p>
                <input
                  value={aiGoal}
                  onChange={(e) => setAiGoal(e.target.value)}
                  placeholder="What is the campaign goal? e.g. win back churned VIPs"
                  className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/50"
                />
                <button
                  onClick={handleGenerateAI}
                  disabled={generating || !aiGoal.trim() || !name.trim()}
                  className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
                >
                  <Sparkles className="w-3 h-3" />
                  {generating ? 'Generating...' : 'Generate with AI'}
                </button>

                {aiSuggestion && (
                  <div className="text-xs space-y-1.5 pt-1">
                    <p className="text-muted-foreground">{aiSuggestion.reasoning}</p>
                    {aiSuggestion.predicted_open_rate && (
                      <div className="flex gap-3">
                        <span className="text-foreground">Open: <strong className="text-primary">{aiSuggestion.predicted_open_rate}%</strong></span>
                        <span className="text-foreground">CTR: <strong className="text-primary">{aiSuggestion.predicted_click_rate}%</strong></span>
                        <span className="text-foreground">CR: <strong className="text-green-400">{aiSuggestion.predicted_conversion_rate}%</strong></span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div>
                <label className="text-xs text-muted-foreground mb-1.5 block">
                  Message Template
                  <span className="ml-2 text-muted-foreground/50">Use {'{{first_name}}'} and {'{{last_purchased_item}}'}</span>
                </label>
                <textarea
                  value={template}
                  onChange={(e) => setTemplate(e.target.value)}
                  placeholder="Hi {{first_name}}, we have an exclusive offer for you..."
                  className="w-full h-28 bg-background border border-border rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-primary/50"
                />
              </div>

              {error && <p className="text-red-400 text-xs">{error}</p>}

              <div className="flex gap-3 pt-1">
                <button
                  onClick={() => setShowForm(false)}
                  className="flex-1 text-sm py-2 rounded-lg border border-border hover:bg-accent transition-colors text-muted-foreground"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  className="flex-1 text-sm py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors font-medium"
                >
                  Create Campaign
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      
      {loading ? (
        <div className="text-center text-muted-foreground text-sm py-10">Loading...</div>
      ) : campaigns.length === 0 ? (
        <div className="gradient-border rounded-xl p-10 text-center">
          <Megaphone className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">No campaigns yet. Create one or use the AI Agent.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map((camp) => (
            <div key={camp.id} className="gradient-border rounded-xl p-4 hover:glow-purple transition-all">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-foreground">{camp.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_COLORS[camp.status] || STATUS_COLORS.draft}`}>
                      {camp.status}
                    </span>
                    {camp.readiness_score > 0 && (
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${
                        camp.readiness_score >= 80 ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                        camp.readiness_score >= 60 ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                        'bg-red-500/10 text-red-400 border-red-500/20'
                      }`}>
                        Readiness: {camp.readiness_score}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-1">{camp.message_template}</p>
                  {camp.goal && (
                    <p className="text-xs text-primary/70 mt-1">Goal: {camp.goal}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                    <span className="bg-accent px-2 py-0.5 rounded">{camp.channel}</span>
                    <span>{formatDate(camp.created_at)}</span>
                    {camp.predicted_metrics?.open_rate && (
                      <span className="text-primary">
                        {camp.predicted_metrics.open_rate}% predicted open
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Link
                    href={`/analytics?campaign=${camp.id}`}
                    className="text-xs px-3 py-1.5 rounded-lg border border-border hover:bg-accent transition-colors"
                  >
                    Analytics
                  </Link>
                  {camp.status === 'draft' && (
                    <button
                      onClick={() => handleSend(camp.id)}
                      disabled={sending === camp.id}
                      className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                      <Send className="w-3 h-3" />
                      {sending === camp.id ? 'Sending...' : 'Send'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
