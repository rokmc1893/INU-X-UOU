/* 로고 — 두 조각이 맞물리는 모양.
 *
 * 이 도구가 하는 일이 그것이다. 왼쪽은 산업이 필요하다고 말한 것, 오른쪽은 시가 하는 사업.
 * 둘이 맞물리는 자리가 겹쳐진 가운데이고, 어긋나면 그 자리가 벌어진다.
 * 색은 화면 전체 규칙을 그대로 쓴다 — 파랑은 맞은 곳, 붉은빛은 벌어진 곳.
 */
export function Mark({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" aria-hidden
         style={{ display: "block", flexShrink: 0 }}>
      <rect x="1.5" y="6" width="15" height="16" rx="4"
            fill="none" stroke="#1f5fd0" strokeWidth="2" />
      <rect x="11.5" y="6" width="15" height="16" rx="4"
            fill="none" stroke="#c0392b" strokeWidth="2" />
      <path d="M11.5 6h5v16h-5z" fill="#1f5fd0" opacity="0.16" />
      <path d="M14 11.5v5" stroke="#16191d" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ size = 26, sub }: { size?: number; sub?: string }) {
  return (
    <span className="flex items-center gap-2">
      <Mark size={size} />
      <span className="flex items-baseline gap-2">
        <b className="text-[19px] font-bold tracking-[-0.03em]">정책핏</b>
        <span className="text-[13px] text-muted">인천</span>
        {sub && <span className="text-[12px] text-faint">{sub}</span>}
      </span>
    </span>
  );
}
