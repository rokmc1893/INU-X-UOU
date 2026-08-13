"use client";

/* 산업 × 필요한 것 격자 — 빈칸이 어디에 몰려 있는지 한 장으로.
 *
 * 칸을 누르면 **그 유형을 주는 사업이 다른 산업에 몇 건 있는지**가 나온다.
 * 「돈을 주는 사업이 없다」와 「돈을 주는 사업은 있는데 이 산업엔 없다」는 전혀 다른
 * 이야기이고, 실제로 후자다 — 이 격자의 요점이 그것이다.
 */
import { useEffect, useState } from "react";
import { API } from "@/lib/api";
import { Src, Tag } from "./bits";

type Cell = {
  covered: number; total: number;
  signals: { id: string; type: string; grade: string; url: string; covered: boolean }[];
};
type Data = {
  needs: { need: string; plain: string; label: string }[];
  industries: string[];
  grid: Record<string, Record<string, Cell>>;
  postures: Record<string, { posture: string; why: string }>;
  supply: Record<string, {
    total: number; byIndustry: string[];
    items: { id: string; name: string; industry: string }[];
  }>;
};

const W = 92;   // 칸 너비
const H = 44;   // 칸 높이
const L = 78;   // 산업 이름 자리
const T = 46;   // 머리글 자리

export default function Matrix() {
  const [d, setD] = useState<Data | null>(null);
  const [sel, setSel] = useState<{ ind: string; need: string } | null>(null);

  useEffect(() => {
    fetch(`${API}/api/matrix`, { cache: "no-store" })
      .then((r) => r.json()).then(setD).catch(() => {});
  }, []);
  if (!d) return null;

  const width = L + d.needs.length * W;
  const height = T + d.industries.length * H;
  const cur = sel ? d.grid[sel.ind]?.[sel.need] : null;
  const sup = sel ? d.supply[sel.need] : null;
  const needPlain = (n: string) => d.needs.find((x) => x.need === n)?.plain ?? n;

  return (
    <section className="mt-8 rounded-lg border border-rule bg-paper p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[17px]">6대 산업 전체 — 빈칸이 어디에 몰려 있나</h2>
        <p className="text-[12px] text-muted">칸을 누르면 근거가 나옵니다</p>
      </div>

      <div className="mt-3 overflow-x-auto">
        <svg width={width} height={height} role="img"
             aria-label="산업별로 기업이 필요하다고 말한 것 중 몇 건이 채워졌는지 보여주는 격자">
          {d.needs.map((n, i) => (
            <text key={n.need} x={L + i * W + W / 2} y={T - 22} textAnchor="middle"
                  className="fill-ink text-[12px] font-semibold">{n.plain}</text>
          ))}
          {d.needs.map((n, i) => (
            <text key={`s${n.need}`} x={L + i * W + W / 2} y={T - 8} textAnchor="middle"
                  className="fill-faint text-[10px]">
              사업 {d.supply[n.need]?.total ?? 0}건
            </text>
          ))}

          {d.industries.map((ind, r) => {
            const y = T + r * H;
            const p = d.postures[ind];
            return (
              <g key={ind}>
                <text x={0} y={y + H / 2 + 4} className="fill-ink text-[12px] font-semibold">
                  {ind}
                </text>
                {p && (
                  <title>{ind} — {p.posture}. {p.why}</title>
                )}
                {d.needs.map((n, c) => {
                  const cell = d.grid[ind]?.[n.need];
                  const x = L + c * W;
                  const on = sel?.ind === ind && sel?.need === n.need;
                  if (!cell)
                    return (
                      <rect key={n.need} x={x + 3} y={y + 3} width={W - 6} height={H - 6}
                            rx={4} className="fill-shell" />
                    );
                  const gap = cell.covered === 0;
                  const part = cell.covered < cell.total;
                  return (
                    <g key={n.need} onClick={() => setSel(on ? null : { ind, need: n.need })}
                       style={{ cursor: "pointer" }}>
                      <rect
                        x={x + 3} y={y + 3} width={W - 6} height={H - 6} rx={4}
                        className={gap ? "fill-gap-soft stroke-gap"
                          : part ? "fill-hold-soft stroke-[#e3d5a8]" : "fill-pen-soft stroke-[#c4d4f2]"}
                        strokeWidth={on ? 2 : 1}
                        strokeDasharray={gap ? "4 3" : undefined}
                      />
                      <text x={x + W / 2} y={y + H / 2 + 5} textAnchor="middle"
                            className={`text-[13px] font-bold ${gap ? "fill-gap" : part ? "fill-hold" : "fill-pen"}`}>
                        {cell.covered}/{cell.total}
                      </text>
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>

      <p className="mt-2 text-[12px] text-muted">
        칸 안의 숫자는 <b>「기업이 말한 것 몇 건 중 몇 건이 채워졌나」</b>입니다.
        점선 붉은 칸이 하나도 안 채워진 곳, 회색 칸은 그 산업에서 그 이야기가 나온 적이 없는 곳입니다.
      </p>

      {sel && cur && (
        <div className="mt-3 rounded-md border border-rule bg-shell p-4">
          <p className="flex flex-wrap items-center gap-2 text-[14px]">
            <b>{sel.ind}</b>
            <span className="text-muted">·</span>
            <b>{needPlain(sel.need)}</b>
            <Tag tone={cur.covered === 0 ? "gap" : "pen"}>
              {cur.covered}÷{cur.total} 채워짐
            </Tag>
          </p>

          <ul className="mt-2 space-y-1 text-[13px]">
            {cur.signals.map((s) => (
              <li key={s.id} className="flex flex-wrap items-baseline gap-1.5">
                <Tag tone={s.covered ? "flat" : "gap"}>{s.covered ? "채워짐" : "없음"}</Tag>
                <span>{s.type}</span>
                <span className="text-[12px] text-muted">{s.id} {s.grade}등급</span>
                <Src url={s.url} label="자료" />
              </li>
            ))}
          </ul>

          {cur.covered === 0 && sup && sup.total > 0 && (
            <p className="mt-3 border-t border-rule pt-2 text-[13px]">
              <b className="text-gap">여기서만 비어 있습니다.</b>{" "}
              「{needPlain(sel.need)}」을 해주는 사업은 다른 산업에 <b>{sup.total}건</b> 있습니다 —{" "}
              {sup.byIndustry.filter((x) => x !== sel.ind).join(", ")}.
              <span className="mt-1 block text-[12px] text-muted">
                {sup.items.filter((x) => x.industry !== sel.ind).slice(0, 3)
                  .map((x) => `${x.name}(${x.industry})`).join(" · ")}
              </span>
            </p>
          )}
          {cur.covered === 0 && (!sup || sup.total === 0) && (
            <p className="mt-3 border-t border-rule pt-2 text-[13px] text-gap">
              「{needPlain(sel.need)}」을 해주는 사업이 6대 산업 어디에도 없습니다.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
