// The theory companion to the demo: the paper's results, with interactive versions of the main ones.
import { useState, type KeyboardEvent } from "react";
import { UndoLab } from "./UndoLab";
import { RefusalLab } from "./RefusalLab";
import { WindowLab } from "./WindowLab";

type Tab = "undo" | "law" | "window" | "map";

/** Arrow-key / Home / End navigation for a row of tabs (roving tabindex). */
function tabKeys<T extends string>(e: KeyboardEvent<HTMLElement>, ids: readonly T[], current: T, select: (id: T) => void) {
  const i = ids.indexOf(current);
  let n = -1;
  if (e.key === "ArrowRight") n = (i + 1) % ids.length;
  else if (e.key === "ArrowLeft") n = (i - 1 + ids.length) % ids.length;
  else if (e.key === "Home") n = 0;
  else if (e.key === "End") n = ids.length - 1;
  if (n < 0) return;
  e.preventDefault();
  select(ids[n]);
  e.currentTarget.parentElement?.querySelectorAll<HTMLElement>('[role="tab"]')[n]?.focus();
}
const TABS: { id: Tab; label: string }[] = [
  { id: "undo", label: "Exact undo & deletion order" },
  { id: "law", label: "Refusal law & probe limit" },
  { id: "window", label: "Persistent names with churn" },
  { id: "map", label: "What is proved" },
];

const TAB_IDS = TABS.map((t) => t.id);

interface Result { ref: string; title: string; status: "new" | "ours" | "classical" | "conditional" | "small"; text: string }
const STATUS: Record<Result["status"], string> = {
  new: "New (elementary)",
  ours: "New as stated",
  classical: "Classical result; finite-size form ours",
  conditional: "Conditional on published bounds",
  small: "Small, model-based",
};
const RESULTS: Result[] = [
  { ref: "Theorem 2, Corollary 3", title: "Stack order is an exact undo", status: "new", text: "For every non-reordering open-addressing scheme, popping the newest key by clearing its cell restores exactly the table that inserting the remaining keys would give. So every insertion-only result carries over to push/pop workloads, up to the first refusal." },
  { ref: "Theorem 4", title: "Which deletion orders are safe", status: "new", text: "For a given table the safe orders are exactly the linear extensions of the dependency relation 'y's probe path passes through x's cell'. Reverse insertion order is the only order safe for every table (greedy schemes: linear, quadratic, double hashing)." },
  { ref: "Proposition 5", title: "Orphan law", status: "ours", text: "The number of keys that depend on a key is a queue length minus one: exact finite-size law; the limit is a discrete M/D/1 queue with mean α/(2(1−α)). The limit law itself is Janson's (2005) Robin Hood displacement law; the link to deletion safety and the finite-size form are ours." },
  { ref: "Theorem 6", title: "Probe complexity under stack discipline", status: "conditional", text: "Combining Theorem 2 with published insertion bounds (Farach-Colton–Krapivin–Kuszmaul; interlinear probing): Θ(log 1/δ) non-greedy, Θ(log² 1/δ) greedy, strictly between insertion-only and random deletions. Conditional on those bounds." },
  { ref: "Theorem 7, Corollary 8", title: "Exact refusal law of a probe-limited table", status: "classical", text: "The refusal probability is the tail of the classical unsuccessful-search cost (Knuth; Janson–Viola). Ours: a short derivation, the explicit finite-size sum, and the proof that the Chernoff-type bound used earlier is loose by a factor growing like L^{3/2}." },
  { ref: "Theorem 10", title: "Refusal-free fill", status: "classical", text: "Exact probability that a whole monotone fill has no refusal, via ℓ-interval parking-function counts (Aguilar-Fraga et al.) and a closed-form generating function; the large-size behaviour is probably implied by Petersson's thesis. We add the exact forms and the design table." },
  { ref: "Proposition 11", title: "Unlimited run at fixed occupancy", status: "classical", text: "Probability that no fresh name can ever be refused; the probe limit for an unlimited run exceeds the one-push limit by about ln m / ln(1/ρ) (Pittel's scale). Exact finite-size values are ours." },
  { ref: "Proposition 12", title: "Bounded churn above a persistent trunk", status: "ours", text: "Any refusal in a schedule that keeps at most s names live above a never-popped trunk implies a window of L cells with at most s−1 empty cells; this is the supremum over schedules, with a closed-form bound and a design table. Modest and elementary; the scan-statistic framework is classical." },
  { ref: "Propositions 13–15", title: "Key lifetime", status: "small", text: "With a fresh key per table the exact law holds against arbitrary adversarial names; with a persistent key and a probe oracle it does not. Model-based, with a model oracle (no timing measured)." },
  { ref: "Proposition 16", title: "Space ledger", status: "small", text: "Exact space identities for five layouts; the compact layout's saving is a stored hash word plus packing, and interning is space-neutral. Accounting, reproduced against the repository's measurements." },
];
const NOT_CLAIMED = [
  "That the refusal law, its Poisson limit or its tail are new (they are classical).",
  "That the orphan limit law is new (it is Janson 2005).",
  "That the separation of Theorem 6 is unconditional.",
  "A limit law for refusals on wide and deep scope trees: open. Proposition 12 settles only bounded churn above a persistent trunk.",
  "Any timing result or hardware claim. The attack results use a model oracle.",
  "Proofs are pen-and-paper with exhaustive and statistical checks; no proof assistant, and no author has yet recorded a reading of them.",
];

