export type Industry =
  | 'default'
  | 'healthcare'
  | 'finance'
  | 'manufacturing'
  | 'energy'
  | 'government'
  | 'cloud'

export type Severity = 'info' | 'low' | 'medium' | 'high' | 'critical'

export interface MitreTechnique {
  id: string
  name: string
  url: string
  confidence: number
}

export interface IOC {
  type: string
  value: string
  context?: string | null
}

export interface TokenHighlight {
  start: number
  end: number
  score: number
  label?: string | null
}

export interface PlaybookItem {
  title: string
  action: string
  sample_query?: string | null
}

export interface PlaybookResponse {
  sector: string
  items: PlaybookItem[]
  notes?: string | null
}

export type AttackNodeType = 'tactic' | 'technique' | 'ioc' | 'sector_risk'

export interface AttackChainNode {
  id: string
  node_type: AttackNodeType
  label: string
  mitre_id?: string | null
  mitre_url?: string | null
  confidence?: number | null
  ioc_type?: string | null
  position: { x: number; y: number }
}

export interface AttackChainEdge {
  id: string
  source: string
  target: string
  label?: string | null
  strength?: number | null
}

export interface AttackChainGraph {
  nodes: AttackChainNode[]
  edges: AttackChainEdge[]
}

export interface DetectionRules {
  title: string
  sigma_yaml: string
  yara_rule?: string | null
  false_positives: string
  severity_sigma_level: string
}

export interface AnalyzeResponse {
  format_detected: string
  severity: Severity
  severity_score: number
  executive_summary: string
  risk_explanation: string
  mitre_techniques: MitreTechnique[]
  iocs: IOC[]
  token_highlights: TokenHighlight[]
  playbook: PlaybookResponse
  detection_rules: DetectionRules
  attack_chain: AttackChainGraph
  model_notes?: string | null
  processing_time_ms: number
}

export interface DemoLogEntry {
  id: string
  title: string
  category: string
  raw_log: string
  expected_severity: string
  mitre_hint: string[]
}

export interface CorrelationCluster {
  cluster_id: number
  log_indices: number[]
  theme: string
  representative_snippet: string
}

export interface BatchAnalyzeResponse {
  results: AnalyzeResponse[]
  clusters: CorrelationCluster[]
  processing_time_ms: number
}

export interface TestSigmaResponse {
  match_count: number
  matching_indices: number[]
  tokens_used: string[]
  parse_error?: string | null
}
