"use client";

/* 랜딩에 얹는 살아 있는 요약.
 *
 * 여기 나오는 숫자는 전부 방금 계산한 것이다. 랜딩에서 이미 결론을 보여 주는 이유는
 * 사업을 고르기 전에 **왜 이 도구가 필요한지**를 알게 하려는 것이다 —
 * 사업이 몰려 있는 곳과 기업이 아쉬워하는 곳이 서로 다르다.
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

function Num({ v, unit }: { v: number; unit: string }) {
  const n = useCountUp(v);
  return (
    <span className="tabular-nums">
      {n.toLocaleString()}<span className="ml-0.5 text-[13px] font-normal text-muted">{unit}</span>
    </span>
  );
}

export default function Live() {
  const [d, setD] = useState<Overview | null>(null);
  useEffect(() => { getOverview().then(setD).catch(() => {}); }, []);
  if (!d) return <div className="h-[132px]" />;

  const top = [...d.needs].sort((a, b) => (b.total - b.covered) - (a.total - a.covered));
  const gapKinds = top.filter((n) => n.covered < n.total).map((n) => n.plain);

  return (
    <div className="rise grid gap-4 md:grid-cols-[auto_1fr]" style={{ animationDelay: ".25s" }}>
      <dl className="flex gap-6">
        {[
          { k: "사업", v: d.ledger.works, u: "건", hint: "조사자가 모은 원장" },
          { k: "기업이 말한 것", v: d.ledger.signals, u: "건", hint: "실태조사·보고서·보도" },
          { k: "방금 이은 관계", v: d.computed.edges, u: "개", hint: "열 때마다 다시 계산" },
        ].map((x) => (
          <div key={x.k}>
            <dt className="text-[12px] text-muted">{x.k}</dt>
            <dd className="text-[26px] font-bold leading-tight"><Num v={x.v} unit={x.u} /></dd>
            <p className="text-[11px] text-faint">{x.hint}</p>
          </div>
        ))}
      </dl>

      <div className="min-w-0 rounded-lg border border-rule bg-paper p-4">
        <p className="text-[13px]">
          기업이 필요하다고 말한 것 <b>{d.computed.needs}건</b> 중{" "}
          <b className="text-gap">{d.computed.gaps}건</b>은 해주는 사업이 없습니다
          {gapKinds.length > 0 && <> — {gapKinds.join("·")}</>}
        </p>
        <ul className="mt-2.5 space-y-1.5">
          {top.map((n, i) => {
            const pct = n.total ? (n.covered / n.total) * 100 : 0;
            return (
              <li key={n.need} className="grid grid-cols-[5rem_1fr_3rem] items-center gap-2">
                <span className={`text-[12px] font-semibold ${n.covered === 0 ? "text-gap" : ""}`}>
                  {n.plain}
                </span>
                <span className="h-2.5 overflow-hidden rounded-sm border border-rule bg-shell">
                  <span
                    className={`grow block h-full ${n.covered === 0 ? "bg-gap-soft" : "bg-pen"}`}
                    style={{ width: `${Math.max(pct, n.covered === 0 ? 100 : 0)}%`,
                             animationDelay: `${0.35 + i * 0.08}s` }}
                  />
                </span>
                <span className="text-right text-[11px] text-muted tabular-nums">
                  {n.covered}÷{n.total}
                </span>
              </li>
            );
          })}
        </ul>
        <p className="mt-2 text-[11px] text-faint">
          채워진 만큼 파랗게 찹니다. 하나도 못 채운 줄은 통째로 붉습니다.
        </p>
      </div>
    </div>
  );
}
