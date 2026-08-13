// 정책핏 인천 — 7분 발표 데크 (8장). node build_deck.js
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625

const INK = "1A2B3C", HARBOR = "0E5A8A", CUT = "C75000", GREEN = "1E7F4F",
      RED = "B42318", GRAY = "8A8F98", PAPER = "FFFFFF", ICE = "E8F0F6";
const F = "Malgun Gothic";

function title(s, t, sub) {
  s.addText(t, { x: 0.5, y: 0.32, w: 9.0, h: 0.6, fontSize: 26, bold: true,
                 color: INK, fontFace: F, margin: 0 });
  if (sub) s.addText(sub, { x: 0.5, y: 0.88, w: 9.0, h: 0.35, fontSize: 13,
                            color: GRAY, fontFace: F, margin: 0 });
}
// 모티프: 결재란 사슬 (stage 6칸 + 절단선)
function chain(s, y, opts = {}) {
  const stages = ["교육훈련", "일경험", "구직지원", "매칭", "채용지원", "정착"];
  const bw = 1.28, gap = 0.22, x0 = 0.5, h = 0.52;
  stages.forEach((st, i) => {
    const x = x0 + i * (bw + gap);
    const empty = opts.emptyIdx && opts.emptyIdx.includes(i);
    s.addShape("rect", { x, y, w: bw, h, fill: { color: empty ? PAPER : PAPER },
      line: { color: empty ? GRAY : INK, width: 1.2, dashType: empty ? "dash" : "solid" } });
    s.addShape("rect", { x, y, w: bw, h: 0.06, fill: { color: i === 0 && opts.anchor ? CUT : HARBOR },
      line: { color: i === 0 && opts.anchor ? CUT : HARBOR, width: 0 } });
    s.addText(st, { x, y: y + 0.08, w: bw, h: 0.36, fontSize: 11.5, bold: true, align: "center",
                    color: empty ? GRAY : INK, fontFace: F, margin: 0 });
    if (i < 5) s.addText("✂", { x: x + bw - 0.02, y: y + 0.1, w: gap + 0.06, h: 0.3,
      fontSize: 12, bold: true, color: CUT, align: "center", fontFace: F, margin: 0 });
  });
}

// ── 1. 표지 (다크) ──
let s = pres.addSlide();
s.background = { color: INK };
s.addText("정책핏 인천", { x: 0.7, y: 1.5, w: 8.6, h: 1.0, fontSize: 48, bold: true,
                           color: PAPER, fontFace: F, margin: 0 });
s.addText("유사·중복 검토를 전화 협의 없이 한 화면에서\n— 정책 그래프가 후보를 찾고, 판단은 사람이 합니다", {
  x: 0.7, y: 2.6, w: 8.6, h: 0.9, fontSize: 18, color: "CADCFC", fontFace: F, margin: 0 });
// 사슬 모티프 (다크 버전)
["교육훈련","일경험","구직지원","매칭","채용지원","정착"].forEach((st,i)=>{
  const x = 0.7 + i * 1.45;
  s.addShape("rect", { x, y: 3.9, w: 1.25, h: 0.44, fill: { color: INK },
                       line: { color: "CADCFC", width: 1 } });
  s.addText(st, { x, y: 3.94, w: 1.25, h: 0.36, fontSize: 10.5, align: "center",
                  color: "CADCFC", fontFace: F, margin: 0 });
  if (i<5) s.addText("✂", { x: x+1.24, y: 3.95, w: 0.22, h: 0.3, fontSize: 11,
                            color: CUT, align: "center", bold: true, fontFace: F, margin: 0 });
});
s.addText("인천대 × 울산대 초광역 해커톤 · 주제 I3 · 2026-08-14", {
  x: 0.7, y: 4.9, w: 8.6, h: 0.35, fontSize: 12, color: GRAY, fontFace: F, margin: 0 });

// ── 2. 문제 발단 ──
s = pres.addSlide(); s.background = { color: PAPER };
title(s, "청년 유출은 앱 하나로 풀리는 문제가 아니다", "확인해 보니, 통념과 데이터가 달랐습니다");
s.addShape("roundRect", { x: 0.5, y: 1.4, w: 4.3, h: 2.5, rectRadius: 0.06,
                          fill: { color: ICE }, line: { color: HARBOR, width: 1 } });
