"""시연 백업: 4화면 내용을 의존성 없는 정적 HTML로 굽는다.

`python -m engine.snapshot` → data/demo_fallback.html
Streamlit·Neo4j·인터넷이 전부 죽어도 브라우저로 열리는 최후 폴백 (스펙 §7).
"""
import csv
import json
from pathlib import Path

from engine import detect
from engine.extract import OCCUPATIONS

STAGES = ["교육훈련", "일경험", "구직지원", "매칭", "채용지원", "정착"]
ANCHOR = "P001"

CSS = """
:root{--ink:#1A2B3C;--harbor:#0E5A8A;--gap:#8A8F98;--cut:#C75000;--parallel:#1E7F4F}
*{box-sizing:border-box}
body{font-family:"Malgun Gothic",sans-serif;color:var(--ink);background:#FBFBF9;
     margin:0;padding:28px 32px;line-height:1.55}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px;
   border-bottom:2px solid var(--ink);padding-bottom:4px}
.sub{color:var(--gap);font-size:13px;margin-bottom:16px}
.banner{background:#0E5A8A12;border:1px solid var(--harbor);padding:10px 14px;
        border-radius:3px;font-size:13.5px;margin-bottom:16px}
.cards{display:flex;gap:12px;margin:12px 0}
.card{flex:1;border:1px solid #D5D9DE;background:#fff;padding:10px 12px;border-radius:3px}
.card b{display:block;font-size:26px;color:var(--harbor)}
.card span{font-size:12px;color:var(--gap)}
.chain{display:flex;align-items:stretch;margin:14px 0}
.stg{flex:1;border:1.5px solid var(--ink);border-top:5px solid var(--harbor);
     background:#fff;padding:7px;text-align:center;font-size:13px;font-weight:700}
.stg.empty{border-style:dashed;border-top-color:var(--gap);color:var(--gap);background:transparent}
.stg.anchor{border-top-color:var(--cut)}
.stg em{display:block;font-size:11px;font-weight:400;color:var(--gap);font-style:normal}
.lnk{width:58px;flex:none;display:flex;flex-direction:column;justify-content:center;
     align-items:center;font-size:11px;font-weight:700;color:var(--cut)}
.lnk.ok{color:var(--parallel)}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}
th,td{border:1px solid #D5D9DE;padding:6px 9px;text-align:left;vertical-align:top}
th{background:#F0EFEA}
.chip{display:inline-block;padding:0 6px;border:1px solid;border-radius:2px;
      font-size:11px;font-weight:700;margin-left:4px}
.c-real{color:var(--harbor)}.c-ver{color:var(--parallel)}.c-press{color:var(--gap)}
.c-conf{color:#B42318}.c-virt{color:#8a6d00}
.note{font-size:12px;color:var(--gap);margin:6px 0}
.act{background:#F0EFEA;border-left:3px solid var(--harbor);padding:8px 12px;
     font-size:12.5px;margin:8px 0}
.metrics{display:flex;gap:12px;margin:10px 0}
.m{flex:1;border:1px solid #D5D9DE;background:#fff;padding:10px;text-align:center}
.m b{display:block;font-size:24px;color:var(--harbor)}
.m span{font-size:11.5px;color:var(--gap)}
.warn{background:#FFF8DC;border:1px solid #c9a800;padding:8px 12px;font-size:12.5px;
      border-radius:3px;margin:14px 0}
"""


def chip(c):
    ev = c.get("evidence_status")
    m = {"PRIMARY_VERIFIED": ("c-ver", "1차 확인"),
         "SECONDARY_PRESS_ONLY": ("c-press", "언론보도 기반"),
         "CONFLICTING_FIGURES": ("c-conf", "수치 충돌")}
    if ev in m:
        return f'<span class="chip {m[ev][0]}">{m[ev][1]}</span>'
    if c.get("data_type", "real") == "real":
        return '<span class="chip c-real">실데이터</span>'
    return '<span class="chip c-virt">가상</span>'


