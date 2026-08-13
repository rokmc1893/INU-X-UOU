"""빈칸이 왜 빈칸인지 — 논리로 가른다.

화면이 비었을 때 그냥 「0건」만 띄우면 담당자는 도구가 고장난 줄 안다. 실제로 미래차를
골랐을 때 화면 1·2가 통째로 비었는데 이유를 말해 주지 않았다.

**빈칸에는 네 가지 뜻이 있고, 서로 반대다.**

    없어서 없다   짝지을 상대가 아예 없다 (사업이 1건뿐이면 겹칠 수가 없다)
    맞아서 없다   대조는 했는데 걸리는 것이 없다
    아직 안 봤다  확인 절차가 여기까지 안 왔다
    못 읽었다     원문에 안 적혀 있어 판정 자체가 불가능하다

앞의 둘은 **문제가 없다**는 뜻이고, 뒤의 둘은 **모른다**는 뜻이다. 이 둘을 같은 「0건」으로
쓰면 "모른다"가 "괜찮다"로 둔갑한다 — 이 프로젝트가 내내 경계해 온 바로 그 오독이다.
"""

# 네 가지 뜻. `ok`는 문제 없음, `unknown`은 모름.
NONE_TO_PAIR = "없어서 없다"     # ok
CHECKED_CLEAN = "맞아서 없다"    # ok
NOT_YET = "아직 안 봤다"         # unknown
UNREADABLE = "못 읽었다"         # unknown

MEANING = {
    NONE_TO_PAIR: "ok",
    CHECKED_CLEAN: "ok",
    NOT_YET: "unknown",
    UNREADABLE: "unknown",
}


def _r(kind, why, fix=None):
    return {"kind": kind, "meaning": MEANING[kind], "why": why, "fix": fix}


def budget(card, status):
    """화면 1 — 예산 대조가 비었을 때."""
    if status:
        return None
    return _r(NOT_YET,
              "조사자 C가 예산 장부와 대조를 마친 사업 10건 안에 이 사업이 없습니다.",
              "인천시 예산서에서 이 사업의 세부사업명을 찾아 금액·소관을 확인하면 채워집니다.")


def overlaps(target, same_industry_works, found):
    """화면 2 — 겹침이 0건일 때.

    겹침이 나오려면 ① 같은 산업 사업이 둘 이상 ② 양쪽 다 직무가 적혀 있어야 한다.
    어느 조건에서 막혔는지에 따라 뜻이 완전히 달라진다.
    """
    if found:
        return None
    others = [c for c in same_industry_works
              if c["policy_id"] != (target or {}).get("policy_id")]
    if len(others) == 0:
        return _r(NONE_TO_PAIR,
                  "이 산업에 견줄 다른 사업이 없습니다. 겹치려면 사업이 둘은 있어야 합니다.",
                  "이 산업의 사업을 더 찾아 넣으면 대조가 시작됩니다.")
    with_occ = [c for c in others if c.get("occupation")]
    if len(with_occ) == 0:
        return _r(UNREADABLE,
                  f"같은 산업 사업이 {len(others)}건 있지만, 그중 어느 것도 "
                  "「누구를 대상으로 하는지」가 원문에 적혀 있지 않습니다.",
                  "사업계획서 원문을 넣으면 대상·직무가 채워지고 대조가 됩니다.")
    return _r(CHECKED_CLEAN,
              f"같은 산업 사업 {len(others)}건과 하나씩 맞춰 봤지만, "
              "받는 사람·주는 것·직무가 모두 같은 짝이 없었습니다.",
              None)


def handoffs(target, same_industry_works, found):
    """화면 2 — 넘기는 절차가 0건일 때."""
    if found:
        return None
    others = [c for c in same_industry_works
              if c["policy_id"] != (target or {}).get("policy_id")]
    if len(others) == 0:
        return _r(NONE_TO_PAIR, "이 산업에 견줄 다른 사업이 없어 넘길 곳도 없습니다.", None)
    staged = [c for c in others if c.get("stage")]
    if len(staged) == 0:
        return _r(UNREADABLE,
                  f"같은 산업 사업이 {len(others)}건 있지만 「어느 단계 사업인지」가 "
                  "원문에 적혀 있지 않아 앞뒤를 가릴 수 없습니다.",
                  "사업계획서 원문을 넣으면 단계가 채워집니다.")
    return _r(CHECKED_CLEAN, "앞뒤 단계 사업과 맞춰 봤지만 끊긴 곳이 없었습니다.", None)


def needs_table(industry, rows_all, rows_real):
    """화면 3 — 「필요한 것」 표가 비었을 때."""
    if rows_real:
        return None
    if not rows_all:
        return _r(NOT_YET,
                  f"조사 원장에 {industry} 산업 자료가 아직 없습니다.",
                  "기업 실태조사·연구보고서를 넣으면 채워집니다.")
    return _r(UNREADABLE,
              f"{industry} 자료가 {len(rows_all)}건 있지만 전부 산업 규모·현원처럼 "
              "「무엇이 모자란지」를 말하지 않는 것들입니다.",
              "부족 인원·자금 애로처럼 모자람을 말하는 자료가 필요합니다.")


def card_means(card):
    """이 사업이 무엇을 해주는지 못 읽었을 때 — 어느 화면에서든 쓴다."""
    if card and card.get("intervention_type"):
        return None
    return _r(UNREADABLE,
              "이 사업이 「무엇을 해주는지」가 원문에 적혀 있지 않아 "
              "기업이 필요하다고 말한 것과 맞출 수 없습니다.",
              "사업계획서 원문을 넣으면 채워집니다.")
