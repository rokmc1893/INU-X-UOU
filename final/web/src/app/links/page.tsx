"use client";

/* ② 사업끼리 겹치거나 끊기지 않았나.
 *
 * 판정 기준은 우리가 정한 것이 아니라 행정 절차 3단계의 반려 사유를 그대로 옮긴 것이다.
 * 그 문장을 화면에 인용해 두면 "왜 이 기준이냐"는 물음에 바로 답이 된다.
 */
import { Loading, PageHead, useReview } from "@/components/Shell";
import { Void } from "@/components/bits";
import { Card, Counts, PairList } from "@/components/parts";
import Relations from "@/components/Relations";

export default function LinksPage() {
  const { r, err } = useReview();
  if (!r) return <Loading err={err} />;
  const o = r.overlaps;

  return (
    <>
      <PageHead
        r={r} title="사업끼리 겹치거나 끊기지 않았나"
        lead="같은 산업 안의 다른 사업과 하나씩 맞춰 봅니다 — 받는 사람·주는 것·직무가 같은지."
      />

      <Counts items={[
        { label: "정리가 필요한 겹침", n: o.harmful.length, tone: "gap" },
        { label: "일부러 나란히 둔 것", n: o.intentional.length },
        { label: "서로 채워 주는 것", n: o.complement.length },
        { label: "넘기는 절차가 없음", n: r.handoffs.items.length },
      ]} />

      <Relations r={r} />

      <PairList
        title="정리가 필요해 보이는 겹침" tone="gap" rows={o.harmful}
        note="받는 사람·주는 것·직무가 모두 같습니다. 두 사업의 소관 부서에 조정 협의를 요청하세요."
      />
      <PairList
        title="겹쳐 보이지만 겹치지 않는 것" tone="flat"
        rows={[...o.intentional, ...o.complement]}
        note="주는 것이 같아도 받는 사람이나 수단이 다릅니다. 검토서에 이 이유를 적어 두면 중복이라는 이유로 잘못 반려당하는 것을 막아 줍니다."
      />
      <PairList
        title="다음 사업으로 넘기는 절차가 없는 곳" tone="flat" rows={r.handoffs.items}
        note="앞 단계를 마친 사람을 뒤 단계로 넘기는 절차가 두 사업 문서 어디에도 없습니다."
      />

      {(o.empty || r.handoffs.empty) && (
        <Card title="비어 있는 까닭">
          <div className="space-y-3">
            <Void r={o.empty} />
            <Void r={r.handoffs.empty} />
          </div>
        </Card>
      )}

      <Card title="이 기준은 어디서 왔나">
        <p className="text-[14px]">
          행정 절차 {r.stage.no}단계 「{r.stage.name}」의 반려 사유가 이것입니다.
        </p>
        <blockquote className="mt-2 border-l-2 border-pen bg-pen-soft px-3 py-2 text-[14px] font-medium">
          {r.duplicateRule}
        </blockquote>
        <p className="mt-2 text-[13px] text-muted">
          그래서 <b>받는 사람 · 주는 것 · 직무</b> 셋을 맞춰 봅니다. 저희가 고른 기준이 아닙니다.
        </p>
        <p className="mt-3 border-t border-rule pt-2 text-[12px] text-muted">
          산업이 서로 다른 쌍은 뺐습니다 — 청년일자리 사업과 항공 정비 클러스터 사이에
          인계 절차가 없다는 지적은 실제 부서 협의로 이어지지 않습니다.
        </p>
      </Card>
    </>
  );
}
