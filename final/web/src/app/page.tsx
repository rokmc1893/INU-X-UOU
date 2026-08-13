"use client";

/* 랜딩 — 맡은 사업을 고르고 들어간다.
 *
 * 실제 사례에서 담당자는 산업을 고르는 것이 아니라 위원회 안건이나 내부 지시로
 * **사업을 배정받아** 시작한다. 그래서 첫 화면이 사업 고르기다.
 * 고를 자리가 첫 화면에 보여야 하므로 소개는 짧게 두고 고르기를 바로 옆에 놓는다.
 *
 * 고르고 나면 판정이 도는 동안 무엇을 하고 있는지 보인다. 미리 짜 둔 답을 꺼내는 것이
 * 아니라 그때 계산한다는 것을 보이려는 것이고, 실제로 그 순서대로 돈다.
 */
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { API, getBusinesses, getReview, type Business } from "@/lib/api";
import Live from "@/components/Live";
import { Logo, Mark } from "@/components/Logo";

/* 판정 서버가 실제로 밟는 차례. api/main.py 의 _state() 와 같은 순서다. */
const STEPS = [
  "사업 원장과 조사 자료 읽는 중",
  "사업끼리 관계 잇는 중",
  "겹치는 곳과 끊긴 곳 가리는 중",
  "필요하다고 말한 것과 맞춰 보는 중",
];

