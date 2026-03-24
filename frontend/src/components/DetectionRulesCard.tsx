import { Copy, Download, FlaskConical, Pencil } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { testSigma } from '../api'
import type { DetectionRules } from '../types'

type RuleMode = 'sigma' | 'yara' | 'both'

export function DetectionRulesCard({
  rules,
  logLines,
}: {
  rules: DetectionRules
  logLines: string[]
}) {
  const [mode, setMode] = useState<RuleMode>('sigma')
  const [customOpen, setCustomOpen] = useState(false)
  const [editTitle, setEditTitle] = useState(rules.title)
  const [editDesc, setEditDesc] = useState('')
  const [sigmaText, setSigmaText] = useState(rules.sigma_yaml)
  const [yaraText, setYaraText] = useState(rules.yara_rule ?? '')
  const [testResult, setTestResult] = useState<string | null>(null)
  const [testLoading, setTestLoading] = useState(false)

  useEffect(() => {
    setSigmaText(rules.sigma_yaml)
    setYaraText(rules.yara_rule ?? '')
    setEditTitle(rules.title)
  }, [rules])

  const yara = rules.yara_rule ?? ''

  const displaySigma = useMemo(() => {
    if (!editDesc.trim()) return sigmaText
    return `# ${editTitle}\n# ${editDesc}\n${sigmaText}`
  }, [editTitle, editDesc, sigmaText])

  const copyPayload = useCallback(() => {
    let t = ''
    if (mode === 'sigma' || mode === 'both') t += displaySigma
    if (mode === 'both') t += '\n\n---\n\n'
    if (mode === 'yara' || mode === 'both') t += yaraText || yara
    void navigator.clipboard.writeText(t)
  }, [mode, displaySigma, yaraText, yara])

  const downloadFile = useCallback(
    (ext: 'yml' | 'yar', body: string, name: string) => {
      const blob = new Blob([body], { type: 'text/plain' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${name.replace(/[^a-zA-Z0-9-_]+/g, '_').slice(0, 60) || 'logguard'}.${ext}`
      a.click()
      URL.revokeObjectURL(a.href)
    },
    [],
  )

  const runTest = useCallback(async () => {
    setTestLoading(true)
    setTestResult(null)
    try {
      const r = await testSigma(sigmaText, logLines)
      if (r.parse_error) {
        setTestResult(`Parse: ${r.parse_error}`)
        return
      }
      const lines = r.matching_indices.map((i) => `#${i}: ${(logLines[i] ?? '').slice(0, 120)}…`).join('\n')
      setTestResult(
        `Matches: ${r.match_count} / ${logLines.length}\nTokens used (sample): ${r.tokens_used.join(', ')}\n${lines || '(no line previews)'}`,
      )
    } catch (e) {
      setTestResult(e instanceof Error ? e.message : 'Test failed')
    } finally {
      setTestLoading(false)
    }
  }, [sigmaText, logLines])

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-zinc-200">Detection rules</h2>
        <div className="flex flex-wrap gap-1 rounded-lg border border-zinc-700 bg-zinc-900 p-0.5">
          {(['sigma', 'yara', 'both'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize ${
                mode === m ? 'bg-red-900/60 text-red-100' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <p className="mt-1 text-xs text-zinc-500">
        Sigma (YAML) by default; YARA for file/memory hunting. Author: LogGuard AI. False positives:{' '}
        {rules.false_positives}
      </p>

      <div className="mt-3 max-h-[420px] overflow-auto rounded-lg border border-zinc-800">
        {(mode === 'sigma' || mode === 'both') && (
          <SyntaxHighlighter
            language="yaml"
            style={oneDark}
            customStyle={{ margin: 0, fontSize: 11, background: '#0c0c0e' }}
            showLineNumbers
          >
            {displaySigma}
          </SyntaxHighlighter>
        )}
        {(mode === 'yara' || mode === 'both') && (yaraText || yara) && (
          <SyntaxHighlighter
            language="javascript"
            style={oneDark}
            customStyle={{ margin: 0, fontSize: 11, background: '#09090b' }}
            showLineNumbers
          >
            {yaraText || yara}
          </SyntaxHighlighter>
        )}
        {mode === 'yara' && !(yaraText || yara) && (
          <p className="p-4 text-sm text-zinc-500">No YARA rule in this response.</p>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void copyPayload()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-600 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <Copy className="h-3.5 w-3.5" /> Copy rule
        </button>
        <button
          type="button"
          onClick={() => {
            setEditTitle(rules.title)
            setEditDesc('')
            setCustomOpen(true)
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-600 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <Pencil className="h-3.5 w-3.5" /> Customize &amp; export
        </button>
        <button
          type="button"
          disabled={testLoading || !logLines.length}
          onClick={() => void runTest()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-red-900/60 bg-red-950/30 px-3 py-1.5 text-xs text-red-200 hover:bg-red-950/50 disabled:opacity-40"
        >
          <FlaskConical className="h-3.5 w-3.5" /> Test rule
        </button>
      </div>

      {testResult && (
        <pre className="mt-3 whitespace-pre-wrap rounded-lg border border-zinc-800 bg-black/40 p-3 font-mono text-xs text-zinc-400">
          {testResult}
        </pre>
      )}

      {customOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog">
          <div className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-xl border border-zinc-700 bg-zinc-950 p-4 shadow-xl">
            <h3 className="text-sm font-semibold text-zinc-100">Customize export</h3>
            <label className="mt-3 block text-xs text-zinc-500">Title</label>
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-200"
            />
            <label className="mt-2 block text-xs text-zinc-500">Description (prefixed as comments)</label>
            <textarea
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              rows={2}
              className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-sm text-zinc-200"
            />
            <label className="mt-2 block text-xs text-zinc-500">Sigma YAML (editable)</label>
            <textarea
              value={sigmaText}
              onChange={(e) => setSigmaText(e.target.value)}
              rows={10}
              className="mt-1 w-full font-mono text-xs rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-zinc-200"
            />
            <label className="mt-2 block text-xs text-zinc-500">YARA (editable)</label>
            <textarea
              value={yaraText}
              onChange={(e) => setYaraText(e.target.value)}
              rows={8}
              className="mt-1 w-full font-mono text-xs rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-zinc-200"
            />
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => downloadFile('yml', displaySigma, editTitle)}
                className="inline-flex items-center gap-1 rounded-lg bg-zinc-100 px-3 py-2 text-xs font-medium text-zinc-900"
              >
                <Download className="h-3.5 w-3.5" /> .yml
              </button>
              {(yaraText || yara) && (
                <button
                  type="button"
                  onClick={() => downloadFile('yar', yaraText || yara, editTitle)}
                  className="inline-flex items-center gap-1 rounded-lg border border-zinc-600 px-3 py-2 text-xs text-zinc-200"
                >
                  <Download className="h-3.5 w-3.5" /> .yar
                </button>
              )}
              <button
                type="button"
                onClick={() => setCustomOpen(false)}
                className="ml-auto rounded-lg px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
