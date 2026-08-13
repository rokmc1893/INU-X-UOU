"use client";

/* 관계도 — 이 사업이 어디에 물려 있나.
 *
 * 선의 종류가 뜻을 나른다. 목록으로는 "몇 건"만 보이는데, 그려 놓으면 이 사업이
 * 어느 쪽으로 얽혀 있는지가 한눈에 들어온다.
 *   굵은 붉은 선  정리가 필요한 겹침
 *   가는 회색 선  겹쳐 보이지만 겹치지 않음
 *   점선          넘기는 절차가 없음
 *
 * 종류가 같은 것끼리 묶어 두면 열 줄이 한 다발로 엉키지 않는다.
 */
import { useState } from "react";
import type { Pair, Review } from "@/lib/api";
import { Src } from "./bits";

type Kind = "harmful" | "same" | "handoff";

const KIND: Record<Kind, { stroke: string; width: number; dash?: string; label: string }> = {
  harmful: { stroke: "#c0392b", width: 2.6, label: "정리 필요" },
  same: { stroke: "#9aa0a6", width: 1.4, label: "겹치지 않음" },
  handoff: { stroke: "#9aa0a6", width: 1.4, dash: "5 4", label: "넘기는 절차 없음" },
};

const W = 940;
const CX = 190;          // 가운데 상자 중심
const LX = 600;          // 이름이 시작하는 자리
const ROW = 34;          // 한 줄 높이
const GROUP_GAP = 12;    // 종류가 바뀌는 자리에 두는 틈

export default function Relations({ r }: { r: Review }) {
  const [sel, setSel] = useState<Pair | null>(null);
  const [hover, setHover] = useState<string | null>(null);

  const rows: { p: Pair; kind: Kind }[] = [
    ...r.overlaps.harmful.map((p) => ({ p, kind: "harmful" as const })),
    ...r.overlaps.intentional.map((p) => ({ p, kind: "same" as const })),
    ...r.overlaps.complement.map((p) => ({ p, kind: "same" as const })),
    ...r.handoffs.items.map((p) => ({ p, kind: "handoff" as const })),
  ];
  if (!rows.length) return null;

  // 종류가 바뀌는 자리에 틈을 둬 다발이 갈라져 보이게 한다
  const ys: number[] = [];
  let y = 30;
  rows.forEach((row, i) => {
    if (i > 0 && rows[i - 1].kind !== row.kind) y += GROUP_GAP;
    ys.push(y);
    y += ROW;
  });
  const H = y + 20;
  const cy = H / 2;

  return (
    <section className="mb-5 rounded-lg border border-rule bg-paper p-5">
      <h2 className="text-[16px]">이 사업이 어디에 물려 있나</h2>
      <p className="mt-1 text-[13px] text-muted">
        오른쪽 이름을 누르면 왜 그렇게 봤는지 나옵니다
      </p>

      <div className="mt-3 overflow-x-auto">
        <svg width={W} height={H} role="img"
             aria-label="검토 대상 사업과 다른 사업들의 관계를 선으로 이은 그림">
          {rows.map((row, i) => {
            const k = KIND[row.kind];
            const ry = ys[i];
            const on = sel?.id === row.p.id;
            const hot = hover === row.p.id;
            const lit = on || hot;
            const dim = (sel || hover) && !lit;
            const name = row.p.name.length > 22 ? `${row.p.name.slice(0, 21)}…` : row.p.name;
            return (
              <g key={`${row.p.id}-${i}`}
                 onClick={() => setSel(on ? null : row.p)}
                 onMouseEnter={() => setHover(row.p.id)}
                 onMouseLeave={() => setHover(null)}
                 style={{ cursor: "pointer" }}>
                {/* 누를 수 있는 넓은 자리 — 글자만 겨냥하지 않아도 눌린다 */}
                <rect x={LX - 26} y={ry - 15} width={W - LX + 22} height={30} rx={5}
                      className={lit ? "fill-pen-soft" : "fill-transparent"} />
                <path
                  d={`M ${CX + 108} ${cy} C ${CX + 250} ${cy}, ${LX - 190} ${ry}, ${LX - 22} ${ry}`}
                  fill="none" stroke={k.stroke}
                  strokeWidth={lit ? k.width + 1.4 : k.width}
                  strokeDasharray={k.dash} opacity={dim ? 0.25 : 1}
                />
                <circle cx={LX - 14} cy={ry} r={lit ? 6 : 4.5} fill={k.stroke}
                        opacity={dim ? 0.25 : 1} />
                <text x={LX} y={ry + 5}
                      className={`text-[13px] ${lit ? "fill-pen font-semibold" : "fill-ink"}`}
                      opacity={dim ? 0.4 : 1}
                      style={{ textDecoration: lit ? "underline" : "none" }}>
                  {name}
                  <title>{row.p.name}</title>
                </text>
                {lit && (
                  <text x={W - 12} y={ry + 5} textAnchor="end"
                        className="fill-pen text-[12px] font-semibold">보기 ›</text>
                )}
              </g>
            );
          })}

          <rect x={CX - 108} y={cy - 27} width={216} height={54} rx={7}
                className="fill-pen-soft stroke-pen" strokeWidth={2} />
          <text x={CX} y={cy - 5} textAnchor="middle"
                className="fill-pen text-[12px] font-bold">지금 검토 중</text>
          <text x={CX} y={cy + 13} textAnchor="middle" className="fill-ink text-[12px]">
            {r.card.name.length > 17 ? `${r.card.name.slice(0, 16)}…` : r.card.name}
            <title>{r.card.name}</title>
          </text>
        </svg>
      </div>

      <p className="mt-1 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-[12px] text-muted">
        {(Object.keys(KIND) as Kind[]).map((k) => {
          const v = KIND[k];
          const n = rows.filter((x) => x.kind === k).length;
          if (!n) return null;
          return (
            <span key={k} className="flex items-center gap-1.5">
              <svg width={26} height={8} aria-hidden>
                <line x1={0} y1={4} x2={26} y2={4} stroke={v.stroke}
                      strokeWidth={v.width} strokeDasharray={v.dash} />
              </svg>
              {v.label} {n}건
            </span>
          );
        })}
      </p>

      {sel ? (
        <div className="mt-3 rounded-md border border-pen bg-pen-soft p-3.5 text-[13px]">
          <p className="text-[14px] font-semibold">{sel.name}<Src url={sel.url} /></p>
          <p className="mt-1">{sel.reason}</p>
        </div>
      ) : (
        <p className="mt-3 rounded-md border border-dashed border-rule bg-shell p-3 text-[13px] text-muted">
          이름을 누르면 그 사업과 어떻게 얽혀 있는지, 원문은 어디인지 여기에 나옵니다.
        </p>
      )}
    </section>
  );
}
