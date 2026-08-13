"use client";

/* ③ 필요한 걸 해주고 있나.
 *
 * 빈칸을 보고 → 어디서 찾는지 알고 → 찾아서 넣으면 → 숫자가 바뀐다.
 * 한 페이지 안에서 한 바퀴가 돌아야 "미리 짜놓은 답"으로 보이지 않는다.
 */
import { useEffect, useState } from "react";
import { Loading, PageHead, useReview } from "@/components/Shell";
import { Slots, Src, Tag } from "@/components/bits";
import { Card, Counts } from "@/components/parts";
import { API, getSources, post, postFile, type Review, type SourceItem } from "@/lib/api";

/* 원장의 추세 표기. 영어를 그대로 내보내면 담당자가 읽을 수 없다. */
const TREND: Record<string, string> = {
  SUSTAINED: "계속 나오는 이야기",
  SPIKE: "최근 부쩍 늘어난 이야기",
};

export default function NeedsPage() {
  const { r, err } = useReview();
  if (!r) return <Loading err={err} />;

  const gaps = r.needs.filter((n) => n.verdict === "uncovered");
  const thin = r.needs.filter((n) => n.verdict === "covered" && n.covers.length === 1);
  const by = new Map<string, { covered: number; total: number; label: string; hint: string }>();
  for (const n of r.needs) {
    const d = by.get(n.plain) ?? { covered: 0, total: 0, label: n.label, hint: n.hint };
    d.total += 1; d.covered += n.verdict === "covered" ? 1 : 0;
    by.set(n.plain, d);
  }

  return (
    <>
      <PageHead
        r={r} title="필요한 걸 해주고 있나"
        lead="기업이 필요하다고 말한 것을 일곱 가지로 나눠, 그걸 해주는 사업이 있는지 하나씩 맞춰 봅니다."
      />

      <div className="stagger">
        <Counts items={[
          { label: "기업이 말한 것", n: r.needs.length },
          { label: "해주는 사업이 없음", n: gaps.length, tone: "gap" },
          { label: "사업 하나에만 걸림", n: thin.length },
          { label: "이 사업이 맡은 것", n: r.needs.filter((n) => n.mine).length, tone: "pen" },
        ]} />
  
        {r.posture && (
          <Card title="이 산업에는 무엇부터 물어야 합니까">
            <p className="flex flex-wrap items-center gap-2 text-[15px]">
              <Tag tone={r.posture.posture === "대응형" ? "pen" : "hold"}>
                {r.posture.posture === "대응형" ? "이미 필요하다고 나옴" : "아직 자료 없음"}
              </Tag>
              <b>{r.posture.question}</b>
            </p>
            <p className="mt-2 text-[13px] text-muted">{r.posture.why}</p>
            <p className="mt-2 border-t border-rule pt-2 text-[12px] text-muted">
              이 구분은 저희가 정한 것이 아니라 조사 자료가 정한 것입니다.
              새 자료가 들어오면 구분도 질문도 저절로 바뀝니다.
            </p>
          </Card>
        )}
  
        <Card title="무엇이 채워졌고 무엇이 비었나"
              sub="칸 이름 밑에 그 칸이 무엇을 세는지 적어 뒀습니다.">
          <ul className="space-y-2.5">
            {[...by].map(([plain, d]) => (
              <li key={plain} className="border-b border-rule pb-2.5 last:border-0 last:pb-0">
                <div className="grid grid-cols-[7rem_1fr_3.5rem] items-center gap-3">
                  <span className={`text-[13px] font-semibold ${d.covered === 0 ? "text-gap" : ""}`}>
                    {plain}
                  </span>
                  <Slots filled={d.covered} empty={d.covered === 0} />
                  <span className="text-right text-[12px] text-muted">{d.covered}÷{d.total}</span>
                </div>
                {/* 문제 표현(label)은 칸 이름과 같은 말이 겹친다 —
                    「일할 사람 / 사람이 없다」. 무엇을 세는지만 남긴다. */}
                <p className="mt-1 text-[11px] leading-snug text-faint">{d.hint}</p>
              </li>
            ))}
          </ul>
        </Card>
  
        {/* 배지를 글자 흐름에 두면 폭이 달라 제목이 배지마다 다른 자리에서 시작한다
            — 「없음」과 「이 사업」의 폭 차이만큼 밀린다. 고정 칸으로 세운다. */}
        <Card title="하나씩 보기"
              sub="왼쪽 표는 그 필요를 해주는 사업이 몇 건인가입니다. 자료마다 근거 등급과 원문이 붙어 있습니다.">
          <ul className="space-y-2.5">
            {[...r.needs].sort((a, b) =>
              (a.verdict === "uncovered" ? 0 : 1) - (b.verdict === "uncovered" ? 0 : 1)
            ).map((n) => (
              <li key={n.signal_id}
                  className="grid grid-cols-[4.5rem_1fr] items-start gap-x-3 border-b border-rule pb-2.5">
                <Tag tone={n.verdict === "uncovered" ? "gap" : n.mine ? "pen" : "flat"}>
                  {n.verdict === "uncovered" ? "없음" : n.mine ? "이 사업" : `${n.covers.length}건`}
                </Tag>
                <span className="min-w-0">
                  <b className="text-[14px]">{n.plain}</b>
                  {/* 원장의 problem_type 이 지원 유형과 같은 말일 때가 있다 —
                      「기업 자금 · 금융」처럼 같은 것을 두 번 읽게 된다. */}
                  {n.problem_type !== n.need && (
                    <span className="text-[14px]"> · {n.problem_type}</span>
                  )}
                  <span className="mt-0.5 block text-[12px] text-muted">
                    {n.value.slice(0, 70)} · {n.signal_id} {n.grade}등급 · {TREND[n.trend] ?? n.trend}{" "}
                    <Src url={n.source_url} label="자료" />
                  </span>
                  {n.limit && (
                    <span className="mt-0.5 block text-[12px] text-faint">
                      이 자료의 한계 — {n.limit.slice(0, 90)}
                    </span>
                  )}
                  {n.verdict === "uncovered" ? (
                    <span className="mt-0.5 block text-[12px] text-gap">
                      이 필요를 해주는 사업이 하나도 없습니다.
                    </span>
                  ) : n.coverNames.filter(Boolean).length > 0 && (
                    <span className="mt-0.5 block text-[12px] text-pen">
                      {n.mine ? "이 사업이 맡고 있습니다 → " : "→ "}
                      {n.coverNames.filter(Boolean).slice(0, 3).join(", ")}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </Card>
  
        {gaps.length > 0 && <FindSources r={r} kinds={[...new Set(gaps.map((g) => g.plain))]} />}
        <Intake industry={(r.card.industry ?? "").split("+")[0]} />
      </div>

    </>
  );
}

/* ── 빈칸 → 어디서 찾나 ─────────────────────────────────── */
function FindSources({ r, kinds }: { r: Review; kinds: string[] }) {
  const [need, setNeed] = useState(kinds[0]);
  const [d, setD] = useState<{ items: SourceItem[]; claim: string | null; checkedOn: string } | null>(null);
  const ind = (r.card.industry ?? "").split("+")[0];

  useEffect(() => { getSources(ind, need).then(setD).catch(() => {}); }, [ind, need]);

  return (
    <Card title={`비어 있는 「${kinds.join("·")}」 자료는 어디서 찾나`}
          sub="지금 열리는 곳과 막힌 곳을 함께 보입니다. 막힌 곳을 지우면 「여기만 보면 다 된다」로 읽힙니다.">
      {kinds.length > 1 && (
        <div className="mb-3 flex gap-1">
          {kinds.map((k) => (
            <button key={k} onClick={() => setNeed(k)}
                    className={`rounded-md border px-2.5 py-1 text-[12px] ${
                      k === need ? "border-pen bg-pen-soft font-semibold text-pen" : "border-rule text-muted"}`}>
              {k}
            </button>
          ))}
        </div>
      )}
      <ul className="space-y-2">
        {d?.items.map((s) => (
          <li key={s.key} className="flex flex-wrap items-baseline gap-2 border-b border-rule pb-2">
            <Tag tone={s.status === "ok" ? "pen" : s.status === "blocked" ? "gap" : "hold"}>
              {s.status_label}
            </Tag>
            <a href={s.link} target="_blank" rel="noopener noreferrer"
               className="text-[14px] font-semibold underline decoration-rule underline-offset-2">
              {s.name}
            </a>
            {!s.direct && s.terms[0] && (
              <span className="text-[12px] text-faint">검색어 {s.terms[0]}</span>
            )}
            <span className="w-full text-[12px] text-muted">{s.what} — {s.note}</span>
          </li>
        ))}
      </ul>
      {d?.claim && (
        <p className="mt-3 text-[12px] text-muted">
          정보공개청구에 쓸 문안 —{" "}
          <code className="rounded bg-shell px-1.5 py-0.5">{d.claim}</code>
        </p>
      )}
      {d && <p className="mt-1 text-[11px] text-faint">접속 여부는 {d.checkedOn} 기준입니다.</p>}
    </Card>
  );
}

/* ── 찾은 자료 넣기 ─────────────────────────────────────── */
function Intake({ industry }: { industry: string }) {
  const [tab, setTab] = useState<"url" | "text" | "pdf">("url");
  const [url, setUrl] = useState("");
  const [text, setText] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; s: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(fn: () => Promise<{ card: { name: string }; note: string }>) {
    setBusy(true); setMsg(null);
    try {
      const d = await fn();
      setMsg({ ok: true, s: `「${d.card.name}」을(를) 받았습니다. ${d.note}` });
      setTimeout(() => location.reload(), 900);
    } catch (e) {
      setMsg({ ok: false, s: e instanceof Error ? e.message : "실패했습니다" });
    } finally { setBusy(false); }
  }

  return (
    <Card title="찾은 자료 넣기"
          sub="넣으면 바로 다시 맞춰 봅니다. 조사 원장 파일은 건드리지 않습니다.">
      <div className="mb-3 flex gap-1">
        {([["url", "주소로"], ["text", "붙여넣기"], ["pdf", "PDF"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => { setTab(k); setMsg(null); }}
                  className={`rounded-md border px-3 py-1.5 text-[13px] ${
                    tab === k ? "border-pen bg-pen-soft font-semibold text-pen" : "border-rule text-muted"}`}>
            {l}
          </button>
        ))}
      </div>

      {tab === "url" && (
        <div className="flex flex-wrap gap-2">
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…"
                 className="min-w-0 flex-1 rounded-md border border-rule px-3 py-2 text-[13px]" />
          <button disabled={busy || !url}
                  onClick={() => run(() => post(`/api/intake/url`, { url, industry }))}
                  className="rounded-md border border-pen bg-pen-soft px-3 py-2 text-[13px] font-semibold text-pen disabled:opacity-50">
            가져오기
          </button>
        </div>
      )}
      {tab === "text" && (
        <div className="space-y-2">
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5}
                    placeholder="비공개 문서는 필요한 대목만 옮겨 적어도 됩니다"
                    className="w-full rounded-md border border-rule px-3 py-2 text-[13px]" />
          <button disabled={busy || text.length < 120}
                  onClick={() => run(() => post(`/api/intake/text`, { text, industry }))}
                  className="rounded-md border border-pen bg-pen-soft px-3 py-2 text-[13px] font-semibold text-pen disabled:opacity-50">
            {text.length < 120 ? `${120 - text.length}자 더 필요합니다` : "가져오기"}
          </button>
        </div>
      )}
      {tab === "pdf" && (
        <div className="space-y-2">
          <input type="file" accept="application/pdf" className="text-[13px]"
                 onChange={(e) => {
                   const f = e.target.files?.[0];
                   if (f) run(() => postFile(`/api/intake/pdf`, f, industry));
                 }} />
          <p className="text-[12px] text-faint">
            사진으로 스캔한 문서는 글자가 아니라 그림이라 읽지 못합니다. 그럴 땐 그렇게 알려 드립니다.
          </p>
        </div>
      )}

      {msg && (
        <p className={`mt-3 rounded-md border p-2.5 text-[13px] ${
          msg.ok ? "border-pen bg-pen-soft text-pen" : "border-gap bg-gap-soft text-gap"}`}>
          {msg.s}
        </p>
      )}
      <p className="mt-3 border-t border-rule pt-2 text-[12px] text-muted">
        판정 서버 {API}
      </p>
    </Card>
  );
}
