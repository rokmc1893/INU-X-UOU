"use client";

/* 관계도 — 이 사업이 어디에 물려 있나.
 *
 * 선의 종류가 뜻을 나른다. 목록으로는 "몇 건"만 보이는데, 그려 놓으면 이 사업이
 * 어느 쪽으로 얽혀 있는지가 한눈에 들어온다.
 *   굵은 붉은 선  정리가 필요한 겹침
 *   가는 회색 선  겹쳐 보이지만 겹치지 않음
 *   점선          넘기는 절차가 없음
 */
import { useState } from "react";
import type { Pair, Review } from "@/lib/api";
import { Src } from "./bits";

type Node = { p: Pair; kind: "harmful" | "same" | "handoff"; x: number; y: number };

const KIND = {
  harmful: { stroke: "#c0392b", width: 2.5, dash: undefined, label: "정리 필요" },
  same: { stroke: "#9aa0a6", width: 1.2, dash: undefined, label: "겹치지 않음" },
  handoff: { stroke: "#9aa0a6", width: 1.2, dash: "5 4", label: "넘기는 절차 없음" },
} as const;

export default function Relations({ r }: { r: Review }) {
  const [sel, setSel] = useState<Pair | null>(null);

  const rows: { p: Pair; kind: Node["kind"] }[] = [
    ...r.overlaps.harmful.map((p) => ({ p, kind: "harmful" as const })),
    ...r.overlaps.intentional.map((p) => ({ p, kind: "same" as const })),
    ...r.overlaps.complement.map((p) => ({ p, kind: "same" as const })),
    ...r.handoffs.items.map((p) => ({ p, kind: "handoff" as const })),
  ];
  if (!rows.length) return null;

  const W = 860, cx = 200, R = 250;
  const H = Math.max(240, rows.length * 34 + 60);
  const cy = H / 2;
  const nodes: Node[] = rows.map((row, i) => {
    const t = rows.length === 1 ? 0.5 : i / (rows.length - 1);
    return { ...row, x: cx + R + 120, y: 40 + t * (H - 80) };
  });

  return (
    <section className="mb-5 rounded-lg border border-rule bg-paper p-5">
      <h2 className="text-[16px]">이 사업이 어디에 물려 있나</h2>
      <p className="mt-1 text-[12px] text-muted">선을 누르면 왜 그렇게 봤는지 나옵니다</p>

      <div className="mt-3 overflow-x-auto">
        <svg width={W} height={H} role="img"
             aria-label="검토 대상 사업과 다른 사업들의 관계를 선으로 이은 그림">
          {nodes.map((n, i) => {
            const k = KIND[n.kind];
            const on = sel?.id === n.p.id;
            return (
              <g key={`${n.p.id}-${i}`} onClick={() => setSel(on ? null : n.p)}
                 style={{ cursor: "pointer" }}>
                <path
                  d={`M ${cx + 96} ${cy} C ${cx + 220} ${cy}, ${n.x - 150} ${n.y}, ${n.x - 8} ${n.y}`}
                  fill="none" stroke={k.stroke} strokeWidth={on ? k.width + 1.5 : k.width}
                  strokeDasharray={k.dash} opacity={sel && !on ? 0.3 : 1}
                />
                <circle cx={n.x} cy={n.y} r={4} fill={k.stroke} opacity={sel && !on ? 0.3 : 1} />
                <text x={n.x + 10} y={n.y + 4} className="fill-ink text-[11px]"
                      opacity={sel && !on ? 0.4 : 1}>
                  {n.p.name.length > 24 ? `${n.p.name.slice(0, 23)}…` : n.p.name}
                  <title>{n.p.name}</title>
                </text>
              </g>
            );
          })}

          <rect x={cx - 96} y={cy - 24} width={192} height={48} rx={6}
                className="fill-pen-soft stroke-pen" strokeWidth={2} />
          <text x={cx} y={cy - 4} textAnchor="middle" className="fill-pen text-[11px] font-bold">
            지금 검토 중
          </text>
          <text x={cx} y={cy + 12} textAnchor="middle" className="fill-ink text-[11px]">
            {r.card.name.length > 18 ? `${r.card.name.slice(0, 17)}…` : r.card.name}
            <title>{r.card.name}</title>
          </text>
        </svg>
      </div>

      <p className="mt-1 flex flex-wrap items-center gap-4 text-[12px] text-muted">
        {Object.entries(KIND).map(([k, v]) => (
          <span key={k} className="flex items-center gap-1.5">
            <svg width={24} height={8}>
              <line x1={0} y1={4} x2={24} y2={4} stroke={v.stroke}
                    strokeWidth={v.width} strokeDasharray={v.dash} />
            </svg>
            {v.label}
          </span>
        ))}
      </p>

      {sel && (
        <div className="mt-3 rounded-md border border-rule bg-shell p-3 text-[13px]">
          <p className="font-medium">{sel.name}<Src url={sel.url} /></p>
          <p className="mt-1 text-muted">{sel.reason}</p>
        </div>
      )}
    </section>
  );
}
