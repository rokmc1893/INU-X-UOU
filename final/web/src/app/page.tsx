"use client";

import { useEffect, useMemo, useState } from "react";
import {
  API, getBusinesses, getDraft, getReview, getSources,
  type Business, type Review, type SourceItem,
} from "@/lib/api";
import { buildChecklist, type Item } from "@/lib/checklist";
import { Slots, Src, Tag, Void } from "@/components/bits";

const DEMO = "IC-BIO-002";

export default function Page() {
  const [list, setList] = useState<Business[]>([]);
  const [pid, setPid] = useState(DEMO);
  const [r, setR] = useState<Review | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { getBusinesses().then((d) => setList(d.items)).catch(() => {}); }, []);
  useEffect(() => {
    setR(null);
    getReview(pid).then(setR).catch(() => {});
  }, [pid]);

  const items = useMemo(() => (r ? buildChecklist(r) : []), [r]);
  const todo = items.filter((i) => i.action).length;

  async function download() {
    if (!r) return;
    setBusy(true);
    try {
      const d = await getDraft(pid);
      const url = URL.createObjectURL(new Blob([d.markdown], { type: "text/markdown" }));
      const a = document.createElement("a");
      a.href = url; a.download = d.filename; a.click();
      URL.revokeObjectURL(url);
    } finally { setBusy(false); }
  }

  return (
    <main className="mx-auto max-w-[1180px] px-6 py-8">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-rule pb-4">
        <div>
          <h1 className="text-[26px] leading-tight">정책핏 인천</h1>
          <p className="mt-1 text-[13px] text-muted">
            맡은 사업이 산업이 필요로 하는 것과 맞는지, 근거와 함께 확인합니다
          </p>
        </div>
        <label className="flex items-center gap-2 text-[13px]">
          <span className="text-muted">맡은 사업</span>
          <select
            value={pid} onChange={(e) => setPid(e.target.value)}
            className="max-w-[420px] rounded-md border border-rule bg-paper px-3 py-2 text-[13px]"
          >
            {list.map((b) => (
              <option key={b.id} value={b.id}>
                [{b.industry}] {b.name}
              </option>
            ))}
          </select>
        </label>
      </header>

      {!r && <p className="text-[13px] text-muted">불러오는 중…</p>}

      {r && (
        <>
          <Summary r={r} todo={todo} />

          <section className="mt-8">
            <div className="mb-3 flex items-baseline gap-3">
              <h2 className="text-[19px]">지금 할 일</h2>
              <span className="text-[13px] text-muted">
                {todo}건 손볼 것 · {items.length - todo}건 확인만
              </span>
            </div>
            <ol className="space-y-2">
              {items.map((it) => (
                <Row
                  key={it.key}
                  n={it.action ? items.filter((x) => x.action).indexOf(it) + 1 : 0}
                  it={it} r={r}
                  open={open === it.key}
                  onToggle={() => setOpen(open === it.key ? null : it.key)}
                  onDownload={download} busy={busy}
                />
              ))}
            </ol>
          </section>

          <Windows r={r} />
        </>
      )}
    </main>
  );
}

