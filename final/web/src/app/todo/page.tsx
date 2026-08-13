"use client";

/* 지금 할 일 — 여기서 시작한다.
 *
 * 항목마다 「지금 이렇다 → 하고 나면 이렇게 된다」를 적고, 근거는 해당 페이지로 넘긴다.
 * 기대효과는 직접효과만 쓴다 (D-002 — 사업성과·지역성과는 이 도구에 귀속하지 않는다).
 */
import Link from "next/link";
import { useMemo } from "react";
import { Loading, PageHead, useReview } from "@/components/Shell";
import { Slots, Src, Tag } from "@/components/bits";
import { buildChecklist } from "@/lib/checklist";
import type { Review } from "@/lib/api";

/* 어디로 가는지는 다르지만 하는 일은 같다 — 그 항목의 근거를 보러 간다.
   단추 말이 넷이면 무엇이 다른지 읽느라 걸린다. */
const GO = {
  budget: "/budget",
  overlap: "/links",
  gap: "/needs",
  draft: "/action",
} as const;
const GO_LABEL = "관련 정보 보기";

export default function Home() {
  const { pid, r, err } = useReview();
  const items = useMemo(() => (r ? buildChecklist(r) : []), [r]);
  const todo = items.filter((i) => i.action);

  if (!r) return <Loading err={err} />;

  return (
    <>
      <PageHead
        r={r} title="지금 할 일"
        lead={`손볼 것 ${todo.length}건 · 확인만 하면 되는 것 ${items.length - todo.length}건`}
      />

      <div className="stagger">
        <section className="mb-6 grid gap-4 md:grid-cols-[1.05fr_1fr]">
          <Summary r={r} />
          <GapBars r={r} />
        </section>
  
        <p className="mb-2.5 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-[12px] text-muted">
          <span className="flex items-center gap-1.5">
            <span className="grid h-5 w-5 place-items-center rounded-[3px] border border-gap text-[11px] font-bold text-gap">1</span>
            붉은 번호는 손보셔야 할 것
          </span>
          <span className="flex items-center gap-1.5">
            <span className="grid h-5 w-5 place-items-center rounded-[3px] border border-pen bg-pen-soft text-[11px] font-bold text-pen">✓</span>
            파란 표는 확인만 하면 되는 것
          </span>
          <span className="text-faint">
            옆의 「사업 N건 · 자료 N건」은 그 항목에 걸린 개수입니다
          </span>
        </p>
  
        <ol className="space-y-2">
          {items.map((it) => {
            const n = it.action ? todo.indexOf(it) + 1 : 0;
            const go = GO[it.section];
            return (
              <li key={it.key}
                  className={`rounded-lg border bg-paper p-4 ${
                    it.action ? "border-rule" : "border-dashed border-rule"}`}>
                <div className="flex items-start gap-3">
                  <span className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-[3px] border text-[11px] font-bold ${
                    it.action ? "border-gap text-gap" : "border-pen bg-pen-soft text-pen"}`}>
                    {it.action ? n : "✓"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="flex flex-wrap items-center gap-2">
                      <b className="text-[15px]">{it.title}</b>
                      {it.count ? (
                        <Tag tone={it.action ? "gap" : "flat"}>
                          {it.unit} {it.count}건
                        </Tag>
                      ) : null}
                    </p>
                    <p className="mt-1 text-[13px] text-muted">{it.now}</p>
                    <p className="mt-1.5 text-[13px] text-pen">→ {it.then}</p>
                  </div>
                  <Link
                    href={{ pathname: go, query: { 사업: pid } }}
                    className="mt-0.5 shrink-0 rounded-md border border-rule px-2.5 py-1 text-[12px] text-muted hover:border-pen hover:text-pen"
                  >
                    {GO_LABEL}
                  </Link>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

    </>
  );
}

function Summary({ r }: { r: Review }) {
  return (
    <div className="rounded-lg border border-rule bg-paper p-5">
      <p className="text-[12px] text-muted">검토 대상</p>
      <h2 className="mt-1 text-[19px] leading-snug">
        {r.card.name}<Src url={r.card.url} />
      </h2>
      <dl className="mt-3 grid grid-cols-[5.5rem_1fr] gap-x-3 gap-y-1.5 text-[13px]">
        <dt className="text-muted">산업</dt><dd>{r.card.industry}</dd>
        <dt className="text-muted">해주는 것</dt>
        <dd>{r.card.means ?? <span className="text-hold">원문에 안 적혀 있음</span>}</dd>
        <dt className="text-muted">예산</dt>
        <dd>{r.budget.won
          ? `${r.budget.won.toLocaleString()}원 (장부 확인)`
          : <span className="text-hold">장부에서 못 찾음</span>}</dd>
        <dt className="text-muted">협의처</dt>
        <dd>{r.consult.length
          ? r.consult.map((c) => (
              <span key={c.team}>{c.team}<Src url={c.source_url} label="부서 근거" /></span>))
          : <span className="text-hold">산업이 확인되지 않아 안내 못 함</span>}</dd>
      </dl>
      <p className="mt-3 border-t border-rule pt-2 text-[12px] text-muted">
        판정은 모두 <b>후보</b>입니다. 확정은 부서 협의로 합니다.
      </p>
    </div>
  );
}

function GapBars({ r }: { r: Review }) {
  const by = new Map<string, { covered: number; total: number }>();
  for (const n of r.needs) {
    const d = by.get(n.plain) ?? { covered: 0, total: 0 };
    d.total += 1; d.covered += n.verdict === "covered" ? 1 : 0;
    by.set(n.plain, d);
  }
  const gaps = r.needs.filter((n) => n.verdict === "uncovered").length;
  return (
    <div className="rounded-lg border border-rule bg-paper p-5">
      <p className="text-[12px] text-muted">이 산업 기업이 말한 것</p>
      <p className="mt-1 text-[15px]">
        <b>{r.needs.length}건</b> 중 해주는 사업이 없는 것{" "}
        <b className={gaps ? "text-gap" : ""}>{gaps}건</b>
      </p>
      <ul className="mt-3 space-y-2">
        {[...by].map(([plain, d]) => (
          <li key={plain} className="grid grid-cols-[4.5rem_1fr_3rem] items-center gap-2">
            <span className={`text-[13px] font-semibold ${d.covered === 0 ? "text-gap" : ""}`}>
              {plain}
            </span>
            <Slots filled={d.covered} empty={d.covered === 0} />
            <span className="text-right text-[12px] text-muted">{d.covered}÷{d.total}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 border-t border-rule pt-2 text-[12px] text-muted">
        점선이 비어 있는 곳입니다.
      </p>
    </div>
  );
}
