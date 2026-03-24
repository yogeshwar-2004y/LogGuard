import { Loader2, Send } from 'lucide-react'
import { useState } from 'react'
import { chatFollowupStream } from '../api'
import type { Industry } from '../types'

export function ChatPanel({
  industry,
  contextSnippet,
}: {
  industry: Industry
  contextSnippet: string
}) {
  const [input, setInput] = useState('')
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function send() {
    const q = input.trim()
    if (!q || loading) return
    setLoading(true)
    setErr(null)
    setReply('')
    try {
      await chatFollowupStream(
        [
          { role: 'user', content: 'Summarize defensive next steps for this log.' },
          { role: 'assistant', content: 'Use containment, enrichment, and hunting queries as outlined in the playbook.' },
          { role: 'user', content: q },
        ],
        industry,
        contextSnippet.slice(0, 6000),
        (chunk) => setReply((r) => r + chunk),
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Chat failed')
    } finally {
      setLoading(false)
      setInput('')
    }
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-4">
      <h3 className="text-sm font-semibold text-zinc-200">Ask follow-up (streamed)</h3>
      <p className="mt-1 text-xs text-zinc-500">Uses the generative model on the backend; no conversation is stored server-side.</p>
      <div className="mt-3 min-h-[100px] rounded-lg border border-zinc-800/80 bg-black/30 p-3 font-mono text-sm text-zinc-300 whitespace-pre-wrap">
        {reply || (loading ? '…' : 'Responses appear here.')}
      </div>
      {err && <p className="mt-2 text-xs text-red-400">{err}</p>}
      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), void send())}
          placeholder="e.g. What Splunk query hunts similar PowerShell?"
          className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-red-800"
        />
        <button
          type="button"
          onClick={() => void send()}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Send
        </button>
      </div>
    </div>
  )
}
