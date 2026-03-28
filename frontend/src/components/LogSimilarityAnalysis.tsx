import { Activity, GitBranch, Network } from 'lucide-react'
import type { SimilarityIncident, TfidfKeywordsByIncident } from '../types'

function keywordsForIncident(
  incidentId: number,
  groups: TfidfKeywordsByIncident[],
): TfidfKeywordsByIncident['keywords'] {
  return groups.find((g) => g.incident_id === incidentId)?.keywords ?? []
}

/** Larger boxes + readable type; horizontal scroll on narrow viewports. */
function TfidfPipelineDiagram() {
  return (
    <div className="overflow-x-auto pb-1">
      <svg
        viewBox="0 0 520 108"
        className="mx-auto block h-[min(7.5rem,28vw)] w-full min-w-[320px] max-w-2xl text-zinc-400"
        aria-hidden
      >
        <defs>
          <marker id="m-tfidf" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill="#f87171" fillOpacity={0.85} />
          </marker>
        </defs>
        <rect x="8" y="32" width="88" height="48" rx="8" fill="#18181b" stroke="#52525b" strokeWidth="1.5" />
        <text x="52" y="58" textAnchor="middle" fill="#e4e4e7" fontSize="12" fontFamily="system-ui, sans-serif">
          Raw logs
        </text>
        <text x="52" y="74" textAnchor="middle" fill="#71717a" fontSize="10" fontFamily="system-ui, sans-serif">
          per line
        </text>
        <line
          x1="96"
          y1="56"
          x2="128"
          y2="56"
          stroke="#f87171"
          strokeOpacity={0.65}
          strokeWidth="2"
          markerEnd="url(#m-tfidf)"
        />
        <rect x="132" y="28" width="108" height="56" rx="8" fill="#18181b" stroke="#52525b" strokeWidth="1.5" />
        <text x="186" y="52" textAnchor="middle" fill="#e4e4e7" fontSize="11" fontFamily="system-ui, sans-serif">
          TfidfVectorizer
        </text>
        <text x="186" y="68" textAnchor="middle" fill="#71717a" fontSize="10" fontFamily="system-ui, sans-serif">
          sklearn
        </text>
        <line
          x1="240"
          y1="56"
          x2="272"
          y2="56"
          stroke="#f87171"
          strokeOpacity={0.65}
          strokeWidth="2"
          markerEnd="url(#m-tfidf)"
        />
        <rect x="276" y="28" width="118" height="56" rx="8" fill="#18181b" stroke="#52525b" strokeWidth="1.5" />
        <text x="335" y="52" textAnchor="middle" fill="#e4e4e7" fontSize="11" fontFamily="system-ui, sans-serif">
          cosine_similarity
        </text>
        <text x="335" y="68" textAnchor="middle" fill="#71717a" fontSize="10" fontFamily="system-ui, sans-serif">
          graph &gt; 0.75
        </text>
        <line
          x1="394"
          y1="56"
          x2="426"
          y2="56"
          stroke="#f87171"
          strokeOpacity={0.65}
          strokeWidth="2"
          markerEnd="url(#m-tfidf)"
        />
        <rect x="430" y="24" width="82" height="64" rx="8" fill="rgba(127,29,29,0.35)" stroke="#991b1b" strokeWidth="1.5" />
        <text x="471" y="54" textAnchor="middle" fill="#fecaca" fontSize="12" fontFamily="system-ui, sans-serif" fontWeight="600">
          Incidents
        </text>
        <text x="471" y="72" textAnchor="middle" fill="#fca5a5" fontSize="10" fontFamily="system-ui, sans-serif">
          + keywords
        </text>
      </svg>
    </div>
  )
}