def build(scope_label, cards, demands):
    edges = detect.build_edges(cards, demands)
    f = detect.run_rules(cards, demands, edges)
    by_id = {c["policy_id"]: c for c in cards}
    name = lambda p: by_id[p].get("name") or p
    out = [f'<h2>분석 범위: {scope_label} — 정책 {len(cards)}건</h2>']

    out.append('<div class="cards">')
    for lbl, n in [("지원 공백 후보", len(f["gaps"])), ("인계 공백 후보", len(f["handoff_breaks"])),
                   ("조정 필요 중복 후보", len(f["overlaps_harmful"])),
                   ("의도적 병행", len(f["overlaps_intentional"])),
                   ("보완 관계", len(f.get("complements", [])))]:
        out.append(f'<div class="card"><b>{n}</b><span>{lbl}</span></div>')
    out.append('</div>')

    # 결재란 사슬
    stage_ids = {s: {c["policy_id"] for c in cards if c.get("stage") == s} for s in STAGES}
    handoff = [(e["src"], e["dst"]) for e in edges if e["type"] == "HANDOFF"]
    out.append('<div class="chain">')
    for i, s in enumerate(STAGES):
        ids = stage_ids[s]
        cls = "stg" + (" empty" if not ids else "") + (" anchor" if ANCHOR in ids else "")
        out.append(f'<div class="{cls}">{s}<em>{"정책 없음" if not ids else f"{len(ids)}건"}</em></div>')
        if i < 5:
            nxt = stage_ids[STAGES[i + 1]]
            ok = any((a in ids and b in nxt) or (a in nxt and b in ids) for a, b in handoff)
            if ids and nxt:
                out.append(f'<div class="lnk{" ok" if ok else ""}">{"인계" if ok else "✂ 없음"}</div>')
            else:
                out.append('<div class="lnk">구간 빔</div>')
    out.append('</div>')

    # 단계별 정책
    out.append('<table><tr><th>단계</th><th>정책</th></tr>')
    for s in STAGES:
        pol = [c for c in cards if c.get("stage") == s]
        cell = "<br>".join(
            f'{"⭐ " if c["policy_id"] == ANCHOR else ""}<a href="{c.get("source_url")}">'
            f'{c.get("name") or c["policy_id"]}</a>{chip(c)} '
            f'<span class="note">{(c.get("owner_dept") or "").replace("인천광역시 ", "")}</span>'
            for c in pol) or '<span class="note">정책 없음</span>'
        out.append(f'<tr><td><b>{s}</b></td><td>{cell}</td></tr>')
    unstaged = [c for c in cards if not c.get("stage")]
    if unstaged:
        out.append('<tr><td><b>사슬 밖</b><br><span class="note">시설·기업지원·계획</span></td><td>'
                   + ", ".join(c.get("name") or c["policy_id"] for c in unstaged) + '</td></tr>')
    out.append('</table>')

    # 직무별 판정
    gap_occ = {g["occupation"]: g["reason"] for g in f["gaps"]}
    hb = {p for x in f["handoff_breaks"] for p in x["items"]}
    oh = {p for x in f["overlaps_harmful"] for p in x["items"]}
    oi = {p for x in f["overlaps_intentional"] for p in x["items"]}
    out.append('<table><tr><th>직무</th><th>정책 수</th><th>판정(후보)</th><th>비고</th></tr>')
    for occ in OCCUPATIONS:
        pol = [c for c in cards if occ in (c.get("occupation") or [])]
        marks = []
        if occ in gap_occ:
            marks.append("⬜ 지원 공백")
        if any(c["policy_id"] in hb for c in pol):
            marks.append("🔶 인계 공백")
        if any(c["policy_id"] in oh for c in pol):
            marks.append("🔴 조정 필요 중복")
        if any(c["policy_id"] in oi for c in pol):
            marks.append("🟢 의도적 병행")
        out.append(f'<tr><td>{occ}</td><td>{len(pol)}</td><td>{" · ".join(marks) or "—"}</td>'
                   f'<td class="note">{gap_occ.get(occ, "")}</td></tr>')
    out.append('</table>')

    # 인계 공백 상위 (기준사업 포함 우선)
    breaks = sorted(f["handoff_breaks"], key=lambda x: ANCHOR not in x["items"])[:6]
    if breaks:
        out.append('<table><tr><th>인계 공백 후보 (상위 6)</th><th>구간</th></tr>')
        for b in breaks:
            out.append(f'<tr><td>{" ↔ ".join(name(p) for p in b["items"])}</td>'
                       f'<td class="note">{b["reason"]}</td></tr>')
        out.append('</table>')
        out.append('<div class="act">→ 다음 행동: 두 사업 소관 부서 간 인계 절차 신설 협조공문. '
                   '예산 불요 조치이므로 즉시 착수 가능.</div>')
    return "\n".join(out)


