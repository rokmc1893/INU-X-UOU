"use client";

/* 관계도 — 이 사업이 어디에 물려 있나.
 *
 * **색이 뜻을 나른다.** 앞서는 「겹치지 않음」과 「넘기는 절차 없음」이 같은 회색이라
 * 점선인지 실선인지로만 갈렸다. 화면 다른 곳에서 쓰는 세 가지 뜻에 그대로 맞춘다.
 *   붉음(gap)   조치가 필요하다        — 정리가 필요한 겹침
 *   파랑(pen)   확인했고 문제없다      — 겹쳐 보이지만 겹치지 않음
 *   황토(hold)  살펴봐야 한다          — 넘기는 절차가 없음
 * 색만으로 가르지 않도록 굵기와 점선도 함께 준다.
 *
 * 폭은 자리에 맞춰 늘고 준다. 이름이 잘리는 길이도 그에 따라 달라진다.
 */
import { useEffect, useRef, useState } from "react";
import type { Pair, Review } from "@/lib/api";
import { Src } from "./bits";

type Kind = "harmful" | "same" | "handoff";

const KIND: Record<Kind, {
  stroke: string; soft: string; width: number; dash?: string;
  label: string; hint: string;
}> = {
  harmful: {
    stroke: "#c0392b", soft: "#fdf0ee", width: 2.6,
    label: "정리가 필요합니다",
    hint: "받는 사람·주는 것·직무가 모두 같습니다. 협의 단계에서 중복으로 반려될 수 있어 미리 조정해야 합니다.",
  },
  handoff: {
    stroke: "#b08a2a", soft: "#fbf6e9", width: 1.6, dash: "5 4",
    label: "다음 사업으로 넘기는 절차가 없습니다",
    hint: "앞 단계를 마친 사람을 뒤 단계 사업으로 넘기는 절차가 두 사업 문서 어디에도 적혀 있지 않습니다. 이어 주려면 절차를 새로 만들어야 합니다.",
  },
  same: {
    stroke: "#1f5fd0", soft: "#eef3fd", width: 1.6,
    label: "겹치지 않습니다",
    hint: "주는 것이 같아도 받는 사람이나 수단이 다릅니다. 검토서에 이 이유를 적어 두면 중복이라는 이유로 잘못 반려당하지 않습니다.",
  },
};
const ORDER: Kind[] = ["harmful", "handoff", "same"];

const CX = 190;
const ROW = 34;
const GROUP_GAP = 14;
const NAME_W = 8.6;   // 13px 한글 한 글자 어림 너비

