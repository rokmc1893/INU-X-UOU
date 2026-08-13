import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import fit
from fit import axes, load, needs
from engine import industry

cards = load.cards()
edges, findings, postures = load.build(cards)
b2 = load.b2()
cov = needs.coverage(cards, b2)
plans = [c for c in cards if load.is_plan(c)]
works = [c for c in cards if not load.is_plan(c)]

slim = []
for c in cards:
    slim.append({
        "policy_id": c["policy_id"],
        "name": c.get("name"),
        "is_plan": load.is_plan(c),
        "strategic_industry": c.get("strategic_industry") or "",
        "owner_dept": c.get("owner_dept") or "",
        "intervention_type": c.get("intervention_type") or "",
        "budget": c.get("budget") or "",
        "budget_status": c.get("budget_status") or "",
        "summary": (c.get("summary") or "")[:220],
        "target": c.get("target") or "",
        "period": c.get("period") or c.get("term") or "",
        "source_url": c.get("source_url") or "",
        "needs_covered": needs.needs_covered_by(c),
        "name_missing": bool(c.get("_name_missing")),
        "industry_guess": industry.industry_of((c.get("name") or "") + str(c.get("summary") or "")) or "",
    })

induce = []
for c in works:
    ind = industry.industry_of((c.get("name") or "") + str(c.get("summary") or ""))
    if ind and postures.get(ind, {}).get("posture") == industry.INDUCING:
        induce.append({"policy_id": c["policy_id"], "name": c["name"], "industry": ind,
                       "evidence": industry.inducement_evidence(c, plans)})

out = {
  "today": "2026-08-13",
  "cards": slim,
  "findings": findings,
  "postures": postures,
  "coverage": cov,
  "axes": axes.all_axes(),
  "axes_coverage": axes.coverage_line(),
  "industries": industry.INDUSTRIES,
  "principle": industry.PRINCIPLE,
  "need_label": needs.NEED_LABEL,
  "responsive": industry.RESPONSIVE,
  "inducing": industry.INDUCING,
  "b2_count": len(b2),
  "inducement": induce,
  "counts": {"works": len(works), "plans": len(plans)},
}
Path("/tmp/dump.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
print(json.dumps({k: (len(v) if isinstance(v,(list,dict)) else v) for k,v in out.items()}, ensure_ascii=False))
print(json.dumps({k: len(v) for k,v in findings.items()}, ensure_ascii=False))
