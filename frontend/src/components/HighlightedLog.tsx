import { useMemo } from 'react'
import type { TokenHighlight } from '../types'

function heatColor(score: number): string {
  if (score >= 0.75) return 'rgba(220, 38, 38, 0.55)'
  if (score >= 0.5) return 'rgba(234, 179, 8, 0.4)'
  if (score >= 0.35) return 'rgba(59, 130, 246, 0.35)'
  return 'rgba(113, 113, 122, 0.25)'
}

export function HighlightedLog({ text, highlights }: { text: string; highlights: TokenHighlight[] }) {
  const segments = useMemo(() => {
    if (!text.length) return []
    const scores = new Float32Array(text.length)
    for (const h of highlights) {
      const a = Math.max(0, h.start)
      const b = Math.min(text.length, h.end)
      for (let i = a; i < b; i++) scores[i] = Math.max(scores[i], h.score)
    }
    const out: { text: string; score: number }[] = []
    let i = 0
    while (i < text.length) {
      const s = scores[i]
      let j = i + 1
      while (j < text.length && scores[j] === s) j++
      out.push({ text: text.slice(i, j), score: s })
      i = j
    }
    return out
  }, [text, highlights])

  return (
    <pre className="whitespace-pre-wrap break-all rounded-lg border border-zinc-800 bg-zinc-950/80 p-4 font-mono text-xs leading-relaxed text-zinc-300">
      {segments.map((seg, idx) =>
        seg.score > 0 ? (
          <span
            key={idx}
            title={`score ${seg.score.toFixed(2)}`}
            style={{
              backgroundColor: heatColor(seg.score),
              borderRadius: 2,
            }}
          >
            {seg.text}
          </span>
        ) : (
          <span key={idx}>{seg.text}</span>
        ),
      )}
    </pre>
  )
}
