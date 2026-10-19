import recorded from "../data/recorded.json";
import { About } from "../components/About";

const TABLES: [string, string][] = [
  ["STRATA", "Interned names, undo stack and scope marks in one caller-supplied buffer (this project)."],
  ["Conventional single-buffer table", "Hash chains in an allocator-free arena; the fair baseline (benchmarks/baselines/arena_chain.hpp)."],
  ["std::unordered_map + undo log", "The algorithm of LLVM's ScopedHashTable, on the standard library map."],
  ["Swiss map + undo log", "The same algorithm on a Swiss-table node map (parallel-hashmap)."],
  ["One hash map per scope", "A stack of maps, the textbook design."],
  ["Interned Swiss flat map", "Names interned once, values in a flat Swiss map."],
];

export function Method() {
  return (
    <div className="stack">
      <header className="page-head">
        <h1>Method &amp; limits</h1>
        <p>How the numbers were produced, what they do not show, and how to reproduce them.</p>
      </header>

      <div className="grid-2">
        <article className="card prose">
          <h3>Measurement setup</h3>
          <dl className="kv">
            <dt>Recorded run</dt><dd><code>{recorded.run}</code></dd>
            <dt>Machine</dt><dd>{recorded.cpu.replace(/\(R\)|\(TM\)/g, "")}</dd>
            <dt>Compiler</dt><dd>{recorded.compiler}</dd>
            <dt>Kernel</dt><dd>{recorded.kernel}</dd>
            <dt>Rounds</dt><dd>{recorded.rounds}</dd>
            <dt>Workloads</dt><dd>Symbol-table calls logged by a patched Tiny C Compiler on 8 open-source C projects</dd>
            <dt>Correctness</dt><dd>Every answer compared with an independent reference model (<code>tests/reference_model.hpp</code>)</dd>
          </dl>
        </article>
        <article className="card prose">
          <h3>Tables compared</h3>
          <ul className="def-list">
            {TABLES.map(([k, v]) => <li key={k}><b>{k}</b><span>{v}</span></li>)}
          </ul>
        </article>
      </div>

      <About />

      <div className="grid-2">
        <article className="card prose">
          <h3>Reproduce</h3>
          <p>In WSL or Linux, from the repository root:</p>
          <pre className="code-block">{`bash scripts/test.sh                 # unit + differential tests
bash scripts/fetch_third_party.sh    # baselines (not copied into the repo)
bash scripts/run_all.sh <label>      # full benchmark run
python scripts/analyze.py results/raw/<run>
python scripts/make_report.py <run>`}</pre>
          <p>This page: <code>cd frontend/web</code>, <code>npm install</code>, <code>npm start</code>. Its figures are regenerated from <code>results/</code> with <code>npm run results</code>.</p>
        </article>
        <article className="card prose">
          <h3>Who made this</h3>
          <p>
            Shubhi Singh and Adhyan Jain, School of Computer Science and Engineering, VIT Vellore; course guide Prof. Bhuvaneshwari M. STRATA follows
            Adhyan Jain's earlier METIS-X symbol table.
          </p>
          <p className="muted">
            Much of the code, the measurements and this interface were produced with an AI coding assistant working in Shubhi Singh's environment, as the
            repository README states. All results are reproducible from the scripts above.
          </p>
          <p><a href="https://github.com/shubhisingh1510/cdesproject" target="_blank" rel="noreferrer">github.com/shubhisingh1510/cdesproject</a></p>
        </article>
      </div>
    </div>
  );
}