function IsolationForestPipelineDiagram() {
  return (
    <div className="overflow-x-auto pb-1">
      <svg
        viewBox="0 0 480 108"
        className="mx-auto block h-[min(7.5rem,28vw)] w-full min-w-[300px] max-w-xl text-zinc-400"
        aria-hidden
      >
        <defs>
          <marker id="m-if" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill="#fbbf24" fillOpacity={0.8} />
          </marker>
        </defs>
        <rect x="8" y="32" width="88" height="48" rx="8" fill="#18181b" stroke="#52525b" strokeWidth="1.5" />
        <text x="52" y="60" textAnchor="middle" fill="#e4e4e7" fontSize="12" fontFamily="system-ui, sans-serif">
          Raw logs
        </text>
        <line
          x1="96"
          y1="56"
          x2="120"
          y2="56"
          stroke="#fbbf24"
          strokeOpacity={0.55}
          strokeWidth="2"
          markerEnd="url(#m-if)"
        />
        <rect x="124" y="26" width="120" height="58" rx="8" fill="#18181b" stroke="#52525b" strokeWidth="1.5" />
        <text x="184" y="50" textAnchor="middle" fill="#e4e4e7" fontSize="11" fontFamily="system-ui, sans-serif">
          MiniLM-L6-v2
        </text>
        <text x="184" y="68" textAnchor="middle" fill="#71717a" fontSize="10" fontFamily="system-ui, sans-serif">
          sentence-transformers
        </text>
        <line
          x1="244"
          y1="56"
          x2="268"
          y2="56"
          stroke="#fbbf24"
          strokeOpacity={0.55}
          strokeWidth="2"
          markerEnd="url(#m-if)"
        />
        <rect x="272" y="26" width="118" height="58" rx="8" fill="#18181b" stroke="#52525b" strokeWidth="1.5" />
        <text x="331" y="50" textAnchor="middle" fill="#e4e4e7" fontSize="11" fontFamily="system-ui, sans-serif">
          IsolationForest
        </text>
        <text x="331" y="68" textAnchor="middle" fill="#71717a" fontSize="10" fontFamily="system-ui, sans-serif">
          sklearn · n_jobs=-1
        </text>
        <line
          x1="390"
          y1="56"
          x2="414"
          y2="56"
          stroke="#fbbf24"
          strokeOpacity={0.55}
          strokeWidth="2"
          markerEnd="url(#m-if)"
        />
        <rect x="418" y="34" width="54" height="44" rx="8" fill="rgba(120,53,15,0.35)" stroke="#b45309" strokeWidth="1.5" />
        <text x="445" y="62" textAnchor="middle" fill="#fde68a" fontSize="12" fontFamily="system-ui, sans-serif" fontWeight="600">
          0–1
        </text>
      </svg>
    </div>
  )
}

function IncidentGraphViz({ indices }: { indices: number[] }) {
  const n = indices.length
  if (n === 0) return null
  const w = Math.min(320, 48 + n * 40)
  const h = 64
  const cx = (i: number) => 32 + (i * (w - 64)) / Math.max(1, n - 1)
  const cy = 40

  return (
    <svg width={w} height={h} className="mt-3 text-red-400/75" aria-hidden>
      {indices.flatMap((_, i) =>
        indices.slice(i + 1).map((_, j) => {
          const jAbs = i + 1 + j
          return (
            <line
              key={`e-${i}-${jAbs}`}
              x1={cx(i)}
              y1={cy}
              x2={cx(jAbs)}
              y2={cy}
              stroke="currentColor"
              strokeWidth="1.5"
              opacity={0.5}
            />
          )
        }),
      )}
      {indices.map((idx, i) => (
        <g key={idx}>
          <circle cx={cx(i)} cy={cy} r="16" className="fill-red-950 stroke-red-500/90" strokeWidth="2" />
          <text
            x={cx(i)}
            y={cy + 5}
            textAnchor="middle"
            fill="#fecaca"
            fontSize="11"
            fontFamily="ui-monospace, monospace"
            fontWeight="600"
          >
            {idx}
          </text>
        </g>
      ))}
    </svg>
  )
}