def main():
    base = Path(__file__).resolve().parent.parent / "data"
    base_cards = [json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted((base / "cards").glob("P*.json"))]
    pool_cards = [json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted((base / "pool" / "cards").glob("IC-*.json"))]
    with open(base / "demand" / "demand_signals.csv", encoding="utf-8-sig") as fp:
        demands = list(csv.DictReader(fp))

    parts = ['<!doctype html><html lang="ko"><head><meta charset="utf-8">'
             '<meta name="viewport" content="width=device-width, initial-scale=1">'
             '<title>정책핏 인천 — 시연 백업</title>',
             f"<style>{CSS}</style></head><body>",
             "<h1>정책핏 인천 — 시연 백업 스냅샷</h1>",
             '<div class="sub">앱·DB·인터넷 없이 열리는 정적 사본 · 기준일 2026-08-13 · '
             '모든 판정은 “후보”이며 확정은 부서 협의로</div>',
             '<div class="banner"><b>이 도구가 대신하는 업무</b> — 신규사업 검토 8단계 중 '
             '3단계 ‘타 부서 협의·유사·중복 검토’(A3 워크플로우 맵, 증거 E020). '
             '유사·중복 사업 자체 검토서 작성에 필요한 후보를 자동 선별한다.</div>',
             build("청년일자리 (기본)", base_cards, demands),
             build("청년일자리 + 바이오", base_cards + pool_cards, demands)]

    rp = base / "results.json"
    if rp.exists():
        r = json.loads(rp.read_text(encoding="utf-8"))
        fmt = lambda v: "—" if v is None else f"{v * 100:.0f}%"
        parts.append("<h2>추출 정확도 실측</h2><div class='metrics'>")
        for lbl, key in [("필드 추출 정확도", "field_accuracy"), ("기권 정확도", "abstention_accuracy"),
                         ("인용 실재율", "span_grounded_rate"), ("중첩 오판 회피", "overlap_correct_rate")]:
            parts.append(f'<div class="m"><b>{fmt(r[key])}</b><span>{lbl}</span></div>')
        parts.append("</div>")
        parts.append(f'<div class="note">자체 정답셋 {r["n_cases"]}건 · 2인 교차판정 전 잠정치. '
                     '인용 실재율이 100%가 아닌 것은 실측 그대로 표기한 것이다.</div>')
    parts.append('<div class="warn">수요신호 4건 중 3건은 <b>가상 표본</b>이며, 바이오생산 1건만 '
                 'B/D급 실신호(전국 단위 보고서·사업주체 서술)다. 공백 판정은 고용24 실데이터 확보 후 확정한다.</div>')

    parts.append("</body></html>")
    out = base / "demo_fallback.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"{out} 생성 — 앱 없이 브라우저로 열면 4화면 핵심 내용이 그대로 나온다")


if __name__ == "__main__":
    main()
