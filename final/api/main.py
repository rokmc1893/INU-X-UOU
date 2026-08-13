"""판정 API — 화면(Next)과 판정(파이썬)을 가른다.

**판정 규칙은 한 줄도 여기로 옮기지 않는다.** `fit`·`scenario`·`engine`을 그대로 부르고
결과를 JSON으로 내보낼 뿐이다. 규칙을 TypeScript로 다시 지으면 테스트 93건이 지켜 주던
것들(널을 다름으로 읽지 않기, 공급지표를 수요로 세지 않기 등)이 다시 깨진다.

    uvicorn api.main:app --port 8600 --reload
"""
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fit  # noqa: F401,E402  — 06_앱의 engine을 sys.path에 올린다
from fit import axes, empty, load, needs  # noqa: E402
from scenario import actors, calendar, intake, report, sources, workflow  # noqa: E402
from engine import industry, refdata  # noqa: E402

TODAY = "2026-08-14"
TODAY_MD = (8, 14)

app = FastAPI(title="정책핏 인천 판정 API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

# 담당자가 올린 자료 — 세션이 아니라 프로세스 수명 동안만 산다. 원장 파일은 건드리지 않는다.
UPLOADED: list = []


def _state():
    cards = load.cards() + UPLOADED
    edges, findings, postures = load.build(cards)
    b2 = load.b2()
    return cards, edges, findings, postures, b2, needs.coverage(cards, b2)


def _works(cards):
    return [c for c in cards if not load.is_plan(c)]


def _card(cards, pid):
    return next((c for c in cards if c["policy_id"] == pid), None)


def _brief(c):
    return {"id": c["policy_id"], "name": c.get("name"),
            "industry": c.get("strategic_industry"), "status": c.get("status"),
            "means": c.get("intervention_type"), "url": c.get("source_url"),
            "uploaded": bool(c.get("_uploaded"))}


@app.get("/api/businesses")
def businesses():
    """맡을 수 있는 사업 목록. 계획 문서와 산업 미상은 뺀다."""
    cards, *_ = _state()
    out = [_brief(c) for c in _works(cards) if c.get("strategic_industry")]
    return {"total": len(out),
            "items": sorted(out, key=lambda x: (x["industry"] or "", x["name"] or ""))}


@app.get("/api/overview")
def overview():
    """열자마자 보이는 것 — 받은 자료와 방금 계산한 것을 갈라서 보낸다."""
    cards, edges, findings, postures, b2, cov = _state()
    works = _works(cards)
    real = [c for c in cov if c["verdict"] in ("covered", "uncovered")]
    by_need, means = {}, {}
    for c in real:
        d = by_need.setdefault(c["need"], {"total": 0, "covered": 0})
        d["total"] += 1
        d["covered"] += c["verdict"] == "covered"
    for c in works:
        for n in needs.needs_covered_by(c):
            means[n] = means.get(n, 0) + 1
    return {
        "today": TODAY,
        "ledger": {"works": len(works), "plans": len(cards) - len(works),
                   "signals": len(b2), "uploaded": len(UPLOADED)},
        "computed": {"edges": len(edges),
                     "findings": sum(len(v) for v in findings.values()),
                     "needs": len(real),
                     "gaps": sum(1 for c in real if c["verdict"] == "uncovered")},
        "needs": [{"need": n, "plain": needs.plain(n), "label": needs.NEED_LABEL[n],
                   "covered": d["covered"], "total": d["total"]}
                  for n, d in sorted(by_need.items(), key=lambda kv: -kv[1]["total"])],
        "means": [{"need": n, "plain": needs.plain(n), "count": v}
                  for n, v in sorted(means.items(), key=lambda kv: -kv[1])],
        "axes": axes.all_axes(),
    }


@app.get("/api/review/{pid}")
def review(pid: str):
    """사업 하나에 대한 전체 판정 — 체크리스트가 이걸로 만들어진다."""
    cards, edges, findings, postures, b2, cov = _state()
    card = _card(cards, pid)
    if card is None:
        raise HTTPException(404, "그런 사업이 없습니다")
    works = _works(cards)
    ind = (card.get("strategic_industry") or "").split("+")[0]
    same = [c for c in works if ind and ind in (c.get("strategic_industry") or "")]

    def mine(key):
        return [f for f in (findings.get(key) or [])
                if pid in f.get("items", []) and f.get("same_industry", True)]

    def pair(f):
        other = next(q for q in f["items"] if q != pid)
        o = _card(cards, other) or {}
        return {"id": other, "name": o.get("name"), "url": o.get("source_url"),
                "reason": f["reason"]}

    budget = refdata.budget_status_for(card)
    dept = next((x for x in findings["dept_mismatch"] if x["pid"] == pid), None)
    mycov = [c for c in cov if ind and ind in c["industry"]
             and c["verdict"] in ("covered", "uncovered")]
    return {
        "card": {**_brief(card), "owner": card.get("owner_dept"),
                 "budget": card.get("budget"),
                 "missing": card.get("missing_fields") or []},
        "budget": {"status": (budget or {}).get("status"),
                   "won": (budget or {}).get("budget_won"),
                   "official_dept": (budget or {}).get("dept"),
                   "line": (budget or {}).get("source"),
                   "mismatch": dept,
                   "empty": empty.budget(card, budget)},
        "overlaps": {
            "harmful": [pair(f) for f in mine("overlaps_harmful")],
            "intentional": [pair(f) for f in mine("overlaps_intentional")],
            "complement": [pair(f) for f in mine("complements")],
            "empty": empty.overlaps(card, same, mine("overlaps_harmful")),
        },
        "handoffs": {"items": [pair(f) for f in mine("handoff_breaks")],
                     "empty": empty.handoffs(card, same, mine("handoff_breaks"))},
        "needs": [{**c, "plain": needs.plain(c["need"]),
                   "label": needs.NEED_LABEL[c["need"]],
                   "mine": pid in c["covers"],
                   "coverNames": [(_card(cards, q) or {}).get("name") for q in c["covers"]]}
                  for c in mycov],
        "posture": postures.get(ind),
        "consult": actors.consult_for(card),
        "reviewers": actors.reviewers_for(card),
        "caveat": actors.CAVEAT,
        "windows": {"open": calendar.open_windows(TODAY_MD),
                    "soon": calendar.upcoming(TODAY_MD, 3)},
        "stage": workflow.our_stage(),
        "duplicateRule": workflow.duplicate_test_source(),
    }


@app.get("/api/sources")
def source_guide(industry: str = "", need: str = ""):
    return {"checkedOn": sources.CHECKED_ON, "summary": sources.summary(),
            "items": sources.for_industry(industry or None, need=need or None),
            "claim": sources.claim_text(need, industry) if need else None}


@app.get("/api/draft/{pid}")
def draft(pid: str, track: str = ""):
    cards, edges, findings, postures, b2, cov = _state()
    card = _card(cards, pid)
    if card is None:
        raise HTTPException(404, "그런 사업이 없습니다")
    ind = (card.get("strategic_industry") or "").split("+")[0]
    mycov = [c for c in cov if ind and ind in c["industry"]]
    names = {c["policy_id"]: c.get("name") for c in cards}
    urls = {c["policy_id"]: c.get("source_url") for c in cards}
    md = report.draft(card, findings, mycov, track or calendar.RENEW_TRACK, TODAY_MD,
                      name_of=lambda q: names.get(q, q), url_of=lambda q: urls.get(q))
    return {"filename": f"검토서초안_{pid}.md", "markdown": md}


class TextIn(BaseModel):
    text: str
    industry: Optional[str] = None
    title: Optional[str] = None


class UrlIn(BaseModel):
    url: str
    industry: Optional[str] = None


@app.post("/api/intake/url")
def intake_url(body: UrlIn):
    try:
        card, note = intake.from_url(body.url, seq=len(UPLOADED) + 1,
                                     industry=body.industry)
    except intake.IntakeError as e:
        raise HTTPException(400, str(e))
    UPLOADED.append(card)
    return {"card": _brief(card), "note": note}


@app.post("/api/intake/text")
def intake_text(body: TextIn):
    try:
        card, note = intake.from_text(body.text, seq=len(UPLOADED) + 1,
                                      industry=body.industry, title=body.title)
    except intake.IntakeError as e:
        raise HTTPException(400, str(e))
    UPLOADED.append(card)
    return {"card": _brief(card), "note": note}


@app.post("/api/intake/pdf")
async def intake_pdf(file: UploadFile = File(...), industry: str = Form("")):
    try:
        card, note = intake.from_pdf(await file.read(), file.filename,
                                     seq=len(UPLOADED) + 1, industry=industry or None)
    except intake.IntakeError as e:
        raise HTTPException(400, str(e))
    UPLOADED.append(card)
    return {"card": _brief(card), "note": note}


@app.delete("/api/intake")
def clear_uploads():
    n = len(UPLOADED)
    UPLOADED.clear()
    return {"removed": n}

@app.get("/api/matrix")
def matrix():
    """6대 산업 × 필요한 것 — 빈칸이 어디에 몰려 있는지 한눈에 보는 격자.

    빈칸마다 **그 유형을 주는 사업이 다른 산업에 몇 건 있는지**를 함께 보낸다.
    「돈을 주는 사업이 없다」와 「돈을 주는 사업은 있는데 이 산업엔 없다」는 전혀 다른
    이야기이고, 실제로 후자다 — 돈을 주는 사업 4건은 로봇·반도체에 있고 돈이 필요한
    곳은 바이오다.
    """
    cards, edges, findings, postures, b2, cov = _state()
    works = _works(cards)
    grid, supply = {}, {}
    for c in works:
        ind = (c.get("strategic_industry") or "").split("+")[0]
        for n in needs.needs_covered_by(c):
            supply.setdefault(n, []).append(
                {"id": c["policy_id"], "name": c.get("name"), "industry": ind or "산업 미상"})
    for x in cov:
        if x["verdict"] not in ("covered", "uncovered"):
            continue
        for ind in (x["industry"] or "").split("+"):
            if not ind:
                continue
            cell = grid.setdefault(ind, {}).setdefault(
                x["need"], {"covered": 0, "total": 0, "signals": []})
            cell["total"] += 1
            cell["covered"] += x["verdict"] == "covered"
            cell["signals"].append(
                {"id": x["signal_id"], "type": x["problem_type"], "grade": x["grade"],
                 "url": x["source_url"], "covered": x["verdict"] == "covered"})
    order = [i for i in industry.INDUSTRIES if i in grid] +             [i for i in grid if i not in industry.INDUSTRIES]
    return {
        "needs": [{"need": n, "plain": needs.plain(n), "label": needs.NEED_LABEL[n]}
                  for n in needs.NEEDS if any(n in g for g in grid.values())],
        "industries": order,
        "grid": grid,
        "postures": {k: {"posture": v["posture"], "why": v["why"]}
                     for k, v in postures.items()},
        "supply": {n: {"total": len(v),
                       "byIndustry": sorted({x["industry"] for x in v}),
                       "items": v[:6]}
                   for n, v in supply.items()},
    }


@app.get("/api/calendar")
def year_calendar():
    """A2 6트랙을 한 해 띠 위에 올린다 — 지금 어디쯤인지 보이게."""
    import re as _re
    out = []
    for t in calendar.tracks():
        w = t["practical_start_window"]
        months = [int(m) for m in _re.findall(r"(\d{1,2})월", w)]
        dl = _re.findall(r"(\d{1,2})월", t["formal_deadline"] or "")
        out.append({
            "name": t["decision_type"],
            "always": ("수시" in w or "연중" in w),
            "startMonth": months[0] if months else None,
            "endMonth": months[1] if len(months) > 1 else (months[0] if months else None),
            "deadlineMonth": int(dl[0]) if dl else None,
            "window": w, "deadline": t["formal_deadline"],
            "docs": t["required_input"], "next": t["next_available_window"],
            "ours": calendar.OUR_DOC.get(t["decision_type"]),
        })
    return {"today": {"month": TODAY_MD[0], "day": TODAY_MD[1]}, "tracks": out}
