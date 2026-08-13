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

const L = 118;   // 트랙 이름 자리 — 짧은 이름을 쓰니 이만큼이면 넉넉하다
const MW = 62;   // 한 달 너비
const RH = 38;   // 한 줄 높이
const T = 52;    // 머리글 + 오늘 표

export default function YearWindows() {
  const [d, setD] = useState<Data | null>(null);
  const [sel, setSel] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/api/calendar`, { cache: "no-store" })
      .then((r) => r.json()).then(setD).catch(() => {});
  }, []);
  if (!d) return null;

  const width = L + 12 * MW;
  const height = T + d.tracks.length * RH + 10;
  const nowX = L + (d.today.month - 1 + d.today.day / 31) * MW;
  const cur = d.tracks.find((t) => t.name === sel);
  /* 띠 옆에는 짧은 이름을 쓴다. 잘라 붙이면 「…추」처럼 뜻이 사라진다.
     전체 이름은 마우스를 올리거나 아래 상자에서 본다. */
  const SHORT: Record<string, string> = {
    "다음 연도 본예산 신규사업": "본예산 신규",
    "기존사업 개편/확대": "기존사업 개편",
    "상반기 추가경정예산(1차 추경)": "1차 추경 (상반기)",
    "하반기 추가경정예산(2차 추경)": "2차 추경 (하반기)",
    "중앙정부/지자체 공모 대응": "공모 대응",
    "RISE 사업계획 수정/연계": "RISE 연계",
  };
  const short = (s: string) => SHORT[s] ?? (s.length > 16 ? `${s.slice(0, 15)}…` : s);

  return (
    <section className="mb-5 rounded-lg border border-rule bg-paper p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[16px]">언제까지 내야 하나</h2>
        <p className="text-[12px] text-muted">
          오늘 {d.today.month}월 {d.today.day}일 · 띠를 누르면 필요한 문서가 나옵니다
        </p>
      </div>

      <div className="mt-3 overflow-x-auto">
        <svg width={width} height={height} role="img"
             aria-label="한 해 열두 달 위에 예산 창구 여섯 갈래가 언제 열리는지 표시한 띠">
          {/* 오늘 이후는 옅게 깔아 「지난 쪽 / 남은 쪽」을 먼저 가른다 */}
          <rect x={L} y={T - 12} width={nowX - L} height={height - T + 4}
                className="fill-shell" opacity={0.6} />

          {Array.from({ length: 12 }).map((_, m) => (
            <text key={m} x={L + m * MW + MW / 2} y={T - 22} textAnchor="middle"
                  className={`text-[11px] ${m + 1 === d.today.month ? "fill-ink font-bold" : "fill-faint"}`}>
              {m + 1}월
            </text>
          ))}
          {Array.from({ length: 13 }).map((_, m) => (
            <line key={m} x1={L + m * MW} y1={T - 12} x2={L + m * MW} y2={height - 8}
                  className="stroke-rule" strokeWidth={1} />
          ))}

          {d.tracks.map((t, i) => {
            const y = T + i * RH;
            const on = sel === t.name;
            const passed = t.endMonth !== null && t.endMonth < d.today.month;
            const x0 = t.startMonth ? L + (t.startMonth - 1) * MW + 2 : 0;
            const w = t.startMonth
              ? ((t.endMonth ?? t.startMonth) - t.startMonth + 1) * MW - 4 : 0;
            const dx = t.deadlineMonth ? L + (t.deadlineMonth - 1) * MW + MW * 0.55 : null;
            return (
              <g key={t.name} onClick={() => setSel(on ? null : t.name)}
                 style={{ cursor: "pointer" }}>
                <text x={0} y={y + 21} className="fill-ink text-[12px]">
                  {short(t.name)}<title>{t.name}</title>
                </text>

                {/* 착수 끝 → 마감까지 이어지는 실 — 둘이 떨어져 있어도 관계가 보이게 */}
                {dx && t.startMonth && dx > x0 + w && (
                  <line x1={x0 + w} y1={y + 16} x2={dx} y2={y + 16}
                        className="stroke-rule" strokeWidth={1} strokeDasharray="2 3" />
                )}

                {t.always ? (
                  <rect x={L + 2} y={y + 8} width={12 * MW - 4} height={17} rx={3}
                        className="fill-pen-soft stroke-pen" strokeWidth={on ? 2 : 1.2}
                        strokeDasharray="6 4" />
                ) : t.startMonth ? (
                  <rect x={x0} y={y + 8} width={w} height={17} rx={3}
                        strokeWidth={on ? 2 : 1.2}
                        className={passed
                          ? "fill-transparent stroke-faint"
                          : "fill-pen-soft stroke-pen"}
                        strokeDasharray={passed ? "3 3" : undefined} />
                ) : null}

                {dx && (
                  <g>
                    <line x1={dx} y1={y + 4} x2={dx} y2={y + 29}
                          className="stroke-gap" strokeWidth={2.5} />
                    <title>마감 {t.deadline}</title>
                  </g>
                )}
              </g>
            );
          })}

          {/* 오늘 — 월 이름과 겹치지 않게 위쪽에 깃발로 */}
          <line x1={nowX} y1={T - 12} x2={nowX} y2={height - 8}
                className="stroke-ink" strokeWidth={2} />
          <rect x={nowX - 17} y={4} width={34} height={16} rx={3} className="fill-ink" />
          <text x={nowX} y={16} textAnchor="middle" className="fill-white text-[10px] font-bold">
            오늘
          </text>
        </svg>
      </div>

      <p className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-[12px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3.5 w-7 rounded-sm border border-pen bg-pen-soft" />
          아직 열려 있음
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3.5 w-7 rounded-sm border border-dashed border-faint" />
          올해는 지남
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3.5 w-7 rounded-sm border border-dashed border-pen bg-pen-soft" />
          수시로 열림
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3.5 w-[3px] bg-gap" /> 마감
        </span>
      </p>

      {cur && (
        <div className="mt-3 rounded-md border border-rule bg-shell p-4 text-[13px]">
          <p className="flex flex-wrap items-center gap-2">
            <b>{cur.name}</b>
            <Tag tone={cur.always ? "pen"
              : cur.endMonth && cur.endMonth < d.today.month ? "flat" : "pen"}>
              {cur.always ? "수시로 열림"
                : cur.endMonth && cur.endMonth < d.today.month ? "올해는 지남" : "아직 열려 있음"}
            </Tag>
          </p>
          <dl className="mt-2 grid grid-cols-[4.5rem_1fr] gap-x-3 gap-y-1">
            <dt className="text-muted">착수</dt><dd>{cur.window}</dd>
            <dt className="text-muted">마감</dt><dd>{cur.deadline}</dd>
            <dt className="text-muted">낼 문서</dt>
            <dd className="flex flex-wrap gap-x-3 gap-y-1">
              {cur.docs.split(/[·,]/).map((x) => x.trim()).filter(Boolean).map((x) => (
                <span key={x}>
                  {x}
                  {cur.ours && x.replace(/\s/g, "").includes(cur.ours.replace(/\s/g, "")) && (
                    <Tag tone="pen"> 여기서 만들어 드립니다</Tag>
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
