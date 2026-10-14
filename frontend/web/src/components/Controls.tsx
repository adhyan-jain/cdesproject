import { useState, type FormEvent } from "react";
import type { Op } from "../lib/engine";
import { TYPES, encodeValue, nameError, type TypeName } from "../lib/values";

const PLACEHOLDER: Record<TypeName, string> = { int: "42", float: "3.14", char: "x", bool: "true" };
export const CAPACITIES = [256, 512, 1024, 2048];

interface Props {
  disabled: boolean;
  capacity: number;
  depth: number;
  onOp: (op: Op) => void;
  onInvalid: (message: string) => void;
  onCapacity: (bytes: number) => void;
  onResetExample: () => void;
}

export function Controls({ disabled, capacity, depth, onOp, onInvalid, onCapacity, onResetExample }: Props) {
  const [name, setName] = useState("count");
  const [type, setType] = useState<TypeName>("int");
  const [value, setValue] = useState("1");

  const declare = (e?: FormEvent) => {
    e?.preventDefault();
    const n = name.trim();
    const bad = nameError(n);
    if (bad) return onInvalid(bad);
    const v = encodeValue(type, value);
    if ("error" in v) return onInvalid(v.error);
    onOp({ op: "declare", name: n, type: TYPES.indexOf(type), value: v.value });
  };
  const lookup = () => {
    const n = name.trim();
    const bad = nameError(n);
    if (bad) return onInvalid(bad);
    onOp({ op: "lookup", name: n });
  };

  return (
    <section className="card controls" aria-labelledby="controls-title">
      <div className="card-head">
        <h2 id="controls-title">Operations</h2>
        <span className="card-hint">calls on strata::Table</span>
      </div>
      <form className="controls-body" onSubmit={declare}>
        <label className="field">
          <span className="label">Variable name</span>
          <input
            className="input mono"
            value={name}
            onChange={(e) => setName(e.target.value)}
            spellCheck={false}
            autoComplete="off"
            maxLength={64}
            placeholder="count"
          />
        </label>
        <div className="field">
          <span className="label" id="type-label">Type</span>
          <div className="segmented" role="radiogroup" aria-labelledby="type-label">
            {TYPES.map((t) => (
              <button
                type="button"
                key={t}
                role="radio"
                aria-checked={type === t}
                className={type === t ? "on" : ""}
                onClick={() => {
                  setType(t);
                  setValue(PLACEHOLDER[t]);
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <label className="field">
          <span className="label">Value</span>
          <input className="input mono" value={value} onChange={(e) => setValue(e.target.value)} spellCheck={false} autoComplete="off" placeholder={PLACEHOLDER[type]} />
        </label>
        <div className="btn-row">
          <button type="submit" className="btn btn-primary grow" disabled={disabled}>
            Declare variable
          </button>
          <button type="button" className="btn grow" onClick={lookup} disabled={disabled}>
            Look up variable
          </button>
        </div>
        <div className="btn-row">
          <button type="button" className="btn grow" onClick={() => onOp({ op: "enter" })} disabled={disabled}>
            <span className="brace" aria-hidden="true">{"{"}</span> Enter scope
          </button>
          <button type="button" className="btn grow" onClick={() => onOp({ op: "exit" })} disabled={disabled || depth === 0} title={depth === 0 ? "Already at Global scope" : undefined}>
            <span className="brace" aria-hidden="true">{"}"}</span> Exit scope
          </button>
        </div>
      </form>
      <div className="controls-foot">
        <label className="field inline">
          <span className="label">Buffer</span>
          <select className="select mono" value={capacity} onChange={(e) => onCapacity(Number(e.target.value))} disabled={disabled}>
            {CAPACITIES.map((c) => (
              <option key={c} value={c}>
                {c >= 1024 ? `${c / 1024} KiB` : `${c} B`}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="btn btn-ghost small" onClick={onResetExample} disabled={disabled}>
          Reset example
        </button>
      </div>
    </section>
  );
}
