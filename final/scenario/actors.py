"""A1 액터 레지스트리 — 누가 결정하고 어느 과와 협의하는가.

산업 구분이 A와 B가 다르다. **판정은 B 기준, 협의처는 A 기준**으로 간다(SCAFFOLD §4).

**미해결**: A1이 두 버전이고 부서 체계가 충돌한다(조직개편 전/후). 앱 풀은 개편 **전**
버전을 쓴다. 화면에 "조직개편 전 기준, 발송 전 재확인"이라고 적는다.
→ `RESEARCH_TODO.md` P0-2.

**데이터 결함**: A1 마지막 행(인천테크노파크)은 필드가 11개로 헤더(12개)보다 하나 적어
컬럼이 밀린다. 로더가 건너뛰거나 보정해야 한다.
"""

# B 판정 산업 → A 부서 기준. SCAFFOLD §4의 표를 그대로 옮긴다.
# '물류·항만'(항만공항정책과·해양항공국)은 B에 대응 산업이 없어 여기 없다.
B_TO_A = {}  # TODO


def consult_for(card):
    """이 사업으로 공문을 보낼 부서 목록.

    돌려주는 각 항목: dept, bureau, decision_right, contact, source_url, as_of
    연락처는 A1 `public_contact`를 그대로 쓰되 **발송 전 재확인** 문구를 함께 낸다.
    """
    raise NotImplementedError


def reviewers_for(card):
    """A3 3단계 검토자 — 원문 규칙 그대로.

    청년사업이면 청년정책담당관, 대학·RISE 연계면 교육협력담당관, 그리고 평가담당관.
    """
    raise NotImplementedError
