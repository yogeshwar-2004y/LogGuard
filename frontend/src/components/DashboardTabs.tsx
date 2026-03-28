import type { LucideIcon } from 'lucide-react'

export type DashboardTabId =
  | 'overview'
  | 'mitre'
  | 'iocs'
  | 'rules'
  | 'attack-chain'
  | 'charts'
  | 'heatmap'
  | 'playbook'
  | 'batch-nlp'
  | 'copilot'

export type DashboardTabDef = {
  id: DashboardTabId
  label: string
  short: string
  icon: LucideIcon
  visible?: boolean
}

export function DashboardTabs({
  tabs,
  active,
  onChange,
}: {
  tabs: DashboardTabDef[]
  active: DashboardTabId
  onChange: (id: DashboardTabId) => void
}) {
  const visible = tabs.filter((t) => t.visible !== false)

  return (
    <div className="sticky top-0 z-10 -mx-1 border-b border-zinc-800 bg-zinc-950/95 px-1 py-1 pb-3 backdrop-blur-md">
      <p className="mb-3 text-[11px] font-medium uppercase tracking-wider text-zinc-500">Analysis views</p>
      <div className="flex flex-wrap gap-2 sm:gap-2.5">
        {visible.map(({ id, label, short, icon: Icon }) => {
          const isOn = active === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id)}
              className={`inline-flex min-h-[2.75rem] items-center gap-2 rounded-lg border px-3 py-2.5 text-left text-xs leading-snug transition sm:min-h-0 sm:px-3.5 sm:py-2.5 sm:text-sm ${
                isOn
                  ? 'border-red-600/90 bg-red-950/55 text-red-50 shadow-md shadow-red-950/30'
                  : 'border-zinc-700/90 bg-zinc-900/50 text-zinc-400 hover:border-zinc-500 hover:bg-zinc-800/50 hover:text-zinc-200'
              }`}
              title={label}
            >
              <Icon className={`h-4 w-4 shrink-0 sm:h-[1.125rem] sm:w-[1.125rem] ${isOn ? 'text-red-400' : 'text-zinc-500'}`} />
              <span className="hidden max-w-[11rem] font-medium sm:inline sm:truncate">{label}</span>
              <span className="font-medium sm:hidden">{short}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
