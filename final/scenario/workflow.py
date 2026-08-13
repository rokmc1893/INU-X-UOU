"""A3 인천광역시 정책·행정 워크플로우 8단계.

우리는 **3단계(타부서 협의·유사·중복 검토)** 하나에 들어간다. 그 단계의 산출 문서가
A3 원문에 「부서 협의 요청서, 유사·중복 사업 자체 검토서」로 적혀 있고, 반려 사유가
「타 부서 기존 사업과 대상·수단·직무 동일」이라 우리 규칙과 정확히 겹치기 때문이다.

**A3에 없는 것을 만들지 않는다**
  - 소요 기간: 4단계(6~9월)·5단계(11~12월) 둘뿐. 나머지는 None이며 화면에 쓰지 않는다.
  - 반려 시 복귀 단계(루프백): A3 mermaid도 본문도 단선 8단계뿐. 전부 None.
  둘 다 `02_조사자료/RESEARCH_TODO.md` P1-3에 조사 과제로 올려 뒀다.
"""

OUR_STAGE = 3
SOURCE = "조사자 A · A3_workflow_map.md"

# duration/loopback이 None인 것은 **A3에 없다**는 뜻이지 '존재하지 않는다'는 뜻이 아니다.
STAGES = [
    dict(no=1, name="문제발굴 & 정책 아이디어 발의",
         writer="실무 주무관 / 인천테크노파크(ITP) 전담PD / 대학 RISE 센터",
         reviewer="담당 팀장", decider="담당 과장",
         inputs=["기업/대학/현장 수요조사서", "국정/시정 과제 추진 지침", "정부 공모 안내문"],
         reject=["근거법령 부재", "시정 방향 불일치", "명확한 수혜 대상 미설정"],
         duration=None, loopback=None),
    dict(no=2, name="주관부서 자체 검토 & 내부방침 수립",
         writer="담당 주무관", reviewer="팀장 및 과장",
         decider="담당 국장 또는 정무/행정부시장",
         inputs=["사업기획서(안)", "내부 방침서(시장/부시장/국장 결재)"],
         reject=["재정 부담 과다", "추진 필요성 소명 부족", "유사한 기존사업 존재"],
         duration=None, loopback=None),
    dict(no=3, name="타 부서 협의 & 유사·중복 검토",
         writer="주관 부서 주무관",
         reviewer="청년정책담당관(청년사업 시), 교육협력담당관(대학/RISE 연계 시), 평가담당관",
         decider="관련 부서장 합의",
         inputs=["부서 협의 요청서", "유사·중복 사업 자체 검토서"],
         reject=["타 부서 기존 사업과 대상·수단·직무 동일(중복 판정)", "예산 중복 반영 방침"],
         duration=None, loopback=None),
    dict(no=4, name="기획조정실 예산담당관 예산 심사",
         writer="주관 부서 주무관", reviewer="예산담당관 예산 1·2팀 심사관",
         decider="예산담당관 → 기획조정실장 → 시장",
         inputs=["사업별 예산요구서", "예산설명서", "성과계획서"],
         reject=["세수 부족에 따른 사업 우선순위 밀림", "산출근거 미흡",
                 "국비/시비 매칭 비율 불합리"],
         duration="매년 6월~9월 본예산 심사", loopback=None),
    dict(no=5, name="위원회 심의 & 시의회 의결",
         writer="기획조정실 예산담당관 및 상임위원회 전문위원",
         reviewer="청년정책조정위원회 / RISE 위원회 → 시의회 상임위",
         decider="인천광역시의회 본회의 (의결)",
         inputs=["인천광역시 세입세출 예산안", "위원회 안건 제출서"],
         reject=["시의회 예산 삭감(수정 의결)", "조례 미비", "위원회 부적절 판정"],
         duration="매년 11월~12월 시의회 정례회", loopback=None),
    dict(no=6, name="사업 공고 & 수행기관 집행",
         writer="주관 부서 및 수행기관(인천테크노파크 등)",
         reviewer="수행기관 센터장/팀장",
         decider="인천테크노파크 원장 / 대학 총장 / 인천광역시장",
         inputs=["사업 추진 확정 공고문", "위수탁 협약서", "지원사업 모집 공고문"],
         reject=["미달 공고(모집 미달)", "기업/청년 참여율 저조로 인한 변경 공고"],
         duration=None, loopback=None),
    dict(no=7, name="성과평가 & 환류 검토",
         writer="수행기관 및 주관부서 주무관",
         reviewer="평가담당관 / 외부 평가위원회", decider="기획조정실장",
         inputs=["최종 실적보고서", "성과평가서", "시정평가서"],
         reject=["목표 KPI 미달성(취업률, 기업 만족도 저하)", "집행률 미진(예산 이월/불용)"],
         duration=None, loopback=None),
    dict(no=8, name="기존사업 개편 / 차년도 반영",
         writer="주관 부서 주무관", reviewer=None,
         decider="담당 국장 및 예산담당관",
         inputs=["차년도 사업 개편안", "사업 통폐합 검토서"],
         # 8단계만 반려 사유 대신 '결과' 4종을 갖는다
         reject=[], duration=None, loopback=None,
         outcomes=["사업 유지", "예산 증액/감액", "기존 사업과 통합", "사업 일몰(종료)"]),
]

# 우리 중복 규칙(대상·수단·직무)의 원문 근거. 발표와 검토서에서 그대로 인용한다.
DUPLICATE_TEST_SOURCE = "타 부서 기존 사업과 대상·수단·직무 동일(중복 판정)"

# A3에서 유일하게 [추론] 태그가 붙은 항목이 우리가 대체하려는 바로 그 절차다.
# 아직 확인되지 않았으므로 화면에서 사실처럼 말하지 않는다 (A5 Q1이 이를 묻는다).
INFORMAL_PRACTICE = dict(
    stage=3, status="추론 — 미확인",
    text="공식 문서 제출 전 주무관 간 전화·메신저를 통한 '사전 핑퐁'으로 중복 조율",
    open_question="A5 Q1 — 어떤 채널로 사전 조율하는지 현장 확인 필요")


def stage(no):
    return next((s for s in STAGES if s["no"] == no), None)


def reject_reasons(no):
    s = stage(no)
    return list(s["reject"]) if s else []


def our_stage():
    return stage(OUR_STAGE)


def duplicate_test_source():
    """중복 판정 기준이 우리가 지어낸 것이 아님을 보이는 원문 문장."""
    return DUPLICATE_TEST_SOURCE


def unknowns():
    """A3가 답하지 않는 것 — 화면에서 감추지 않고 밝힌다."""
    return [
        "단계별 소요 기간이 4·5단계에만 있다. 나머지 6개 단계는 A3에 없다.",
        "반려됐을 때 어느 단계로 돌아가는지가 A3에 없다(단선 8단계).",
        f"3단계 사전 조율 절차는 [추론]이다 — {INFORMAL_PRACTICE['open_question']}",
    ]
