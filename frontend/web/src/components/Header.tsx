export type EngineHealth = { state: "checking" } | { state: "ready"; compiler: string } | { state: "down" };
export type Page = "overview" | "analyse" | "lab" | "theory" | "benchmarks" | "stress" | "method";
export const PAGES: { id: Page; label: string }[] = [
  { id: "overview", label: "Home" },
  { id: "analyse", label: "Analyse your code" },
  { id: "lab", label: "Live lab" },
  { id: "benchmarks", label: "Benchmarks" },
  { id: "stress", label: "Stress tests" },
  { id: "theory", label: "Theory" },
  { id: "method", label: "About" },
];
// The top bar shows five groups; a group with several pages gets a row of sub-tabs (SubNav).
const GROUPS: { label: string; pages: Page[]; hint: string }[] = [
  { label: "Home", pages: ["overview"], hint: "What STRATA is, in one page" },
  { label: "Try it", pages: ["analyse", "lab"], hint: "Paste your code, or drive the table by hand" },
  { label: "Results", pages: ["benchmarks", "stress"], hint: "What was measured" },
  { label: "Theory", pages: ["theory"], hint: "What was proved" },
  { label: "About", pages: ["method"], hint: "Method, limits, team" },
];
const groupOf = (p: Page) => GROUPS.find((g) => g.pages.includes(p))!;

function Logo() {
  // Four memory regions stacked into one block: index, records, undo, free.
  return (
    <svg className="logo" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="7" fill="var(--text)" />
      <rect x="7" y="8" width="18" height="4" rx="1" fill="var(--c-index)" />
      <rect x="7" y="14" width="12" height="4" rx="1" fill="var(--bg)" />
      <rect x="21" y="14" width="4" height="4" rx="1" fill="var(--c-undo)" />
      <rect x="7" y="20" width="7" height="4" rx="1" fill="var(--bg)" opacity=".55" />
    </svg>
  );
}

interface Props {
  page: Page;
  onPage: (p: Page) => void;
  health: EngineHealth;
  onRetry: () => void;
  onRunDemo: () => void;
  onReset: () => void;
  demoActive: boolean;
  busy: boolean;
}

export function SubNav({ page, onPage }: { page: Page; onPage: (p: Page) => void }) {
  const g = groupOf(page);
  if (g.pages.length < 2) return null;
  return (
    <nav className="subnav" aria-label={g.label}>
      {g.pages.map((id) => (
        <a key={id} href={`#/${id}`} className={page === id ? "on" : ""} aria-current={page === id ? "page" : undefined}
          onClick={(e) => { e.preventDefault(); onPage(id); }}>
          {PAGES.find((p) => p.id === id)!.label}
        </a>
      ))}
      <span className="subnav-hint">{g.hint}</span>
    </nav>
  );
}

export function Header({ page, onPage, health, onRetry, onRunDemo, onReset, demoActive, busy }: Props) {
  const ready = health.state === "ready";
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <button className="brand" onClick={() => onPage("overview")} aria-label="STRATA overview">
          <Logo />
          <span className="wordmark">STRATA</span>
          <span className="brand-sep" aria-hidden="true" />
          <span className="brand-sub">Compiler Memory Lab</span>
        </button>
        <nav className="nav" aria-label="Sections">
          {GROUPS.map((g) => {
            const on = g.pages.includes(page);
            return (
              <a key={g.label} href={`#/${g.pages[0]}`} className={on ? "on" : ""} aria-current={on ? "page" : undefined} title={g.hint}
                onClick={(e) => { e.preventDefault(); onPage(g.pages[0]); }}>
                {g.label}
              </a>
            );
          })}
        </nav>
        <div className="topbar-actions">
          <div className={`engine-pill engine-${health.state}`} role="status" aria-live="polite">
            <span className="dot" aria-hidden="true" />
            {health.state === "checking" && "Connecting…"}
            {health.state === "ready" && (
              <span>
                Engine ready <span className="pill-meta">g++ {health.compiler}</span>
              </span>
            )}
            {health.state === "down" && (
              <span>
                Engine offline{" "}
                <button className="link" onClick={onRetry}>
                  Retry
                </button>
              </span>
            )}
          </div>
          {page === "lab" && (
            <button className="btn btn-ghost" onClick={onReset} disabled={!ready || busy}>
              Reset
            </button>
          )}
          <button className="btn btn-primary" onClick={onRunDemo} disabled={!ready || busy || demoActive}>
            <svg viewBox="0 0 16 16" aria-hidden="true" className="ico">
              <path d="M5 3.5v9l7-4.5-7-4.5z" fill="currentColor" />
            </svg>
            Guided demo
          </button>
        </div>
      </div>
    </header>
  );
}