/* ── 요약 — 이 사업이 무엇을 채우고 무엇이 비었나 ───────────── */
function Summary({ r, todo }: { r: Review; todo: number }) {
  const byNeed = new Map<string, { covered: number; total: number; label: string }>();
  for (const n of r.needs) {
    const d = byNeed.get(n.plain) ?? { covered: 0, total: 0, label: n.label };
    d.total += 1; d.covered += n.verdict === "covered" ? 1 : 0;
    byNeed.set(n.plain, d);
  }
  return (
    <section className="grid gap-4 md:grid-cols-[1.1fr_1fr]">
      <div className="rounded-lg border border-rule bg-paper p-5">
        <p className="text-[12px] text-muted">검토 대상</p>
        <h2 className="mt-1 text-[20px] leading-snug">
          {r.card.name}<Src url={r.card.url} />
        </h2>
        <dl className="mt-3 grid grid-cols-[5.5rem_1fr] gap-x-3 gap-y-1.5 text-[13px]">
          <dt className="text-muted">산업</dt><dd>{r.card.industry}</dd>
          <dt className="text-muted">해주는 것</dt>
          <dd>{r.card.means ?? <span className="text-hold">원문에 안 적혀 있음</span>}</dd>
          <dt className="text-muted">예산</dt>
          <dd>{r.budget.won ? `${r.budget.won.toLocaleString()}원 (장부 확인)` : "장부에서 못 찾음"}</dd>
          <dt className="text-muted">협의처</dt>
          <dd>
            {r.consult.map((c) => (
              <span key={c.team}>{c.team}<Src url={c.source_url} label="부서 근거" /></span>
            ))}
          </dd>
        </dl>
        <p className="mt-3 border-t border-rule pt-2 text-[12px] text-muted">
          행정 절차 {r.stage.no}단계 「{r.stage.name}」에서 쓰는 문서입니다.
          판정은 모두 후보이고 확정은 부서 협의로 합니다.
        </p>
      </div>

      <div className="rounded-lg border border-rule bg-paper p-5">
        <p className="text-[12px] text-muted">이 산업 기업이 말한 것</p>
        <p className="mt-1 text-[15px]">
          <b>{r.needs.length}건</b> 중 해주는 사업이 없는 것{" "}
          <b className="text-gap">{r.needs.filter((n) => n.verdict === "uncovered").length}건</b>
        </p>
        <ul className="mt-3 space-y-2">
          {[...byNeed].map(([plain, d]) => (
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
          점선이 비어 있는 곳입니다. 옆의 숫자는 「말한 것 몇 건 중 몇 건이 채워졌나」입니다.
        </p>
      </div>
    </section>
  );
}

/* ── 체크리스트 한 줄 ────────────────────────────────────── */
function Row({ n, it, r, open, onToggle, onDownload, busy }: {
  n: number; it: Item; r: Review; open: boolean;
  onToggle: () => void; onDownload: () => void; busy: boolean;
}) {
  return (
    <li className={`rounded-lg border bg-paper ${it.action ? "border-rule" : "border-dashed border-rule"}`}>
      <button
        onClick={onToggle}
        className="flex w-full items-start gap-3 p-4 text-left"
        aria-expanded={open}
      >
        <span className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-[3px] border text-[11px] font-bold
          ${it.action ? "border-gap text-gap" : "border-pen bg-pen-soft text-pen"}`}>
          {it.action ? n : "✓"}
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <b className="text-[15px]">{it.title}</b>
            {it.count ? <Tag tone={it.action ? "gap" : "flat"}>{it.count}건</Tag> : null}
          </span>
          <span className="mt-1 block text-[13px] text-muted">{it.now}</span>
          <span className="mt-1.5 block text-[13px] text-pen">→ {it.then}</span>
        </span>
        <span className="mt-1 shrink-0 text-[12px] text-faint">{open ? "닫기" : "근거"}</span>
      </button>
      {open && (
        <div className="border-t border-rule p-4">
          <Evidence it={it} r={r} onDownload={onDownload} busy={busy} />
        </div>
      )}
    </li>
  );
}

/* ── 항목별 근거 ─────────────────────────────────────────── */
function Evidence({ it, r, onDownload, busy }: {
  it: Item; r: Review; onDownload: () => void; busy: boolean;
}) {
  if (it.section === "budget")
    return (
      <div className="space-y-3 text-[13px]">
        {r.budget.mismatch && (
          <table className="w-full border-collapse">
            <tbody>
              <tr className="border-b border-rule">
                <td className="w-40 py-1.5 text-muted">사업 문서에 적힌 소관</td>
                <td className="py-1.5">{r.budget.mismatch.card}</td>
              </tr>
              <tr className="border-b border-rule">
                <td className="py-1.5 text-muted">공식 예산 장부의 소관</td>
                <td className="py-1.5 font-semibold">{r.budget.mismatch.official}</td>
              </tr>
              <tr>
                <td className="py-1.5 text-muted">예산서 항목</td>
                <td className="py-1.5">{r.budget.line ?? "미확인"}</td>
              </tr>
            </tbody>
          </table>
        )}
        <Void r={r.budget.empty} />
        <p className="text-[12px] text-muted">{r.caveat}</p>
      </div>
    );

  if (it.section === "overlap")
    return (
      <div className="space-y-4 text-[13px]">
        <Group title="받는 사람·주는 것·직무가 모두 같음" tone="gap" rows={r.overlaps.harmful} />
        <Group title="주는 것은 같지만 받는 사람·지역이 다름" tone="flat" rows={r.overlaps.intentional} />
        <Group title="수단이 달라 서로 채워 줌" tone="flat" rows={r.overlaps.complement} />
        <Group title="다음 사업으로 넘기는 절차가 없음" tone="flat" rows={r.handoffs.items} />
        <Void r={r.overlaps.empty} />
        <Void r={r.handoffs.empty} />
        <p className="rounded-md bg-shell p-2.5 text-[12px] text-muted">
          이 기준은 저희가 정한 것이 아닙니다. 협의 단계의 반려 사유가
          「{r.duplicateRule}」입니다.
        </p>
      </div>
    );

  if (it.section === "gap") return <Gaps r={r} />;

  return (
    <div className="space-y-3 text-[13px]">
      <p>초안에 들어가는 것 — 판정 결과와 근거, <b>못 본 것과 그 이유</b>, 협의 요청 부서,
        다음 창구와 마감. 수치마다 원문 링크가 붙습니다.</p>
      <button
        onClick={onDownload} disabled={busy}
        className="rounded-md border border-pen bg-pen-soft px-3 py-2 text-[13px] font-semibold text-pen disabled:opacity-50"
      >
        {busy ? "만드는 중…" : "검토서 초안 내려받기 (.md)"}
      </button>
      <ul className="list-disc space-y-1 pl-5 text-[12px] text-muted">
        {r.reviewers.map((x) => <li key={x.who}>{x.who} — {x.why}</li>)}
      </ul>
    </div>
  );
}

function Group({ title, tone, rows }: {
  title: string; tone: "gap" | "flat"; rows: { id: string; name: string; url: string | null; reason: string }[];
}) {
  if (!rows.length) return null;
  return (
    <div>
      <p className="mb-1.5 flex items-center gap-2">
        <Tag tone={tone}>{rows.length}건</Tag>
        <b className="text-[13px]">{title}</b>
      </p>
      <ul className="space-y-1.5">
        {rows.slice(0, 6).map((p) => (
          <li key={p.id} className="border-l-2 border-rule pl-3">
            <span className="font-medium">{p.name}</span><Src url={p.url} />
            <span className="block text-[12px] text-muted">{p.reason}</span>
          </li>
        ))}
        {rows.length > 6 && (
          <li className="pl-3 text-[12px] text-faint">…외 {rows.length - 6}건</li>
        )}
      </ul>
    </div>
  );
}

/* ── 빈칸과 그 자료를 어디서 찾나 ────────────────────────── */
function Gaps({ r }: { r: Review }) {
  const gaps = r.needs.filter((n) => n.verdict === "uncovered");
  const kinds = [...new Set(gaps.map((g) => g.plain))];
  const [need, setNeed] = useState(kinds[0] ?? "");
  const [src, setSrc] = useState<{ items: SourceItem[]; claim: string | null; checkedOn: string } | null>(null);
  const ind = (r.card.industry ?? "").split("+")[0];

  useEffect(() => {
    if (!need) return;
    getSources(ind, need).then(setSrc).catch(() => {});
  }, [need, ind]);

  return (
    <div className="space-y-4 text-[13px]">
      <ul className="space-y-2">
        {r.needs.map((n) => (
          <li key={n.signal_id} className="flex flex-wrap items-start gap-2 border-b border-rule pb-2">
            <Tag tone={n.verdict === "uncovered" ? "gap" : n.mine ? "pen" : "flat"}>
              {n.verdict === "uncovered" ? "없음" : n.mine ? "내 사업" : `${n.covers.length}건`}
            </Tag>
            <span className="min-w-0 flex-1">
              <b>{n.plain}</b> · {n.problem_type}
              <span className="block text-[12px] text-muted">
                {n.value.slice(0, 60)} · {n.signal_id} {n.grade}등급
                <Src url={n.source_url} label="자료" />
              </span>
              {n.coverNames.length > 0 && (
                <span className="block text-[12px] text-muted">
                  → {n.coverNames.filter(Boolean).slice(0, 2).join(", ")}
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>

      {kinds.length > 0 && (
        <div className="rounded-md border border-rule bg-shell p-3">
          <p className="mb-2">
            <b>「{kinds.join("·")}」</b> 자료는 어디서 찾나
            {kinds.length > 1 && (
              <select
                value={need} onChange={(e) => setNeed(e.target.value)}
                className="ml-2 rounded border border-rule bg-paper px-2 py-1 text-[12px]"
              >
                {kinds.map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
            )}
          </p>
          <ul className="space-y-1.5">
            {src?.items.map((s) => (
              <li key={s.key} className="flex flex-wrap items-baseline gap-2">
                <Tag tone={s.status === "ok" ? "pen" : s.status === "blocked" ? "gap" : "hold"}>
                  {s.status_label}
                </Tag>
                <a href={s.link} target="_blank" rel="noopener noreferrer"
                   className="font-semibold underline decoration-rule underline-offset-2">
                  {s.name}
                </a>
                {!s.direct && s.terms[0] && (
                  <span className="text-[12px] text-faint">검색어 {s.terms[0]}</span>
                )}
                <span className="w-full text-[12px] text-muted">{s.what} — {s.note}</span>
              </li>
            ))}
          </ul>
          {src?.claim && (
            <p className="mt-2 border-t border-rule pt-2 text-[12px] text-muted">
              정보공개청구 문안 — <code className="bg-paper px-1">{src.claim}</code>
            </p>
          )}
          {src && <p className="mt-1 text-[11px] text-faint">접속 여부는 {src.checkedOn} 기준입니다.</p>}
        </div>
      )}
    </div>
  );
}

/* ── 창구와 마감 ─────────────────────────────────────────── */
function Windows({ r }: { r: Review }) {
  return (
    <section className="mt-8 rounded-lg border border-rule bg-paper p-5">
      <h2 className="text-[17px]">언제까지 내야 하나</h2>
      <div className="mt-3 grid gap-4 md:grid-cols-2">
        <div>
          <p className="mb-1.5 text-[12px] text-muted">지금 열려 있는 창구</p>
          <ul className="space-y-1 text-[13px]">
            {r.windows.open.map((o) => (
              <li key={o.track.decision_type}>
                <b>{o.track.decision_type}</b>{o.always && " (수시)"}
                <span className="block text-[12px] text-muted">
                  마감 {o.track.formal_deadline}
                </span>
              </li>
            ))}
            {!r.windows.open.length && <li className="text-muted">오늘 기준 열린 창구가 없습니다</li>}
          </ul>
        </div>
        <div>
          <p className="mb-1.5 text-[12px] text-muted">곧 열리는 창구</p>
          <ul className="space-y-1 text-[13px]">
            {r.windows.soon.map((u) => (
              <li key={u.track.decision_type}>
                <b>{u.track.decision_type}</b>
                <span className="block text-[12px] text-muted">
                  {u.opens} 착수 · 마감 {u.track.formal_deadline}
                </span>
              </li>
            ))}
            {!r.windows.soon.length && <li className="text-muted">3개월 안에 열리는 창구가 없습니다</li>}
          </ul>
        </div>
      </div>
    </section>
  );
}
