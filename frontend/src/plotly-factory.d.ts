declare module 'plotly.js/dist/plotly.js' {
  const Plotly: unknown
  export default Plotly
}

declare module 'react-plotly.js/factory.js' {
  import type { ComponentType } from 'react'

  export default function createPlotlyComponent(plotly: unknown): ComponentType<Record<string, unknown>>
}
