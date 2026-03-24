import { useMemo } from 'react'
import type { ComponentType, CSSProperties } from 'react'
import PlotlyMod from 'plotly.js/dist/plotly.js'
import FactoryMod from 'react-plotly.js/factory.js'
import { unwrapCjsDefault } from '../lib/cjsInterop'
import type { AnalyzeResponse, Severity } from '../types'

type PlotProps = {
  data: Record<string, unknown>[]
  layout?: Record<string, unknown>
  config?: Record<string, unknown>
  style?: CSSProperties
  className?: string
}

const createPlotlyComponent = unwrapCjsDefault<
  (plotly: unknown) => ComponentType<PlotProps>
>(FactoryMod)
const Plotly = unwrapCjsDefault<typeof PlotlyMod>(PlotlyMod)
const Plot = createPlotlyComponent(Plotly) as ComponentType<PlotProps>

const TS_RE = /\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?/g

function extractTs(line: string): string | null {
  TS_RE.lastIndex = 0
  const m = TS_RE.exec(line)
  return m ? m[0].replace(' ', 'T') : null
}

function severityOrder(s: Severity): number {
  const o: Record<Severity, number> = { info: 0, low: 1, medium: 2, high: 3, critical: 4 }
  return o[s] ?? 0
}

export function DashboardCharts({
  result,
  batch,
  rawLines,
  primaryRaw,
}: {
  result: AnalyzeResponse | null
  batch: AnalyzeResponse[] | null
  rawLines: string[] | null
  primaryRaw?: string | null
}) {
  const pieData = useMemo(() => {
    if (batch?.length) {
      const counts: Record<string, number> = {}
      for (const r of batch) counts[r.severity] = (counts[r.severity] || 0) + 1
      const labels = Object.keys(counts)
      const values = labels.map((l) => counts[l])
      return { labels, values }
    }
    if (result) {
      const order: Severity[] = ['info', 'low', 'medium', 'high', 'critical']
      const values = order.map((s) => (s === result.severity ? Math.max(5, result.severity_score * 100) : 0))
      return { labels: order, values }
    }
    return null
  }, [batch, result])

  const timeline = useMemo(() => {
    const pts: { t: string; y: number }[] = []
    if (rawLines?.length && batch?.length && rawLines.length === batch.length) {
      rawLines.forEach((line, idx) => {
        const ts = extractTs(line)
        const r = batch[idx]
        if (ts && r) pts.push({ t: ts, y: severityOrder(r.severity) })
      })
    } else if (primaryRaw && result) {
      const ts = extractTs(primaryRaw)
      if (ts) pts.push({ t: ts, y: severityOrder(result.severity) })
    }
    if (!pts.length) return null
    pts.sort((a, b) => a.t.localeCompare(b.t))
    return pts
  }, [rawLines, batch, result, primaryRaw])

  if (!pieData) return null

  const layoutBase = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#a1a1aa', family: 'DM Sans, sans-serif', size: 11 },
    margin: { t: 28, r: 12, b: 28, l: 36 },
    showlegend: true,
    legend: { orientation: 'h' as const, y: -0.12 },
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">
        <p className="px-2 pt-2 text-xs font-medium uppercase tracking-wider text-zinc-500">Threat mix</p>
        <Plot
          data={[
            {
              type: 'pie',
              labels: pieData.labels,
              values: pieData.values,
              marker: {
                colors: ['#52525b', '#16a34a', '#ca8a04', '#ea580c', '#dc2626'],
              },
              hole: 0.45,
              textinfo: 'label+percent',
            },
          ]}
          layout={{
            ...layoutBase,
            title: { text: batch?.length ? 'Batch severities' : 'Severity spectrum', font: { size: 13 } },
            height: 280,
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: '100%' }}
        />
      </div>
      <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-2">
        <p className="px-2 pt-2 text-xs font-medium uppercase tracking-wider text-zinc-500">Timeline</p>
        {timeline ? (
          <Plot
            data={[
              {
                type: 'scatter',
                mode: 'lines+markers',
                x: timeline.map((p) => p.t),
                y: timeline.map((p) => p.y),
                line: { color: '#dc2626', width: 2 },
                marker: { size: 9, color: '#f87171' },
              },
            ]}
            layout={{
              ...layoutBase,
              title: { text: 'Severity index vs timestamp', font: { size: 13 } },
              yaxis: {
                tickvals: [0, 1, 2, 3, 4],
                ticktext: ['info', 'low', 'medium', 'high', 'critical'],
              },
              height: 280,
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        ) : (
          <p className="p-6 text-sm text-zinc-500">
            Timeline appears when logs include parseable ISO-style timestamps (e.g. 2024-11-02T14:22:01Z).
          </p>
        )}
      </div>
    </div>
  )
}
