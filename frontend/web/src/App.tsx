import { useCallback, useEffect, useRef, useState } from "react";
import { EngineError, health, runOps, type EngineState, type Op } from "./lib/engine";
import { Header, PAGES, type EngineHealth, type Page } from "./components/Header";
import { Controls } from "./components/Controls";
import { StatusLine, type StatusSource } from "./components/StatusLine";
import { SymbolTable } from "./components/SymbolTable";
import { MemoryInspector } from "./components/MemoryInspector";
import { Timeline } from "./components/Timeline";
import { GuidedDemo, DEMO_CAPACITY, DEMO_STEPS } from "./components/GuidedDemo";
import { describe } from "./lib/describe";
import { CodeEditor } from "./components/CodeEditor";
import { CodeError, compile, EXAMPLES, type LineOp } from "./lib/minic";
import { Overview } from "./pages/Overview";
import { Benchmarks } from "./pages/Benchmarks";
import { Stress } from "./pages/Stress";
import { Method } from "./pages/Method";

const pageFromHash = (): Page => {
  const h = window.location.hash.replace(/^#\/?/, "");
  return (PAGES.find((p) => p.id === h)?.id ?? "overview");
};

const DEFAULT_CAPACITY = 512;
const MAX_OPS = 400;
const EXAMPLE: Op[] = [
  { op: "declare", name: "count", type: 0, value: 1 },
  { op: "declare", name: "rate", type: 1, value: 0x40200000 },   // 2.5f
  { op: "declare", name: "ready", type: 3, value: 1 },
];
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function App() {
  const [page, setPage] = useState<Page>(pageFromHash);
  useEffect(() => {
    const on = () => setPage(pageFromHash());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  const go = useCallback((p: Page) => {
    if (window.location.hash !== `#/${p}`) window.location.hash = `/${p}`;
    setPage(p);
    window.scrollTo({ top: 0 });
  }, []);
  const [engine, setEngine] = useState<EngineHealth>({ state: "checking" });
  const [capacity, setCapacity] = useState(DEFAULT_CAPACITY);
  const [state, setState] = useState<EngineState | null>(null);
  const [status, setStatus] = useState<StatusSource>({ kind: "idle" });
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<"ops" | "code">("ops");
  const [code, setCode] = useState(EXAMPLES[0].code);
  const [compiled, setCompiled] = useState<{ ops: LineOp[]; src: string } | null>(null);
  const [codeDone, setCodeDone] = useState(0);
  const [codeErrorLine, setCodeErrorLine] = useState<number | null>(null);
  const [lines, setLines] = useState<(number | undefined)[]>([]);
  const [demo, setDemo] = useState<{ active: boolean; step: number; playing: boolean }>({ active: false, step: 0, playing: false });

  // The log of operations is the whole table: the engine replays it on a fresh strata::Table.
  const opsRef = useRef<Op[]>([]);
  const capRef = useRef(DEFAULT_CAPACITY);
  const seq = useRef(0);

  const linesRef = useRef<(number | undefined)[]>([]);
  // lines: the source line of each operation when it came from the code window
  const commit = useCallback(async (cap: number, ops: Op[], opLines?: (number | undefined)[]) => {
    const s = await runOps(cap, ops);
    opsRef.current = ops;
    linesRef.current = opLines ?? ops.map((_, i) => linesRef.current[i]);
    setLines(linesRef.current);
    capRef.current = cap;
    setCapacity(cap);
    setState(s);
    return s;
  }, []);

  const fail = useCallback((e: unknown) => {
    const message = e instanceof Error ? e.message : String(e);
    if (e instanceof EngineError && e.unavailable) setEngine({ state: "down" });
    setStatus({ kind: "error", message, seq: ++seq.current });
  }, []);

  const reset = useCallback(async (cap: number, ops: Op[] = []) => {
    const s = await commit(cap, ops, ops.map(() => undefined));
    const last = s.ops[s.ops.length - 1];
    setStatus(last ? { kind: "op", result: last, seq: ++seq.current } : { kind: "idle" });
    return s;
  }, [commit]);

  const connect = useCallback(async () => {
    setEngine({ state: "checking" });
    const h = await health();
    if (!h) return setEngine({ state: "down" });
    setEngine({ state: "ready", compiler: h.compiler });
    try { await reset(capRef.current, opsRef.current); } catch (e) { fail(e); }
  }, [reset, fail]);

  useEffect(() => { void connect(); }, [connect]);

  // One user operation: append it and let the engine replay the log.
  const apply = useCallback(async (op: Op) => {
    if (opsRef.current.length >= MAX_OPS) {
      setStatus({ kind: "invalid", message: `The demo keeps at most ${MAX_OPS} operations. Reset to continue.`, seq: ++seq.current });
      return null;
    }
    const s = await commit(capRef.current, [...opsRef.current, op], [...linesRef.current, undefined]);
    setStatus({ kind: "op", result: s.ops[s.ops.length - 1], seq: ++seq.current });
    return s;
  }, [commit]);

  // ---- code window: the program becomes a list of operations, run in full or one at a time ----
  const stripLine = (ops: LineOp[]): Op[] => ops.map(({ line: _line, ...op }) => op as Op);
  const showProgress = (s: EngineState, n: number) => {
    const last = s.ops[s.ops.length - 1];
    setStatus(last ? { kind: "op", result: last, seq: ++seq.current }
      : { kind: "invalid", message: n === 0 ? "This program makes no symbol-table calls. Declare a variable or use one." : "Restarted.", seq: ++seq.current });
  };
  const compileCode = (): { ops: LineOp[]; src: string } | null => {
    try {
      const c = { ops: compile(code).ops, src: code };
      setCompiled(c);
      setCodeDone(0);
      setCodeErrorLine(null);
      return c;
    } catch (e) {
      if (e instanceof CodeError) {
        setCodeErrorLine(e.line);
        setStatus({ kind: "invalid", message: `Line ${e.line}: ${e.message}`, seq: ++seq.current });
        return null;
      }
      throw e;
    }
  };
  const codeRun = () => guarded(async () => {
    const c = compileCode();
    if (!c) return;
    const s = await commit(capRef.current, stripLine(c.ops), c.ops.map((o) => o.line));
    setCodeDone(c.ops.length);
    showProgress(s, c.ops.length);
  });
  const codeStep = () => guarded(async () => {
    let c = compiled, done = codeDone;
    if (!c || c.src !== code) {
      c = compileCode();
      if (!c) return;
      done = 0;
    }
    if (done >= c.ops.length) return;
    const upto = c.ops.slice(0, done + 1);
    const s = await commit(capRef.current, stripLine(upto), upto.map((o) => o.line));
    setCodeDone(done + 1);
    showProgress(s, c.ops.length);
  });
  const codeRestart = () => guarded(async () => {
    await commit(capRef.current, [], []);
    setCodeDone(0);
    setStatus({ kind: "idle" });
  });

  const guarded = useCallback(async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try { await fn(); } catch (e) { fail(e); } finally { setBusy(false); }
  }, [fail]);

  // ---- guided demo: five deterministic steps on a 256-byte table ----------------------
  const demoStep = useCallback(async (i: number) => {
    switch (i) {
      case 0:
        await reset(DEMO_CAPACITY);
        await sleep(250);
        await apply({ op: "declare", name: "count", type: 0, value: 1 });
        break;
      case 1:
        await apply({ op: "enter" });
        break;
      case 2:
        await apply({ op: "declare", name: "count", type: 0, value: 2 });
        await sleep(900);
        await apply({ op: "lookup", name: "count" });
        break;
      case 3:
        await apply({ op: "exit" });
        await sleep(1100);
        await apply({ op: "lookup", name: "count" });
        break;
      case 4: {
        for (let k = 0; k < 40; k++) {
          const s = await apply({ op: "declare", name: `symbol_filler_${String(k).padStart(2, "0")}`, type: 0, value: k });
          if (!s || s.ops[s.ops.length - 1].effect === "refused") break;
          await sleep(320);
        }
        // Show the refusal for a moment, then prove the old state is intact.
        await sleep(1800);
        const s = await apply({ op: "lookup", name: "count" });
        await sleep(1400);
        // Keep the refusal as the headline result of the step.
        const refusal = s && [...s.ops].reverse().find((o) => o.effect === "refused");
        if (refusal) setStatus({ kind: "op", result: refusal, seq: ++seq.current });
        break;
      }
    }
  }, [apply, reset]);

  const demoRunning = useRef(false);
  const demoStepRef = useRef(0);
  demoStepRef.current = demo.step;
  const nextDemoStep = useCallback(async () => {
    if (demoRunning.current) return;
    demoRunning.current = true;
    setBusy(true);
    try {
      const i = demoStepRef.current;
      await demoStep(i);
      setDemo((d) => ({ ...d, step: i + 1, playing: d.playing && i + 1 < DEMO_STEPS.length }));
    } catch (e) {
      fail(e);
      setDemo((d) => ({ ...d, playing: false }));
    } finally {
      demoRunning.current = false;
      setBusy(false);
    }
  }, [demoStep, fail]);

  useEffect(() => {
    if (!demo.active || !demo.playing || busy || demo.step >= DEMO_STEPS.length) return;
    const t = setTimeout(() => void nextDemoStep(), demo.step === 0 ? 300 : 2800);
    return () => clearTimeout(t);
  }, [demo, busy, nextDemoStep]);

  const startDemo = () => { go("lab"); setTab("ops"); setDemo({ active: true, step: 0, playing: true }); };
  const restartDemo = () => {
    demoStepRef.current = 0;
    setDemo({ active: true, step: 0, playing: true });
  };
  const closeDemo = () => setDemo({ active: false, step: 0, playing: false });

  const ready = engine.state === "ready";
  const controlsDisabled = !ready || busy || !state || (demo.active && demo.playing);

  return (
    <div className="app">
      <Header
        page={page}
        onPage={go}
        health={engine}
        onRetry={() => void connect()}
        onRunDemo={startDemo}
        onReset={() => { closeDemo(); void guarded(() => reset(capRef.current)); }}
        demoActive={demo.active}
        busy={busy}
      />
      <main className="page">
        {page === "overview" && <Overview go={go} />}
        {page === "benchmarks" && <Benchmarks ready={ready} />}
        {page === "stress" && <Stress />}
        {page === "method" && <Method />}
        {page === "lab" && (<>
        <header className="page-head">
          <h1>Live lab</h1>
          <p>
            Every operation here runs on the real <code>strata::Table</code> from <code>include/strata/strata.hpp</code>, compiled into a local
            C++ engine, inside one fixed buffer of <b className="mono">{capacity >= 1024 ? `${capacity / 1024} KiB` : `${capacity} bytes`}</b>.
            Declare names, open and close scopes, or write a small C program and step through the calls a compiler would make.
          </p>
        </header>

        {demo.active && (
          <GuidedDemo
            step={demo.step}
            outcome={status.kind === "op" ? describe(status.result) : undefined}
            playing={demo.playing}
            busy={busy}
            onNext={() => void nextDemoStep()}
            onTogglePlay={() => setDemo((d) => ({ ...d, playing: !d.playing }))}
            onRestart={restartDemo}
            onClose={closeDemo}
          />
        )}

        {engine.state === "down" && (
          <div className="card offline" role="alert">
            <b>The local STRATA engine is not reachable.</b> Start it from the repository with <code>cd frontend/web</code> then <code>npm start</code>, and
            press Retry. Nothing on this page is simulated, so it stays empty without the engine.
            <button className="btn small" onClick={() => void connect()}>Retry</button>
          </div>
        )}

        <div className="workspace">
          <div className="col-left">
            <div className="tabs" role="tablist" aria-label="Input">
              <button role="tab" aria-selected={tab === "ops"} className={tab === "ops" ? "on" : ""} onClick={() => setTab("ops")}>Operations</button>
              <button role="tab" aria-selected={tab === "code"} className={tab === "code" ? "on" : ""} onClick={() => { setTab("code"); }} disabled={demo.active && demo.playing}>
                Write code
              </button>
            </div>
            {tab === "code" ? (
              <CodeEditor
                code={code}
                onCode={(c) => { setCode(c); setCodeErrorLine(null); }}
                capacity={capacity}
                onCapacity={(c) => void guarded(async () => { await reset(c); setCodeDone(0); })}
                disabled={controlsDisabled}
                total={compiled && compiled.src === code ? compiled.ops.length : null}
                done={codeDone}
                currentLine={compiled && compiled.src === code && codeDone > 0 ? (compiled.ops[codeDone - 1]?.line ?? null) : null}
                errorLine={codeErrorLine}
                stale={compiled !== null && compiled.src !== code}
                onRun={() => void codeRun()}
                onStep={() => void codeStep()}
                onRestart={() => void codeRestart()}
              />
            ) : (
            <Controls
              disabled={controlsDisabled}
              capacity={capacity}
              depth={state?.stats.depth ?? 0}
              onOp={(op) => void guarded(() => apply(op))}
              onInvalid={(message) => setStatus({ kind: "invalid", message, seq: ++seq.current })}
              onCapacity={(c) => void guarded(() => reset(c))}
              onResetExample={() => { closeDemo(); void guarded(() => reset(capRef.current, EXAMPLE)); }}
            />
            )}
            <StatusLine source={status} />
            {state && <Timeline state={state} lines={lines} />}
          </div>
          <div className="col-right">
            {state ? (
              <>
                <SymbolTable state={state} />
                <MemoryInspector state={state} />
              </>
            ) : (
              <div className="card placeholder">{engine.state === "checking" ? "Connecting to the C++ engine…" : "Waiting for the engine."}</div>
            )}
          </div>
        </div>

        {state && (
          <p className="verify mono">
            engine {state.engine.source} · g++ {state.engine.compiler} · fixed mode · checks: invariants {state.checks.invariants ? "✓" : "✗"} · resolve()
            agrees {state.checks.resolveAgrees ? "✓" : "✗"} · reference model agrees {state.checks.modelAgrees ? "✓" : "✗"} · digest {state.digest}
          </p>
        )}
        </>)}
      </main>
      <footer className="foot">
        <span>STRATA · compiler design project, SCOPE, VIT Vellore</span>
        <span>Figures from recorded run <code>{"20261013-143828-paper"}</code> · interface in <code>frontend/</code>; the table itself is unchanged.</span>
      </footer>
    </div>
  );
}
