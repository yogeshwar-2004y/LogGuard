import { ExternalLink } from 'lucide-react'
import type { MitreTechnique } from '../types'

export function MitreMatrix({ techniques }: { techniques: MitreTechnique[] }) {
  if (!techniques.length) {
    return (
      <p className="text-sm text-zinc-500">No MITRE mappings above confidence threshold — refine the log or enrich with threat intel.</p>
    )
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {techniques.map((m) => (
        <a
          key={m.id + m.name}
          href={m.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex flex-col rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 transition hover:border-red-900/60 hover:bg-zinc-900"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-sm font-semibold text-red-400">{m.id}</span>
            <ExternalLink className="h-4 w-4 shrink-0 text-zinc-500 group-hover:text-red-400" />
          </div>
          <p className="mt-1 text-sm text-zinc-200">{m.name}</p>
          <p className="mt-2 text-xs text-zinc-500">Confidence {(m.confidence * 100).toFixed(0)}%</p>
        </a>
      ))}
    </div>
  )
}
