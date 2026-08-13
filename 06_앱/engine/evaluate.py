"""gold_set 대비 채점 → results.json. 화면 4가 수치를 읽는다 (스펙 §6)."""
import csv
import json
from pathlib import Path


def _get_field(card, dotted):
    cur = card
    for part in dotted.split("."):
        if cur is None:
            return None
        cur = cur.get(part) if isinstance(cur, dict) else None
    return cur


def _rate(hits, total):
    return None if total == 0 else hits / total


def score(cards, gold_rows, detect_result):
    field_hit = field_n = abst_hit = abst_n = ov_hit = ov_n = 0
    details = []
    pairs = {"harmful": [set(f["items"]) for f in detect_result.get("overlaps_harmful", [])],
             "intentional": [set(f["items"]) for f in detect_result.get("overlaps_intentional", [])]}
    for row in gold_rows:
        ct, ok = row["check_type"], False
        if ct == "field":
            card = cards.get(row["policy_id"], {})
            got = _get_field(card, row["field"])
            ok = str(got) == str(row["gold_value"]) if got is not None else row["gold_value"] == ""
            field_hit += ok
            field_n += 1
        elif ct == "abstention":
            card = cards.get(row["policy_id"], {})
            got = _get_field(card, row["field"])
            abstained = got is None and row["field"] in (card.get("missing_fields") or [])
            ok = abstained if row["gold_value"] == "" else not abstained
            abst_hit += ok
            abst_n += 1
        elif ct == "overlap_label":
            want = set(row["policy_id"].split(":"))
            label = row["gold_value"]
            ok = want in pairs.get(label, []) and all(want not in v for k, v in pairs.items() if k != label)
            ov_hit += ok
            ov_n += 1
        details.append({"case_id": row["case_id"], "ok": bool(ok)})
    span_hits = span_n = 0
    for card in cards.values():
        for field, hit in (card.get("_span_check") or {}).items():
            span_hits += bool(hit)
            span_n += 1
    return {"field_accuracy": _rate(field_hit, field_n),
            "abstention_accuracy": _rate(abst_hit, abst_n),
            "span_grounded_rate": _rate(span_hits, span_n),
            "overlap_correct_rate": _rate(ov_hit, ov_n),
            "n_cases": len(gold_rows), "details": details}


def main():
    base = Path(__file__).resolve().parent.parent / "data"
    cards = {}
    from engine.extract import parse_meta, _norm
    for p in sorted((base / "cards").glob("P*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        raw = next((base / "policies" / "raw").glob(f"{c['policy_id']}_*.txt"), None)
        if raw:  # 인용 실재율: source_span이 원문에 실재하는지 재검증
            _, body = parse_meta(raw.read_text(encoding="utf-8"))
            nb = _norm(body)
            c["_span_check"] = {f: (_norm(q) in nb)
                                for f, q in (c.get("source_span") or {}).items() if q}
        cards[c["policy_id"]] = c
    with open(base / "gold" / "gold_set.csv", encoding="utf-8-sig") as f:
        gold = list(csv.DictReader(f))
    demands = []
    dp = base / "demand" / "demand_signals.csv"
    if dp.exists():
        with open(dp, encoding="utf-8-sig") as f:
            demands = list(csv.DictReader(f))
    from engine.detect import build_edges, run_rules
    card_list = list(cards.values())
    result = score(cards, gold, run_rules(card_list, demands, build_edges(card_list, demands)))
    (base / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "details"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
