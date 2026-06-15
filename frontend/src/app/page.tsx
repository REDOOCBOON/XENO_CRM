'use client'

import { useEffect, useState } from 'react'
import { getDashboardKPIs, getOpportunities, seedMockData, scanOpportunities } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import {
  TrendingUp, Users, Megaphone, ArrowUpRight,
  RefreshCw, Database, Zap, Target
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts'

type KPIData = {
  attributed_revenue: number
  total_revenue: number
  campaign_count: number
  funnel: {
    sent: number
    delivered: number
    opened: number
    clicked: number
    converted: number
  }
  channel_performance: Array<{
    channel: string
    sent: number
    open_rate: number
    click_rate: number
    conversion_rate: number
    conversions: number
  }>
  reactivated_customers: number
}

type Opportunity = {
  id: string
  title: string
  description: string
  type: string
  audience_size: number
  expected_revenue_impact: number
  confidence_score: number
  suggested_channel: string
  status: string
}

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [seedDone, setSeedDone] = useState(false)
  const [error, setError] = useState('')

  const loadData = async () => {
    try {
      const [kpiData, oppData] = await Promise.all([
        getDashboardKPIs(),
        getOpportunities()
      ])
      setKpis(kpiData)
      setOpportunities(oppData || [])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSeed = async () => {
    setSeeding(true)
    try {
      await seedMockData()
      setSeedDone(true)
      await loadData()
    } catch(e: any) {
      setError(e.message)
    } finally {
      setSeeding(false)
    }
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      await scanOpportunities()
      const oppData = await getOpportunities()
      setOpportunities(oppData || [])
    } catch (e: any) {
      setError(e.message)
    } finally {
      setScanning(false)
    }
  }

  const funnelData = kpis ? [
    { name: 'Sent', value: kpis.funnel.sent, color: '#6366f1' },
    { name: 'Delivered', value: kpis.funnel.delivered, color: '#8b5cf6' },
    { name: 'Opened', value: kpis.funnel.opened, color: '#a78bfa' },
    { name: 'Clicked', value: kpis.funnel.clicked, color: '#c4b5fd' },
    { name: 'Converted', value: kpis.funnel.converted, color: '#22c55e' },
  ] : []

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground text-sm">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Your AI marketing performance overview
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${scanning ? 'animate-spin' : ''}`} />
            Scan Opportunities
          </button>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
          >
            <Database className="w-3 h-3" />
            {seeding ? 'Seeding...' : seedDone ? 'Reseed Data' : 'Seed Mock Data'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-red-400 text-sm">
          {error} - make sure the backend is running on port 8000
        </div>
      )}

      
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground">Attributed Revenue</span>
              <TrendingUp className="w-4 h-4 text-green-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">
              {formatCurrency(kpis.attributed_revenue)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              from {formatCurrency(kpis.total_revenue)} total
            </p>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground">Campaigns Run</span>
              <Megaphone className="w-4 h-4 text-primary" />
            </div>
            <p className="text-2xl font-bold text-foreground">{kpis.campaign_count}</p>
            <p className="text-xs text-muted-foreground mt-1">all time</p>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground">Messages Sent</span>
              <Zap className="w-4 h-4 text-yellow-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">{kpis.funnel.sent}</p>
            <p className="text-xs text-green-400 mt-1">
              {kpis.funnel.converted} converted
            </p>
          </div>

          <div className="stat-card">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground">Re-activated</span>
              <Users className="w-4 h-4 text-cyan-400" />
            </div>
            <p className="text-2xl font-bold text-foreground">{kpis.reactivated_customers}</p>
            <p className="text-xs text-muted-foreground mt-1">churn winbacks</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        
        {kpis && (
          <div className="gradient-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Conversion Funnel</h3>
            {kpis.funnel.sent === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No campaigns sent yet. Seed data or run a campaign.
              </div>
            ) : (
              <div className="space-y-3">
                {funnelData.map((stage, i) => {
                  const pct = funnelData[0].value > 0
                    ? Math.round((stage.value / funnelData[0].value) * 100)
                    : 0
                  return (
                    <div key={stage.name}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">{stage.name}</span>
                        <span className="text-foreground font-medium">
                          {stage.value.toLocaleString()} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2 bg-border rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: stage.color
                          }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        
        {kpis && kpis.channel_performance.length > 0 && (
          <div className="gradient-border rounded-xl p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Channel Performance</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={kpis.channel_performance} barSize={28}>
                <XAxis dataKey="channel" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(224 71% 6%)',
                    border: '1px solid hsl(216 34% 17%)',
                    borderRadius: '8px',
                    fontSize: '12px'
                  }}
                  formatter={(val: any) => [`${val}%`]}
                />
                <Bar dataKey="open_rate" name="Open Rate" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="click_rate" name="CTR" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-foreground">AI Opportunity Feed</h3>
          <span className="text-xs text-muted-foreground">{opportunities.length} active</span>
        </div>

        {opportunities.length === 0 ? (
          <div className="gradient-border rounded-xl p-8 text-center">
            <Target className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">No opportunities detected yet.</p>
            <p className="text-xs text-muted-foreground/60 mt-1">Seed mock data then click "Scan Opportunities"</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {opportunities.map((opp) => (
              <div key={opp.id} className="gradient-border rounded-xl p-4 hover:glow-purple transition-all duration-200">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                    {opp.type}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {Math.round(opp.confidence_score * 100)}% confidence
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-foreground mt-2">{opp.title}</h4>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{opp.description}</p>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground">{opp.audience_size} customers</p>
                    <p className="text-sm font-bold text-green-400">
                      {formatCurrency(opp.expected_revenue_impact)}
                    </p>
                  </div>
                  <a
                    href={`/agent?opp=${opp.id}&channel=${opp.suggested_channel}`}
                    className="text-xs px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors flex items-center gap-1"
                  >
                    Launch <ArrowUpRight className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
