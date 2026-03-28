import {
  BarChart3,
  BookOpen,
  FileCode2,
  FileUp,
  Flame,
  Fingerprint,
  LayoutDashboard,
  Loader2,
  MessageSquare,
  Network,
  Radar,
  ScrollText,
  Shield,
  Sparkles,
  Target,
  Trash2,
  Workflow,
} from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import {
  analyzeBatchLines,
  analyzeBatchUpload,
  analyzeLog,
  downloadPdf,
  fetchDemoLogs,
  iocsToCsv,
} from './api'
import { AttackChainSection } from './components/AttackChainFlow'
import { ChatPanel } from './components/ChatPanel'
import { DetectionRulesCard } from './components/DetectionRulesCard'
import { DashboardCharts } from './components/DashboardCharts'
import { LogSimilarityAnalysis } from './components/LogSimilarityAnalysis'
import { DashboardTabs, type DashboardTabId } from './components/DashboardTabs'
import { HighlightedLog } from './components/HighlightedLog'
import { IOCTable } from './components/IOCTable'
import { MitreMatrix } from './components/MitreMatrix'
import { SeverityBanner } from './components/SeverityBanner'
import type { AnalyzeResponse, BatchAnalyzeResponse, Industry } from './types'

const INDUSTRIES: { value: Industry; label: string }[] = [
  { value: 'default', label: 'Default' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'finance', label: 'Finance' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'energy', label: 'Energy' },
  { value: 'government', label: 'Government' },
  { value: 'cloud', label: 'Cloud' },
]

