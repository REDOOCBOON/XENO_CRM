'use client'

import { useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { submitGoal, executeGoalCampaign } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { Zap, Sparkles, Send, CheckCircle, AlertTriangle } from 'lucide-react'

type Proposal = {
  goal: string
  segment_ast: any
  audience_size: number
  recommended_channel: string
  message_template: string
  reasoning: string
  readiness_score: number
  predictions: {
    open_rate: number
    click_rate: number
    conversion_rate: number
    revenue_impact: number
    spam_risk: string
    deliverability_risk: string
  }
}

const EXAMPLE_GOALS = [
  'bring back inactive premium shoppers',
  'increase repeat purchases from shoe buyers',
  'upsell regular shoppers to premium tier',
  'win back customers who haven\'t ordered in 60 days',
  'cross-sell accessories to recent buyers',
]

function AgentContent() {
  const params = useSearchParams()

  const [goal, setGoal] = useState('')
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [executed, setExecuted] = useState(false)
  const [autonomous, setAutonomous] = useState(false)
  const [campaignName, setCampaignName] = useState('')
  const [error, setError] = useState('')

  const handleSubmitGoal = async () => {
    if (!goal.trim()) return
    setLoading(true)
    setError('')
    setProposal(null)
    setExecuted(false)
    try {
      const result = await submitGoal(goal)
      setProposal(result)
      
      setCampaignName(`${goal.substring(0, 40)} - ${new Date().toLocaleDateString()}`)
    } catch(e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!proposal) return
    setExecuting(true)
    setError('')
    try {
      await executeGoalCampaign({
        goal: proposal.goal,
        name: campaignName || `Campaign: ${goal.substring(0, 30)}`,
        segment_ast: proposal.segment_ast,
        channel: proposal.recommended_channel,
        message_template: proposal.message_template,
        readiness_score: proposal.readiness_score,
        predictions: proposal.predictions,
        autonomous: autonomous,
      })
      setExecuted(true)
    } catch(e: any) {
      setError(e.message)
    } finally {
      setExecuting(false)
    }
  }

  const readinessColor = proposal
    ? proposal.readiness_score >= 80 ? 'text-green-400'
      : proposal.readiness_score >= 60 ? 'text-yellow-400'
      : 'text-red-400'
    : ''

  return (
    <div className="space-y-5 animate-fade-in max-w-3xl">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Zap className="w-5 h-5 text-primary" />
          <h1 className="text-2xl font-bold">AI Campaign Agent</h1>
        </div>
        <p className="text-muted-foreground text-sm">
          Describe a marketing goal. The AI agent will analyze your audience, draft copy,
          select the best channel, and predict performance - all in one shot.
        </p>
      </div>

      
      <div className="gradient-border rounded-xl p-5 space-y-4">
        <p className="text-sm font-medium text-foreground">What is your marketing goal?</p>

        
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_GOALS.map((eg) => (
            <button
              key={eg}
              onClick={() => setGoal(eg)}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-border hover:border-primary/40 hover:bg-primary/5 hover:text-foreground text-muted-foreground transition-colors"
            >
              {eg}
            </button>
          ))}
        </div>

        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmitGoal()
          }}
          placeholder="e.g. bring back inactive premium shoppers who spent more than 500 in the last 90 days"
          rows={3}
          className="w-full bg-background border border-border rounded-lg p-3 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none focus:outline-none focus:border-primary/50 transition-colors"
        />

        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmitGoal}
            disabled={loading || !goal.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? 'Agent is thinking...' : 'Analyze & Propose'}
          </button>
          <span className="text-xs text-muted-foreground">Ctrl+Enter to submit</span>
        </div>

        {error && (
          <p className="text-red-400 text-xs bg-red-500/5 border border-red-500/20 rounded-lg p-3">{error}</p>
        )}
      </div>

      
      {loading && (
        <div className="gradient-border rounded-xl p-8 text-center space-y-2">
          <div className="flex justify-center gap-1">
            {['Segmentation', 'Channel Routing', 'Copywriting', 'Predictions'].map((step, i) => (
              <div key={step} className="flex items-center gap-1">
                <span className="text-xs text-muted-foreground animate-pulse-slow" style={{ animationDelay: `${i * 0.3}s` }}>
                  {step}
                </span>
                {i < 3 && <span className="text-muted-foreground/30 text-xs">-</span>}
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground/50">Multi-agent orchestrator running...</p>
        </div>
      )}

      {proposal && !loading && !executed && (
        <div className="space-y-4 animate-fade-in">
          
          <div className="gradient-border rounded-xl p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Campaign Proposal</p>
                <h2 className="text-lg font-bold text-foreground">Agent Analysis Complete</h2>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground mb-1">Readiness Score</p>
                <p className={`text-3xl font-black ${readinessColor}`}>{proposal.readiness_score}<span className="text-base">/100</span></p>
              </div>
            </div>

            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="bg-background rounded-lg p-3 border border-border">
                <p className="text-xs text-muted-foreground">Audience</p>
                <p className="text-xl font-bold text-foreground mt-1">{proposal.audience_size}</p>
                <p className="text-xs text-muted-foreground">customers matched</p>
              </div>
              <div className="bg-background rounded-lg p-3 border border-border">
                <p className="text-xs text-muted-foreground">Channel</p>
                <p className="text-lg font-bold text-primary mt-1">{proposal.recommended_channel}</p>
                <p className="text-xs text-muted-foreground">recommended</p>
              </div>
              <div className="bg-background rounded-lg p-3 border border-border">
                <p className="text-xs text-muted-foreground">Est. Revenue</p>
                <p className="text-xl font-bold text-green-400 mt-1">
                  {formatCurrency(proposal.predictions.revenue_impact)}
                </p>
                <p className="text-xs text-muted-foreground">projected</p>
              </div>
              <div className="bg-background rounded-lg p-3 border border-border">
                <p className="text-xs text-muted-foreground">Spam Risk</p>
                <p className={`text-lg font-bold mt-1 ${proposal.predictions.spam_risk === 'Low' ? 'text-green-400' : 'text-yellow-400'}`}>
                  {proposal.predictions.spam_risk}
                </p>
                <p className="text-xs text-muted-foreground">deliverability</p>
              </div>
            </div>

            
            <div className="border-t border-border pt-4">
              <p className="text-xs text-muted-foreground mb-3">Predicted Performance</p>
              <div className="flex items-end gap-3 h-16">
                {[
                  { label: 'Open', value: proposal.predictions.open_rate, color: '#8b5cf6' },
                  { label: 'Click', value: proposal.predictions.click_rate, color: '#f59e0b' },
                  { label: 'Convert', value: proposal.predictions.conversion_rate, color: '#22c55e' },
                ].map((m) => (
                  <div key={m.label} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-xs font-bold" style={{ color: m.color }}>{m.value}%</span>
                    <div className="w-full rounded-t" style={{
                      backgroundColor: m.color + '30',
                      height: `${Math.max(8, (m.value / 100) * 48)}px`,
                      borderTop: `2px solid ${m.color}`
                    }} />
                    <span className="text-xs text-muted-foreground">{m.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          
          <div className="gradient-border rounded-xl p-5">
            <p className="text-xs text-muted-foreground mb-2">Generated Message Copy</p>
            <div className="bg-background rounded-lg p-3 border border-border">
              <p className="text-sm text-foreground leading-relaxed">{proposal.message_template}</p>
            </div>
            {proposal.reasoning && (
              <p className="text-xs text-muted-foreground mt-2 italic">{proposal.reasoning}</p>
            )}
          </div>

          
          <div className="gradient-border rounded-xl p-5">
            <p className="text-xs text-muted-foreground mb-2">Segment Rules (AI-compiled)</p>
            <div className="bg-background rounded-lg p-3 border border-border space-y-1.5">
              <p className="text-xs text-primary mb-2">Conjunction: {proposal.segment_ast?.conjunction}</p>
              {proposal.segment_ast?.conditions?.map((cond: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">{cond.field}</span>
                  <span className="text-muted-foreground">{cond.operator}</span>
                  <span className="bg-accent border border-border px-2 py-0.5 rounded font-mono">{String(cond.value)}</span>
                </div>
              ))}
            </div>
          </div>

          
          <div className="gradient-border rounded-xl p-5 space-y-4">
            <p className="text-sm font-semibold text-foreground">Launch Campaign</p>

            <input
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/50"
              placeholder="Campaign name"
            />

            
            <div className="flex items-center justify-between p-3 bg-background rounded-lg border border-border">
              <div>
                <p className="text-sm font-medium text-foreground">Autonomous Mode</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  AI launches without waiting for approval. For demo purposes.
                </p>
              </div>
              <button
                onClick={() => setAutonomous(!autonomous)}
                className={`relative w-11 h-6 rounded-full transition-colors ${autonomous ? 'bg-primary' : 'bg-border'}`}
              >
                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${autonomous ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>

            {proposal.readiness_score < 60 && (
              <div className="flex items-start gap-2 p-3 bg-yellow-500/5 border border-yellow-500/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                <p className="text-xs text-yellow-400">
                  Readiness score is low ({proposal.readiness_score}/100). Consider revising the message template
                  to improve deliverability before launching.
                </p>
              </div>
            )}

            <button
              onClick={handleExecute}
              disabled={executing || proposal.audience_size === 0}
              className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-primary-foreground rounded-xl text-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              {executing ? 'Launching Campaign...' :
               autonomous ? 'Execute Autonomously' : 'Approve & Launch'}
            </button>

            {proposal.audience_size === 0 && (
              <p className="text-xs text-muted-foreground text-center">
                No customers matched the segment. Try a broader goal or seed mock data first.
              </p>
            )}
          </div>
        </div>
      )}

      
      {executed && (
        <div className="gradient-border rounded-xl p-8 text-center space-y-3 animate-fade-in">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
          <h2 className="text-lg font-bold text-foreground">Campaign Launched</h2>
          <p className="text-sm text-muted-foreground">
            The campaign is being dispatched to {proposal?.audience_size} customers via {proposal?.recommended_channel}.
            Simulated events will process in the background.
          </p>
          <div className="flex gap-3 justify-center pt-2">
            <button
              onClick={() => { setExecuted(false); setProposal(null); setGoal(''); }}
              className="text-sm px-4 py-2 rounded-lg border border-border hover:bg-accent transition-colors"
            >
              New Goal
            </button>
            <a
              href="/analytics"
              className="text-sm px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              View Analytics
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

export default function AgentPage() {
  return (
    <Suspense fallback={<div className="text-muted-foreground text-sm py-10">Loading agent...</div>}>
      <AgentContent />
    </Suspense>
  )
}
