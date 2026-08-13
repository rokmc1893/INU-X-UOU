import Link from "next/link";
import type { ReactNode } from "react";

/** 문서 머리 — 화면 이름과 무엇을 기준으로 본 것인지. */
export function DocHead({ title, kicker }: { title: string; kicker: ReactNode }) {
  return (
    <header>
      <h1 className="doctitle">{title}</h1>
      <p className="dockicker">{kicker}</p>
    </header>
  );
}

/** 항목 블록. 왼쪽은 이름칸, 오른쪽은 내용 — 공문서 별지 서식과 같은 배치. */
export function Field({
  label,
  sub,
  children,
}: {
  label: string;
  sub?: string;
  children: ReactNode;
}) {
  return (
    <section className="field">
      <h2>
        {label}
        {sub ? <small>{sub}</small> : null}
      </h2>
      <div>{children}</div>
    </section>
  );
}

export function Badge({ kind, children }: { kind: "ok" | "warn" | "act" | "na"; children: ReactNode }) {
  return <span className={`v ${kind}`}>{children}</span>;
}

export function Callout({
  kind = "na",
  title,
  children,
}: {
  kind?: "ok" | "warn" | "act" | "na";
  title: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className={`callout ${kind}`}>
      <b>{title}</b>
      {children}
    </div>
  );
}

export function Fold({
  summary,
  count,
  children,
  open,
}: {
  summary: ReactNode;
  count?: ReactNode;
  children: ReactNode;
  open?: boolean;
}) {
  return (
    <details className="fold" open={open}>
      <summary>
        <b>{summary}</b>
        {count != null ? <span className="count">{count}</span> : null}
      </summary>
      <div className="foldbody">{children}</div>
    </details>
  );
}

/**
 * 확신 게이지 — 전체 중 얼마나 재 봤는지 눈에 보이게 둔다.
 * 재지 못한 몫은 비워 두지 않고 사선을 긋는다. 빈칸은 "문제 없음"으로 읽히기 때문이다.
 */
export function Gauge({
  measured,
  total,
  label,
}: {
  measured: number;
  total: number;
  label: ReactNode;
}) {
  const pct = total > 0 ? Math.min(100, Math.round((measured / total) * 100)) : 0;
  return (
    <div className="gauge">
      <div
        className="bar"
        role="img"
        aria-label={`전체 ${total}건 중 ${measured}건 확인 (${pct}%)`}
      >
        <i style={{ width: `${pct}%` }} />
        <u />
      </div>
      <p>{label}</p>
    </div>
  );
}

/**
 * 판정 도장. 이 도구가 내놓는 것은 확정이 아니라 후보라는 사실을 화면에 한 번은 못 박는다.
 */
export function Stamp() {
  return (
    <svg className="stamp" viewBox="0 0 100 100" aria-label="이 판정은 후보입니다. 확정이 아닙니다.">
      <defs>
        <path id="stamp-arc-top" d="M50,50 m-37,0 a37,37 0 1,1 74,0" fill="none" />
        <path id="stamp-arc-bottom" d="M50,50 m-31,0 a31,31 0 1,0 62,0" fill="none" />
      </defs>
      <circle cx="50" cy="50" r="46" fill="none" stroke="var(--seal)" strokeWidth="2.5" />
      <circle cx="50" cy="50" r="41" fill="none" stroke="var(--seal)" strokeWidth="0.9" />
      <text fill="var(--seal)" fontSize="9.5" letterSpacing="1.6" fontFamily="var(--sans)">
        <textPath href="#stamp-arc-top" startOffset="50%" textAnchor="middle">
          정책핏 인천 · 판정
        </textPath>
      </text>
      <text fill="var(--seal)" fontSize="7.5" letterSpacing="1.2" fontFamily="var(--sans)">
        <textPath href="#stamp-arc-bottom" startOffset="50%" textAnchor="middle">
          확정 아님
        </textPath>
      </text>
      <text
        x="50"
        y="56"
        textAnchor="middle"
        fill="var(--seal)"
        fontSize="21"
        fontFamily="var(--serif)"
      >
        후보
      </text>
    </svg>
  );
}

/** 축의 한계. 못 하는 것을 지우지 않고 같은 자리에 같은 모양으로 적는다. */
export function Limit({ children }: { children: ReactNode }) {
  return (
    <p className="note">
      <b>이 축의 한계</b> — {children}
    </p>
  );
}

export function ScreenLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link href={href}>{children}</Link>;
}