export default function App() {
  const [industry, setIndustry] = useState<Industry>('default')
  const [logText, setLogText] = useState('')
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [batch, setBatch] = useState<BatchAnalyzeResponse | null>(null)
  const [rawLines, setRawLines] = useState<string[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [demoLoading, setDemoLoading] = useState(false)
  const [batchFile, setBatchFile] = useState<File | null>(null)
  const [dashboardTab, setDashboardTab] = useState<DashboardTabId>('overview')
  const [batchIndex, setBatchIndex] = useState(0)

  const showBatchNlpTab = Boolean(batch && batch.results.length >= 2)

  const logLinesForTest = useMemo(() => {
    if (rawLines?.length) return rawLines
    const t = logText.trim()
    return t ? [t] : []
  }, [rawLines, logText])

  const batchAttackChains = useMemo(() => {
    if (!batch?.results || batch.results.length <= 1) return null
    return batch.results.map((r) => r.attack_chain)
  }, [batch])

  const runAnalyze = useCallback(async () => {
    const t = logText.trim()
    if (!t) {
      setError('Paste a log or load a demo.')
      return
    }
    setLoading(true)
    setError(null)
    setBatch(null)
    setRawLines(null)
    setBatchIndex(0)
    setDashboardTab('overview')
    try {
      const r = await analyzeLog(t, industry)
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }, [logText, industry])

  const runBatch = useCallback(async () => {
    const lines = logText
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean)
    if (lines.length < 2) {
      setError('Enter at least two non-empty lines or upload a multi-line file for batch mode.')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const b = await analyzeBatchLines(lines, industry)
      setBatch(b)
      setBatchIndex(0)
      setDashboardTab('overview')
      setRawLines(lines)
      setResult(b.results[0] ?? null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Batch failed')
      setBatch(null)
    } finally {
      setLoading(false)
    }
  }, [logText, industry])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (!f) return
    void f.text().then((t) => setLogText(t))
  }, [])

  const onFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setBatchFile(f)
    void f.text().then((t) => setLogText(t))
  }, [])

  const runBatchUpload = useCallback(async () => {
    if (!batchFile) {
      setError('Choose a file first (upload control above).')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const b = await analyzeBatchUpload(batchFile, industry)
      setBatch(b)
      setBatchIndex(0)
      setDashboardTab('overview')
      const lines = (await batchFile.text()).split(/\r?\n/).filter((l) => l.trim())
      setRawLines(lines)
      setResult(b.results[0] ?? null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Batch upload failed')
      setBatch(null)
    } finally {
      setLoading(false)
    }
  }, [batchFile, industry])

  const loadDemos = useCallback(async () => {
    setDemoLoading(true)
    setError(null)
    try {
      const demos = await fetchDemoLogs()
      window.__logguardDemos = demos
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load demos')
    } finally {
      setDemoLoading(false)
    }
  }, [])

  const loadDemoById = useCallback(async (id: string) => {
    setDemoLoading(true)
    try {
      let demos = window.__logguardDemos
      if (!demos) demos = await fetchDemoLogs()
      const d = demos.find((x) => x.id === id)
      if (d) setLogText(d.raw_log)
    } finally {
      setDemoLoading(false)
    }
  }, [])

  const exportPdf = useCallback(async () => {
    if (!result) return
    setPdfLoading(true)
    setError(null)
    try {
      const blob = await downloadPdf(result)
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'logguard-report.pdf'
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'PDF export failed')
    } finally {
      setPdfLoading(false)
    }
  }, [result])

  const exportCsv = useCallback(() => {
    if (!result?.iocs.length) return
    const blob = new Blob([iocsToCsv(result.iocs)], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'logguard-iocs.csv'
    a.click()
    URL.revokeObjectURL(a.href)
  }, [result])

  const dashboardTabDefs = useMemo(
    () => [
      { id: 'overview' as const, label: 'Overview', short: 'Home', icon: LayoutDashboard },
      { id: 'mitre' as const, label: 'MITRE ATT&CK', short: 'MITRE', icon: Target },
      { id: 'iocs' as const, label: 'IOCs', short: 'IOCs', icon: Fingerprint },
      { id: 'rules' as const, label: 'Sigma / YARA', short: 'Rules', icon: FileCode2 },
      { id: 'attack-chain' as const, label: 'Attack chain', short: 'Chain', icon: Workflow },
      { id: 'charts' as const, label: 'Charts', short: 'Charts', icon: BarChart3 },
      { id: 'heatmap' as const, label: 'Log heatmap', short: 'Heat', icon: Flame },
      { id: 'playbook' as const, label: 'Playbook', short: 'Play', icon: BookOpen },
      {
        id: 'batch-nlp' as const,
        label: 'Log similarity',
        short: 'Sim',
        icon: Network,
      },
      { id: 'copilot' as const, label: 'SOC co-pilot', short: 'Chat', icon: MessageSquare },
    ],
    [],
  )

  return (
    <div className="flex min-h-svh">
      <aside className="hidden w-56 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950/90 p-4 md:flex">
        <div className="flex items-center gap-2 text-red-500">
          <Shield className="h-8 w-8" />
          <span className="font-semibold tracking-tight text-zinc-100">LogGuard AI</span>
        </div>
        <p className="mt-2 text-xs leading-snug text-zinc-500">SIEM classifier · MITRE · IOC · SOC co-pilot</p>
        <nav className="mt-8 flex flex-col gap-1 text-sm">
          <span className="flex items-center gap-2 rounded-lg bg-red-950/40 px-3 py-2 text-red-200">
            <LayoutDashboard className="h-4 w-4" /> Dashboard
          </span>
          <span className="flex items-center gap-2 px-3 py-2 text-zinc-500">
            <Radar className="h-4 w-4" /> Models via Hugging Face
          </span>
          <span className="flex items-center gap-2 px-3 py-2 text-zinc-500">
            <ScrollText className="h-4 w-4" /> No log retention
          </span>
        </nav>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col" aria-busy={loading || pdfLoading}>
        {(loading || pdfLoading) && (
          <div
            className="h-0.5 w-full shrink-0 animate-pulse bg-gradient-to-r from-red-950 via-red-500 to-red-950"
            role="progressbar"
            aria-label="Request in progress"
          />
        )}
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 bg-black/20 px-4 py-3 backdrop-blur md:px-8">
          <div>
            <h1 className="text-lg font-semibold text-zinc-100">Operations dashboard</h1>
            <p className="text-xs text-zinc-500">Paste, upload, or load curated demo telemetry</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value as Industry)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-200"
            >
              {INDUSTRIES.map((i) => (
                <option key={i.value} value={i.value}>
                  {i.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void loadDemos()}
              className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
            >
              Refresh demos list
            </button>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-6 p-4 md:flex-row md:p-8">
          <section className="flex min-w-0 flex-1 flex-col gap-4">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={onDrop}
              className="rounded-xl border border-dashed border-zinc-700 bg-zinc-950/40 p-4"
            >
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <label className="text-sm font-medium text-zinc-300">Log input</label>
                <div className="flex flex-wrap gap-2">
                  <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700">
                    <FileUp className="h-3.5 w-3.5" />
                    Upload .log / .txt / .json
                    <input type="file" accept=".log,.txt,.csv,.json" className="hidden" onChange={onFile} />
                  </label>
                  <button
                    type="button"
                    onClick={() => setLogText('')}
                    className="inline-flex items-center gap-1 rounded-lg border border-zinc-700 px-2 py-1.5 text-xs text-zinc-400 hover:text-zinc-200"
                  >
                    <Trash2 className="h-3.5 w-3.5" /> Clear
                  </button>
                </div>
              </div>
              <textarea
                value={logText}
                onChange={(e) => setLogText(e.target.value)}
                rows={14}
                placeholder="Paste CEF, Syslog, JSON, or plain text…"
                className="w-full resize-y rounded-lg border border-zinc-800 bg-black/40 p-3 font-mono text-sm text-zinc-200 outline-none ring-red-900/30 focus:ring-2"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void runAnalyze()}
                  className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  Analyze log
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => void runBatch()}
                  className="rounded-lg border border-zinc-600 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
                >
                  Analyze batch (multi-line)
                </button>
                <button
                  type="button"
                  disabled={loading || !batchFile}
                  onClick={() => void runBatchUpload()}
                  title="Uses multipart /analyze-batch-upload on the API"
                  className="rounded-lg border border-red-900/50 px-4 py-2 text-sm text-red-200/90 hover:bg-red-950/30 disabled:opacity-40"
                >
                  Batch upload (server parse)
                </button>
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Quick demos</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {[
                  ['demo-batch-nlp-lab', 'NLP batch lab'],
                  ['demo-ransomware-cef', 'Ransomware CEF'],
                  ['demo-ransomware-rundll32', 'Rundll32'],
                  ['demo-iot-brute', 'IoT SSH'],
                  ['demo-health-phi', 'Healthcare'],
                  ['demo-cloud-iam', 'Cloud IAM'],
                  ['demo-benign-patch', 'Benign patch'],
                ].map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    disabled={demoLoading}
                    onClick={() => void loadDemoById(id)}
                    className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-zinc-300 hover:border-red-900 hover:text-red-200"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {error && <p className="rounded-lg border border-red-900/50 bg-red-950/30 px-3 py-2 text-sm text-red-300">{error}</p>}
          </section>

          <section className="flex w-full min-w-0 flex-[1.2] flex-col gap-4">
            {result && (
              <div className="flex flex-col gap-4">
                <div className="space-y-3">
                  {batch && batch.results.length > 1 && (
                    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-zinc-800/90 bg-zinc-950/70 px-4 py-3">
                      <label htmlFor="batch-log-idx" className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                        Batch log
                      </label>
                      <select
                        id="batch-log-idx"
                        value={batchIndex}
                        onChange={(e) => {
                          const i = Number(e.target.value)
                          if (!batch?.results[i]) return
                          setBatchIndex(i)
                          setResult(batch.results[i])
                          if (rawLines?.[i] !== undefined) setLogText(rawLines[i])
                        }}
                        className="min-w-[10rem] rounded-lg border border-zinc-600 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
                      >
                        {batch.results.map((_, i) => (
                          <option key={i} value={i}>
                            {i + 1} / {batch.results.length}
                            {batch.anomaly_scores?.[i] != null && batch.anomaly_scores[i] > 0.6
                              ? ' · outlier'
                              : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <SeverityBanner
                    severity={result.severity}
                    score={result.severity_score}
                    format={result.format_detected}
                    ms={result.processing_time_ms}
                    anomalyScore={batch ? (result.anomaly_score ?? null) : null}
                    isolationAnomaly={Boolean(batch && result.isolation_anomaly_flag)}
                  />
                </div>

                <DashboardTabs tabs={dashboardTabDefs} active={dashboardTab} onChange={setDashboardTab} />

                <div className="min-h-[280px] rounded-xl border border-zinc-800/80 bg-zinc-950/20 p-4 sm:p-5">
                  {dashboardTab === 'overview' && (
                    <div className="space-y-4">
                      <div className="grid gap-4 lg:grid-cols-2">
                        <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                          <h2 className="text-sm font-semibold text-zinc-200">Executive summary</h2>
                          <p className="mt-2 text-sm leading-relaxed text-zinc-400">{result.executive_summary}</p>
                        </div>
                        <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                          <h2 className="text-sm font-semibold text-zinc-200">Risk explanation</h2>
                          <p className="mt-2 text-sm leading-relaxed text-zinc-400">{result.risk_explanation}</p>
                        </div>
                      </div>
                      <div>
                        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">Exports</p>
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            disabled={pdfLoading}
                            onClick={() => void exportPdf()}
                            className="inline-flex items-center gap-2 rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:opacity-50"
                          >
                            {pdfLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                            Download PDF report
                          </button>
                          <button
                            type="button"
                            onClick={exportCsv}
                            disabled={!result.iocs.length}
                            className="rounded-lg border border-zinc-600 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800 disabled:opacity-40"
                          >
                            Export IOCs CSV
                          </button>
                        </div>
                      </div>
                      {result.model_notes && (
                        <p className="text-xs text-zinc-600">Pipeline: {result.model_notes}</p>
                      )}
                    </div>
                  )}

                  {dashboardTab === 'mitre' && (
                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                      <h2 className="text-sm font-semibold text-zinc-200">MITRE ATT&amp;CK</h2>
                      <p className="mt-1 text-xs text-zinc-500">Techniques inferred from log content and sector context.</p>
                      <div className="mt-3">
                        <MitreMatrix techniques={result.mitre_techniques} />
                      </div>
                    </div>
                  )}

                  {dashboardTab === 'iocs' && (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                        <h2 className="text-sm font-semibold text-zinc-200">Indicators of compromise</h2>
                        <div className="mt-3">
                          <IOCTable iocs={result.iocs} />
                        </div>
                      </div>
                      {result.iocs.length > 0 && (
                        <button
                          type="button"
                          onClick={exportCsv}
                          className="rounded-lg border border-zinc-600 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800"
                        >
                          Export IOCs CSV
                        </button>
                      )}
                    </div>
                  )}

                  {dashboardTab === 'rules' && (
                    <DetectionRulesCard rules={result.detection_rules} logLines={logLinesForTest} />
                  )}

                  {dashboardTab === 'attack-chain' && (
                    <AttackChainSection graph={result.attack_chain} batchGraphs={batchAttackChains} />
                  )}

                  {dashboardTab === 'charts' && (
                    <DashboardCharts
                      result={result}
                      batch={batch?.results ?? null}
                      rawLines={rawLines}
                      primaryRaw={logText}
                    />
                  )}

                  {dashboardTab === 'heatmap' && (
                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                      <h2 className="text-sm font-semibold text-zinc-200">Suspicion heatmap (NER + keyword proxy)</h2>
                      <p className="mt-1 text-xs text-zinc-500">
                        Remote models do not expose SHAP; spans reflect NER entities, IOC-like tokens, and cyber lexicon
                        hits.
                      </p>
                      <div className="mt-3 max-h-[min(24rem,50vh)] overflow-auto">
                        <HighlightedLog text={logText} highlights={result.token_highlights} />
                      </div>
                    </div>
                  )}

                  {dashboardTab === 'playbook' && (
                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                      <h2 className="text-sm font-semibold text-zinc-200">Sector playbook</h2>
                      <ul className="mt-3 space-y-3 text-sm text-zinc-400">
                        {result.playbook.items.map((p, i) => (
                          <li key={i} className="rounded-lg border border-zinc-800/80 bg-black/20 p-3">
                            <p className="font-medium text-zinc-200">{p.title}</p>
                            <p className="mt-1">{p.action}</p>
                            {p.sample_query && (
                              <pre className="mt-2 overflow-x-auto rounded bg-zinc-900 p-2 font-mono text-xs text-red-200/90">
                                {p.sample_query}
                              </pre>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {dashboardTab === 'batch-nlp' && (
                    <div className="space-y-4">
                      <LogSimilarityAnalysis
                        incidents={batch?.incidents ?? []}
                        tfidfKeywords={batch?.tfidf_keywords ?? []}
                        rawLines={rawLines}
                        anomalyScores={batch?.anomaly_scores}
                        hasFullBatch={showBatchNlpTab}
                      />
                      {showBatchNlpTab && batch && batch.clusters.length > 0 && (
                        <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                          <h2 className="text-sm font-semibold text-zinc-200">Batch correlation (clustering)</h2>
                          <ul className="mt-2 space-y-2 text-sm text-zinc-400">
                            {batch.clusters.map((c) => (
                              <li key={c.cluster_id} className="rounded border border-zinc-800 p-2">
                                <span className="text-red-300/90">{c.theme}</span> — indices {c.log_indices.join(', ')}
                                <p className="mt-1 font-mono text-xs text-zinc-500">{c.representative_snippet}</p>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {dashboardTab === 'copilot' && (
                    <ChatPanel industry={industry} contextSnippet={logText} />
                  )}
                </div>
              </div>
            )}

            {!result && !loading && (
              <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-zinc-800 border-dashed p-8 text-center text-zinc-500">
                <Radar className="mb-4 h-12 w-12 text-zinc-700" />
                <p className="max-w-md text-sm">
                  Run analysis, then use the <span className="text-zinc-400">Analysis views</span> tabs for MITRE, IOCs,
                  Sigma/YARA, attack chain, charts, heatmap, playbook, log similarity (TF-IDF / Isolation Forest), and SOC
                  co-pilot.
                </p>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}

declare global {
  interface Window {
    __logguardDemos?: import('./types').DemoLogEntry[]
  }
}
