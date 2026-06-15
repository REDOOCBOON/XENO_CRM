'use client'

import { useEffect, useState } from 'react'
import { getSegments, parseNLSegment, previewSegment, createSegment } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Filter, Sparkles, Eye, Save, ChevronRight } from 'lucide-react'

type Segment = {
  id: string
  name: string
  description: string
  definition_json: any
  created_at: string
}

export default function SegmentsPage() {
  const [segments, setSegments] = useState<Segment[]>([])
  const [nlPrompt, setNlPrompt] = useState('')
  const [segmentName, setSegmentName] = useState('')
  const [parsedDef, setParsedDef] = useState<any>(null)
  const [previewCount, setPreviewCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [previewing, setPreviewing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getSegments().then(setSegments).catch(console.error)
  }, [])

  const handleParse = async () => {
    if (!nlPrompt.trim()) return
    setLoading(true)
    setError('')
    setParsedDef(null)
    setPreviewCount(null)
    try {
      const def = await parseNLSegment(nlPrompt)
      setParsedDef(def)
    } catch(e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async () => {
    if (!parsedDef) return
    setPreviewing(true)
    try {
      const result = await previewSegment(parsedDef)
      setPreviewCount(result.count)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setPreviewing(false)
    }
  }

  const handleSave = async () => {
    if (!parsedDef || !segmentName.trim()) {
      setError('Enter a segment name first')
      return
    }
    setSaving(true)
    try {
      const newSeg = await createSegment({
        name: segmentName,
        description: nlPrompt,
        definition_json: parsedDef
      })
      setSegments(prev => [newSeg, ...prev])
      setNlPrompt('')
      setSegmentName('')
      setParsedDef(null)
      setPreviewCount(null)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const samplePrompts = [
    'bring back inactive premium shoppers',
    'customers who bought shoes in the last 60 days',
    'regular shoppers with high spend',
    'vip customers who haven\'t ordered recently',
  ]

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">AI Segment Builder</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Describe your audience in plain English - AI will build the query
        </p>
      </div>

      
      <div className="gradient-border rounded-xl p-5 space-y-4">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-primary mt-1 shrink-0" />
          <div className="flex-1 space-y-3">
            <p className="text-sm font-medium text-foreground">Describe your target audience</p>

            
            <div className="flex flex-wrap gap-2">
              {samplePrompts.map((p) => (
                <button
                  key={p}
                  onClick={() => setNlPrompt(p)}
                  className="text-xs px-2.5 py-1.5 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors text-muted-foreground hover:text-foreground"
                >
                  {p}
                </button>
              ))}
            </div>

            <textarea
              value={nlPrompt}
              onChange={(e) => setNlPrompt(e.target.value)}
              placeholder="e.g. bring back inactive premium shoppers who spent over 500"
              className="w-full h-24 bg-background border border-border rounded-lg p-3 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none focus:outline-none focus:border-primary/50 transition-colors"
            />

            <button
              onClick={handleParse}
              disabled={loading || !nlPrompt.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {loading ? 'Parsing with AI...' : 'Parse Audience'}
            </button>
          </div>
        </div>

        {error && (
          <p className="text-red-400 text-xs border border-red-500/20 bg-red-500/5 rounded-lg p-3">{error}</p>
        )}

        
        {parsedDef && (
          <div className="border-t border-border pt-4 space-y-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Generated Filter Rules</p>
            <div className="bg-background rounded-lg p-3 border border-border">
              <p className="text-xs text-muted-foreground mb-2">Conjunction: <span className="text-primary">{parsedDef.conjunction}</span></p>
              <div className="space-y-1.5">
                {parsedDef.conditions?.map((cond: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">{cond.field}</span>
                    <span className="text-muted-foreground">{cond.operator}</span>
                    <span className="bg-accent px-2 py-0.5 rounded font-mono">{String(cond.value)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handlePreview}
                disabled={previewing}
                className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors disabled:opacity-50"
              >
                <Eye className="w-3 h-3" />
                {previewing ? 'Counting...' : 'Preview Audience Size'}
              </button>

              {previewCount !== null && (
                <span className="text-sm font-bold text-foreground">
                  {previewCount} customers matched
                </span>
              )}
            </div>

            {previewCount !== null && (
              <div className="flex items-center gap-3">
                <input
                  value={segmentName}
                  onChange={(e) => setSegmentName(e.target.value)}
                  placeholder="Segment name (e.g. Inactive VIPs)"
                  className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50"
                />
                <button
                  onClick={handleSave}
                  disabled={saving || !segmentName.trim()}
                  className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 hover:bg-green-500/20 transition-colors disabled:opacity-50"
                >
                  <Save className="w-3 h-3" />
                  {saving ? 'Saving...' : 'Save Segment'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Saved Segments ({segments.length})</h3>
        {segments.length === 0 ? (
          <div className="gradient-border rounded-xl p-6 text-center">
            <Filter className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground text-sm">No segments saved yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {segments.map((seg) => (
              <div key={seg.id} className="gradient-border rounded-xl p-4 flex items-center justify-between hover:glow-purple transition-all">
                <div>
                  <p className="text-sm font-semibold text-foreground">{seg.name}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{seg.description || 'No description'}</p>
                  <p className="text-xs text-muted-foreground/50 mt-1">{formatDate(seg.created_at)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
                    {seg.definition_json?.conditions?.length || 0} rules
                  </span>
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
