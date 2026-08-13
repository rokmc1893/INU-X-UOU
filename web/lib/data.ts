/**
 * 판정 결과를 읽어 화면이 쓸 모양으로 자른다.
 *
 * 판정 자체는 여기서 하지 않는다. 규칙은 `final/` 스트림릿 앱(검증된 engine)이 돌리고,
 * 그 결과를 `scripts/dump_data.py`가 `data/policyfit.json`으로 떨어뜨린다. 이 파일은
 * 고르고 세는 일만 한다 — 숫자를 손으로 적어 두지 않는다.
 */
import raw from "@/data/policyfit.json";

export type Card = {
  policy_id: string;
  name: string;
  is_plan: boolean;
  strategic_industry: string;
  owner_dept: string;
  intervention_type: string;
  budget: string;
  budget_status: string;
  summary: string;
  source_url: string;
  needs_covered: string[];
  name_missing: boolean;
  industry_guess: string;
};

export type Axis = {
  rank: string;
  outcome: string;
  score: string;
  c_status: string;
  key: string | null;
  covered: "full" | "partial" | "none";
  module: string | null;
  gap: string;
};

export type Coverage = {
  signal_id: string;
  industry: string;
  problem_type: string;
  need: string | null;
  grade: string;
  trend: string;
  value: string;
  limit: string;
  source_url: string;
  covers: string[];
  generic: number;
  verdict: "covered" | "uncovered" | "not_a_need" | "admin_task";
};

export type Posture = {
  industry: string;
  posture: string;
  question: string;
  label: string;
  why: string;
  signals: string[];
  measured: string[];
  near_miss: string[];
};

export type Pair = { items: string[]; same_industry: boolean; reason: string; evidence?: string };

export type BudgetRow = {
  pid: string;
  source: string;
  status: string;
  budget_won: number | null;
  dept: string | null;
  detail: string;
  b_said: string | null;
  loose?: boolean;
  note?: string;
};

export type DeptRow = { pid: string; card: string; official: string };

export type Inducement = {
  policy_id: string;
  name: string;
  industry: string;
  evidence: { test: string; ok: boolean; detail: string }[];
};

type Findings = {
  handoff_breaks: Pair[];
  gaps: unknown[];
  overlaps_harmful: Pair[];
  overlaps_intentional: Pair[];
  complements: Pair[];
  budget_confirmed: BudgetRow[];
  budget_unverified: BudgetRow[];
  budget_conflicts: BudgetRow[];
  dept_mismatch: DeptRow[];
};

const db = raw as unknown as {
  today: string;
  cards: Card[];
  findings: Findings;
  postures: Record<string, Posture>;
  coverage: Coverage[];
  axes: Axis[];
  axes_coverage: { total: number; partial: number; none: number };
  industries: string[];
  principle: string;
  need_label: Record<string, string>;
  responsive: string;
  inducing: string;
  b2_count: number;
  inducement: Inducement[];
  counts: { works: number; plans: number };
};

export const TODAY = db.today;
export const INDUSTRIES = db.industries;
export const ALL = "전체";
export const PRINCIPLE = db.principle;
export const NEED_LABEL = db.need_label;
export const RESPONSIVE = db.responsive;
export const INDUCING = db.inducing;
export const AXES = db.axes;
export const AXES_COVERAGE = db.axes_coverage;
export const POSTURES = db.postures;
export const COVERAGE = db.coverage;
export const FINDINGS = db.findings;
export const INDUCEMENT = db.inducement;
export const SIGNAL_ROWS = db.b2_count;

export const CARDS = db.cards;
export const WORKS = CARDS.filter((c) => !c.is_plan);
export const PLANS = CARDS.filter((c) => c.is_plan);

const BY_ID = new Map(CARDS.map((c) => [c.policy_id, c]));

/** 사업명. 못 읽은 카드도 지우지 않는다 — 이름 자리에 ID가 남는다. */
export function nameOf(pid: string): string {
  return BY_ID.get(pid)?.name ?? pid;
}

export function cardOf(pid: string): Card | undefined {
  return BY_ID.get(pid);
}

/**
 * 고른 산업의 범위 안인가.
 * 카드의 산업이 비어 있으면 범위 밖으로 본다 — 비어 있는 것은 "모든 산업"이 아니라 "모른다"다.
 */
export function inScope(card: Card | undefined, pick: string): boolean {
  if (pick === ALL) return true;
  if (!card) return false;
  const v = card.strategic_industry || "";
  return v.includes(pick) || v.includes("공통");
}

export function isIndustry(value: string | null | undefined, pick: string): boolean {
  return pick === ALL || (value ?? "").includes(pick);
}

export const AXIS: Record<string, Axis> = Object.fromEntries(
  AXES.filter((a) => a.key).map((a) => [a.key as string, a]),
);

/** 화면 1 — 예산 축. */
export function budgetView(pick: string) {
  const keep = function <T extends { pid: string }>(rows: T[]): T[] {
    return rows.filter((r) => inScope(BY_ID.get(r.pid), pick));
  };
  const confirmed = keep(FINDINGS.budget_confirmed);
  const unverified = keep(FINDINGS.budget_unverified);
  const conflicts = keep(FINDINGS.budget_conflicts);
  const deptMismatch = keep(FINDINGS.dept_mismatch);
  return {
    confirmed,
    unverified,
    conflicts,
    deptMismatch,
    checked: confirmed.length + unverified.length + conflicts.length,
    works: WORKS.filter((c) => inScope(c, pick)).length,
  };
}

