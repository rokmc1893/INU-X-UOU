"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ALL, INDUSTRIES, PLANS, SCREENS, SIGNAL_ROWS, TODAY, WORKS } from "@/lib/data";

/** 지금 고른 산업. 주소에 남겨 두면 화면을 옮겨도 범위가 유지되고, 그대로 공유할 수 있다. */
export function useIndustry(): string {
  const params = useSearchParams();
  const v = params.get("ind");
  return v && INDUSTRIES.includes(v) ? v : ALL;
}

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const pick = useIndustry();

  const withPick = (href: string) => (pick === ALL ? href : `${href}?ind=${encodeURIComponent(pick)}`);

  return (
    <div className="shell">
      <nav className="rail" aria-label="화면">
        <div className="brand">
          <b>정책핏 인천</b>
          <span>Policy Fit Incheon</span>
        </div>

        <div className="nav">
          {SCREENS.map((s) => (
            <Link
              key={s.href}
              href={withPick(s.href)}
              className="step"
              aria-current={pathname === s.href ? "page" : undefined}
            >
              <em>{s.n}</em>
              <span>
                <b>{s.title}</b>
                <i>{s.note}</i>
              </span>
            </Link>
          ))}
        </div>

        <div className="railfoot">
          <dl>
            <dt>사업</dt>
            <dd>{WORKS.length}건</dd>
            <dt>계획</dt>
            <dd>{PLANS.length}건</dd>
            <dt>수요신호</dt>
            <dd>{SIGNAL_ROWS}행</dd>
          </dl>
          화면 순서는 조사자 C의 성과축 순위를 그대로 따릅니다.
        </div>
      </nav>

      <main className="main">
        <div className="topbar">
          <span>기준일 {TODAY}</span>
          <span className="spacer" />
          <label className="picker">
            산업
            <select
              value={pick}
              onChange={(e) => {
                const v = e.target.value;
                router.push(v === ALL ? pathname : `${pathname}?ind=${encodeURIComponent(v)}`);
              }}
            >
              <option value={ALL}>{ALL}</option>
              {INDUSTRIES.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </label>
        </div>
        {children}
      </main>
    </div>
  );
}
