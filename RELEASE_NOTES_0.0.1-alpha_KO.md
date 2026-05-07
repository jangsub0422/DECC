# DECC 0.0.1-alpha

DECC `0.0.1-alpha`는 이 프로젝트의 첫 공개 알파 릴리스입니다.

## 주요 내용

- 자연어 요청을 plasmid JSON 명세로 분해합니다.
- 공통 프로그램 구조에 대한 profile 기반 정규화를 제공합니다.
- Python 모듈의 batch 생성 및 검증 경로를 포함합니다.
- plasmid와 생성 결과물을 run 단위로 저장합니다.
- `integration.py`를 통해 `final_app.py`를 연결합니다.
- 멀티라인 입력과 run 관리를 위한 Streamlit wrapper를 제공합니다.

## 이 릴리스를 어떻게 소개하면 좋은가

이 릴리스는 다음과 같이 소개하는 것이 적절합니다.

- 실험적인 알파 버전입니다.
- 구조화된 프로토타입입니다.
- 로컬 우선 AI 소프트웨어 생성 파이프라인입니다.

아직 생산 환경용 완성형 생성기로 소개하기에는 이릅니다.

## GitHub 릴리스 요약 예시

DECC 0.0.1-alpha는 구조화된 AI 보조 코드 생성 파이프라인의 첫 공개 알파 버전입니다.
이 릴리스에는 architect 기반 blueprint 생성, profile-aware normalization, run 단위 산출물 저장, contract-aware validation, integration linking, 그리고 Streamlit wrapper가 포함되어 있습니다.

## 주의사항

- 생성 결과물은 반드시 사람이 직접 검토해야 합니다.
- 일부 profile과 prompt는 계속 조정 중입니다.
- API 및 모델 특성에 따라 분해와 생성 품질이 달라질 수 있습니다.
- API 기반 생성은 비용과 운영 변동성을 높일 수 있습니다.
- end-to-end 안정성은 개선 중이지만 아직 확정되지 않았습니다.
