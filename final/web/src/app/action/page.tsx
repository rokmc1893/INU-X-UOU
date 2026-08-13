"use client";

/* ④ 조치 제안 — 검토서 초안을 받아 결재문서에 붙인다.
 *
 * 이 도구는 정책을 제안하지 않는다. 발의권은 과(課) 단위이고 성립 결정은 담당 과장이다.
 * 우리는 검토서 초안과 근거만 낸다.
 */
import { useState } from "react";
import { Loading, PageHead, useReview } from "@/components/Shell";
import { Src, Tag } from "@/components/bits";
import { Card } from "@/components/parts";
import YearWindows from "@/components/YearWindows";
import { getDraft } from "@/lib/api";

const TRACKS = ["기존사업 개편/확대", "다음 연도 본예산 신규사업"];

export default function ActionPage() {
  const { pid, r, err } = useReview();
  const [track, setTrack] = useState(TRACKS[0]);
  const [md, setMd] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!r) return <Loading err={err} />;

  async function make(download: boolean) {
    setBusy(true);
    try {
      const d = await getDraft(pid, track);
      setMd(d.markdown);
      if (download) {
        const u = URL.createObjectURL(new Blob([d.markdown], { type: "text/markdown" }));
        const a = document.createElement("a");
        a.href = u; a.download = d.filename; a.click();
        URL.revokeObjectURL(u);
      }
    } finally { setBusy(false); }
  }

  return (
    <>
      <PageHead
        r={r} title="조치 제안"
        lead="판정을 결재문서에 붙일 수 있는 형태로 내보냅니다. 최종 판단은 담당자가 합니다."
      />

      <Card title="검토서 초안"
            sub="판정 결과와 근거, 못 본 것과 그 이유, 협의 요청 부서, 다음 창구와 마감이 들어갑니다. 수치마다 원문 링크가 붙습니다.">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[13px] text-muted">어느 창구로</span>
          {TRACKS.map((t) => (
            <button key={t} onClick={() => { setTrack(t); setMd(null); }}
                    className={`rounded-md border px-3 py-1.5 text-[13px] ${
                      t === track ? "border-pen bg-pen-soft font-semibold text-pen" : "border-rule text-muted"}`}>
              {t}
            </button>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button onClick={() => make(true)} disabled={busy}
                  className="rounded-md border border-pen bg-pen px-3.5 py-2 text-[13px] font-semibold text-white disabled:opacity-50">
            {busy ? "만드는 중…" : "내려받기 (.md)"}
          </button>
          <button onClick={() => make(false)} disabled={busy}
                  className="rounded-md border border-rule px-3.5 py-2 text-[13px] text-muted hover:border-pen hover:text-pen">
            미리 보기
          </button>
        </div>
        {md && (
          <pre className="mt-3 max-h-[420px] overflow-auto rounded-md border border-rule bg-shell p-3 text-[12px] leading-relaxed whitespace-pre-wrap">
            {md}
          </pre>
        )}
      </Card>

      <Card title="공문은 어디로 보내나">
        {r.consult.length ? (
          <ul className="space-y-2">
            {r.consult.map((c) => (
              <li key={c.team} className="border-l-2 border-pen pl-3">
                <p className="text-[15px] font-semibold">
                  {c.team} <span className="text-[13px] font-normal text-muted">({c.bureau})</span>
                  <Src url={c.source_url} label="부서 근거" />
                </p>
                <p className="text-[12px] text-muted">{c.decision_right}</p>
                <p className="text-[12px] text-muted">연락처 {c.contact}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[13px] text-hold">산업이 확인되지 않아 협의처를 안내하지 못합니다.</p>
        )}
        <p className="mt-3 rounded-md bg-shell p-2.5 text-[12px] text-muted"
           dangerouslySetInnerHTML={{ __html: r.caveat }} />
        <p className="mt-3 text-[13px]">
          <b>같이 검토하는 사람</b>
        </p>
        <ul className="mt-1 space-y-1 text-[13px]">
          {r.reviewers.map((x) => (
            <li key={x.who}>
              <Tag tone="flat">{x.who}</Tag>{" "}
              <span className="text-muted">{x.why}</span>
            </li>
          ))}
        </ul>
      </Card>

      <YearWindows />

      <Card title="이 판정을 그대로 믿으면 안 되는 이유">
        <ul className="list-disc space-y-1.5 pl-5 text-[13px]">
          <li>모든 판정은 <b>후보</b>입니다. 확정은 부서 협의로 합니다.</li>
          <li>판정에 AI는 관여하지 않습니다 — 원문에서 항목을 뽑는 데만 쓰고,
            무엇이 겹치고 무엇이 비었는지 고르는 일은 규칙이 합니다.</li>
          <li>원문에 없는 값은 채우지 않고 비워 둡니다.
            {r.card.missing.length > 0 && (
              <> 이 사업은 <b>{r.card.missing.length}개 항목</b>이 원문에 없어 비어 있습니다.</>
            )}
          </li>
          <li>예산 장부 대조는 아직 일부만 끝났습니다. 「장부에서 못 찾음」은
            <b> 「예산이 없다」가 아닙니다</b>.</li>
        </ul>
      </Card>
    </>
  );
}
