import type { Severity } from '../types'

const styles: Record<Severity, string> = {
  critical: 'from-red-950/90 to-red-900/40 border-red-600 text-red-100',
  high: 'from-orange-950/80 to-orange-900/30 border-orange-600 text-orange-100',
  medium: 'from-amber-950/70 to-amber-900/25 border-amber-600 text-amber-100',
  low: 'from-emerald-950/60 to-emerald-900/20 border-emerald-700 text-emerald-100',
  info: 'from-zinc-800/80 to-zinc-900/40 border-zinc-600 text-zinc-200',
}

export function SeverityBanner({ severity, score, format, ms }: { severity: Severity; score: number; format: string; ms: number }) {
  return (
    <div
      className={`rounded-xl border bg-gradient-to-r px-5 py-4 ${styles[severity]}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-white/70">Classification</p>
          <p className="text-2xl font-bold tracking-tight">{severity.toUpperCase()}</p>
        </div>
        <div className="text-right text-sm opacity-90">
          <p>
            Score <span className="font-mono font-semibold">{score.toFixed(3)}</span>
          </p>
          <p className="text-xs text-white/60">
            Format: <span className="font-mono">{format}</span> · {ms} ms
          </p>
        </div>
      </div>
    </div>
  )
}
