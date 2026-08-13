/* 화면 조각.
 *
 * 화면 전체를 관통하는 규칙: 실선 = 확인함 / 점선 = 모른다.
 * 이 규칙이 무너지면 「모른다」가 「괜찮다」로 읽힌다.
 */
import type { Empty } from "@/lib/api";

export function Src({ url, label = "원문" }: { url?: string | null; label?: string }) {
  if (url && url.startsWith("http"))
    return (
      <a className="src" href={url} target="_blank" rel="noopener noreferrer">{label}</a>
    );
  return <span className="src-none" title="원문 주소가 원장에 없습니다">주소 없음</span>;
}

export function Tag({ tone, children }: {
  tone: "pen" | "gap" | "hold" | "flat"; children: React.ReactNode;
}) {
  const map = {
    pen: "text-pen border-[#c4d4f2] bg-pen-soft",
    gap: "text-gap border-[#eec4bd] bg-gap-soft",
    hold: "text-hold border-[#e3d5a8] bg-hold-soft border-dashed",
    flat: "text-muted border-rule bg-white",
  } as const;
  return (
    <span className={`inline-block shrink-0 rounded-[3px] border px-1.5 text-[11px] font-semibold leading-5 ${map[tone]}`}>
      {children}
    </span>
  );
}

/** 빈칸 상자 — 왜 비었는지 한 줄, 어떻게 채우는지 한 줄. */
export function Void({ r }: { r: Empty }) {
  if (!r) return null;
  const unknown = r.meaning === "unknown";
  return (
    <div className={`rounded-md border p-3 ${unknown
      ? "border-dashed border-rule bg-shell" : "border-[#c4d4f2] bg-pen-soft"}`}>
      <Tag tone={unknown ? "hold" : "pen"}>{r.kind}</Tag>
      <p className="mt-1.5 text-[13px] leading-relaxed text-ink">{r.why}</p>
      {r.fix && <p className="mt-1 text-[12px] text-muted">→ {r.fix}</p>}
    </div>
  );
}

/** 채워짐과 빈칸을 같은 자리에서 견주는 막대. */
export function Slots({ filled, empty }: { filled: number; empty: boolean }) {
  if (empty) return <div className="flex"><span className="slot-empty" /></div>;
  return (
    <div className="flex gap-[3px]">
      {Array.from({ length: Math.min(filled, 14) }).map((_, i) => (
        <span key={i} className="slot" />
      ))}
    </div>
  );
}
