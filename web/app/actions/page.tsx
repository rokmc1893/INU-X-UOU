"use client";

import Link from "next/link";
import { useIndustry } from "@/components/Shell";
import { Badge, Callout, DocHead, Field, Fold } from "@/components/ui";
import { ALL, actions } from "@/lib/data";

export default function Actions() {
  const pick = useIndustry();
  const v = actions(pick);
  const q = pick === ALL ? "" : `?ind=${encodeURIComponent(pick)}`;

  return (
    <div className="page">
      <DocHead
        title="조치 제안"
        kicker={
          <>
            판정을 행동으로 옮깁니다. <b>최종 판단은 담당자가 합니다.</b> · 산업 {pick}
          </>
        }
      />

      <Field label="먼저 할 것" sub="판정에서 그대로">
        {v.todo.length > 0 ? (
          <ol className="todo">
            {v.todo.map((t) => (
              <li key={t.title}>
                <div>
                  <b>{t.title}</b>
                  <p>{t.why}</p>
                  <Link href={`${t.href}${q}`}>근거 보기 — {t.where}</Link>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <Callout kind="ok" title="이 범위에서는 즉시 조치할 항목이 없습니다" />
        )}
      </Field>

      <Field label="유도형" sub="수요 대신 무엇으로">
        {v.induced.length > 0 ? (
          <>
            <p className="lede">
              수요 실측치가 없다는 것 자체는 흠이 아닙니다. 대신 아래 셋을 답할 수 있어야
              &ldquo;수요도 없는데 왜 하느냐&rdquo;는 질문을 넘길 수 있습니다.
            </p>
            {v.induced.slice(0, 6).map((row) => {
              const ok = row.evidence.filter((e) => e.ok).length;
              return (
                <Fold
                  key={row.policy_id}
                  open={ok === 0}
                  summary={`[${row.industry}] ${row.name}`}
                  count={`근거 ${ok}/3`}
                >
                  <ul className="tests">
                    {row.evidence.map((e) => (
                      <li key={e.test}>
                        <Badge kind={e.ok ? "ok" : "act"}>{e.ok ? "확보" : "없음"}</Badge>
                        <b>{e.test}</b>
                        <span className="detail">{e.detail}</span>
                      </li>
                    ))}
                  </ul>
                </Fold>
              );
            })}
            <p className="note">
              「선점논거」는 어느 원장에도 없습니다. <b>지어내지 않고 없다고 표시합니다.</b>
            </p>
          </>
        ) : (
          <p className="note">이 범위에는 유도형 산업 사업이 없습니다.</p>
        )}
      </Field>

      <Field label="주의" sub="그대로 믿지 마세요">
        <p className="lede">
          모든 판정은 <b>후보</b>입니다. 확정은 부서 협의로 합니다. 판정에 AI는 관여하지 않습니다 —
          원문에서 항목을 뽑는 데만 쓰고, 고르는 일은 규칙이 합니다. 원문에 없는 값은 채우지 않고{" "}
          <b>비워 둡니다</b>.
        </p>
        {v.unnamed.length > 0 && (
          <p className="note">
            사업명을 읽지 못한 카드 {v.unnamed.length}건이 있습니다 (
            <span className="sig">{v.unnamed.map((c) => c.policy_id).join(", ")}</span>) — 지우지
            않고 표시해 뒀습니다.
          </p>
        )}
      </Field>
    </div>
  );
}
