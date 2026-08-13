"use client";

/* ① 예산이 제대로 붙어 있나 — 공식 예산 장부와 대조한다. */
import { Loading, PageHead, useReview } from "@/components/Shell";
import { Src, Tag, Void } from "@/components/bits";
import { Card, Counts, RatioBar } from "@/components/parts";

export default function BudgetPage() {
  const { r, err } = useReview();
  if (!r) return <Loading err={err} />;
  const b = r.budget;

  return (
    <>
      <PageHead
        r={r} title="예산이 제대로 붙어 있나"
        lead="사업 문서에 적힌 금액·소관 부서를 인천시 공식 예산 장부와 맞춰 봅니다."
      />

      <div className="stagger">
        <Counts items={[
          { label: "장부와 일치", n: b.won ? 1 : 0, tone: "pen" },
          { label: "소관이 다름", n: b.mismatch ? 1 : 0, tone: "gap",
            hint: b.mismatch ? "공문 보낼 과가 바뀝니다" : undefined },
          { label: "금액 재검토", n: b.status === "NEEDS_REVIEW" ? 1 : 0, tone: "gap" },
          { label: "장부에서 못 찾음", n: b.status ? 0 : 1,
            hint: "「예산이 없다」가 아닙니다" },
        ]} />
  
        {b.mismatch && (
          <Card title="소관 부서가 장부와 다릅니다"
                sub="공문을 잘못된 과로 보내면 회신이 오지 않습니다. 장부 쪽이 맞습니다.">
            <table className="w-full border-collapse text-[13px]">
              <tbody>
                <tr className="border-b border-rule">
                  <td className="w-44 py-2 text-muted">사업 문서에 적힌 소관</td>
                  <td className="py-2">{b.mismatch.card}</td>
                </tr>
                <tr className="border-b border-rule">
                  <td className="py-2 text-muted">공식 예산 장부의 소관</td>
                  <td className="py-2 text-[15px] font-bold text-pen">{b.mismatch.official}</td>
                </tr>
                <tr>
                  <td className="py-2 text-muted">장부의 사업 항목명</td>
                  <td className="py-2">{b.line ?? "미확인"}</td>
                </tr>
                {b.note && (
                  <tr>
                    <td className="py-2 align-top text-muted">어떻게 확인했나</td>
                    <td className="py-2 text-[12px] text-muted">{b.note}</td>
                  </tr>
                )}
              </tbody>
            </table>
            <p className="mt-3 rounded-md bg-shell p-2.5 text-[12px] text-muted"
               dangerouslySetInnerHTML={{ __html: r.caveat }} />
          </Card>
        )}
  
        {b.won && (
          <Card title="장부에서 확인한 금액">
            <p className="text-[26px] font-bold leading-none">
              {b.won.toLocaleString()}<span className="ml-1 text-[14px] font-normal">원</span>
              <Tag tone="pen">{b.status === "EXACT" || b.status === "RESOLVED" ? "정확히 일치" : "느슨한 일치"}</Tag>
            </p>
            <dl className="mt-3 grid grid-cols-[7rem_1fr] gap-x-3 gap-y-1.5 text-[13px]">
              <dt className="text-muted">사업 문서의 값</dt>
              <dd>{r.card.budget ?? "적혀 있지 않음"}</dd>
              <dt className="text-muted">장부 항목</dt><dd>{b.line ?? "미확인"}</dd>
              <dt className="text-muted">장부의 소관</dt><dd>{b.official_dept ?? "미확인"}</dd>
            </dl>
          </Card>
        )}
  
        {b.empty && <Card title="이 사업은 아직 대조하지 못했습니다"><Void r={b.empty} /></Card>}
  
        <Card title="이 도구가 대조를 마친 범위"
              sub="장부 대조는 조사자가 손으로 맞춰 본 것이라 아직 일부만 끝났습니다.">
          <RatioBar done={10} total={52} label="6대 산업 사업 중 장부 대조가 끝난 것" />
          <p className="mt-3 text-[13px]">
            나머지는 <b>「예산이 없다」가 아니라 「아직 확인하지 못했다」</b>입니다.
            장부에서 못 찾았다는 이유로 사업을 깎으면 안 됩니다.
          </p>
          <p className="mt-2 text-[12px] text-muted">
            채우려면 인천시 예산서에서 이 사업의 세부사업명을 찾아 금액과 소관을 확인하면 됩니다.
          </p>
        </Card>
  
        <p className="text-[12px] text-faint">
          검토 대상 원문 <Src url={r.card.url} />
        </p>
      </div>

    </>
  );
}
