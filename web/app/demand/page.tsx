"use client";

import { useIndustry } from "@/components/Shell";
import { Badge, Callout, DocHead, Field, Fold, Limit } from "@/components/ui";
import {
  ALL,
  AXIS,
  INDUSTRIES,
  NEED_LABEL,
  POSTURES,
  PRINCIPLE,
  RESPONSIVE,
  demandView,
  nameOf,
} from "@/lib/data";

export default function Demand() {
  const pick = useIndustry();
  const v = demandView(pick);
  const a = AXIS.fit;
  const shown = INDUSTRIES.filter((i) => pick === ALL || pick === i);

  const rows = [...v.real].sort((x, y) => {
    const byVerdict = Number(x.verdict !== "uncovered") - Number(y.verdict !== "uncovered");
    return byVerdict !== 0 ? byVerdict : x.covers.length - y.covers.length;
  });

  return (
    <div className="page">
      <DocHead
        title="산업 수요와 맞는가"
        kicker={
          <>
            성과축 3순위 · 조사자 C의 <b>{a.c_status}</b> · 타당성 {a.score} · 산업 {pick}
          </>
        }
      />

      <Field label="가려는 것" sub="산업마다 다른 질문">
        <div className="verdict" style={{ background: "var(--sheet)" }}>
          <h3 style={{ marginBottom: ".4rem" }}>{PRINCIPLE}</h3>
          <p>
            그래서 산업마다 물어야 할 질문이 다릅니다. 이미 수요가 있는 산업엔 &ldquo;그 수요를
            덮었는가&rdquo;를, 아직 수요가 없는 산업엔 &ldquo;수요를 만들 근거가 있는가&rdquo;를
            묻습니다.
          </p>
        </div>

        <div className="scroll" style={{ marginTop: "1.2rem" }}>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: "6rem" }}>산업</th>
                <th style={{ width: "5rem" }}>태세</th>
                <th>물어야 할 질문</th>
                <th>그렇게 본 이유</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((ind) => {
                const p = POSTURES[ind];
                return (
                  <tr key={ind}>
                    <td className="lead">{ind}</td>
                    <td>
                      <Badge kind={p.posture === RESPONSIVE ? "ok" : "act"}>{p.posture}</Badge>
                    </td>
                    <td>{p.question}</td>
                    <td>
                      <span className="sub" style={{ fontSize: ".78rem" }}>
                        {p.why}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="note">
          태세는 사람이 정한 것이 아니라 <b>수요신호가 정한 것</b>입니다. 새 조사가 들어오면 태세도
          질문도 저절로 바뀝니다.
        </p>
      </Field>

      <Field label="대조" sub="수요 ↔ 사업">
        <p className="lede">
          직무 하나가 아니라 <b>지원 유형 7가지</b>로 맞춥니다 —
          사람·기술·돈·판로·받쳐 줄 기업·공간·행정. 예전에는 사람 축만 봤습니다.
        </p>

        <div className="scroll">
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: "6.5rem" }}>필요한 것</th>
                <th style={{ width: "5rem" }}>산업</th>
                <th>무엇이 확인됐는가</th>
                <th style={{ width: "10rem" }}>덮는 사업</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => {
                const n = c.covers.length;
                return (
                  <tr key={c.signal_id} className={n === 0 ? "void" : undefined}>
                    <td>
                      <span className="lead">{c.need}</span>
                      <span className="sub">{NEED_LABEL[c.need as string]}</span>
                    </td>
                    <td>{c.industry}</td>
                    <td>
                      {c.problem_type}
                      <span className="sub">
                        {c.value} · <span className="sig">{c.signal_id}</span> {c.grade}등급{" "}
                        {c.trend}
                      </span>
                    </td>
                    <td className={n === 0 ? "hatch" : undefined}>
                      {n === 0 ? (
                        <Badge kind="act">없음</Badge>
                      ) : n === 1 ? (
                        <Badge kind="na">1건뿐</Badge>
                      ) : (
                        <Badge kind="ok">{n}건</Badge>
                      )}
                      {n > 0 && n <= 2 && (
                        <span className="sub">
                          {c.covers.map((p) => nameOf(p).slice(0, 18)).join(", ")}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Field>

      {v.uncovered.length > 0 && (
        <Field label="공백" sub="덮는 사업이 없음">
          <Callout
            kind="act"
            title={`덮는 사업이 없는 수요 ${v.uncovered.length}건 — 전부 「${v.gapKinds.join(", ")}」입니다.`}
          >
            <ul>
              {v.uncovered.map((c) => (
                <li key={c.signal_id}>
                  <b>
                    {c.industry} · {c.problem_type}
                  </b>{" "}
                  — {c.value} <span className="sig">{c.signal_id}</span>
                  <br />
                  <span style={{ color: "var(--ink-3)" }}>이 신호의 한계: {c.limit}</span>
                </li>
              ))}
            </ul>
          </Callout>
        </Field>
      )}

      {v.thin.length > 0 && (
        <Field label="얇은 곳" sub="사업 1건에 기댐">
          <Callout
            kind="warn"
            title={`덮는 사업이 1건뿐인 수요 ${v.thin.length}건 — 그 사업이 멈추면 바로 공백이 됩니다.`}
          >
            <p>{v.thin.map((c) => `${c.industry} ${c.need}`).join(", ")}</p>
          </Callout>
        </Field>
      )}

      <Field label="뺀 것" sub="수요로 세지 않음">
        <Fold
          summary={`수요로 세지 않은 신호 ${v.admin.length + v.notNeed.length}건 — 왜 뺐는지`}
          count={`행정 ${v.admin.length} · 비수요 ${v.notNeed.length}`}
        >
          <p style={{ margin: "0 0 .5rem" }}>
            <b>행정 과제 {v.admin.length}건</b> — 집행지연·수요조사 노후화·데이터 공백처럼{" "}
            <b>사업으로 덮는 것이 아닌</b> 신호입니다. 공백으로 세면 잘못된 경보가 됩니다.
          </p>
          <p style={{ margin: "0 0 .6rem" }}>
            <b>수요가 아닌 것 {v.notNeed.length}건</b> — 산업 규모·현원·&ldquo;수요가 없다&rdquo;는
            역방향 신호입니다. &ldquo;크다&rdquo;를 &ldquo;모자란다&rdquo;로 바꿔 읽지 않습니다.
          </p>
          <ul>
            {[...v.admin, ...v.notNeed].slice(0, 14).map((c) => (
              <li key={c.signal_id}>
                <span className="sig">{c.signal_id}</span> {c.industry} · {c.problem_type}
              </li>
            ))}
          </ul>
        </Fold>

        <Limit>
          사업 {v.works}건 중 <b>{v.unreadable}건</b>은 원문에 <b>주는 것(수단)이 안 적혀 있어</b>{" "}
          어떤 수요와도 맞출 수 없습니다. &ldquo;덮는 사업이 없다&rdquo;와 &ldquo;수단을 못
          읽었다&rdquo;는 다릅니다.
        </Limit>
      </Field>
    </div>
  );
}
