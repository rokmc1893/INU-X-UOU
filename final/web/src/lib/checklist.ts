/* 체크리스트 — 판정 결과를 「지금 이렇다 → 하고 나면 이렇게 된다」로 옮긴다.
 *
 * 기대효과는 **직접효과만** 쓴다. 결정로그 D-002에서 성과 귀속을 넷으로 갈라 놓고
 * 뒤 두 단계(사업성과·지역성과)는 이 도구에 귀속하지 않기로 했다.
 *   쓸 수 있다 — "공문을 잘못 보내지 않는다", "중복이라고 잘못 반려당하지 않는다"
 *   쓸 수 없다 — "취업률이 오른다", "매출이 는다"
 */
import type { Review } from "./api";

export type Item = {
  key: string;
  title: string;
  /** 지금 자료가 말하는 상태 */
  now: string;
  /** 이걸 하고 나면 달라지는 것 — 직접효과만 */
  then: string;
  /** 손댈 것이 있는가. false면 확인만 하고 넘어가는 항목 */
  action: boolean;
  /** 근거를 어디서 보나 */
  section: "budget" | "overlap" | "gap" | "draft";
  /** 몇 건인지. **무엇의 건수인지 단위를 함께 적는다** —
      항목마다 세는 대상이 달라서(사업이냐 자료냐) 숫자만 두면 뜻이 흐려진다. */
  count?: number;
  unit?: string;
};

export function buildChecklist(r: Review): Item[] {
  const out: Item[] = [];
  const gaps = r.needs.filter((n) => n.verdict === "uncovered");
  const gapKinds = [...new Set(gaps.map((g) => g.plain))];
  const thin = r.needs.filter((n) => n.verdict === "covered" && n.covers.length === 1);
  const mine = r.needs.filter((n) => n.mine);

  if (r.budget.mismatch) {
    out.push({
      key: "dept", section: "budget", action: true, title: "공문 보낼 과를 바로잡는다",
      now: `사업 문서에는 ${r.budget.mismatch.card}, 공식 예산 장부에는 ${r.budget.mismatch.official}.`,
      then: "엉뚱한 과로 공문이 가서 회신을 못 받는 일이 없습니다.",
    });
  } else if (r.budget.empty) {
    out.push({
      key: "budget", section: "budget", action: true, title: "예산 장부와 대조한다",
      now: r.budget.empty.why,
      then: "금액과 소관 과를 확정해 협의처를 정확히 잡을 수 있습니다.",
    });
  } else if (r.budget.won) {
    out.push({
      key: "budget-ok", section: "budget", action: false,
      title: "예산은 장부와 맞습니다",
      now: `공식 장부 ${r.budget.won.toLocaleString()}원 · 소관 ${r.budget.official_dept ?? "확인"}.`,
      then: "예산 심의에서 금액 근거를 바로 댈 수 있습니다.",
    });
  }

  if (r.overlaps.harmful.length) {
    out.push({
      key: "dup", section: "overlap", action: true,
      count: r.overlaps.harmful.length, unit: "사업",
      title: "겹치는 사업과 조정을 협의한다",
      now: `${r.overlaps.harmful[0].name} 등 ${r.overlaps.harmful.length}건과 받는 사람·주는 것·직무가 같습니다.`,
      then: `협의 단계에서 「${r.duplicateRule}」로 반려되는 것을 미리 막습니다.`,
    });
  } else if (r.overlaps.empty) {
    out.push({
      key: "dup-none", section: "overlap",
      action: r.overlaps.empty.meaning === "unknown",
      title: r.overlaps.empty.meaning === "unknown"
        ? "겹치는지 아직 가릴 수 없습니다" : "겹치는 사업은 없습니다",
      now: r.overlaps.empty.why,
      then: r.overlaps.empty.meaning === "unknown"
        ? "사업 원문을 넣으면 겹침 여부를 가릴 수 있습니다."
        : "검토서에 「중복 없음」을 근거와 함께 적을 수 있습니다.",
    });
  }

  const notDup = r.overlaps.intentional.length + r.overlaps.complement.length;
  if (notDup) {
    out.push({
      key: "notdup", section: "overlap", action: true, count: notDup, unit: "사업",
      title: "겹쳐 보이지만 아닌 것을 검토서에 적는다",
      now: `${notDup}건은 주는 것이 같아도 받는 사람이나 수단이 다릅니다.`,
      then: "중복이라는 이유로 잘못 반려당하는 것을 막아 줍니다.",
    });
  }

  // 연계 끊김은 관계도에만 있고 할 일에는 없었다. 화면이 짚어 놓고 「그래서 뭘 하라는
  // 건가」에 답을 안 한 셈이다. 이어 줄 절차를 만들지는 담당자가 정할 일이므로
  // 「만들지 **판단한다**」로 둔다 — 우리가 이으라고 정하지 않는다.
  if (r.handoffs.items.length) {
    out.push({
      key: "handoff", section: "overlap", action: true,
      count: r.handoffs.items.length, unit: "쌍",
      title: "이어 줄 절차를 만들지 판단한다",
      now: `${r.handoffs.items.length}쌍은 앞 사업을 마친 사람이 뒤 사업으로 넘어가는 `
        + `절차가 두 사업 문서 어디에도 없습니다.`,
      then: "이어 줄 곳을 개편안에 넣거나, 넣지 않는 이유를 검토서에 적을 수 있습니다.",
    });
  }

  if (gaps.length) {
    out.push({
      key: "gap", section: "gap", action: true, count: gaps.length, unit: "자료",
      // 칸 이름 뒤에 조사를 붙이면 「공간·장비를」·「기업 자금을」처럼 칸마다 달라진다.
      // 「칸을」·「에 관한」으로 받아 이름이 무엇이든 문장이 성립하게 둔다.
      title: `비어 있는 「${gapKinds.join("·")}」 칸을 채울지 판단한다`,
      now: `${gapKinds.join("·")}에 관한 자료가 ${gaps.length}건 있는데 해주는 사업이 없습니다.`,
      then: "이 사업을 넓힐지 새로 만들지, 근거를 갖고 정할 수 있습니다.",
    });
  }

  if (thin.length) {
    out.push({
      key: "thin", section: "gap", action: true, count: thin.length, unit: "자료",
      title: "사업 하나에만 걸린 것을 표시한다",
      now: `${[...new Set(thin.map((t) => t.plain))].join("·")}에 관한 자료 ${thin.length}건이 `
        + `사업 하나에 걸려 있습니다.`,
      then: "그 사업이 멈추면 바로 빈칸이 된다는 것을 예산 심의에서 근거로 씁니다.",
    });
  }

  if (mine.length) {
    out.push({
      key: "mine", section: "gap", action: false, count: mine.length, unit: "자료",
      title: "이 사업이 맡고 있는 자리를 확인합니다",
      now: `${[...new Set(mine.map((m) => m.plain))].join("·")}에 관한 자료 ${mine.length}건을 `
        + `이 사업이 채우고 있습니다.`,
      then: "개편안에서 무엇을 유지해야 하는지 분명해집니다.",
    });
  }

  out.push({
    key: "draft", section: "draft", action: true,
    title: "검토서 초안을 받아 결재문서에 붙인다",
    now: "판정과 미확인 항목이 원문 링크와 함께 정리돼 있습니다.",
    then: "검토자가 근거를 직접 눌러 확인할 수 있습니다.",
  });

  return out;
}
