import { Camera, Info } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background,
  Controls,
  type Edge,
  Handle,
  MarkerType,
  MiniMap,
  type Node,
  type NodeProps,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { toPng } from 'html-to-image'
import type { AttackChainGraph, AttackChainNode as ACNode } from '../types'

function ChainNode({ data }: NodeProps) {
  const t = (data.nodeType as string) || 'tactic'
  const styles: Record<string, string> = {
    tactic: 'border-blue-500/90 bg-blue-950/95 text-blue-100',
    technique: 'border-orange-500/90 bg-orange-950/95 text-orange-100',
    ioc: 'border-red-600 bg-red-950/95 text-red-100',
    sector_risk: 'border-purple-500/90 bg-purple-950/95 text-purple-100',
  }
  const c = styles[t] || styles.tactic
  return (
    <div className={`max-w-[220px] rounded-lg border-2 px-2 py-2 text-center text-[10px] leading-tight shadow-lg ${c}`}>
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0 !bg-zinc-400" />
      <div className="font-medium">{String(data.label)}</div>
      {data.confidence != null && (
        <div className="mt-0.5 text-[9px] opacity-80">{Math.round(Number(data.confidence) * 100)}%</div>
      )}
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0 !bg-zinc-400" />
    </div>
  )
}

const nodeTypes = { chain: ChainNode }

function toFlowGraph(g: AttackChainGraph): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = g.nodes.map((n: ACNode) => ({
    id: n.id,
    type: 'chain',
    position: { x: n.position.x, y: n.position.y },
    data: {
      label: n.label,
      nodeType: n.node_type,
      mitre_id: n.mitre_id,
      mitre_url: n.mitre_url,
      confidence: n.confidence,
      ioc_type: n.ioc_type,
    },
  }))
  const edges: Edge[] = g.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label ?? '',
    markerEnd: { type: MarkerType.ArrowClosed, color: '#71717a' },
    style: {
      stroke: '#52525b',
      strokeWidth: 1 + 2 * (e.strength ?? 0.35),
    },
    labelStyle: { fill: '#a1a1aa', fontSize: 9 },
    labelBgStyle: { fill: '#18181b', fillOpacity: 0.9 },
    labelBgPadding: [4, 2] as [number, number],
  }))
  return { nodes, edges }
}

function FlowCanvas({
  graph,
  onSelect,
}: {
  graph: AttackChainGraph
  onSelect: (n: ACNode | null) => void
}) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => toFlowGraph(graph), [graph])
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  useEffect(() => {
    const { nodes: n, edges: e } = toFlowGraph(graph)
    setNodes(n)
    setEdges(e)
  }, [graph, setNodes, setEdges])

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const raw = graph.nodes.find((x) => x.id === node.id)
      onSelect(raw ?? null)
    },
    [graph.nodes, onSelect],
  )

  return (
    <div className="logguard-flow h-[420px] w-full rounded-lg border border-zinc-800 bg-[#09090b]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#27272a" gap={16} />
        <Controls className="!bg-zinc-900 !border-zinc-700 [&_button]:!fill-zinc-300" />
        <MiniMap
          className="!bg-zinc-900 !border-zinc-700"
          nodeColor={(n) => {
            const t = (n.data?.nodeType as string) || ''
            if (t === 'tactic') return '#3b82f6'
            if (t === 'technique') return '#ea580c'
            if (t === 'ioc') return '#dc2626'
            if (t === 'sector_risk') return '#a855f7'
            return '#52525b'
          }}
        />
        <Panel position="top-left" className="rounded border border-zinc-700 bg-zinc-950/95 p-2 text-[10px] text-zinc-400">
          <div className="font-semibold text-zinc-300">Legend</div>
          <div className="mt-1 flex flex-col gap-0.5">
            <span>
              <span className="inline-block h-2 w-2 rounded-full bg-blue-500" /> Tactic
            </span>
            <span>
              <span className="inline-block h-2 w-2 rounded-full bg-orange-500" /> Technique
            </span>
            <span>
              <span className="inline-block h-2 w-2 rounded-full bg-red-600" /> IOC
            </span>
            <span>
              <span className="inline-block h-2 w-2 rounded-full bg-purple-500" /> Sector risk
            </span>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}

export function AttackChainSection({
  graph,
  batchGraphs,
}: {
  graph: AttackChainGraph
  batchGraphs?: AttackChainGraph[] | null
}) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [selected, setSelected] = useState<ACNode | null>(null)
  const [tIdx, setTIdx] = useState(0)

  const activeGraph = useMemo(() => {
    if (batchGraphs && batchGraphs.length > 1) return batchGraphs[tIdx] ?? graph
    return graph
  }, [batchGraphs, graph, tIdx])

  useEffect(() => {
    setTIdx(0)
  }, [batchGraphs, graph])

  const exportPng = useCallback(() => {
    const el = wrapRef.current?.querySelector('.logguard-flow') as HTMLElement | null
    if (!el) return
    void toPng(el, { backgroundColor: '#09090b', pixelRatio: 2 }).then((dataUrl) => {
      const a = document.createElement('a')
      a.href = dataUrl
      a.download = 'logguard-attack-chain.png'
      a.click()
    })
  }, [])

  return (
    <div ref={wrapRef} className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-zinc-200">Attack chain</h2>
        <button
          type="button"
          onClick={() => exportPng()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-600 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <Camera className="h-3.5 w-3.5" /> Export PNG
        </button>
      </div>
      <p className="mt-1 text-xs text-zinc-500">
        Interactive MITRE tactics → techniques → IOCs. Drag, zoom, pan. Click a node for details; edge thickness
        reflects link strength.
      </p>

      {batchGraphs && batchGraphs.length > 1 && (
        <div className="mt-3 flex items-center gap-3">
          <label className="text-xs text-zinc-500">Batch timeline</label>
          <input
            type="range"
            min={0}
            max={batchGraphs.length - 1}
            value={tIdx}
            onChange={(e) => setTIdx(Number(e.target.value))}
            className="h-1 flex-1 accent-red-600"
          />
          <span className="font-mono text-xs text-zinc-400">
            {tIdx + 1}/{batchGraphs.length}
          </span>
        </div>
      )}

      <div className="mt-3 flex flex-col gap-3 lg:flex-row">
        <div className="min-w-0 flex-1">
          <ReactFlowProvider>
            <FlowCanvas graph={activeGraph} onSelect={setSelected} />
          </ReactFlowProvider>
        </div>
        <aside className="w-full shrink-0 rounded-lg border border-zinc-800 bg-black/30 p-3 lg:w-64">
          <div className="flex items-center gap-1 text-xs font-semibold text-zinc-300">
            <Info className="h-3.5 w-3.5" /> Node details
          </div>
          {selected ? (
            <div className="mt-2 space-y-2 text-xs text-zinc-400">
              <p className="text-zinc-200">{selected.label}</p>
              <p className="capitalize text-zinc-500">Type: {selected.node_type.replace('_', ' ')}</p>
              {selected.mitre_id && (
                <a
                  href={selected.mitre_url ?? `https://attack.mitre.org/techniques/${selected.mitre_id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-red-400 hover:underline"
                >
                  Open MITRE {selected.mitre_id}
                </a>
              )}
              {selected.ioc_type && <p>IOC type: {selected.ioc_type}</p>}
              {selected.confidence != null && <p>Score: {(selected.confidence * 100).toFixed(0)}%</p>}
            </div>
          ) : (
            <p className="mt-2 text-xs text-zinc-600">Click a node in the graph.</p>
          )}
        </aside>
      </div>
    </div>
  )
}
