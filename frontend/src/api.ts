import type {
  AnalyzeResponse,
  BatchAnalyzeResponse,
  DemoLogEntry,
  Industry,
  TestSigmaResponse,
} from './types'

const base = () => import.meta.env.VITE_API_BASE || '/api'

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const t = await res.text()
    throw new Error(t || res.statusText)
  }
  return res.json() as Promise<T>
}

export async function analyzeLog(logText: string, industry: Industry): Promise<AnalyzeResponse> {
  const res = await fetch(`${base()}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ log_text: logText, industry }),
  })
  return parseJson<AnalyzeResponse>(res)
}

export async function analyzeBatchUpload(file: File, industry: Industry): Promise<BatchAnalyzeResponse> {
  const fd = new FormData()
  fd.append('industry', industry)
  fd.append('files', file)
  const res = await fetch(`${base()}/analyze-batch-upload`, { method: 'POST', body: fd })
  return parseJson<BatchAnalyzeResponse>(res)
}

export async function analyzeBatchLines(lines: string[], industry: Industry): Promise<BatchAnalyzeResponse> {
  const res = await fetch(`${base()}/analyze-batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      logs: lines.map((raw_log, i) => ({ raw_log, line_index: i })),
      industry,
    }),
  })
  return parseJson<BatchAnalyzeResponse>(res)
}

export async function fetchDemoLogs(): Promise<DemoLogEntry[]> {
  const res = await fetch(`${base()}/demo-logs`)
  return parseJson<DemoLogEntry[]>(res)
}

export async function downloadPdf(result: AnalyzeResponse): Promise<Blob> {
  const res = await fetch(`${base()}/report/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(result),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.blob()
}

export async function chatFollowup(
  messages: { role: 'user' | 'assistant'; content: string }[],
  industry: Industry,
  contextLogSnippet?: string,
): Promise<string> {
  const res = await fetch(`${base()}/chat-followup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, industry, context_log_snippet: contextLogSnippet }),
  })
  const data = await parseJson<{ reply: string }>(res)
  return data.reply
}

export async function chatFollowupStream(
  messages: { role: 'user' | 'assistant'; content: string }[],
  industry: Industry,
  contextLogSnippet: string | undefined,
  onChunk: (s: string) => void,
): Promise<void> {
  const res = await fetch(`${base()}/chat-followup/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, industry, context_log_snippet: contextLogSnippet }),
  })
  if (!res.ok || !res.body) throw new Error('Stream failed')
  const reader = res.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const payload = line.slice(6).trim()
        if (payload === '[DONE]') return
        if (payload.startsWith('[error]')) throw new Error(payload)
        try {
          onChunk(JSON.parse(payload) as string)
        } catch {
          onChunk(payload)
        }
      }
    }
  }
}

export async function testSigma(sigmaYaml: string, logs: string[]): Promise<TestSigmaResponse> {
  const res = await fetch(`${base()}/test-sigma`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sigma_yaml: sigmaYaml, logs }),
  })
  return parseJson<TestSigmaResponse>(res)
}

export function iocsToCsv(iocs: AnalyzeResponse['iocs']): string {
  const rows = [['type', 'value', 'context'], ...iocs.map((i) => [i.type, i.value, i.context ?? ''])]
  return rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
}