s.addText("통념", { x: 0.8, y: 1.6, w: 3.7, h: 0.4, fontSize: 15, bold: true, color: HARBOR, fontFace: F, margin: 0 });
s.addText([
  { text: "\"청년이 인천을 떠난다\"", options: { fontSize: 16, bold: true, breakLine: true } },
  { text: "→ 매칭 플랫폼을 만들면 될까?", options: { fontSize: 13, color: GRAY } },
], { x: 0.8, y: 2.1, w: 3.7, h: 1.5, color: INK, fontFace: F, margin: 0 });
s.addShape("roundRect", { x: 5.2, y: 1.4, w: 4.3, h: 2.5, rectRadius: 0.06,
                          fill: { color: PAPER }, line: { color: CUT, width: 1.5 } });
s.addText("확인된 사실", { x: 5.5, y: 1.6, w: 3.7, h: 0.4, fontSize: 15, bold: true, color: CUT, fontFace: F, margin: 0 });
s.addText([
  { text: "2025 인천 순유입률 1.1% — 전국 1위", options: { fontSize: 15, bold: true, breakLine: true } },
  { text: "인천은 모든 연령대에서 순유입 (주민등록 주소 기준)", options: { fontSize: 12, color: GRAY, breakLine: true } },
  { text: "청년 32.8%는 직장이 관외에", options: { fontSize: 15, bold: true, breakLine: true } },
  { text: "역외취업 사유 1위: \"원하는 직무의 일자리 부재\" 33.6%", options: { fontSize: 12, color: GRAY } },
], { x: 5.5, y: 2.05, w: 3.7, h: 1.75, color: INK, fontFace: F, margin: 0 });
s.addText("출처: 통계청 2025 국내인구이동통계(A급, E005) · 인천연구원 MZ-X세대 일자리 전략 연구, 청년 2,000명 실태조사(A급, E006)", {
  x: 0.5, y: 4.15, w: 9.0, h: 0.3, fontSize: 10.5, color: GRAY, fontFace: F, margin: 0 });
s.addText("그래서 우리는 \"바꿀 수 없는 것\" 대신 \"바꿀 수 있는 것\"을 찾았습니다 →", {
  x: 0.5, y: 4.7, w: 9.0, h: 0.4, fontSize: 15, bold: true, color: INK, fontFace: F, margin: 0 });

// ── 3. 재정의 ──
s = pres.addSlide(); s.background = { color: PAPER };
title(s, "바꿀 수 있는 것: 정책 결정의 품질", "I3의 두 축 중 '산업·정책 연계 부족'을 직접 타겟");
const steps = [["정책핏의 직접효과", "근거 완전성 · 검토속도 · 누락탐지", HARBOR, "플랫폼 귀속: 높음"],
               ["행정 중간효과", "사업 보완·연결·통합, 예산조정", HARBOR, "중간"],
               ["정책의 사업성과", "기업 충원 · 취업·임금·근속", GRAY, "귀속하지 않음"],
               ["지역 장기성과", "산업생태계 · 청년 정착", GRAY, "귀속하지 않음"]];
steps.forEach((st, i) => {
  const x = 0.5 + i * 2.35;
  s.addShape("roundRect", { x, y: 1.45, w: 2.15, h: 1.55, rectRadius: 0.05,
    fill: { color: i < 2 ? ICE : PAPER }, line: { color: st[2], width: 1.2 } });
  s.addText(st[0], { x: x + 0.12, y: 1.55, w: 1.95, h: 0.5, fontSize: 12.5, bold: true, color: st[2], fontFace: F, margin: 0 });
  s.addText(st[1], { x: x + 0.12, y: 2.05, w: 1.95, h: 0.6, fontSize: 10.5, color: INK, fontFace: F, margin: 0 });
  s.addText(st[3], { x: x + 0.12, y: 2.62, w: 1.95, h: 0.3, fontSize: 9.5, italic: true, color: GRAY, fontFace: F, margin: 0 });
  if (i < 3) s.addText("→", { x: x + 2.13, y: 1.95, w: 0.25, h: 0.4, fontSize: 16, color: GRAY, fontFace: F, margin: 0, align: "center" });
});
s.addText([
  { text: "인천 청년정책의 결정은 대부분 기존사업 조정이다  ", options: { fontSize: 14, bold: true } },
  { text: "— 제2차 청년정책 기본계획 69개 사업 중 계속·확대 85.5%, 교육·훈련 분야는 92.3% (인천 청년정책 포트폴리오 한정, E008·E010)", options: { fontSize: 12, color: GRAY } },
], { x: 0.5, y: 3.35, w: 9.0, h: 0.65, color: INK, fontFace: F, margin: 0 });
s.addShape("roundRect", { x: 0.5, y: 4.15, w: 9.0, h: 1.0, rectRadius: 0.06, fill: { color: INK } });
s.addText("\"연계 부족의 해법은 유사 사업을 하나 더 만드는 것이 아닐 가능성이 높습니다.\n그러나 기존 사업을 실제로 이어 주는 권한·정보·인계장치는 새로 만들어야 할 수 있습니다.\"", {
  x: 0.8, y: 4.27, w: 8.4, h: 0.8, fontSize: 13.5, bold: true, color: PAPER, fontFace: F, margin: 0 });

