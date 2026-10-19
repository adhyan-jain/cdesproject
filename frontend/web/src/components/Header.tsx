export type EngineHealth = { state: "checking" } | { state: "ready"; compiler: string } | { state: "down" };
export type Page = "overview" | "lab" | "theory" | "benchmarks" | "stress" | "method";
export const PAGES: { id: Page; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "lab", label: "Live lab" },
  { id: "theory", label: "Theory" },
  { id: "benchmarks", label: "Benchmarks" },
  { id: "stress", label: "Stress tests" },
  { id: "method", label: "Method & limits" },
];

export function Logo() {
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
          {PAGES.map((p) => (
            <a key={p.id} href={`#/${p.id}`} className={page === p.id ? "on" : ""} aria-current={page === p.id ? "page" : undefined}
              onClick={(e) => { e.preventDefault(); onPage(p.id); }}>
              {p.label}
            </a>
          ))}
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
