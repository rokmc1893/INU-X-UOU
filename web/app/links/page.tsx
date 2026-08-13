"use client";

import { Callout, DocHead, Field, Fold, Limit } from "@/components/ui";
import { useIndustry } from "@/components/Shell";
import { AXIS, type Pair, linkView, nameOf } from "@/lib/data";

function groupBreaks(rows: Pair[]) {
  const g = new Map<string, string[][]>();
  for (const f of rows) {
    const cur = g.get(f.reason) ?? [];
    cur.push(f.items);
    g.set(f.reason, cur);
  }
  return Array.from(g.entries()).sort((a, b) => b[1].length - a[1].length);
}

export default function Links() {
  const pick = useIndustry();
  const v = linkView(pick);
  const a = AXIS.ecosystem;

  return (
    <div className="page">
      <DocHead
        title="사업끼리 이어지는가"
        kicker={
          <>
            성과축 2순위 · 조사자 C의 <b>{a.c_status}</b> · 타당성 {a.score} · 산업 {pick}
          </>
        }
      />

      <Field label="한눈에" sub="사업 사이의 관계">
        <dl className="metrics">
          <div className="metric alert">
            <dt>조정 필요 중복</dt>
            <dd>
              {v.harmful.length}
              <small>건</small>
            </dd>
            <p className="hint">받는 사람·주는 것·직무가 모두 같습니다</p>
          </div>
          <div className="metric">
            <dt>의도적 병행</dt>
            <dd>
              {v.intentional.length}
              <small>건</small>
            </dd>
            <p className="hint">주는 것은 같지만 받는 사람이 다릅니다</p>
          </div>
          <div className="metric good">
            <dt>보완 관계</dt>
            <dd>
              {v.complements.length}
              <small>건</small>
            </dd>
            <p className="hint">주는 것이 달라 중복이 아닙니다</p>
          </div>
          <div className="metric">
            <dt>인계 끊김</dt>
            <dd>
              {v.breaks.length}
              <small>쌍</small>
            </dd>
          </div>
        </dl>
      </Field>

      {v.harmful.length > 0 && (
        <Field label="중복 후보" sub="협의에 올릴 것">
          <ul className="pairs">
            {v.harmful.map((f, i) => (
              <li key={i}>
                <div className="p">
                  <b>{nameOf(f.items[0])}</b>
                  <span>↔</span>
                  <b>{nameOf(f.items[1])}</b>
                </div>
                <span className="why">{f.reason}</span>
              </li>
            ))}
          </ul>
          <Callout kind="act" title="두 사업의 소관 부서에 조정 협의를 요청하세요.">
            <p>
              중복 <b>&lsquo;확정&rsquo;이 아니라 &lsquo;후보&rsquo;입니다</b> — 확정은 부서
              협의로 합니다.
            </p>
          </Callout>
        </Field>
      )}

      {v.complements.length > 0 && (
        <Field label="중복 아님" sub="반려를 막는 근거">
          <p className="lede">
            주는 것이 달라서 겹치지 않습니다. 검토서에 이유를 적어 두면 나중에 중복이라는 이유로
            잘못 반려당하는 것을 막아 줍니다.
          </p>
          <ul className="pairs">
            {v.complements.slice(0, 8).map((f, i) => (
              <li key={i}>
                <div className="p">
                  {nameOf(f.items[0])} <span>↔</span> {nameOf(f.items[1])}
                </div>
                <span className="why">{f.reason}</span>
              </li>
            ))}
          </ul>
          {v.complements.length > 8 && (
            <p className="note">…외 {v.complements.length - 8}쌍</p>
          )}
        </Field>
      )}

      <Field label="인계 끊김" sub="다음 단계로 못 넘김">
        {v.breaks.length > 0 ? (
          <div>
            {groupBreaks(v.breaks).map(([reason, pairs]) => (
              <Fold key={reason} summary={reason} count={`${pairs.length}쌍`}>
                <ul>
                  {pairs.slice(0, 8).map((p, i) => (
                    <li key={i}>
                      {nameOf(p[0])} → {nameOf(p[1])}
                    </li>
                  ))}
                </ul>
                {pairs.length > 8 && <p className="note">…외 {pairs.length - 8}쌍</p>}
              </Fold>
            ))}
          </div>
        ) : (
          <Callout kind="ok" title="이 산업 안에서는 인계 끊김 후보가 없습니다" />
        )}

        {v.crossIndustry > 0 && (
          <p className="note">
            산업이 서로 다른 {v.crossIndustry}쌍은 뺐습니다 — 「청년도약기지」와 「대한항공 MRO
            클러스터」 사이에 인계 절차가 없다는 지적은 실제 부서 협의로 이어지지 않기 때문입니다.
            <b> 지운 것이 아니라 세어서 밝힙니다.</b>
          </p>
        )}

        <Limit>{a.gap}</Limit>
      </Field>
    </div>
  );
}
