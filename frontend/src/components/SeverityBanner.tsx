import { AlertTriangle, Cpu } from 'lucide-react'
import type { Severity } from '../types'

const styles: Record<Severity, string> = {
  critical: 'from-red-950/90 to-red-900/40 border-red-600 text-red-100',
  high: 'from-orange-950/80 to-orange-900/30 border-orange-600 text-orange-100',
  medium: 'from-amber-950/70 to-amber-900/25 border-amber-600 text-amber-100',
  low: 'from-emerald-950/60 to-emerald-900/20 border-emerald-700 text-emerald-100',
  info: 'from-zinc-800/80 to-zinc-900/40 border-zinc-600 text-zinc-200',
}

const ANOMALY_THRESHOLD = 0.6

/** Semi-circular gauge; label kept outside SVG to avoid overlap with body text. */
function AnomalyGauge({ value, threshold }: { value: number; threshold: number }) {
  const v = Math.min(1, Math.max(0, value))
  const r = 48
  const cx = 56
  const cy = 52
  const arcLen = Math.PI * r
  const filled = v * arcLen
  const thrAngle = Math.PI * (1 - threshold)
  const thrX = cx + r * Math.cos(Math.PI - thrAngle)
  const thrY = cy - r * Math.sin(Math.PI - thrAngle)

  return (
    <div className="flex shrink-0 flex-col items-center gap-1">
      <svg width="112" height="58" viewBox="0 0 112 58" className="overflow-visible" aria-hidden>
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="rgba(0,0,0,0.4)"
          strokeWidth="7"
          strokeLinecap="round"
        />
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={v > threshold ? 'rgb(251 191 36)' : 'rgba(255,255,255,0.5)'}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${arcLen}`}
        />
        <line
          x1={thrX}
          y1={thrY}
          x2={thrX}
          y2={thrY - 9}
          stroke="rgba(250,250,250,0.45)"
          strokeWidth="1.5"
        />
      </svg>
      <span className="text-center text-[10px] font-mono leading-tight text-white/55">
        threshold {threshold}
      </span>
    </div>
  )
}

export function SeverityBanner({
  severity,
  score,
  format,
  ms,
  anomalyScore,
  isolationAnomaly,
}: {
  severity: Severity
  score: number
  format: string
  ms: number
  anomalyScore?: number | null
  isolationAnomaly?: boolean
}) {
  const a = anomalyScore
  const showAnomaly = typeof a === 'number' && !Number.isNaN(a)
  const normalizeSeverityDisplay = (s: number) => {
    if (!Number.isFinite(s)) return 0
    if (s >= 0 && s <= 1) return s
    /* Backend / model quirks: values like 8.99 often mean 0.899 */
    if (s > 1 && s <= 10) return Math.min(1, s / 10)
    return Math.min(1, Math.max(0, s))
  }
  const displayScore = normalizeSeverityDisplay(score)

  return (
    <div className={`rounded-xl border bg-gradient-to-r px-4 py-5 sm:px-6 ${styles[severity]}`}>
      {/* Primary classification: single column, no side-by-side with gauge (prevents overlap). */}
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-2 gap-y-2">
          <p className="text-xs uppercase tracking-[0.2em] text-white/70">Classification</p>
          <span className="inline-flex max-w-full items-center gap-1 rounded border border-white/20 bg-black/25 px-2 py-1 text-[10px] font-medium leading-snug text-white/75 sm:text-[11px]">
            <Cpu className="h-3.5 w-3.5 shrink-0" />
            <span className="break-words">HF Inference · zero-shot / NER / LLM</span>
          </span>
          {isolationAnomaly && (
            <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/60 bg-black/30 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
              <AlertTriangle className="h-3 w-3 shrink-0" />
              NLP outlier
            </span>
          )}
        </div>

        <div className="border-b border-white/10 pb-4">
          <p className="text-3xl font-bold leading-none tracking-tight sm:text-4xl">{severity.toUpperCase()}</p>
          <p className="mt-3 text-sm leading-relaxed opacity-95">
            Severity model score{' '}
            <span className="font-mono text-base font-semibold tabular-nums">{displayScore.toFixed(3)}</span>
            <span className="text-xs text-white/50"> (0–1)</span>
          </p>
          <p className="mt-2 text-xs leading-relaxed text-white/60">
            Format <span className="font-mono text-white/80">{format}</span> · pipeline {ms} ms
          </p>
        </div>
      </div>

      {showAnomaly && (
        <div className="mt-5 rounded-lg border border-white/15 bg-black/30 p-4 sm:p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-200/90">
            Secondary detector · Isolation Forest
          </p>
          <div className="mt-4 flex flex-col gap-5 sm:flex-row sm:items-start sm:gap-6">
            <AnomalyGauge value={a} threshold={ANOMALY_THRESHOLD} />
            <div className="min-w-0 flex-1 space-y-3 text-sm">
              <p className="text-xs leading-relaxed text-white/80 sm:text-sm">
                <span className="font-semibold text-white">Isolation Forest</span> (scikit-learn,{' '}
                <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-[11px] text-white/90">
                  n_jobs=-1
                </code>
                ) on <span className="font-semibold text-white">MiniLM</span> sentence embeddings. Scores are{' '}
                <span className="italic">relative to this batch</span> (MinMax); flag if &gt; {ANOMALY_THRESHOLD}.
              </p>
              <div>
                <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-wide text-white/45">
                  <span>Anomaly score</span>
                  <span className="font-mono text-white/80">{a.toFixed(3)}</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-black/40">
                  <div
                    className={`h-full rounded-full transition-all ${a > ANOMALY_THRESHOLD ? 'bg-amber-400' : 'bg-white/50'}`}
                    style={{ width: `${Math.min(100, a * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
