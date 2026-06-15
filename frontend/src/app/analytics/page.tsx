'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { getCampaigns, getCampaignAnalytics } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { BarChart2, TrendingUp } from 'lucide-react'

type Analytics = {
  campaign_id: string
  name: string
  channel: string
  status: string
  funnel: {
    sent: number
    delivered: number
    failed: number
    opened: number
    clicked: number
    converted: number
  }
  revenue: number
  ai_report: string
}

type Campaign = {
  id: string
  name: string
  status: string
}

function AnalyticsContent() {
  const params = useSearchParams()
  const campaignParam = params.get('campaign')

  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedId, setSelectedId] = useState<string>(campaignParam || '')
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getCampaigns().then((data) => {
      setCampaigns(data || [])
      if (!selectedId && data && data.length > 0) {
        setSelectedId(data[0].id)
      }
    }).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedId) return
    setLoading(true)
    setAnalytics(null)
    getCampaignAnalytics(selectedId)
      .then(setAnalytics)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [selectedId])

  const funnelStages = analytics ? [
    { label: 'Sent', value: analytics.funnel.sent, color: '#6366f1' },
    { label: 'Delivered', value: analytics.funnel.delivered, color: '#8b5cf6' },
    { label: 'Opened', value: analytics.funnel.opened, color: '#f59e0b' },
    { label: 'Clicked', value: analytics.funnel.clicked, color: '#f97316' },
    { label: 'Converted', value: analytics.funnel.converted, color: '#22c55e' },
  ] : []

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Campaign Analytics</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Funnel metrics and AI-generated performance analysis
        </p>
      </div>

      
      <div className="gradient-border rounded-xl p-4">
        <label className="text-xs text-muted-foreground mb-2 block">Select Campaign</label>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary/50 text-foreground"
        >
          <option value="">-- select a campaign --</option>
          {campaigns.map((c) => (
            <option key={c.id} value={c.id}>{c.name} ({c.status})</option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="text-center text-muted-foreground text-sm py-10">Loading analytics...</div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
      )}

      {analytics && !loading && (
        <>
          
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-foreground">{analytics.funnel.sent}</p>
              <p className="text-xs text-muted-foreground mt-1">Total Sent</p>
            </div>
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-yellow-400">
                {analytics.funnel.sent > 0 ? Math.round(analytics.funnel.opened / analytics.funnel.sent * 100) : 0}%
              </p>
              <p className="text-xs text-muted-foreground mt-1">Open Rate</p>
            </div>
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-orange-400">
                {analytics.funnel.opened > 0 ? Math.round(analytics.funnel.clicked / analytics.funnel.opened * 100) : 0}%
              </p>
              <p className="text-xs text-muted-foreground mt-1">Click Rate</p>
            </div>
            <div className="stat-card text-center">
              <p className="text-3xl font-bold text-green-400">
                {formatCurrency(analytics.revenue)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">Revenue</p>
            </div>
          </div>

          
          <div className="gradient-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Delivery Funnel</h3>
            <div className="space-y-3">
              {funnelStages.map((stage) => {
                const max = funnelStages[0].value || 1
                const pct = Math.round((stage.value / max) * 100)
                return (
                  <div key={stage.label}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-muted-foreground">{stage.label}</span>
                      <span className="font-medium text-foreground">{stage.value.toLocaleString()} <span className="text-muted-foreground">({pct}%)</span></span>
                    </div>
                    <div className="h-3 bg-border rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700 ease-out"
                        style={{ width: `${pct}%`, backgroundColor: stage.color }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>

            {analytics.funnel.failed > 0 && (
              <div className="mt-3 pt-3 border-t border-border">
                <p className="text-xs text-red-400">
                  {analytics.funnel.failed} messages failed to deliver
                </p>
              </div>
            )}
          </div>

          
          {analytics.ai_report && (
            <div className="gradient-border rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">AI Performance Analysis</h3>
              </div>
              <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                {analytics.ai_report}
              </div>
            </div>
          )}
        </>
      )}

      {!selectedId && !loading && (
        <div className="gradient-border rounded-xl p-10 text-center">
          <BarChart2 className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">Select a campaign to view analytics</p>
        </div>
      )}
    </div>
  )
}

export default function AnalyticsPage() {
  return (
    <Suspense fallback={<div className="text-muted-foreground text-sm py-10 text-center">Loading...</div>}>
      <AnalyticsContent />
    </Suspense>
  )
}
