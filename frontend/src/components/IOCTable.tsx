import { ExternalLink } from 'lucide-react'
import type { IOC } from '../types'

function vtUrl(t: string, v: string) {
  if (t === 'ip') return `https://www.virustotal.com/gui/ip-address/${encodeURIComponent(v)}`
  if (t === 'domain') return `https://www.virustotal.com/gui/domain/${encodeURIComponent(v)}`
  if (t === 'url') return `https://www.virustotal.com/gui/url/${encodeURIComponent(v)}`
  if (t === 'hash') return `https://www.virustotal.com/gui/file/${encodeURIComponent(v)}`
  return `https://www.virustotal.com/gui/search/${encodeURIComponent(v)}`
}

function abuseIp(v: string) {
  return `https://www.abuseipdb.com/check/${encodeURIComponent(v)}`
}

function hybridHash(v: string) {
  return `https://www.hybrid-analysis.com/search?query=${encodeURIComponent(v)}`
}

export function IOCTable({ iocs }: { iocs: IOC[] }) {
  if (!iocs.length) {
    return <p className="text-sm text-zinc-500">No IOCs extracted from this log.</p>
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-800 bg-zinc-900/80 text-xs uppercase tracking-wide text-zinc-500">
            <th className="px-3 py-2">Type</th>
            <th className="px-3 py-2">Value</th>
            <th className="px-3 py-2">Intel</th>
          </tr>
        </thead>
        <tbody>
          {iocs.map((ioc, i) => (
            <tr key={i} className="border-b border-zinc-800/80 hover:bg-zinc-900/40">
              <td className="px-3 py-2 font-mono text-xs text-red-300/90">{ioc.type}</td>
              <td className="max-w-[240px] truncate px-3 py-2 font-mono text-xs text-zinc-200" title={ioc.value}>
                {ioc.value}
              </td>
              <td className="px-3 py-2">
                <div className="flex flex-wrap gap-2">
                  <a
                    href={vtUrl(ioc.type, ioc.value)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300 hover:bg-red-950/50 hover:text-red-200"
                  >
                    VT <ExternalLink className="h-3 w-3" />
                  </a>
                  {ioc.type === 'ip' && (
                    <a
                      href={abuseIp(ioc.value)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300 hover:bg-red-950/50 hover:text-red-200"
                    >
                      AbuseIPDB <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                  {ioc.type === 'hash' && (
                    <a
                      href={hybridHash(ioc.value)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300 hover:bg-red-950/50 hover:text-red-200"
                    >
                      Hybrid <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