// ── 4. 기존 방식과 남은 공백 (선행서비스 비교 — 에이전트 확정 후 갱신) ──
s = pres.addSlide(); s.background = { color: PAPER };
title(s, "기존 도구는 정책을 '찾아주는' 도구다", "정책을 '만드는 사람'의 유사·중복 검토를 돕는 도구는 확인되지 않았다");
const cmpRows = [
  [{ text: "", options: {} }, { text: "온통청년", options: { bold: true } }, { text: "기업마당", options: { bold: true } }, { text: "인천청년포털", options: { bold: true } }, { text: "정책핏 인천", options: { bold: true, color: HARBOR } }],
  ["대상 사용자", "청년 구직자", "중소기업", "청년 구직자", { text: "공무원 (검토 3단계)", options: { bold: true } }],
  ["핵심 기능", "정책 검색·안내", "지원사업 공고", "사업 안내·신청", { text: "정책 관계 판정", options: { bold: true } }],
  ["정책 사이 관계\n(중복·공백·인계)", "―", "―", "―", { text: "규칙 4종 + 그래프", options: { bold: true, color: HARBOR } }],
  ["검토서 산출물", "―", "―", "―", { text: "자체 검토서 초안 생성", options: { bold: true, color: HARBOR } }],
];
s.addTable(cmpRows, { x: 0.5, y: 1.5, w: 9.0, rowH: 0.52, fontSize: 12, fontFace: F,
  color: INK, border: { color: "D5D9DE", pt: 0.75 }, align: "center", valign: "middle",
  fill: { color: PAPER } });
s.addText("3개 포털 2026-08-13 실접속 확인 완료 (A급, 증거원장 E017~E019) · 확인 범위: 공개 메뉴 기준 — 발견: 정책 간 조정은 현재 위원회 심의(사람 절차)로만 존재", {
  x: 0.5, y: 4.65, w: 9.0, h: 0.3, fontSize: 10.5, color: GRAY, fontFace: F, margin: 0 });

// ── 5. 해결 원리 ──
s = pres.addSlide(); s.background = { color: PAPER };
title(s, "AI가 하는 일과 하지 않는 일을 분리했다", "흩어진 사업을 같은 구조로 정규화하면, 안 보이던 관계가 보인다");
const roles = [["LLM — 추출만", "원문 → 정책카드\n기권 계약: 없는 필드는 '모름'\n인용은 원문 그대로", HARBOR],
               ["규칙 — 판정", "공백 · 인계 공백 · 조정 필요 중복\n· 의도적 병행 (Cypher/파이썬)\ndetect.py에 import openai 없음", GREEN],
               ["사람 — 결정", "모든 판정은 '후보'\n검토서 초안 → 담당자 확정\n부서 협의로만 확정", CUT]];
