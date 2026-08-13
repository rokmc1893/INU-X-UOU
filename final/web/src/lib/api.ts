/* 판정 API 클라이언트.
 *
 * 판정은 전부 파이썬 쪽에서 한다. 여기서는 부르고 받을 뿐이며, 규칙을 이쪽으로 옮기지
 * 않는다 — 옮기면 테스트 93건이 지켜 주던 것들(널을 다름으로 읽지 않기, 공급 지표를
 * 수요로 세지 않기)이 다시 깨진다.
 */
export const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8600";

export type Business = {
  id: string; name: string; industry: string | null;
  status: string | null; means: string | null; url: string | null;
  uploaded: boolean;
  /** 그 산업에서 비어 있는 것 — 고르기 전에 무엇이 걸려 있는지 보이게 */
  gaps?: string[];
};

/** 빈칸의 뜻. ok = 맞춰 봤고 걸리는 게 없다 / unknown = 아직 모른다 */
export type Empty = {
  kind: string; meaning: "ok" | "unknown"; why: string; fix: string | null;
} | null;

export type Pair = { id: string; name: string; url: string | null; reason: string };

export type NeedRow = {
  need: string; plain: string; label: string; hint: string;
  verdict: "covered" | "uncovered";
  signal_id: string; problem_type: string; value: string; grade: string;
  trend: string; limit: string; source_url: string;
  covers: string[]; coverNames: (string | null)[]; mine: boolean;
};

export type Review = {
  card: Business & {
    owner: string | null; budget: string | null;
    /** 원문에 값이 아예 없던 항목 */
    missing: string[];
    /** 값은 있으나 뒷받침할 원문 문장을 못 찾은 항목 */
    noQuote: string[];
  };
  budget: {
    status: string | null; won: number | null; official_dept: string | null;
    /** 예산서에 적힌 사업 항목명 */
    line: string | null;
    /** 어떻게 확인했는지 */
    note: string | null;
    /** 어느 원장에서 왔는지 */
    ledger: string | null;
    mismatch: { pid: string; card: string; official: string } | null;
    empty: Empty;
  };
  overlaps: { harmful: Pair[]; intentional: Pair[]; complement: Pair[]; empty: Empty };
  handoffs: { items: Pair[]; empty: Empty };
  needs: NeedRow[];
  posture: { posture: string; question: string; why: string } | null;
  consult: {
    team: string; bureau: string; decision_right: string;
    contact: string; source_url: string;
  }[];
  reviewers: { who: string; why: string }[];
  caveat: string;
  windows: {
    open: { track: Record<string, string>; always: boolean }[];
    soon: { track: Record<string, string>; opens: string; months_away: number }[];
  };
  stage: { no: number; name: string; inputs: string[]; reject: string[] };
  duplicateRule: string;
};

export type Overview = {
  today: string;
  ledger: { works: number; plans: number; signals: number; uploaded: number };
  computed: { edges: number; findings: number; needs: number; gaps: number };
  needs: { need: string; plain: string; label: string; hint: string;
           covered: number; total: number }[];
  means: { need: string; plain: string; count: number }[];
  axes: { rank: string; outcome: string; covered: string; module: string | null; gap: string }[];
};

export type SourceItem = {
  key: string; name: string; status: string; status_label: string;
  link: string; direct: boolean; terms: string[];
  gives: string[]; what: string; note: string;
};

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export const getBusinesses = () => get<{ total: number; items: Business[] }>("/api/businesses");
export const getOverview = () => get<Overview>("/api/overview");
export const getReview = (id: string) => get<Review>(`/api/review/${id}`);
export const getDraft = (id: string, track?: string) =>
  get<{ filename: string; markdown: string }>(
    `/api/draft/${id}${track ? `?track=${encodeURIComponent(track)}` : ""}`);
export const getSources = (industry?: string, need?: string) =>
  get<{ checkedOn: string; summary: Record<string, number>; items: SourceItem[]; claim: string | null }>(
    `/api/sources?industry=${encodeURIComponent(industry ?? "")}&need=${encodeURIComponent(need ?? "")}`);

export async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.detail ?? "실패했습니다");
  return j;
}

export async function postFile<T>(path: string, file: File, industry?: string): Promise<T> {
  const fd = new FormData();
  fd.append("file", file);
  if (industry) fd.append("industry", industry);
  const r = await fetch(`${API}${path}`, { method: "POST", body: fd });
  const j = await r.json();
  if (!r.ok) throw new Error(j.detail ?? "실패했습니다");
  return j;
}
