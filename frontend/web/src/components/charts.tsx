// Small SVG charts for the results pages. No chart library: each chart measures its container,
// draws thin marks with a recessive grid, carries a hover/focus tooltip, and its card can switch
// to a plain table so no value depends on hovering or on colour.
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

// ---- shared pieces ---------------------------------------------------------------------------
const SERIES = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"] as const;

function useWidth<T extends HTMLElement>(): [React.RefObject<T>, number] {
  const ref = useRef<T>(null);
  const [w, setW] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    setW(el.clientWidth);
    const ro = new ResizeObserver(() => setW(el.clientWidth));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

interface Tip { x: number; y: number; title: string; rows: { key?: string; color?: string; value: string; label?: string }[] }

function Tooltip({ tip, width }: { tip: Tip | null; width: number }) {
  if (!tip) return null;
  const left = Math.min(Math.max(tip.x + 14, 4), Math.max(4, width - 230));
  return (
    <div className="viz-tip" style={{ left, top: Math.max(tip.y - 10, 0) }} role="status">
      <div className="viz-tip-title">{tip.title}</div>
      {tip.rows.map((r, i) => (
        <div className="viz-tip-row" key={r.key ?? i}>
          {r.color && <span className="viz-key-line" style={{ background: r.color }} />}
          <b>{r.value}</b>
          {r.label && <span>{r.label}</span>}
        </div>
      ))}
    </div>
  );
}

function Legend({ items, shape = "rect" }: { items: { label: string; color: string; hollow?: boolean }[]; shape?: "rect" | "line" }) {
  return (
    <ul className="viz-legend" aria-label="Legend">
      {items.map((it) => (
        <li key={it.label}>
          <span className={`viz-swatch ${shape}`} style={{ background: it.hollow ? "transparent" : it.color, borderColor: it.color }} />
          {it.label}
        </li>
      ))}
    </ul>
  );
}

/** Card around a chart with a title, a note and a Chart / Table switch. */
export function ChartCard({ title, sub, children, table, footer, actions }: {
  title: string; sub?: ReactNode; children: ReactNode; table: ReactNode; footer?: ReactNode; actions?: ReactNode;
}) {
  const [view, setView] = useState<"chart" | "table">("chart");
  return (
    <article className="card viz-card reveal">
      <div className="viz-head">
        <div>
          <h3>{title}</h3>
          {sub && <p className="viz-sub">{sub}</p>}
        </div>
        <div className="viz-head-actions">
          {actions}
          <div className="viewseg" role="tablist" aria-label={`${title}: view`}>
            <button role="tab" aria-selected={view === "chart"} className={view === "chart" ? "on" : ""} onClick={() => setView("chart")}>Chart</button>
            <button role="tab" aria-selected={view === "table"} className={view === "table" ? "on" : ""} onClick={() => setView("table")}>Table</button>
          </div>
        </div>
      </div>
      <div className="viz-body">{view === "chart" ? children : <div className="table-wrap">{table}</div>}</div>
      {footer && <div className="viz-foot">{footer}</div>}
    </article>
  );
}

function niceMax(v: number) {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  for (const m of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (m * p >= v) return m * p;
  return 10 * p;
}
function ticks(max: number, n = 4) {
  const step = max / n;
  return Array.from({ length: n + 1 }, (_, i) => +(i * step).toPrecision(6));
}

// ---- horizontal bars: one value per row, the highlighted row in the accent ------------------
interface BarRow { key: string; label: string; value: number; highlight?: boolean; detail?: string }

export function BarList({ rows, format, log = false, axisLabel }: {
  rows: BarRow[]; format: (v: number) => string; log?: boolean; axisLabel: string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [tip, setTip] = useState<Tip | null>(null);
  const longest = Math.max(...rows.map((r) => r.label.length));
  const labelW = Math.min(190, width * 0.42, Math.max(70, longest * 7 + 16));
  const valueW = 84;
  const rowH = 34, bar = 16, top = 6, axisH = 40;
  const anyHighlight = rows.some((r) => r.highlight);
  const plotW = Math.max(40, width - labelW - valueW - 8);
  const vals = rows.map((r) => r.value);
  const max = log ? Math.pow(10, Math.ceil(Math.log10(Math.max(...vals)))) : niceMax(Math.max(...vals));
  const min = log ? 1 : 0;
  const x = (v: number) => (log ? (Math.log10(Math.max(v, 1)) - Math.log10(min)) / (Math.log10(max) - Math.log10(min)) : v / max) * plotW;
  const decades = Array.from({ length: Math.log10(max) + 1 }, (_, i) => Math.pow(10, i));
  const tickVals = log ? decades.filter((_, i) => plotW >= 220 || i % 2 === 0) : ticks(max, plotW < 200 ? 2 : 4);
  const h = top + rows.length * rowH + axisH;
  return (
    <div className="viz" ref={ref} onPointerLeave={() => setTip(null)}>
      {width > 0 && (
        <svg width={width} height={h} role="img" aria-label={`${axisLabel}: ${rows.map((r) => `${r.label} ${format(r.value)}`).join(", ")}`}>
          <g transform={`translate(${labelW},0)`}>
            {tickVals.map((t) => (
              <g key={t} transform={`translate(${x(t)},0)`}>
                <line y1={top - 2} y2={top + rows.length * rowH} className="viz-grid" />
                <text y={top + rows.length * rowH + 16} className="viz-axis" textAnchor="middle">{log ? compactTick(t) : compactTick(t)}</text>
              </g>
            ))}
            <text x={plotW} y={h - 3} className="viz-axis" textAnchor="end">{axisLabel}{log ? " · log scale" : ""}</text>
          </g>
          {rows.map((r, i) => {
            const y = top + i * rowH;
            const w = Math.max(2, x(r.value));
            return (
              <g key={r.key} className={`viz-row ${r.highlight ? "hl" : ""}`}
                tabIndex={0}
                onPointerMove={(e) => setTip({ x: e.nativeEvent.offsetX, y: y, title: r.label, rows: [{ value: format(r.value), label: r.detail }] })}
                onFocus={() => setTip({ x: labelW + w, y, title: r.label, rows: [{ value: format(r.value), label: r.detail }] })}
                onBlur={() => setTip(null)}>
                <rect x={0} y={y} width={width} height={rowH} fill="transparent" />
                <text x={labelW - 10} y={y + rowH / 2 + 4} textAnchor="end" className={`viz-label ${r.highlight ? "strong" : ""}`}>{r.label}</text>
                <path d={barPath(labelW, y + (rowH - bar) / 2, w, bar)} className="viz-bar" style={{ fill: r.highlight || !anyHighlight ? "var(--s1)" : "var(--s-mute)" }} />
                <text x={labelW + w + 6} y={y + rowH / 2 + 4} className={`viz-value ${r.highlight ? "strong" : ""}`}>{format(r.value)}</text>
              </g>
            );
          })}
        </svg>
      )}
      <Tooltip tip={tip} width={width} />
    </div>
  );
}

// Bar growing right from the baseline: square at the baseline, 4px rounded data end.
function barPath(x0: number, y: number, w: number, h: number) {
  const r = Math.min(4, w / 2, h / 2);
  return `M${x0},${y} H${x0 + w - r} Q${x0 + w},${y} ${x0 + w},${y + r} V${y + h - r} Q${x0 + w},${y + h} ${x0 + w - r},${y + h} H${x0} Z`;
}
// Column growing up from the baseline.
function colPath(x: number, yBase: number, w: number, h: number) {
  const r = Math.min(4, w / 2, h / 2);
  const yTop = yBase - h;
  return `M${x},${yBase} V${yTop + r} Q${x},${yTop} ${x + r},${yTop} H${x + w - r} Q${x + w},${yTop} ${x + w},${yTop + r} V${yBase} Z`;
}
function compactTick(t: number) {
  if (t >= 1e6) return `${t / 1e6}M`;
  if (t >= 1e3) return `${t / 1e3}K`;
  return `${+t.toPrecision(3)}`;
}

// ---- paired columns: two series per category ---------------------------------------------
export function PairedColumns({ categories, series, format, axisLabel }: {
  categories: { key: string; label: string }[];
  series: { label: string; values: number[] }[];
  format: (v: number) => string; axisLabel: string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [tip, setTip] = useState<Tip | null>(null);
  const left = 44, right = 8, top = 24, bottom = 34, h = 262;
  const plotW = Math.max(60, width - left - right), plotH = h - top - bottom;
  const max = niceMax(Math.max(...series.flatMap((s) => s.values)));
  const band = plotW / categories.length;
  const colW = Math.min(22, (band - 14) / series.length - 2);
  const y = (v: number) => (v / max) * plotH;
  return (
    <div className="viz" ref={ref} onPointerLeave={() => setTip(null)}>
      <Legend items={series.map((s, i) => ({ label: s.label, color: SERIES[i] }))} />
      {width > 0 && (
        <svg width={width} height={h} role="img" aria-label={axisLabel}>
          <g transform={`translate(${left},${top})`}>
            {ticks(max).map((t) => (
              <g key={t} transform={`translate(0,${plotH - y(t)})`}>
                <line x2={plotW} className="viz-grid" />
                <text x={-8} y={4} textAnchor="end" className="viz-axis">{compactTick(t)}</text>
              </g>
            ))}
            {categories.map((c, ci) => {
              const groupW = series.length * colW + (series.length - 1) * 2;
              const gx = ci * band + (band - groupW) / 2;
              const showTip = (px: number) => setTip({ x: left + px, y: top + 10, title: c.label, rows: series.map((s, si) => ({ color: SERIES[si], value: format(s.values[ci]), label: s.label })) });
              return (
                <g key={c.key} tabIndex={0} className="viz-col-group"
                  onPointerMove={() => showTip(gx + groupW)} onFocus={() => showTip(gx + groupW)} onBlur={() => setTip(null)}>
                  <rect x={ci * band} y={0} width={band} height={plotH} fill="transparent" />
                  {series.map((s, si) => (
                    <path key={s.label} d={colPath(gx + si * (colW + 2), plotH, colW, Math.max(2, y(s.values[ci])))} style={{ fill: SERIES[si] }} className="viz-bar" />
                  ))}
                  <text x={ci * band + band / 2} y={plotH + 18} textAnchor="middle" className="viz-axis">{c.label}</text>
                </g>
              );
            })}
            <line y1={plotH} y2={plotH} x2={plotW} className="viz-baseline" />
          </g>
          <text x={left - 8} y={10} textAnchor="end" className="viz-axis">{axisLabel}</text>
        </svg>
      )}
      <Tooltip tip={tip} width={width} />
    </div>
  );
}

// ---- forest plot: a difference with its 95% interval per row, zero in the middle -------------
interface ForestRow { key: string; label: string; value: number; low: number; high: number; detail?: string }

export function ForestPlot({ rows, negLabel, posLabel, unit = "%" }: { rows: ForestRow[]; negLabel: string; posLabel: string; unit?: string }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [tip, setTip] = useState<Tip | null>(null);
  const labelW = Math.min(130, Math.max(90, width * 0.22)), verdictW = 108;
  const rowH = 30, top = 8, axisH = 44;
  const plotW = Math.max(60, width - labelW - verdictW - 8);
  const ext = niceMax(Math.max(...rows.flatMap((r) => [Math.abs(r.low), Math.abs(r.high)]), 5));
  const x = (v: number) => ((v + ext) / (2 * ext)) * plotW;
  const h = top + rows.length * rowH + axisH;
  const tickVals = [-ext, -ext / 2, 0, ext / 2, ext];
  const verdict = (r: ForestRow) => (r.low > 0 ? posLabel : r.high < 0 ? negLabel : "not established");
  return (
    <div className="viz" ref={ref} onPointerLeave={() => setTip(null)}>
      {width > 0 && (
        <svg width={width} height={h} role="img" aria-label={rows.map((r) => `${r.label}: ${r.value}${unit} (${r.low} to ${r.high})`).join("; ")}>
          <g transform={`translate(${labelW},0)`}>
            {tickVals.map((t) => (
              <g key={t} transform={`translate(${x(t)},0)`}>
                <line y1={top - 2} y2={top + rows.length * rowH} className={t === 0 ? "viz-zero" : "viz-grid"} />
                <text y={top + rows.length * rowH + 16} className="viz-axis" textAnchor="middle">{t > 0 ? "+" : ""}{+t.toFixed(1)}{unit}</text>
              </g>
            ))}
            <text x={x(0) - 8} y={h - 6} className="viz-axis" textAnchor="end">← STRATA {negLabel}</text>
            <text x={x(0) + 8} y={h - 6} className="viz-axis">STRATA {posLabel} →</text>
          </g>
          {rows.map((r, i) => {
            const y = top + i * rowH + rowH / 2;
            const est = r.low > 0 || r.high < 0;
            const show = () => setTip({ x: labelW + x(r.value), y: y - 10, title: r.label, rows: [
              { value: `${r.value > 0 ? "+" : ""}${r.value}${unit}`, label: "median difference" },
              { value: `${r.low} to ${r.high}${unit}`, label: "95% interval" },
              ...(r.detail ? [{ value: r.detail }] : []),
            ] });
            return (
              <g key={r.key} tabIndex={0} className="viz-row" onPointerMove={show} onFocus={show} onBlur={() => setTip(null)}>
                <rect x={0} y={y - rowH / 2} width={width} height={rowH} fill="transparent" />
                <text x={labelW - 10} y={y + 4} textAnchor="end" className="viz-label">{r.label}</text>
                <line x1={labelW + x(r.low)} x2={labelW + x(r.high)} y1={y} y2={y} className="viz-ci" />
                <circle cx={labelW + x(r.value)} cy={y} r={5} className={est ? "viz-dot" : "viz-dot hollow"} />
                <text x={width - 4} y={y + 4} textAnchor="end" className={`viz-verdict ${est ? "strong" : ""}`}>{verdict(r)}</text>
              </g>
            );
          })}
        </svg>
      )}
      <Tooltip tip={tip} width={width} />
      <Legend shape="rect" items={[{ label: "interval excludes 0", color: "var(--s1)" }, { label: "interval includes 0", color: "var(--s1)", hollow: true }]} />
    </div>
  );
}

// ---- line chart with a crosshair that lists every series at the nearest x -------------------
export function LineChart({ xs, xLabel, xFormat, series, yFormat, yLabel, logY = false, logX = false, height = 260 }: {
  xs: number[]; xLabel: string; xFormat: (v: number) => string;
  series: { label: string; values: (number | null)[]; color?: string }[];
  yFormat: (v: number) => string; yLabel: string; logY?: boolean; logX?: boolean; height?: number;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const left = 58, right = 16, top = 24, bottom = 40;
  const plotW = Math.max(60, width - left - right), plotH = height - top - bottom;
  const all = series.flatMap((s) => s.values.filter((v): v is number => v !== null));
  const yMax = logY ? Math.pow(10, Math.ceil(Math.log10(Math.max(...all)))) : niceMax(Math.max(...all));
  const yMin = logY ? Math.pow(10, Math.floor(Math.log10(Math.min(...all)))) : 0;
  const fx = (v: number) => (logX ? Math.log2(v) : v);
  const x0 = fx(xs[0]), x1 = fx(xs[xs.length - 1]);
  const px = (v: number) => ((fx(v) - x0) / (x1 - x0 || 1)) * plotW;
  const py = (v: number) => plotH - (logY ? (Math.log10(v) - Math.log10(yMin)) / (Math.log10(yMax) - Math.log10(yMin)) : (v - yMin) / (yMax - yMin)) * plotH;
  const yt = logY ? Array.from({ length: Math.round(Math.log10(yMax / yMin)) + 1 }, (_, i) => yMin * Math.pow(10, i)) : ticks(yMax);
  const colors = series.map((s, i) => s.color ?? SERIES[i]);
  const onMove = (e: React.PointerEvent) => {
    const mx = e.nativeEvent.offsetX - left;
    let best = 0;
    xs.forEach((v, i) => { if (Math.abs(px(v) - mx) < Math.abs(px(xs[best]) - mx)) best = i; });
    setHover(best);
  };
  const tip: Tip | null = hover === null ? null : {
    x: left + px(xs[hover]), y: top, title: `${xLabel}: ${xFormat(xs[hover])}`,
    rows: series.map((s, i) => ({ key: s.label, color: colors[i], value: s.values[hover] === null ? "—" : yFormat(s.values[hover] as number), label: s.label })),
  };
  return (
    <div className="viz" ref={ref}>
      <Legend shape="line" items={series.map((s, i) => ({ label: s.label, color: colors[i] }))} />
      {width > 0 && (
        <svg width={width} height={height} role="img" aria-label={`${yLabel} by ${xLabel}`}
          onPointerMove={onMove} onPointerLeave={() => setHover(null)} tabIndex={0}
          onKeyDown={(e) => { if (e.key === "ArrowRight") setHover((h) => Math.min(xs.length - 1, (h ?? -1) + 1)); if (e.key === "ArrowLeft") setHover((h) => Math.max(0, (h ?? 1) - 1)); }}
          onBlur={() => setHover(null)}>
          <g transform={`translate(${left},${top})`}>
            {yt.map((t) => (
              <g key={t} transform={`translate(0,${py(t)})`}>
                <line x2={plotW} className="viz-grid" />
                <text x={-8} y={4} textAnchor="end" className="viz-axis">{yFormat(t)}</text>
              </g>
            ))}
            {xs.map((v) => (
              <text key={v} x={px(v)} y={plotH + 18} textAnchor="middle" className="viz-axis">{xFormat(v)}</text>
            ))}
            <text x={plotW} y={plotH + 34} textAnchor="end" className="viz-axis">{xLabel}</text>
            <line y1={plotH} y2={plotH} x2={plotW} className="viz-baseline" />
            {hover !== null && <line x1={px(xs[hover])} x2={px(xs[hover])} y1={0} y2={plotH} className="viz-crosshair" />}
            {series.map((s, si) => {
              const pts = xs.map((v, i) => (s.values[i] === null ? null : [px(v), py(s.values[i] as number)] as const)).filter((p): p is readonly [number, number] => p !== null);
              return (
                <g key={s.label}>
                  <polyline points={pts.map((p) => p.join(",")).join(" ")} className="viz-line" style={{ stroke: colors[si] }} />
                  {pts.map(([cx, cy], i) => (
                    <circle key={i} cx={cx} cy={cy} r={hover !== null && px(xs[hover]) === cx ? 5 : 4} className="viz-marker" style={{ fill: colors[si] }} />
                  ))}
                </g>
              );
            })}
          </g>
          <text x={left} y={10} className="viz-axis">{yLabel}{logY ? " · log scale" : ""}</text>
        </svg>
      )}
      <Tooltip tip={tip} width={width} />
    </div>
  );
}
