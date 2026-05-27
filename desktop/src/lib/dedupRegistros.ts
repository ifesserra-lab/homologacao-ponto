/**
 * SIGRH creates one table row per calendar day of a licença period.
 * Parser stores all rows, so a 5-day licença paternidade produces 5 identical rows.
 * This merges rows with the same date: union arrays, keep first non-null scalar.
 */
export function dedupRegistros(registros: any[]): any[] {
  const map = new Map<string, any>();
  for (const r of registros) {
    const key = r.data ?? r.dia_semana ?? JSON.stringify(r);
    if (!map.has(key)) {
      map.set(key, { ...r, ocorrencias: [...(r.ocorrencias ?? [])], marcacoes: [...(r.marcacoes ?? [])] });
    } else {
      const merged = map.get(key);
      for (const [k, v] of Object.entries(r)) {
        if (k === "data" || k === "dia_semana") continue;
        if (k === "ocorrencias" || k === "marcacoes") {
          merged[k] = [...new Set([...merged[k], ...(r[k] as string[])])];
        } else if ((merged[k] === null || merged[k] === undefined) && v !== null && v !== undefined) {
          merged[k] = v;
        }
      }
    }
  }
  return [...map.values()];
}