export default function Landing() {
  const router = useRouter();
  const [list, setList] = useState<Business[]>([]);
  const [q, setQ] = useState("");
  const [pid, setPid] = useState<string | null>(null);
  const [going, setGoing] = useState(false);
  const [step, setStep] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getBusinesses().then((d) => setList(d.items))
      .catch(() => setErr("판정 서버에 닿지 않습니다"));
  }, []);

  const groups = useMemo(() => {
    const hit = list.filter((b) =>
      !q || b.name.includes(q) || (b.industry ?? "").includes(q));
    const m = new Map<string, Business[]>();
    for (const b of hit) {
      const k = b.industry ?? "산업 미상";
      m.set(k, [...(m.get(k) ?? []), b]);
    }
    return [...m];
  }, [list, q]);

  async function start(id: string) {
    setPid(id); setGoing(true); setStep(0);
    const tick = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 420);
    try {
      await getReview(id);            // 실제로 판정을 돌려 본다
      clearInterval(tick);
      setStep(STEPS.length);
      setTimeout(() => router.push(`/todo?${new URLSearchParams({ 사업: id })}`), 380);
    } catch (e) {
      clearInterval(tick);
      setGoing(false);
      setErr(e instanceof Error ? e.message : "판정을 불러오지 못했습니다");
    }
  }

  if (going) return <Booting step={step} name={list.find((b) => b.id === pid)?.name ?? ""} />;

  return (
    <main className="mx-auto max-w-[1180px] px-6 py-7">
      <div className="rise"><Logo /></div>

      <header className="mt-7">
        <p className="rise text-[13px] font-semibold tracking-wide text-pen"
           style={{ animationDelay: ".05s" }}>
          인천광역시 · 6대 전략산업
        </p>
        <h1 className="rise mt-2 max-w-[25ch] text-[34px] leading-[1.28] tracking-tight sm:text-[40px]"
            style={{ animationDelay: ".1s" }}>
          맡으신 사업이 <span className="whitespace-nowrap text-pen">필요하다고 말한 것</span>과{" "}
          <br className="hidden sm:inline" />맞는지 확인합니다
        </h1>
        <p className="rise mt-3.5 max-w-[600px] text-[15px] leading-[1.7] text-muted"
           style={{ animationDelay: ".15s" }}>
          예산 장부와 어긋난 곳, 다른 사업과 겹치는 곳, 현장이 아쉬워하는데 아무도
          안 하고 있는 곳을 <b className="text-ink">근거와 함께</b> 짚어
          결재문서에 붙일 검토서 초안까지 만들어 드립니다.
        </p>
      </header>

      <div className="mt-7 grid items-start gap-4 lg:grid-cols-[1.15fr_1fr]">
        <section className="rise rounded-xl border border-rule bg-paper p-5"
                 style={{ animationDelay: ".2s" }}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-[19px]">검토를 맡으실 사업을 고르시오</h2>
              <p className="mt-0.5 text-[12px] text-muted">
                위원회 안건이나 내부 지시로 배정받은 사업입니다
              </p>
            </div>
            <input
              value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="사업명·산업으로 찾기"
              className="w-[190px] rounded-md border border-rule px-3 py-1.5 text-[13px]"
            />
          </div>

          {err && (
            <p className="mt-3 rounded-md border border-dashed border-rule bg-shell p-3 text-[13px]">
              {err}
              <span className="mt-1 block text-[12px] text-faint">
                판정 서버를 켜 주세요 — <code>{API}</code>
              </span>
            </p>
          )}

          <div className="mt-4 max-h-[380px] space-y-4 overflow-y-auto pr-1">
            {groups.map(([ind, items]) => (
              <div key={ind}>
                <p className="mb-1.5 text-[12px] font-semibold text-faint">
                  {ind} <span className="font-normal">{items.length}건</span>
                </p>
                <ul className="space-y-1.5">
                  {items.map((b) => (
                    <li key={b.id}>
                      <button
                        onClick={() => start(b.id)}
                        className="pick w-full rounded-lg border border-rule px-3.5 py-2.5 text-left hover:border-pen hover:bg-pen-soft"
                      >
                        <span className="block text-[14px] font-medium leading-snug">
                          {b.name}
                        </span>
                        <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] text-muted">
                          <span>{b.status ?? "상태 미상"}</span>
                          <span>·</span>
                          <span>{b.means ?? "해주는 것이 원문에 안 적힘"}</span>
                          {b.gaps && b.gaps.length > 0 && (
                            <span className="rounded-[3px] border border-[#eec4bd] bg-gap-soft px-1.5 font-semibold text-gap">
                              {b.gaps.join("·")} 비어 있음
                            </span>
                          )}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {!groups.length && !err && (
              <p className="text-[13px] text-muted">찾으시는 사업이 없습니다.</p>
            )}
          </div>
        </section>

        <div className="rise" style={{ animationDelay: ".26s" }}>
          <Live />
        </div>
      </div>

      <ul className="rise mt-6 flex flex-wrap gap-x-7 gap-y-2 border-t border-rule pt-4 text-[13px] text-muted"
          style={{ animationDelay: ".32s" }}>
        <li>판정은 모두 <b className="text-ink">후보</b>입니다. 확정은 부서 협의로 합니다.</li>
        <li>고르는 일에 AI는 관여하지 않습니다.</li>
        <li>원문에 없는 값은 채우지 않고 비워 둡니다.</li>
      </ul>
    </main>
  );
}

/* 판정이 도는 동안 — 무엇을 하고 있는지 보인다. */
function Booting({ step, name }: { step: number; name: string }) {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="w-full max-w-[430px]">
        <div className="mb-7 flex justify-center"><Mark size={34} /></div>
        <p className="text-[13px] text-muted">검토 대상</p>
        <p className="mt-1 text-[19px] font-bold leading-snug">{name}</p>
        <ul className="mt-6 space-y-2.5">
          {STEPS.map((s, i) => {
            const done = i < step;
            const now = i === step;
            return (
              <li key={s} className="flex items-center gap-2.5 text-[14px]">
                <span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border text-[11px] ${
                  done ? "border-pen bg-pen text-white"
                    : now ? "border-pen text-pen" : "border-rule text-faint"}`}>
                  {done ? "✓" : i + 1}
                </span>
                <span className={done ? "text-muted" : now ? "font-semibold" : "text-faint"}>
                  {s}
                </span>
                {now && (
                  <span className="ml-auto h-1.5 w-1.5 animate-ping rounded-full bg-pen" />
                )}
              </li>
            );
          })}
        </ul>
        <div className="mt-6 h-1 w-full overflow-hidden rounded-full bg-rule">
          <div className="h-full bg-pen transition-[width] duration-300"
               style={{ width: `${(step / STEPS.length) * 100}%` }} />
        </div>
        <p className="mt-3 text-[12px] text-faint">
          미리 만들어 둔 답을 꺼내는 것이 아니라 지금 계산합니다.
        </p>
      </div>
    </main>
  );
}