roles.forEach((r, i) => {
  const x = 0.5 + i * 3.1;
  s.addShape("roundRect", { x, y: 1.45, w: 2.9, h: 1.75, rectRadius: 0.06,
    fill: { color: PAPER }, line: { color: r[2], width: 1.5 } });
  s.addText(r[0], { x: x + 0.15, y: 1.58, w: 2.6, h: 0.4, fontSize: 15, bold: true, color: r[2], fontFace: F, margin: 0 });
  s.addText(r[1], { x: x + 0.15, y: 2.0, w: 2.6, h: 1.1, fontSize: 11.5, color: INK, fontFace: F, margin: 0 });
});
s.addText([
  { text: "왜 규칙만으로 안 되나 — ", options: { bold: true } },
  { text: "비정형 원문을 카드로 정규화하는 일은 규칙이 못 한다.  ", options: {} },
  { text: "왜 LLM만으로 안 되나 — ", options: { bold: true } },
  { text: "타 부서 사업에 '중복' 낙인을 찍는 판정을 확률 모델에 맡길 수 없다.", options: {} },
], { x: 0.5, y: 3.4, w: 9.0, h: 0.6, fontSize: 12.5, color: INK, fontFace: F, margin: 0 });
s.addShape("roundRect", { x: 0.5, y: 4.15, w: 9.0, h: 0.95, rectRadius: 0.06, fill: { color: ICE } });
s.addText([
  { text: "LLM 금지 목록 (화면에 노출):  ", options: { bold: true, color: HARBOR } },
  { text: "출처 없는 사실 보완 · 정합성 점수 직접 생성 · 사업폐지/예산삭감 자동결정", options: { color: INK } },
], { x: 0.8, y: 4.42, w: 8.4, h: 0.45, fontSize: 12.5, fontFace: F, margin: 0 });

// ── 6. 라이브 데모 ──
s = pres.addSlide(); s.background = { color: PAPER };
title(s, "라이브 데모 — 150초", "기준사업: 인천 청년도약기지 · 분석 범위를 산업 선택으로 확장");
chain(s, 1.45, { anchor: true, emptyIdx: [5] });
const demo = [["① 검토 개요", "판정 4종 카운트 + 예산 달력 D-day"],
              ["② 정책 연계 지도", "결재란 사슬 — 인계 없는 구간 ✂ 절단선\n🔴 라이브: gpt-4o 원문 재추출 (실호출)"],
              ["③ 유사·중복 검토표", "직무 × 판정 + 실행된 Cypher 질의 노출"],
              ["④ 조치 제안서", "검토서 초안 다운로드 + 정확도 실측"]];
demo.forEach((d, i) => {
  const x = 0.5 + (i % 2) * 4.65, y = 2.35 + Math.floor(i / 2) * 1.12;
  s.addShape("roundRect", { x, y, w: 4.45, h: 1.0, rectRadius: 0.05,
    fill: { color: i === 1 ? ICE : PAPER }, line: { color: HARBOR, width: 1 } });
  s.addText(d[0], { x: x + 0.15, y: y + 0.08, w: 4.15, h: 0.32, fontSize: 13, bold: true, color: HARBOR, fontFace: F, margin: 0 });
  s.addText(d[1], { x: x + 0.15, y: y + 0.4, w: 4.15, h: 0.55, fontSize: 11, color: INK, fontFace: F, margin: 0 });
});
s.addText([
  { text: "점수를 만드는 두 장면 — ", options: { bold: true } },
  { text: "\"이건 중첩이지만 의도된 병행입니다\" (유사 ≠ 낭비) · \"새로 만들 필요가 낮은 것\" (AI가 신규 제안만 뱉는 도구가 아님)", options: {} },
], { x: 0.5, y: 4.72, w: 9.0, h: 0.55, fontSize: 12, color: INK, fontFace: F, margin: 0 });
s.addNotes("시연 실패 대비 녹화 백업 준비. 화면에 실데이터/가상 라벨 상시 노출.");

// ── 7. 검증 ──
s = pres.addSlide(); s.background = { color: PAPER };
title(s, "저희는 취업률을 올렸다고 말하지 않습니다", "자체 정답셋 31건 실측 — 2인 교차판정 전 잠정치");
s.addChart(pres.ChartType.bar, [{
  name: "필드 추출 정확도", labels: ["v2", "v3", "v4", "v6 최종"], values: [42, 92, 92, 100] }], {
  x: 0.5, y: 1.45, w: 4.2, h: 2.5, chartColors: [HARBOR], showValue: true,
  dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 11,
  showTitle: true, title: "정답셋이 프롬프트를 개선시켰다 (%)", titleFontSize: 12, titleColor: INK,
  showLegend: false, catAxisLabelColor: INK, valAxisLabelColor: GRAY,
  valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" },
  valAxisMaxVal: 100, fontFace: F });