function KeywordBarChart({ keywords }: { keywords: { term: string; score: number }[] }) {
  const max = Math.max(...keywords.map((k) => k.score), 1e-9)
  return (
    <div className="mt-3 space-y-2.5" role="img" aria-label="TF-IDF term weights">
      {keywords.map((k, i) => (
        <div key={`${k.term}-${i}`} className="flex items-center gap-3 text-sm">
          <span className="w-32 shrink-0 truncate font-mono text-sm text-red-200/90 sm:w-36" title={k.term}>
            {k.term}
          </span>
          <div className="h-6 min-w-0 flex-1 overflow-hidden rounded-md bg-zinc-900">
            <div
              className="h-full rounded-l-md bg-gradient-to-r from-red-900/85 to-red-600/75 transition-all"
              style={{ width: `${Math.min(100, (k.score / max) * 100)}%` }}
            />
          </div>
          <span className="w-16 shrink-0 text-right font-mono text-xs text-zinc-400 tabular-nums sm:text-sm">
            {k.score.toFixed(3)}
          </span>
        </div>
      ))}
    </div>
  )
}

function BatchAnomalyBarChart({ scores }: { scores: number[] }) {
  const TH = 0.6
  const max = Math.max(...scores, 1e-9)
  return (
    <div className="mt-4 space-y-2" role="img" aria-label="Per-log anomaly scores">
      <p className="text-xs leading-relaxed text-zinc-500">
        Bar length is proportional to score within this batch. Vertical rule marks threshold <span className="font-mono text-zinc-400">{TH}</span>.
      </p>
      {scores.map((s, i) => (
        <div key={i} className="flex items-center gap-3 text-sm">
          <span className="w-9 shrink-0 font-mono text-sm text-zinc-500">#{i}</span>
          <div className="relative h-7 min-w-0 flex-1 overflow-hidden rounded-md bg-zinc-900">
            <div
              className={`h-full rounded-l-md ${s > TH ? 'bg-amber-500/90' : 'bg-amber-900/45'}`}
              style={{ width: `${Math.min(100, (s / max) * 100)}%` }}
            />
            <div
              className="pointer-events-none absolute bottom-0 top-0 w-0.5 bg-white/50"
              style={{ left: `${Math.min(100, (TH / max) * 100)}%` }}
            />
          </div>
          <span
            className={`w-14 shrink-0 text-right font-mono text-sm tabular-nums ${s > TH ? 'text-amber-300' : 'text-zinc-500'}`}
          >
            {s.toFixed(2)}
          </span>
        </div>
      ))}
    </div>
  )
}

