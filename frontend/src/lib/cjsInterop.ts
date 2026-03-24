/** Vite/node often surface CJS `module.exports = fn` as `{ default: fn }`. */

export function unwrapCjsDefault<T>(mod: unknown): T {
  let x: unknown = mod
  for (let i = 0; i < 4; i++) {
    if (x === null || x === undefined) break
    if (typeof x !== 'object') break
    if (!('default' in x)) break
    const d = (x as { default: unknown }).default
    if (d === undefined) break
    x = d
  }
  return x as T
}