export default function Relations({ r }: { r: Review }) {
  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(900);
  const [sel, setSel] = useState<Pair | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) =>
      setW(Math.max(560, Math.round(e.contentRect.width))));
    ro.observe(el);
    const t = setTimeout(() => setShown(true), 30);
    return () => { ro.disconnect(); clearTimeout(t); };
  }, []);

  const all: { p: Pair; kind: Kind }[] = [
    ...r.overlaps.harmful.map((p) => ({ p, kind: "harmful" as const })),
    ...r.overlaps.intentional.map((p) => ({ p, kind: "same" as const })),
    ...r.overlaps.complement.map((p) => ({ p, kind: "same" as const })),
    ...r.handoffs.items.map((p) => ({ p, kind: "handoff" as const })),
  ];
  if (!all.length) return null;
  const rows = ORDER.flatMap((k) => all.filter((x) => x.kind === k));

  const LX = Math.min(600, Math.max(430, W * 0.52));   // 이름이 시작하는 자리
  const maxChars = Math.max(10, Math.floor((W - LX - 66) / NAME_W));

  const ys: number[] = [];
  let y = 30;
  rows.forEach((row, i) => {
    if (i > 0 && rows[i - 1].kind !== row.kind) y += GROUP_GAP;
    ys.push(y); y += ROW;
  });
  const H = y + 20;
  const cy = H / 2;
  const cut = (s: string) => (s.length > maxChars ? `${s.slice(0, maxChars - 1)}…` : s);

  return (
    <section className="mb-5 rounded-lg border border-rule bg-paper p-5">
      <h2 className="text-[16px]">이 사업이 어디에 물려 있나</h2>
      <p className="mt-1 text-[13px] text-muted">
        오른쪽 이름을 누르면 왜 그렇게 봤는지 나옵니다
      </p>

      <div ref={box} className="mt-3 w-full overflow-x-auto">
        <svg width={W} height={H} role="img"
             aria-label="검토 대상 사업과 다른 사업들의 관계를 선으로 이은 그림">
          {rows.map((row, i) => {
            const k = KIND[row.kind];
            const ry = ys[i];
            const on = sel?.id === row.p.id;
            const hot = hover === row.p.id;
            const lit = on || hot;
            const dim = (sel || hover) && !lit;
            return (
              <g key={`${row.p.id}-${i}`}
                 onClick={() => setSel(on ? null : row.p)}
                 onMouseEnter={() => setHover(row.p.id)}
                 onMouseLeave={() => setHover(null)}
                 style={{
                   cursor: "pointer",
                   opacity: shown ? (dim ? 0.28 : 1) : 0,
                   transform: shown ? "none" : "translateX(-14px)",
                   transition: `opacity .45s ease ${i * 55}ms, transform .45s cubic-bezier(.2,.7,.3,1) ${i * 55}ms`,
                 }}>
                <rect x={LX - 26} y={ry - 15} width={W - LX + 22} height={30} rx={5}
                      fill={lit ? k.soft : "transparent"} />
                <path
                  d={`M ${CX + 108} ${cy} C ${CX + 240} ${cy}, ${LX - 180} ${ry}, ${LX - 22} ${ry}`}
                  fill="none" stroke={k.stroke}
                  strokeWidth={lit ? k.width + 1.4 : k.width}
                  strokeDasharray={k.dash}
                  style={{ transition: "stroke-width .15s ease" }}
                />
                <circle cx={LX - 14} cy={ry} r={lit ? 6 : 4.5} fill={k.stroke}
                        style={{ transition: "r .15s ease" }} />
                <text x={LX} y={ry + 5} className="text-[13px]"
                      fill={lit ? k.stroke : "#16191d"}
                      fontWeight={lit ? 600 : 400}
                      style={{ textDecoration: lit ? "underline" : "none" }}>
                  {cut(row.p.name)}
                  <title>{row.p.name}</title>
                </text>
                {lit && (
                  <text x={W - 12} y={ry + 5} textAnchor="end"
                        className="text-[12px] font-semibold" fill={k.stroke}>보기 ›</text>
                )}
              </g>
            );
          })}

          <g style={{
            opacity: shown ? 1 : 0,
            transition: "opacity .4s ease",
          }}>
            <rect x={CX - 108} y={cy - 27} width={216} height={54} rx={7}
                  className="fill-pen-soft stroke-pen" strokeWidth={2} />
            <text x={CX} y={cy - 5} textAnchor="middle"
                  className="fill-pen text-[12px] font-bold">지금 검토 중</text>
            <text x={CX} y={cy + 13} textAnchor="middle" className="fill-ink text-[12px]">
              {r.card.name.length > 17 ? `${r.card.name.slice(0, 16)}…` : r.card.name}
              <title>{r.card.name}</title>
            </text>
          </g>
        </svg>
      </div>

      <ul className="mt-2 space-y-2 border-t border-rule pt-3">
        {ORDER.map((k) => {
          const v = KIND[k];
          const n = rows.filter((x) => x.kind === k).length;
          if (!n) return null;
          return (
            <li key={k} className="grid grid-cols-[2.2rem_1fr] gap-2.5">
              <svg width={30} height={16} aria-hidden className="mt-1">
                <line x1={0} y1={8} x2={30} y2={8} stroke={v.stroke}
                      strokeWidth={v.width} strokeDasharray={v.dash} />
              </svg>
              <div>
                <p className="text-[13px] font-semibold" style={{ color: v.stroke }}>
                  {v.label} <span className="font-normal">— {n}건</span>
                </p>
                <p className="mt-0.5 text-[12px] leading-relaxed text-muted">{v.hint}</p>
              </div>
            </li>
          );
        })}
      </ul>

      {sel ? (
        <div className="rise mt-3 rounded-md border p-3.5 text-[13px]"
             style={{
               borderColor: KIND[rows.find((x) => x.p.id === sel.id)!.kind].stroke,
               background: KIND[rows.find((x) => x.p.id === sel.id)!.kind].soft,
             }}>
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
