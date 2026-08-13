"use client";

/* 공통 껍데기 — 머리에 다섯 갈래를 늘 띄우고, 맡은 사업을 주소에 싣는다.
 *
 * 주소에 실어 두면 페이지를 옮겨도 맡은 사업이 유지되고, 시연 때 링크 하나로
 * 그 자리를 바로 열 수 있다 (`/budget?사업=IC-BIO-002`).
 */
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getBusinesses, getReview, type Business, type Review } from "@/lib/api";
import { Logo } from "./Logo";

export const NAV = [
  { href: "/todo", label: "지금 할 일", no: "" },
  { href: "/budget", label: "예산이 제대로 붙어 있나", no: "1" },
  { href: "/links", label: "사업끼리 겹치거나 끊기지 않았나", no: "2" },
  { href: "/needs", label: "필요한 걸 해주고 있나", no: "3" },
  { href: "/action", label: "조치 제안", no: "4" },
];

export const DEMO = "IC-BIO-002";

/** 주소에서 맡은 사업을 읽는다. */
export function usePid() {
  const sp = useSearchParams();
  return sp.get("사업") || DEMO;
}

/** 맡은 사업 하나의 판정 결과. */
export function useReview() {
  const pid = usePid();
  const [r, setR] = useState<Review | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    setR(null); setErr(null);
    getReview(pid).then(setR).catch((e) => setErr(String(e)));
  }, [pid]);
  return { pid, r, err };
}

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const bare = path === "/";   // 랜딩에서는 머리를 감춘다
  const router = useRouter();
  const pid = usePid();
  const [list, setList] = useState<Business[]>([]);

  useEffect(() => { getBusinesses().then((d) => setList(d.items)).catch(() => {}); }, []);

  if (bare) return <>{children}</>;

  return (
    <div className="min-h-screen">
      <header className="border-b border-rule bg-paper">
        <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-3 px-6 py-3">
          <Link href={{ pathname: "/todo", query: { 사업: pid } }} className="shrink-0">
            <Logo />
          </Link>
          <label className="flex min-w-0 flex-1 items-center justify-end gap-2 text-[13px]">
            <span className="shrink-0 text-muted">맡은 사업</span>
            <select
              value={pid}
              onChange={(e) =>
                router.push(`${path}?${new URLSearchParams({ 사업: e.target.value })}`)}
              className="max-w-[430px] min-w-0 flex-1 rounded-md border border-rule bg-paper px-3 py-1.5 text-[13px]"
            >
              {list.map((b) => (
                <option key={b.id} value={b.id}>[{b.industry}] {b.name}</option>
              ))}
            </select>
          </label>
        </div>
        <nav className="mx-auto max-w-[1180px] px-6">
          <ul className="-mb-px flex flex-wrap gap-1">
            {NAV.map((n) => {
              const on = path === n.href;
              return (
                <li key={n.href}>
                  <Link
                    href={{ pathname: n.href, query: { 사업: pid } }}
                    className={`inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-[13px] ${
                      on ? "border-pen font-semibold text-pen" : "border-transparent text-muted hover:text-ink"
                    }`}
                  >
                    {n.no && (
                      <span className={`grid h-[18px] w-[18px] place-items-center rounded-[3px] text-[11px] font-bold ${
                        on ? "bg-pen text-white" : "bg-shell text-faint"}`}>{n.no}</span>
                    )}
                    {n.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </header>
      {/* key를 길로 두면 페이지를 옮길 때마다 새로 그려져 애니메이션이 다시 돈다 */}
      <main key={path} className="pagefade mx-auto max-w-[1180px] px-6 py-7">
        {children}
      </main>
    </div>
  );
}

/** 페이지 머리 — 어디에 있고 무엇을 보는 중인지. */
export function PageHead({ r, title, lead }: {
  r: Review | null; title: string; lead: string;
}) {
  return (
    <div className="mb-5 border-b border-rule pb-4">
      <h1 className="text-[23px] leading-tight">{title}</h1>
      <p className="mt-1 text-[13px] text-muted">{lead}</p>
      {r && (
        <p className="mt-2 text-[12px] text-faint">
          검토 대상 <b className="text-ink">{r.card.name}</b> · {r.card.industry} ·
          행정 절차 {r.stage.no}단계 「{r.stage.name}」
        </p>
      )}
    </div>
  );
}

export function Loading({ err }: { err?: string | null }) {
  if (err) return (
    <p className="rounded-md border border-dashed border-rule bg-shell p-4 text-[13px]">
      판정을 불러오지 못했습니다. 판정 서버가 떠 있는지 확인해 주세요.
      <span className="mt-1 block text-[12px] text-faint">{err}</span>
    </p>
  );
  return <p className="text-[13px] text-muted">불러오는 중…</p>;
}
