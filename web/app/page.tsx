"use client";

import { useIndustry } from "@/components/Shell";
import { Badge, DocHead, Field, Fold, Stamp } from "@/components/ui";
import {
  ALL,
  AXES,
  AXES_COVERAGE,
  PLANS,
  SIGNAL_ROWS,
  TODAY,
  WORKS,
  headline,
} from "@/lib/data";

const AXIS_MARK = {
  full: { kind: "ok" as const, text: "판정함" },
  partial: { kind: "warn" as const, text: "일부만" },
  none: { kind: "act" as const, text: "판정 못 함" },
};

export default function Overview() {
  const pick = useIndustry();
  const h = headline(pick);
  const gaps = h.gapKinds.join("·");

  return (
    <div className="page">
      <DocHead
        title="무엇을 보는가"
        kicker={
          <>
            인천 6대 전략산업의 <b>사업</b>과 <b>산업 수요</b>를 대조해, 어긋난 곳을 후보로
            골라냅니다. 확정은 부서 협의로 합니다. · 기준일 {TODAY} · 산업 {pick}
          </>
        }
      />

      <Field label="결론" sub="지금 자료로">
        <div className="verdict">
          <Stamp />
          {h.uncovered > 0 ? (
            <h3>
              {pick === ALL ? "인천 6대 산업" : pick}의 공백은{" "}
              <span className="keep">
                <mark>「{gaps}」</mark>에
              </span>{" "}
              몰려 있습니다
            </h3>
          ) : (
            <h3>이 범위에서는 덮는 사업이 없는 수요가 나오지 않았습니다</h3>
          )}
          <p>
            대조한 산업 수요 {h.matched}건 중 덮는 사업이 없는 것은 <b>{h.uncovered}건</b>
            {h.uncovered > 0 ? (
              <>
                이고, 그 <b>전부</b>가 {gaps} 수요입니다.
              </>
            ) : (
              "입니다."
            )}{" "}
            {h.byNeed.map(([n, v]) => `${n} ${v.total - v.gap}÷${v.total} 덮임`).join(" / ")}
            <br />
            반면 사업이 주는 것은 {h.means.map(([n, v]) => `${n} ${v}건`).join(", ")}입니다 —{" "}
            {h.uncovered > 0 ? (
              <b>
                정책이 몰려 있는 곳({h.crowded.join("·")})과 모자란 곳({gaps})이 다릅니다.
              </b>
            ) : (
              <b>몰려 있는 곳은 {h.crowded.join("·")}입니다.</b>
            )}
          </p>
        </div>
        <p className="note">
          이 문장의 숫자는 <b>화면 3의 실측을 그대로 끌어온 것</b>입니다. 손으로 적어 둔 숫자는
          한 곳도 없습니다 — 자료가 바뀌면 문장도 바뀝니다.
        </p>
      </Field>

      <Field label="판정 범위" sub="7개 성과축">
        <p className="lede">
          산업과 정책이 어긋나면 7가지 문제가 생깁니다. 이 도구는 그중{" "}
          <b>{AXES_COVERAGE.partial}가지를 일부만</b> 판정하고{" "}
          <b>{AXES_COVERAGE.none}가지는 판정하지 못합니다.</b> 못 하는 축은 지우지 않고 사선을
          그어 뒀습니다.
        </p>

        <div className="stripe">
          {AXES.map((a) => (
            <div key={a.rank} className={`band ${a.covered}`} title={a.gap}>
              <em>{a.rank}</em>
              <span>{a.outcome}</span>
              <div className="fill" />
            </div>
          ))}
        </div>
        <p className="note">
          축과 순위는 우리가 짓지 않았습니다. 조사자 C의{" "}
          <code>C1_outcome_feasibility_matrix.csv</code>를 그대로 읽습니다.
        </p>

        <div className="scroll" style={{ marginTop: "1.4rem" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: "1.6rem" }}>순위</th>
                <th>생기는 문제</th>
                <th style={{ width: "5.5rem" }}>이 도구는</th>
                <th>무엇으로 / 왜 못 하는지</th>
              </tr>
            </thead>
            <tbody>
              {AXES.map((a) => {
                const m = AXIS_MARK[a.covered];
                return (
                  <tr key={a.rank} className={a.covered === "none" ? "void" : undefined}>
                    <td className="num">{a.rank}</td>
                    <td>
                      <span className="lead">{a.outcome}</span>
                      <span className="sub">
                        조사자 C · {a.c_status} · 타당성 {a.score}
                      </span>
                    </td>
                    <td>
                      <Badge kind={m.kind}>{m.text}</Badge>
                    </td>
                    <td className={a.covered === "none" ? "hatch" : undefined}>
                      {a.module ? (
                        <>
                          {a.module}
                          <span className="sub">한계: {a.gap}</span>
                        </>
                      ) : (
                        <span className="sub">{a.gap}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="note">
          자료가 없는 것이지 문제가 없는 것이 아닙니다. 사선 친 칸은 <b>판정하지 못한 칸</b>이고,
          빈칸으로 두면 &ldquo;문제 없음&rdquo;으로 읽히기 때문에 긋습니다.
        </p>
      </Field>

      <Field label="낱말" sub="셋을 구분합니다">
        <dl className="defs">
          <div>
            <dt>산업</dt>
            <dd>
              <b>필요가 나오는 쪽.</b> 사람·기술·돈·판로·받쳐 줄 기업·공간이 모자란다고 신호가
              나옵니다 — 지금 {SIGNAL_ROWS}행
            </dd>
          </div>
          <div>
            <dt>정책</dt>
            <dd>
              <b>방향을 정하는 상위 문서.</b> 기본계획·종합계획·전략. 예산이 직접 붙지 않아 중복
              검토 대상이 아닙니다 — 지금 {PLANS.length}건
            </dd>
          </div>
          <div>
            <dt>사업</dt>
            <dd>
              <b>예산이 붙는 실행 단위 — 이 도구가 검토하는 대상.</b> 지금 {WORKS.length}건
            </dd>
          </div>
        </dl>
      </Field>

      <Field label="근거" sub="어디까지 확인했나">
        <Fold summary="이 6개 산업 목록은 어디서 왔습니까 — 근거 등급" count="SECONDARY_PRESS_ONLY">
          <p style={{ margin: "0 0 .6rem" }}>
            <b>확인된 것</b> — 「인천 전략산업육성 종합계획」(2023 수립, 산업정책과 총괄)이 2015년{" "}
            <b>8대</b>를 <b>6대</b>로 재편했다고 적혀 있습니다 (정책원장 <code>IC-COM-001</code>).
          </p>
          <p style={{ margin: "0 0 .6rem" }}>
            <b>확인 못 한 것</b> — 그 종합계획의 <b>원문·고시문을 확보하지 못했습니다.</b> 근거는
            언론기사 1건이고 등급은 <code>SECONDARY_PRESS_ONLY</code>입니다. 민선8기
            시정운영계획·산업발전 기본계획·지역산업진흥계획은 조사 원장에 없습니다. 발표에서
            &ldquo;인천시가 지정한 6대&rdquo;라고 단정하지 않습니다.
          </p>
          <p style={{ margin: "0 0 .6rem" }}>
            <b>주의</b> — 조사자 A는 <b>다른 6대</b>를 쓰고 있었습니다(바이오·반도체·미래모빌리티·
            로봇항공·물류항만·스마트시티AI). 이쪽은 <b>부서명 기준</b>이라 협의 대상을 찾을 때는
            A의 구분이 더 맞을 수 있습니다.
          </p>
          <p style={{ margin: 0 }}>
            <b>배타적 분류가 아닙니다</b> — 양자는 바이오와 디지털데이터에 걸쳐 있고,
            반도체·바이오는 같은 과 소관이라 예산이 섞여 있습니다.
          </p>
        </Fold>
      </Field>
    </div>
  );
}
