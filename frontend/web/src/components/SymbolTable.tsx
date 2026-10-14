import { Fragment, useEffect, useState } from "react";
import type { EngineState, ExitItem } from "../lib/engine";
import { formatValue, scopeName, typeName } from "../lib/values";
import { ScopeTrail } from "./ScopeTrail";

// Visible declarations are STRATA's identifier records (one per visible name, holding the
// innermost declaration). Hidden declarations are the shadow entries on its undo stack.
export function SymbolTable({ state }: { state: EngineState }) {
  const last = state.ops[state.ops.length - 1];
  const stamp = `${state.ops.length}:${state.digest}`;
  const [leaving, setLeaving] = useState<{ stamp: string; items: ExitItem[] }>({ stamp: "", items: [] });

  useEffect(() => {
    if (last?.op === "X" && last.effect === "exited") {
      const items = [...(last.removed ?? []), ...(last.restored ?? [])];
      setLeaving({ stamp, items });
      const t = setTimeout(() => setLeaving({ stamp: "", items: [] }), 1600);
      return () => clearTimeout(t);
    }
    setLeaving({ stamp: "", items: [] });
  }, [stamp]); // eslint-disable-line react-hooks/exhaustive-deps

  const hiddenBy = new Map<string, { value: number; type: number; depth: number }[]>();
  for (const u of state.undo) if (u.kind === "shadow") hiddenBy.set(u.name, [...(hiddenBy.get(u.name) ?? []), u]);

  const touched = (last?.op === "D" || last?.op === "V") && last.effect !== "refused" && last.effect !== "undeclared" ? last.name : undefined;
  const resolved = last?.op === "L" && last.found ? last.name : undefined;
  const restored = new Set(last?.op === "X" ? (last.restored ?? []).map((r) => r.name) : []);
  const removedHere = leaving.stamp === stamp ? leaving.items.filter((i) => !i.restored) : [];
  const replacedHere = new Map(leaving.stamp === stamp ? leaving.items.filter((i) => i.restored).map((i) => [i.name, i]) : []);

  return (
    <section className="card table-card" aria-labelledby="table-title">
      <div className="card-head">
        <h2 id="table-title">Symbol table</h2>
        <span className="card-hint">
          {state.stats.liveIdentifiers} visible · {state.stats.liveDeclarations} declarations
        </span>
      </div>
      <ScopeTrail state={state} />
      <div className="table-wrap">
        <table className="symtab">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Value</th>
              <th>Scope</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {state.records.length === 0 && removedHere.length === 0 && (
              <tr className="empty-row">
                <td colSpan={5}>
                  The table is empty. Declare a variable to store it in the buffer.
                </td>
              </tr>
            )}
            {state.records.map((r) => {
              const hidden = hiddenBy.get(r.name) ?? [];
              const cls = [
                "row",
                touched === r.name ? "flash" : "",
                resolved === r.name ? "resolved" : "",
                restored.has(r.name) ? "flash-restore" : "",
                hidden.length ? "is-shadowing" : "",
              ].join(" ");
              const replaced = replacedHere.get(r.name);
              return (
                <Fragment key={`${r.name}:${r.ref}`}>
                  {replaced && (
                    <tr className="row leaving" key={`${stamp}-out-${r.name}`}>
                      <td className="mono name">{r.name}</td>
                      <td>{typeName(replaced.type)}</td>
                      <td className="mono">{formatValue(replaced.type, replaced.value)}</td>
                      <td>{scopeName(replaced.depth)}</td>
                      <td><span className="chip chip-muted">scope ended</span></td>
                    </tr>
                  )}
                  <tr className={cls} key={`${stamp}-${r.name}`}>
                    <td className="mono name">{r.name}</td>
                    <td>{typeName(r.type)}</td>
                    <td className="mono">{formatValue(r.type, r.value)}</td>
                    <td>{scopeName(r.depth)}</td>
                    <td>
                      {restored.has(r.name) ? (
                        <span className="chip chip-restore">restored</span>
                      ) : hidden.length ? (
                        <span className="chip chip-shadow">shadowing</span>
                      ) : (
                        <span className="chip chip-ok">visible</span>
                      )}
                      {resolved === r.name && <span className="chip chip-lookup">lookup</span>}
                    </td>
                  </tr>
                  {hidden.map((h, i) => (
                    <tr className={`row hidden-row ${touched === r.name && i === 0 && last?.effect === "shadow" ? "slide-in" : ""}`} key={`${stamp}-${r.name}-h${i}`}>
                      <td className="mono name">
                        <span className="hidden-mark" aria-hidden="true">└</span>
                        {r.name}
                      </td>
                      <td>{typeName(h.type)}</td>
                      <td className="mono">{formatValue(h.type, h.value)}</td>
                      <td>{scopeName(h.depth)}</td>
                      <td>
                        <span className="chip chip-muted">hidden · on undo stack</span>
                      </td>
                    </tr>
                  ))}
                </Fragment>
              );
            })}
            {removedHere.map((x) => (
              <tr className="row leaving" key={`${stamp}-gone-${x.name}`}>
                <td className="mono name">{x.name}</td>
                <td>{typeName(x.type)}</td>
                <td className="mono">{formatValue(x.type, x.value)}</td>
                <td>{scopeName(x.depth)}</td>
                <td><span className="chip chip-muted">removed</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {last?.op === "X" && last.effect === "exited" && (
        <p className="table-note" key={stamp}>
          Scope exit popped the undo stack: {last.restored?.length ? `${last.restored.length} hidden declaration${last.restored.length > 1 ? "s" : ""} restored` : "nothing to restore"}
          {last.removed?.length ? `, ${last.removed.length} name${last.removed.length > 1 ? "s" : ""} removed from the index` : ""}.
        </p>
      )}
    </section>
  );
}