export function Theory() {
  const [tab, setTab] = useState<Tab>("undo");
  return (
    <section className="theory" aria-labelledby="theory-title">
      <div className="intro">
        <h1 id="theory-title">Stack-disciplined open addressing: the theory.</h1>
        <p>
          The companion to the paper <i>Stack-Disciplined Open Addressing: Exact Undo, Exact Refusal Probabilities, and Key-Lifetime Rules for Bounded-Memory Scoped Tables</i>.
          Everything on these pages is computed in your browser from the paper&rsquo;s formulas and a small model of linear probing; it does not use the C++ engine.
          The same code is checked against the Python programs that produce the paper&rsquo;s tables when you run <code>npm test</code>.{" "}
          <a className="th-link" href="/strata-theory-paper.pdf" target="_blank" rel="noreferrer">Open the paper (PDF)</a>
        </p>
      </div>

      <div className="th-tabs" role="tablist" aria-label="Theory sections">
        {TABS.map((t) => (
          <button key={t.id} id={`th-tab-${t.id}`} role="tab" aria-selected={tab === t.id} aria-controls="th-panel" tabIndex={tab === t.id ? 0 : -1}
            className={tab === t.id ? "on" : ""} onClick={() => setTab(t.id)} onKeyDown={(e) => tabKeys(e, TAB_IDS, tab, setTab)}>{t.label}</button>
        ))}
      </div>

      <div id="th-panel" role="tabpanel" aria-labelledby={`th-tab-${tab}`}>
      {tab === "undo" && (
        <>
          <p className="th-lead"><b>Theorems 2 and 4, Proposition 5.</b> A scoped table pops names in last-in-first-out order. Clear the newest key and nothing else changes; clear any other and the keys that probed past it are lost.</p>
          <UndoLab />
        </>
      )}
      {tab === "law" && (
        <>
          <p className="th-lead"><b>Theorem 7, Propositions 11 and 12.</b> How large must the probe limit be so that a refusal is rare? Three different questions have three different answers.</p>
          <RefusalLab />
        </>
      )}
      {tab === "window" && (
        <>
          <p className="th-lead"><b>Proposition 12.</b> Global names stay, local scopes come and go. A refusal needs a dense stretch of occupied cells in the persistent part; the fewer names a scope can add, the denser that stretch must already be.</p>
          <WindowLab />
        </>
      )}
      {tab === "map" && (
        <div className="th-map">
          {RESULTS.map((r) => (
            <article key={r.ref} className="card th-result">
              <div className="th-result-head"><span className="th-ref">{r.ref}</span><span className={`th-chip ${r.status}`}>{STATUS[r.status]}</span></div>
              <h3>{r.title}</h3>
              <p>{r.text}</p>
            </article>
          ))}
          <article className="card th-result wide">
            <h3>What the paper does not claim</h3>
            <ul className="plain">{NOT_CLAIMED.map((x) => <li key={x}>{x}</li>)}</ul>
          </article>
        </div>
      )}
      </div>
    </section>
  );
}
