"use client";

/* 랜딩 오른쪽에 얹는 살아 있는 요약.
 *
 * 여기 나오는 숫자는 전부 방금 계산한 것이다. 사업을 고르기 전에 **왜 이 도구가
 * 필요한지**를 알게 하려는 것이다 — 사업이 몰려 있는 곳과 현장이 아쉬워하는 곳이
 * 서로 다르다.
 */
import { useEffect, useRef, useState } from "react";
import { getOverview, type Overview } from "@/lib/api";

/** 0에서 값까지 숫자가 올라간다. 값은 실제 판정 결과다. */
function useCountUp(to: number, ms = 900) {
  const [n, setN] = useState(0);
  const raf = useRef(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setN(to); return; }
    const t0 = performance.now();
    const step = (t: number) => {
      const p = Math.min((t - t0) / ms, 1);
      setN(Math.round(to * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf.current);
  }, [to, ms]);
  return n;
}

function Stat({ label, v, unit, hint }: {
  label: string; v: number; unit: string; hint: string;
}) {
  const n = useCountUp(v);
  return (
    <div className="min-w-0">
      <p className="text-[12px] text-muted">{label}</p>
      <p className="mt-0.5 text-[24px] font-bold leading-none tabular-nums">
        {n.toLocaleString()}
        <span className="ml-0.5 text-[13px] font-normal text-muted">{unit}</span>
      </p>
      <p className="mt-1 text-[11px] leading-snug text-faint">{hint}</p>
    </div>
  );
}

export default function Live() {
  const [d, setD] = useState<Overview | null>(null);
  useEffect(() => { getOverview().then(setD).catch(() => {}); }, []);
  if (!d) return <div className="h-[300px] rounded-xl border border-rule bg-paper" />;

  const top = [...d.needs].sort((a, b) => (b.total - b.covered) - (a.total - a.covered));
  const gapKinds = top.filter((n) => n.covered < n.total).map((n) => n.plain);

  return (
    <section className="rounded-xl border border-rule bg-paper p-5">
      <h2 className="text-[15px]">지금 원장에 있는 것</h2>
      <div className="mt-3 grid grid-cols-3 gap-3 border-b border-rule pb-4">
        <Stat label="사업" v={d.ledger.works} unit="건" hint="조사자가 모은 원장" />
        <Stat label="필요하다는 자료" v={d.ledger.signals} unit="건"
              hint="실태조사·보고서·보도" />
        <Stat label="방금 이은 관계" v={d.computed.edges} unit="개"
              hint="열 때마다 다시 계산" />
      </div>

      <p className="mt-4 text-[14px] leading-relaxed">
        필요하다고 말한 것 <b>{d.computed.needs}건</b> 중{" "}
        <b className="text-gap">{d.computed.gaps}건</b>은 해주는 사업이 없습니다
      </p>
      {gapKinds.length > 0 && (
        <p className="mt-0.5 text-[13px] text-gap">비어 있는 것 — {gapKinds.join(" · ")}</p>
      )}

      <ul className="mt-3 space-y-2">
        {top.map((n, i) => {
          const pct = n.total ? (n.covered / n.total) * 100 : 0;
          const empty = n.covered === 0;
          return (
            <li key={n.need} className="grid grid-cols-[6.5rem_1fr_3.2rem] items-center gap-2.5">
              <span className={`text-[13px] font-semibold ${empty ? "text-gap" : ""}`}>
                {n.plain}
              </span>
              <span className="h-3 overflow-hidden rounded-sm border border-rule bg-shell">
                <span
                  className={`grow block h-full ${empty ? "bg-gap-soft" : "bg-pen"}`}
                  style={{ width: `${empty ? 100 : pct}%`,
                           animationDelay: `${0.3 + i * 0.08}s` }}
                />
              </span>
              <span className="text-right text-[12px] text-muted tabular-nums">
                {n.covered}÷{n.total}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 text-[11px] leading-snug text-faint">
        채워진 만큼 파랗게 찹니다. 하나도 못 채운 줄은 통째로 붉습니다.
        {" "}<b className="font-semibold">기업 자금</b>은 기업이 밖에서 구하는 돈이라,
        사업에 붙은 예산과 다릅니다.
      </p>
    </section>
  );
}
