// Plain-language background and limitations; the measured numbers are in Accuracy.tsx.
export function About() {
  return (
    <section className="about" aria-labelledby="about-title">
      <h2 id="about-title" className="section-title">About STRATA</h2>
      <div className="about-grid">
        <article className="card explain">
          <h3>What is a symbol table?</h3>
          <p>
            While a compiler reads a program it keeps a dictionary of every name it has seen: <code>count</code> is an <code>int</code>, declared
            here. Each time the program uses a name, the compiler looks it up. That dictionary is the symbol table.
          </p>
        </article>
        <article className="card explain">
          <h3>What is shadowing?</h3>
          <p>
            A name declared inside <code>{"{ }"}</code> can reuse an outer name. Inside the block the inner one wins; when the block ends, the outer
            one must come back exactly as it was.
          </p>
        </article>
        <article className="card explain">
          <h3>Why one fixed buffer?</h3>
          <p>
            Ordinary tables call the allocator for every name. On a small embedded device that makes memory use unpredictable. STRATA keeps everything
            in one block the caller provides: it never allocates, and its memory need is known in advance.
          </p>
        </article>
        <article className="card explain">
          <h3>How does the undo stack work?</h3>
          <p>
            Each name has one record holding its innermost declaration. A declaration that hides another saves the old value on an undo stack at the
            end of the buffer. Leaving a scope pops that stack: hidden values are restored, new names are removed.
          </p>
        </article>
        <article className="card explain">
          <h3>What happens when it is full?</h3>
          <p>
            Space is reserved before anything is written. If it does not fit, the call returns <code>kNoMemory</code> and the table is bit-for-bit
            unchanged. Nothing is ever half-done.
          </p>
        </article>
      </div>

      <div className="about-grid one">
        <article className="card results">
          <h3>Limitations</h3>
          <ul className="plain">
            <li>STRATA is <b>not faster</b> than a well-built conventional allocator-free table; its gains are predictable memory and far fewer allocations.</li>
            <li>Most of the saving comes from using one buffer at all; STRATA's own design adds about 17% less memory on top.</li>
            <li>Embedded runs were on an <b>emulated</b> Cortex-M3 (QEMU, 64 KiB RAM), not real hardware.</li>
            <li>Traces come from one compiler (TCC) and C code only. Inside the chibicc compiler the output was identical but compile time did not improve.</li>
            <li>The default hash is unkeyed; crafted names can slow it down. An opt-in keyed hash and probe limit exist (not used in this demo).</li>
            <li>The algorithm (hash table + undo stack) is textbook; the contribution is the bounded-memory implementation, its guarantees and the measurements.</li>
          </ul>
        </article>
      </div>
    </section>
  );
}