const met = [["인용 실재율", "89%", "100%이 아닙니다 — 실측 그대로", CUT],
             ["기권 정확도", "100%", "모르면 '모름'이라 말한 비율", HARBOR],
             ["중첩 오판 회피", "100%", "의도적 병행을 중복으로 안 몬 비율", GREEN]];
met.forEach((m, i) => {
  const y = 1.45 + i * 0.85;
  s.addShape("roundRect", { x: 5.0, y, w: 4.5, h: 0.75, rectRadius: 0.05,
    fill: { color: PAPER }, line: { color: m[3], width: 1.2 } });
  s.addText(m[1], { x: 5.15, y: y + 0.08, w: 1.1, h: 0.6, fontSize: 24, bold: true, color: m[3], fontFace: F, margin: 0 });
  s.addText([{ text: m[0], options: { bold: true, breakLine: true, fontSize: 12 } },
             { text: m[2], options: { fontSize: 10.5, color: GRAY } }],
    { x: 6.3, y: y + 0.08, w: 3.1, h: 0.6, color: INK, fontFace: F, margin: 0 });
});
s.addText([
  { text: "검증하지 않은 것: ", options: { bold: true, color: RED } },
  { text: "실제 취업·근속 증가 · 기업 매출 · 청년 순유출 감소 · 기관 도입 의향 — 3일 해커톤에서 증명할 수 없는 것은 주장하지 않는다", options: { color: INK } },
], { x: 0.5, y: 4.35, w: 9.0, h: 0.6, fontSize: 12, fontFace: F, margin: 0 });
s.addText("전 과정 결정로그 D-001~D-016 · 프롬프트 v2→v6 반복은 정답셋 실측으로 유도됨", {
  x: 0.5, y: 4.95, w: 9.0, h: 0.3, fontSize: 10.5, color: GRAY, fontFace: F, margin: 0 });

// ── 8. 한계와 다음 단계 (다크 클로징) ──
s = pres.addSlide(); s.background = { color: INK };
s.addText("한계를 먼저 말하고, 확장은 실물로 보였습니다", {
  x: 0.7, y: 0.45, w: 8.6, h: 0.6, fontSize: 24, bold: true, color: PAPER, fontFace: F, margin: 0 });
const lim = [["한계", "공개데이터만으로 정책 인과효과는 증명 불가. 수요신호 일부는 가상 표본 — 화면에 그대로 표기.\n개인정보 사용 0 (설계상 금지). 실제 공무원 검증은 아직 받지 않았습니다.", GRAY],
             ["측정 설계", "효과를 측정했다가 아니라, 어떻게 잴지와 무엇이 나오면 실패인지를 미리 정했습니다.\n주지표 K1: 검토서 초안까지의 작업 단계 수 — 줄지 않으면 실패로 기록 (08_효과측정_설계).", "CADCFC"],
             ["운영 로드맵", "6대 산업 전체 · 고용24 실수요 연동 · 자동 서칭 · Neo4j 수천 건 그래프.\n정책이 이어지는 것은 청년 정착의 충분조건이 아니라 전제조건입니다.", "CADCFC"]];
lim.forEach((l, i) => {
  const y = 1.35 + i * 1.25;
  s.addText(l[0], { x: 0.7, y, w: 2.0, h: 0.4, fontSize: 15, bold: true, color: "CADCFC", fontFace: F, margin: 0 });
  s.addText(l[1], { x: 2.9, y, w: 6.4, h: 1.1, fontSize: 12.5, color: l[2] === GRAY ? "AEB6BF" : PAPER, fontFace: F, margin: 0 });
});
s.addText("정책핏 인천 — 판단은 사람이, 근거는 그래프가  ·  근거: A3 워크플로우 맵(E020) · 통계청·인천연구원(E005·E006)", {
  x: 0.7, y: 5.0, w: 8.6, h: 0.4, fontSize: 14, bold: true, color: "CADCFC", fontFace: F, margin: 0 });

pres.writeFile({ fileName: "정책핏_인천_발표_v1.pptx" }).then(() => console.log("OK"));