/** 화면 2 — 생태계 축. 산업이 다른 쌍은 접는다 — 실제 부서 협의로 이어지지 않는다. */
export function linkView(pick: string) {
  const keep = (f: Pair) =>
    (f.same_industry ?? true) && f.items.every((p) => inScope(BY_ID.get(p), pick));
  return {
    harmful: FINDINGS.overlaps_harmful.filter(keep),
    intentional: FINDINGS.overlaps_intentional.filter(keep),
    complements: FINDINGS.complements.filter(keep),
    breaks: FINDINGS.handoff_breaks.filter(keep),
    crossIndustry: FINDINGS.handoff_breaks.filter((f) => !(f.same_industry ?? true)).length,
  };
}

/** 화면 3 — 산업 수요와 사업의 대조. */
export function demandView(pick: string) {
  const scoped = COVERAGE.filter((c) => isIndustry(c.industry, pick));
  const real = scoped.filter((c) => c.verdict === "covered" || c.verdict === "uncovered");
  const uncovered = real.filter((c) => c.verdict === "uncovered");
  const thin = real.filter((c) => c.verdict === "covered" && c.covers.length === 1);
  const scopedWorks = WORKS.filter((c) => inScope(c, pick));
  return {
    scoped,
    real,
    uncovered,
    thin,
    admin: scoped.filter((c) => c.verdict === "admin_task"),
    notNeed: scoped.filter((c) => c.verdict === "not_a_need"),
    gapKinds: Array.from(new Set(uncovered.map((c) => c.need as string))).sort(),
    works: scopedWorks.length,
    unreadable: scopedWorks.filter((c) => c.needs_covered.length === 0).length,
  };
}

/** 화면 0의 결론 — 화면 3의 실측을 그대로 끌어온다. 손으로 쓴 숫자를 두지 않는다. */
export function headline(pick: string) {
  const d = demandView(pick);
  const byNeed = new Map<string, { total: number; gap: number }>();
  for (const c of d.real) {
    const k = c.need as string;
    const cur = byNeed.get(k) ?? { total: 0, gap: 0 };
    cur.total += 1;
    if (c.verdict === "uncovered") cur.gap += 1;
    byNeed.set(k, cur);
  }
  const means = new Map<string, number>();
  for (const c of WORKS) for (const n of c.needs_covered) means.set(n, (means.get(n) ?? 0) + 1);
  const ranked = Array.from(means.entries()).sort((a, b) => b[1] - a[1]);
  return {
    matched: d.real.length,
    uncovered: d.uncovered.length,
    gapKinds: d.gapKinds,
    byNeed: Array.from(byNeed.entries()).sort((a, b) => a[0].localeCompare(b[0], "ko")),
    means: ranked,
    crowded: ranked.slice(0, 2).map(([n]) => n),
  };
}

/** 화면 4 — 먼저 할 것. 판정에서 그대로 끌어온다. */
export function actions(pick: string) {
  const b = budgetView(pick);
  const l = linkView(pick);
  const d = demandView(pick);
  const todo: { title: string; why: string; where: string; href: string }[] = [];
  if (b.deptMismatch.length)
    todo.push({
      title: "소관 부서를 고치고 협의처를 바꾼다",
      why: `${b.deptMismatch.length}건의 사업이 공식 예산 원장과 다른 과로 적혀 있습니다. 공문을 잘못 보내면 회신이 오지 않습니다.`,
      where: "예산이 새는가",
      href: "/budget",
    });
  if (d.uncovered.length)
    todo.push({
      title: `「${d.gapKinds.join(", ")}」 수요를 덮을 사업을 검토한다`,
      why: `${d.uncovered.length}건의 산업 수요에 대응하는 사업이 없습니다. 먼저 수요조사서가 필요하고, 본예산은 마감됐으니 1차 추경이나 공모가 빠릅니다.`,
      where: "산업 수요와 맞는가",
      href: "/demand",
    });
  if (l.harmful.length)
    todo.push({
      title: `중복 후보 ${l.harmful.length}건을 부서 협의에 올린다`,
      why: "받는 사람·주는 것·직무가 모두 같습니다. 확정이 아니라 후보입니다.",
      where: "사업끼리 이어지는가",
      href: "/links",
    });
  if (d.thin.length)
    todo.push({
      title: `사업 1건에만 기대는 수요 ${d.thin.length}건을 표시한다`,
      why: "그 사업이 멈추면 바로 공백이 됩니다. 예산 심의 때 근거로 씁니다.",
      where: "산업 수요와 맞는가",
      href: "/demand",
    });
  return {
    todo,
    induced: INDUCEMENT.filter((i) => isIndustry(i.industry, pick)),
    unnamed: CARDS.filter((c) => c.name_missing),
  };
}

export const SCREENS = [
  { n: "0", href: "/", title: "무엇을 보는가", note: "범위와 한계" },
  { n: "1", href: "/budget", title: "예산이 새는가", note: "성과축 1순위" },
  { n: "2", href: "/links", title: "사업끼리 이어지는가", note: "성과축 2순위" },
  { n: "3", href: "/demand", title: "산업 수요와 맞는가", note: "성과축 3순위" },
  { n: "4", href: "/actions", title: "조치 제안", note: "행동으로" },
];