export function LogSimilarityAnalysis({
  incidents,
  tfidfKeywords,
  rawLines,
  anomalyScores,
  hasFullBatch,
}: {
  incidents: SimilarityIncident[]
  tfidfKeywords: TfidfKeywordsByIncident[]
  rawLines: string[] | null
  anomalyScores?: number[]
  hasFullBatch: boolean
}) {
  return (
    <div className="space-y-8">
      <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Network className="h-5 w-5 shrink-0 text-red-400" />
          <h2 className="text-base font-semibold text-zinc-100 sm:text-lg">Log similarity &amp; batch NLP</h2>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-zinc-500">
          Two <span className="text-zinc-400">local</span> algorithms complement the Hugging Face pipeline. They run on{' '}
          <strong className="font-medium text-zinc-300">batch</strong> requests only (≥2 log lines).
        </p>

        <div className="mt-8 grid gap-8 border-t border-zinc-800/90 pt-8 lg:grid-cols-2">
          <div className="min-w-0 space-y-3">
            <p className="flex items-center gap-2 text-sm font-semibold text-red-200">
              <GitBranch className="h-4 w-4 shrink-0" />
              TF-IDF + cosine similarity
            </p>
            <p className="text-sm leading-relaxed text-zinc-500">
              Sparse vectors per log → pairwise cosine → link if similarity &gt;{' '}
              <code className="rounded bg-zinc-900 px-1.5 py-0.5 font-mono text-xs text-zinc-300">0.75</code> → connected
              components = incidents. Top terms aggregate TF-IDF mass per group.
            </p>
            <div className="rounded-xl border border-zinc-800/80 bg-black/30 p-4 sm:p-5">
              <TfidfPipelineDiagram />
            </div>
          </div>
          <div className="min-w-0 space-y-3">
            <p className="flex items-center gap-2 text-sm font-semibold text-amber-200">
              <Activity className="h-4 w-4 shrink-0" />
              Isolation Forest
            </p>
            <p className="text-sm leading-relaxed text-zinc-500">
              Sentence embeddings → isolation trees → scores scaled to{' '}
              <code className="rounded bg-zinc-900 px-1.5 py-0.5 font-mono text-xs text-zinc-300">0–1</code> within the batch
              to surface outliers vs the cohort.
            </p>
            <div className="rounded-xl border border-zinc-800/80 bg-black/30 p-4 sm:p-5">
              <IsolationForestPipelineDiagram />
            </div>
          </div>
        </div>
      </div>

      {!hasFullBatch && (
        <div className="rounded-xl border border-dashed border-zinc-600 bg-zinc-950/40 p-8 text-center">
          <p className="mx-auto max-w-lg text-sm leading-relaxed text-zinc-400">
            Run <span className="font-semibold text-zinc-300">Analyze batch (multi-line)</span> or{' '}
            <span className="font-semibold text-zinc-300">Batch upload</span> with at least two lines to populate TF-IDF
            incidents, keyword bars, and per-log anomaly scores.
          </p>
        </div>
      )}

      {hasFullBatch && anomalyScores && anomalyScores.length > 0 && (
        <div className="rounded-xl border border-amber-900/50 bg-amber-950/15 p-5 sm:p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-200/90">Isolation Forest — per log</h3>
          <BatchAnomalyBarChart scores={anomalyScores} />
        </div>
      )}

      {hasFullBatch && !incidents.length && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-5">
          <h3 className="text-base font-medium text-zinc-200">TF-IDF incidents</h3>
          <p className="mt-2 text-sm leading-relaxed text-zinc-500">
            No groups above the cosine threshold — lines in this batch are dissimilar in bag-of-words space, or the batch is
            too small.
          </p>
        </div>
      )}

      {incidents.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-5 sm:p-6">
          <h3 className="text-base font-semibold text-zinc-100 sm:text-lg">TF-IDF incidents &amp; terms</h3>
          <ul className="mt-6 space-y-8">
            {incidents.map((inc) => {
              const kws = keywordsForIncident(inc.incident_id, tfidfKeywords)
              return (
                <li key={inc.incident_id} className="rounded-xl border border-zinc-800/90 bg-black/30 p-5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="text-base font-medium text-red-200">Incident #{inc.incident_id + 1}</span>
                    <span className="font-mono text-sm text-zinc-500">
                      mean cos {inc.mean_cosine_similarity.toFixed(3)} · min {inc.min_cosine_similarity.toFixed(3)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-zinc-500">
                    Log indices: <span className="font-mono text-zinc-300">{inc.log_indices.join(', ')}</span>
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">Similarity component (indices = positions in batch)</p>
                  <IncidentGraphViz indices={inc.log_indices} />
                  {rawLines && (
                    <ul className="mt-4 max-h-36 space-y-2 overflow-y-auto text-sm leading-snug text-zinc-500">
                      {inc.log_indices.slice(0, 6).map((idx) => (
                        <li key={idx} className="break-all font-mono text-xs sm:text-sm" title={rawLines[idx]}>
                          <span className="text-zinc-600">[{idx}]</span> {rawLines[idx]?.slice(0, 140)}
                          {(rawLines[idx]?.length ?? 0) > 140 ? '…' : ''}
                        </li>
                      ))}
                      {inc.log_indices.length > 6 && (
                        <li className="text-zinc-600">+{inc.log_indices.length - 6} more…</li>
                      )}
                    </ul>
                  )}
                  {kws.length > 0 && (
                    <div className="mt-5 border-t border-zinc-800/70 pt-5">
                      <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Top TF-IDF terms</p>
                      <KeywordBarChart keywords={kws} />
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
