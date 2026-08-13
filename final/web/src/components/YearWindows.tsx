"use client";

/* 한 해 창구 띠 — 지금 어디쯤인지, 무엇이 열려 있고 무엇이 지났는지.
 *
 * A2 결정 달력 6트랙을 12개월 위에 올린다. 오늘 선을 그어 두면
 * 「본예산은 이미 지났고 지금 열린 건 공모뿐」이 문장이 아니라 그림으로 보인다.
 */
import { useEffect, useState } from "react";
import { API } from "@/lib/api";
import { Tag } from "./bits";

type Track = {
  name: string; always: boolean;
  startMonth: number | null; endMonth: number | null; deadlineMonth: number | null;
  window: string; deadline: string; docs: string; next: string; ours: string | null;
};
type Data = { today: { month: number; day: number }; tracks: Track[] };

const L = 128;          // 트랙 이름 자리
const MW = 62;          // 한 달 너비
const RH = 34;          // 한 줄 높이
const T = 26;           // 머리글

export default function YearWindows() {
  const [d, setD] = useState<Data | null>(null);
  const [sel, setSel] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/api/calendar`, { cache: "no-store" })
      .then((r) => r.json()).then(setD).catch(() => {});
  }, []);
  if (!d) return null;

  const width = L + 12 * MW;
  const height = T + d.tracks.length * RH + 8;
  const nowX = L + (d.today.month - 1 + d.today.day / 31) * MW;
  const cur = d.tracks.find((t) => t.name === sel);

  return (
    <section className="mt-8 rounded-lg border border-rule bg-paper p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[17px]">언제까지 내야 하나</h2>
        <p className="text-[12px] text-muted">
          오늘 {d.today.month}월 {d.today.day}일 · 띠를 누르면 필요한 문서가 나옵니다
        </p>
      </div>

      <div className="mt-3 overflow-x-auto">
        <svg width={width} height={height} role="img"
             aria-label="한 해 열두 달 위에 예산 창구 여섯 갈래가 언제 열리는지 표시한 띠">
          {Array.from({ length: 12 }).map((_, m) => (
            <text key={m} x={L + m * MW + MW / 2} y={16} textAnchor="middle"
                  className={`text-[11px] ${m + 1 === d.today.month ? "fill-ink font-bold" : "fill-faint"}`}>
              {m + 1}월
            </text>
          ))}
          {Array.from({ length: 13 }).map((_, m) => (
            <line key={m} x1={L + m * MW} y1={T - 6} x2={L + m * MW} y2={height - 6}
                  className="stroke-rule" strokeWidth={1} />
          ))}

          {d.tracks.map((t, i) => {
            const y = T + i * RH;
            const on = sel === t.name;
            const passed = t.endMonth !== null && t.endMonth < d.today.month;
            return (
              <g key={t.name} onClick={() => setSel(on ? null : t.name)}
                 style={{ cursor: "pointer" }}>
                <text x={0} y={y + 20} className="fill-ink text-[11px]">
                  {t.name.length > 13 ? `${t.name.slice(0, 12)}…` : t.name}
                  <title>{t.name}</title>
                </text>
                {t.always ? (
                  <rect x={L + 2} y={y + 8} width={12 * MW - 4} height={16} rx={3}
                        className="fill-pen-soft stroke-[#c4d4f2]" strokeWidth={on ? 2 : 1}
                        strokeDasharray="5 4" />
                ) : t.startMonth ? (
                  <rect
                    x={L + (t.startMonth - 1) * MW + 2} y={y + 8}
                    width={((t.endMonth ?? t.startMonth) - t.startMonth + 1) * MW - 4}
                    height={16} rx={3} strokeWidth={on ? 2 : 1}
                    className={passed ? "fill-shell stroke-rule" : "fill-pen-soft stroke-[#c4d4f2]"}
                  />
                ) : null}
                {t.deadlineMonth && (
                  <g>
                    <line x1={L + (t.deadlineMonth - 1) * MW + MW * 0.9}
                          y1={y + 4} x2={L + (t.deadlineMonth - 1) * MW + MW * 0.9} y2={y + 28}
                          className="stroke-gap" strokeWidth={2} />
                    <title>마감 {t.deadline}</title>
                  </g>
                )}
              </g>
            );
          })}

          <line x1={nowX} y1={T - 10} x2={nowX} y2={height - 4}
                className="stroke-ink" strokeWidth={2} />
          <text x={nowX} y={T - 14} textAnchor="middle" className="fill-ink text-[10px] font-bold">
            오늘
          </text>
        </svg>
      </div>

      <p className="mt-2 flex flex-wrap items-center gap-3 text-[12px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-6 rounded-sm border border-[#c4d4f2] bg-pen-soft" /> 착수 기간
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-6 rounded-sm border border-rule bg-shell" /> 이미 지남
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3.5 w-0.5 bg-gap" /> 마감
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-6 rounded-sm border border-dashed border-[#c4d4f2] bg-pen-soft" /> 수시
        </span>
      </p>

      {cur && (
        <div className="mt-3 rounded-md border border-rule bg-shell p-4 text-[13px]">
          <p className="flex flex-wrap items-center gap-2">
            <b>{cur.name}</b>
            <Tag tone={cur.always ? "pen" : cur.endMonth && cur.endMonth < d.today.month ? "flat" : "pen"}>
              {cur.always ? "수시" : cur.endMonth && cur.endMonth < d.today.month ? "올해는 지남" : "열려 있음"}
            </Tag>
          </p>
          <dl className="mt-2 grid grid-cols-[4.5rem_1fr] gap-x-3 gap-y-1">
            <dt className="text-muted">착수</dt><dd>{cur.window}</dd>
            <dt className="text-muted">마감</dt><dd>{cur.deadline}</dd>
            <dt className="text-muted">낼 문서</dt>
            <dd>
              {cur.docs.split(/[·,]/).map((x) => x.trim()).filter(Boolean).map((x) => (
                <span key={x} className="mr-2 inline-block">
                  {x}
                  {cur.ours && x.replace(/\s/g, "").includes(cur.ours.replace(/\s/g, "")) && (
                    <Tag tone="pen"> 이 도구가 만들어 줍니다</Tag>
                  )}
                </span>
              ))}
            </dd>
            <dt className="text-muted">놓치면</dt><dd>{cur.next}</dd>
          </dl>
        </div>
      )}
    </section>
  );
}
