"use client";

import { useIndustry } from "@/components/Shell";
import { Badge, DocHead, Field, Gauge, Limit } from "@/components/ui";
import { AXIS, budgetView, nameOf } from "@/lib/data";

export default function Budget() {
  const pick = useIndustry();
  const v = budgetView(pick);
  const a = AXIS.budget;

  return (
    <div className="page">
      <DocHead
        title="예산이 새는가"
        kicker={
          <>
            성과축 1순위 · 조사자 C의 <b>{a.c_status}</b> · 타당성 {a.score} · 산업 {pick}
          </>
        }
      />

      <Field label="한눈에" sub="공식 예산 원장 대조">
        <dl className="metrics">
          <div className="metric good">
            <dt>원장과 일치</dt>
            <dd>
              {v.confirmed.length}
              <small>건</small>
            </dd>
          </div>
          <div className="metric alert">
            <dt>재검토 필요</dt>
            <dd>
              {v.conflicts.length}
              <small>건</small>
            </dd>
          </div>
          <div className="metric alert">
            <dt>소관 불일치</dt>
            <dd>
              {v.deptMismatch.length}
              <small>건</small>
            </dd>
            <p className="hint">사업 문서의 소관 부서가 공식 원장과 다릅니다</p>
          </div>
          <div className="metric">
            <dt>원장에서 못 찾음</dt>
            <dd>
              {v.unverified.length}
              <small>건</small>
            </dd>
            <p className="hint">&ldquo;예산이 없다&rdquo;가 아니라 &ldquo;아직 못 찾았다&rdquo;</p>
          </div>
        </dl>

        <Gauge
          measured={v.checked}
          total={v.works}
          label={
            <>
              사업 {v.works}건 중 <b>{v.checked}건</b>만 원장과 대조가 끝났습니다. 사선 친 몫은
              판정하지 않은 몫입니다.
            </>
          }
        />
      </Field>

      {v.deptMismatch.length > 0 && (
        <Field label="소관 불일치" sub="협의처가 바뀝니다">
          <p className="lede">
            공문을 잘못된 과로 보내면 회신이 오지 않습니다. 아래는 공식 예산 원장 기준으로 고쳐야
            할 것들입니다.
          </p>
          <div className="scroll">
            <table className="tbl">
              <thead>
                <tr>
                  <th>사업</th>
                  <th style={{ width: "13rem" }}>사업 문서에 적힌 소관</th>
                  <th style={{ width: "14rem" }}>공식 예산 원장의 소관</th>
                </tr>
              </thead>
              <tbody>
                {v.deptMismatch.map((x) => (
                  <tr key={x.pid}>
                    <td>
                      {nameOf(x.pid)}
                      <span className="sub">{x.pid}</span>
                    </td>
                    <td style={{ color: "var(--ink-3)" }}>{x.card}</td>
                    <td className="lead">{x.official}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Field>
      )}

      {v.conflicts.length > 0 && (
        <Field label="금액 어긋남" sub="다시 봐야 합니다">
          <ul className="pairs">
            {v.conflicts.map((x) => (
              <li key={x.pid}>
                <div className="p">
                  <b>{nameOf(x.pid)}</b>
                  <Badge kind="act">{x.status}</Badge>
                </div>
                <span className="why">
                  {x.budget_won ? `원장 ${x.budget_won.toLocaleString("ko-KR")}원 · ` : ""}
                  {x.detail}
                </span>
              </li>
            ))}
          </ul>
        </Field>
      )}

      <Field label="대조 완료" sub={`${v.confirmed.length}건`}>
        {v.confirmed.length > 0 ? (
          <div className="scroll">
            <table className="tbl">
              <thead>
                <tr>
                  <th>사업</th>
                  <th style={{ width: "11rem" }}>공식 원장 금액</th>
                  <th style={{ width: "8rem" }}>매칭</th>
                </tr>
              </thead>
              <tbody>
                {v.confirmed.map((x) => (
                  <tr key={x.pid}>
                    <td>
                      {nameOf(x.pid)}
                      <span className="sub">
                        {x.pid}
                        {x.dept ? ` · ${x.dept}` : ""}
                      </span>
                    </td>
                    <td className="num">
                      {x.budget_won ? `${x.budget_won.toLocaleString("ko-KR")}원` : "—"}
                    </td>
                    <td>
                      <Badge kind={x.loose ? "na" : "ok"}>{x.loose ? "느슨" : "정확"}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="note">이 산업 범위에는 원장 대조가 끝난 사업이 없습니다.</p>
        )}

        {v.unverified.length > 0 && (
          <ul className="pairs" style={{ marginTop: "1.2rem" }}>
            {v.unverified.map((x) => (
              <li key={x.pid}>
                <div className="p">
                  <b>{nameOf(x.pid)}</b>
                  <Badge kind="na">{x.status}</Badge>
                </div>
                <span className="why">{x.detail}</span>
              </li>
            ))}
          </ul>
        )}

        <Limit>
          {a.gap} 대조가 끝난 것은 사업 {v.works}건 중 {v.checked}건입니다. 나머지는 &ldquo;예산이
          없다&rdquo;가 아니라 <b>&ldquo;아직 확인하지 못했다&rdquo;</b>입니다.
        </Limit>
      </Field>
    </div>
  );
}
