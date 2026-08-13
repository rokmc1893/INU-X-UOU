"use client";

/* 페이지들이 나눠 쓰는 조각. */
import { Src, Tag } from "./bits";
import type { Pair } from "@/lib/api";

/** 숫자 넷을 나란히 — 페이지 머리에서 한눈에. */
export function Counts({ items }: {
  items: { label: string; n: number; tone?: "gap" | "pen" | "flat"; hint?: string }[];
}) {
  return (
    <ul className="mb-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((x) => (
        <li key={x.label}
            className={`rounded-lg border bg-paper p-3 ${
              x.tone === "gap" && x.n > 0 ? "border-gap" : "border-rule"}`}>
          <p className="text-[12px] text-muted">{x.label}</p>
          <p className={`mt-0.5 text-[22px] font-bold leading-none ${
            x.tone === "gap" && x.n > 0 ? "text-gap" : x.tone === "pen" ? "text-pen" : ""}`}>
            {x.n}<span className="ml-0.5 text-[13px] font-normal text-muted">건</span>
          </p>
          {x.hint && <p className="mt-1 text-[11px] text-faint">{x.hint}</p>}
        </li>
      ))}
    </ul>
  );
}

/** 쌍 목록 — 겹침·넘기는 절차에 두루 쓴다. */
export function PairList({ title, tone, rows, note }: {
  title: string; tone: "gap" | "flat"; rows: Pair[]; note?: string;
}) {
  if (!rows.length) return null;
  return (
    <section className="mb-5 rounded-lg border border-rule bg-paper p-5">
      <p className="mb-1 flex flex-wrap items-center gap-2">
        <Tag tone={tone}>{rows.length}건</Tag>
        <b className="text-[15px]">{title}</b>
      </p>
      {note && <p className="mb-2 text-[12px] text-muted">{note}</p>}
      <ul className="mt-2 space-y-2">
        {rows.map((p) => (
          <li key={p.id} className={`border-l-2 pl-3 ${tone === "gap" ? "border-gap" : "border-rule"}`}>
            <span className="text-[14px] font-medium">{p.name}</span><Src url={p.url} />
            <span className="mt-0.5 block text-[12px] text-muted">{p.reason}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function Card({ title, children, sub }: {
  title?: string; sub?: string; children: React.ReactNode;
}) {
  return (
    <section className="mb-5 rounded-lg border border-rule bg-paper p-5">
      {title && <h2 className="text-[16px]">{title}</h2>}
      {sub && <p className="mt-1 text-[12px] text-muted">{sub}</p>}
      <div className={title ? "mt-3" : ""}>{children}</div>
    </section>
  );
}

/** 몇 건 중 몇 건이 확인됐나 — 한 줄 막대. */
export function RatioBar({ done, total, label }: {
  done: number; total: number; label: string;
}) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-baseline justify-between text-[13px]">
        <span>{label}</span>
        <span className="text-muted">{done}÷{total}건 ({pct}%)</span>
      </div>
      <div className="mt-1 h-3 w-full overflow-hidden rounded-sm border border-rule bg-shell">
        <div className="h-full bg-pen" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
