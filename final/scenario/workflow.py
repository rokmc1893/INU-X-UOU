"""A3 인천광역시 정책·행정 워크플로우 8단계.

우리는 **3단계(타부서 협의·유사·중복 검토)** 하나에 들어간다. 그 단계의 산출 문서가
A3 원문에 「부서 협의 요청서, 유사·중복 사업 자체 검토서」로 적혀 있고, 반려 사유가
「타 부서 기존 사업과 대상·수단·직무 동일」이라 우리 규칙과 정확히 겹치기 때문이다.

**A3에 없는 것을 만들지 않는다**
  - 소요 기간: 4단계(6~9월)·5단계(11~12월) 둘뿐. 나머지는 None으로 두고 화면에 안 쓴다.
  - 반려 시 복귀 단계(루프백): A3 mermaid도 본문도 단선 8단계뿐. None으로 둔다.
  둘 다 `RESEARCH_TODO.md` P1-3에 조사 과제로 올려 뒀다.
"""

OUR_STAGE = 3

# 각 항목: no, name, writer, reviewer, decider, inputs, reject_reasons, duration, loopback
# duration/loopback이 None인 것은 **A3에 없다**는 뜻이지 '없다'는 뜻이 아니다.
STAGES = []  # TODO: A3_workflow_map.md 표를 그대로 옮긴다


def stage(no):
    """단계 하나. 없는 번호면 None."""
    raise NotImplementedError


def reject_reasons(no):
    """그 단계에서 반려되는 사유 — A3 원문 표현 그대로."""
    raise NotImplementedError


def duplicate_test_source():
    """우리 중복 규칙의 원문 근거 문장을 돌려준다.

    발표와 검토서에서 "이 기준은 우리가 정한 것이 아니다"를 보이는 데 쓴다.
    """
    raise NotImplementedError
