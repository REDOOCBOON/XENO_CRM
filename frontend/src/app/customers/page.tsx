'use client'

import { useEffect, useState } from 'react'
import { getCustomers, getCustomerIntelligence, recalculateIntelligence } from '@/lib/api'
import { formatDate, formatCurrency, getRiskClass, truncate } from '@/lib/utils'
import { Users, RefreshCw, ChevronRight, X } from 'lucide-react'

type Customer = {
  id: string
  first_name: string
  last_name: string
  email: string
  phone: string
  properties: {
    tier?: string
    gender?: string
    age?: number
    location?: string
  }
  created_at: string
}

type Intelligence = {
  churn_score: number
  predicted_ltv: number
  preferred_channel: string
  engagement_score: number
  affinity_categories: string[]
  risk_classification: string
  persona_summary: string
  next_best_action: {
    type: string
    recommendation: string
    confidence: number
    estimated_revenue_gain: number
  }
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Customer | null>(null)
  const [intel, setIntel] = useState<Intelligence | null>(null)
  const [intelLoading, setIntelLoading] = useState(false)
  const [recalculating, setRecalculating] = useState(false)

  useEffect(() => {
    getCustomers()
      .then(setCustomers)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const openProfile = async (cust: Customer) => {
    setSelected(cust)
    setIntel(null)
    setIntelLoading(true)
    try {
      const data = await getCustomerIntelligence(cust.id)
      setIntel(data)
    } catch (e) {
      
      console.log('no intel for this customer yet')
    } finally {
      setIntelLoading(false)
    }
  }

  const handleRecalc = async () => {
    setRecalculating(true)
    try {
      await recalculateIntelligence()
      
      if (selected) {
        const data = await getCustomerIntelligence(selected.id)
        setIntel(data)
      }
    } catch(e) {
      console.error(e)
    } finally {
      setRecalculating(false)
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Customers</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {customers.length} customers - click any row to view AI intelligence profile
          </p>
        </div>
        <button
          onClick={handleRecalc}
          disabled={recalculating}
          className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${recalculating ? 'animate-spin' : ''}`} />
          Recalculate Intelligence
        </button>
      </div>

      {loading ? (
        <div className="text-muted-foreground text-sm py-10 text-center">Loading...</div>
      ) : customers.length === 0 ? (
        <div className="gradient-border rounded-xl p-10 text-center">
          <Users className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground text-sm">No customers yet.</p>
          <p className="text-xs text-muted-foreground/60 mt-1">Go to dashboard and click "Seed Mock Data"</p>
        </div>
      ) : (
        <div className="gradient-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Name</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Email</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Tier</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Location</th>
                <th className="text-left p-4 text-xs text-muted-foreground font-medium">Joined</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr
                  key={c.id}
                  onClick={() => openProfile(c)}
                  className="border-b border-border/50 hover:bg-accent/50 cursor-pointer transition-colors"
                >
                  <td className="p-4 font-medium">{c.first_name} {c.last_name}</td>
                  <td className="p-4 text-muted-foreground">{truncate(c.email, 28)}</td>
                  <td className="p-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full capitalize border ${
                      c.properties.tier === 'vip' ? 'bg-violet-500/10 text-violet-400 border-violet-500/20' :
                      c.properties.tier === 'premium' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                      'bg-gray-500/10 text-gray-400 border-gray-500/20'
                    }`}>
                      {c.properties.tier || 'regular'}
                    </span>
                  </td>
                  <td className="p-4 text-muted-foreground">{c.properties.location || '-'}</td>
                  <td className="p-4 text-muted-foreground">{formatDate(c.created_at)}</td>
                  <td className="p-4">
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      
      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/50" onClick={() => setSelected(null)} />
          <div className="relative w-full max-w-md bg-card border-l border-border h-full overflow-y-auto">
            <div className="p-5 border-b border-border flex items-start justify-between">
              <div>
                <h2 className="font-bold text-foreground">{selected.first_name} {selected.last_name}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">{selected.email}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              
              <div className="grid grid-cols-2 gap-3">
                {[
                  ['Phone', selected.phone],
                  ['Tier', selected.properties.tier || 'regular'],
                  ['Gender', selected.properties.gender || '-'],
                  ['Age', selected.properties.age?.toString() || '-'],
                  ['Location', selected.properties.location || '-'],
                ].map(([label, val]) => (
                  <div key={label} className="gradient-border rounded-lg p-3">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="text-sm font-medium mt-0.5 capitalize">{val}</p>
                  </div>
                ))}
              </div>

              
              <div className="pt-2">
                <h3 className="text-sm font-semibold text-foreground mb-3">AI Intelligence Profile</h3>
                {intelLoading ? (
                  <div className="text-muted-foreground text-sm text-center py-6">Computing profile...</div>
                ) : !intel ? (
                  <div className="text-muted-foreground text-sm text-center py-6">
                    No intelligence data yet. Run "Recalculate Intelligence" first.
                  </div>
                ) : (
                  <div className="space-y-3">
                    
                    <div className="gradient-border rounded-xl p-4">
                      <p className="text-xs text-muted-foreground">Persona</p>
                      <p className="text-base font-bold text-foreground mt-1">{intel.persona_summary}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full border mt-2 inline-block ${getRiskClass(intel.risk_classification)}`}>
                        {intel.risk_classification}
                      </span>
                    </div>

                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="gradient-border rounded-lg p-3">
                        <p className="text-xs text-muted-foreground">Predicted LTV</p>
                        <p className="text-lg font-bold text-green-400 mt-1">
                          {formatCurrency(Number(intel.predicted_ltv))}
                        </p>
                      </div>
                      <div className="gradient-border rounded-lg p-3">
                        <p className="text-xs text-muted-foreground">Preferred Channel</p>
                        <p className="text-base font-bold text-primary mt-1">{intel.preferred_channel}</p>
                      </div>
                    </div>

                    
                    <div className="gradient-border rounded-xl p-4 space-y-3">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-muted-foreground">Churn Risk</span>
                          <span className={intel.churn_score > 0.6 ? 'text-red-400' : 'text-green-400'}>
                            {Math.round(intel.churn_score * 100)}%
                          </span>
                        </div>
                        <div className="h-1.5 bg-border rounded-full">
                          <div
                            className={`h-full rounded-full ${intel.churn_score > 0.6 ? 'bg-red-500' : intel.churn_score > 0.3 ? 'bg-yellow-500' : 'bg-green-500'}`}
                            style={{ width: `${intel.churn_score * 100}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-muted-foreground">Engagement Score</span>
                          <span className="text-foreground">{Math.round(intel.engagement_score * 100)}%</span>
                        </div>
                        <div className="h-1.5 bg-border rounded-full">
                          <div
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${intel.engagement_score * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    
                    {intel.affinity_categories.length > 0 && (
                      <div className="gradient-border rounded-xl p-4">
                        <p className="text-xs text-muted-foreground mb-2">Category Affinities</p>
                        <div className="flex flex-wrap gap-1.5">
                          {intel.affinity_categories.map((cat) => (
                            <span key={cat} className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 capitalize">
                              {cat}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    
                    {intel.next_best_action && (
                      <div className="gradient-border rounded-xl p-4 border-primary/30">
                        <p className="text-xs text-muted-foreground mb-1">Next Best Action</p>
                        <p className="text-sm font-semibold text-foreground">{intel.next_best_action.recommendation}</p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                          <span className="capitalize bg-accent px-2 py-0.5 rounded">{intel.next_best_action.type}</span>
                          <span>{Math.round(intel.next_best_action.confidence * 100)}% confidence</span>
                          <span className="text-green-400">+{formatCurrency(intel.next_best_action.estimated_revenue_gain)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
