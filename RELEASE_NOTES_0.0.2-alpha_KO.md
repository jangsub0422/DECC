# DECC 0.0.2-alpha

DECC `0.0.2-alpha`는 Digital E. coli Code Compiler 프로젝트의 두 번째 공개 알파 릴리스입니다.

이번 릴리스는 초기 파이프라인을 더 쉽게 실행하고, 실패 원인을 더 쉽게 추적할 수 있도록 만드는 데 초점을 맞췄습니다. 기본 흐름은 유지하면서 모델 선택, batch 리포트, integration 단계의 검사를 강화했습니다.

## 주요 변경 사항

- Gemini, OpenAI, Claude의 모델 목록을 provider에서 조회하는 기능을 추가했습니다.
- 모델 목록 조회에 실패해도 사용할 수 있도록 fallback 모델 목록을 유지합니다.
- hosted API 기본 모델명과 API quickstart 예시를 최신 기준으로 정리했습니다.
- run 단위 `batch_report.json`과 `batch_report.md`를 추가했습니다.
- `final_app.py`를 연결하기 전에 생성 모듈 import smoke check를 수행합니다.
- run 폴더 안의 `final_app.py` snapshot이 생성 모듈 스캔에 섞이지 않도록 제외했습니다.
- `requirements.txt`에 의존성 버전 범위를 추가했습니다.
- 프로젝트 풀네임을 Digital E. coli Code Compiler로 정리했습니다.
- 영어 API quickstart 문서를 추가했습니다.

## 현재 권장 실행 방향

- 기본 권장 경로는 Python, Streamlit, Ollama를 사용하는 로컬 우선 워크플로우입니다.
- hosted API는 architect 분해와 모듈 코드 생성 단계에서 사용할 수 있습니다.
- hosted API 사용은 선택 사항이며 비용과 provider별 동작 차이가 발생할 수 있습니다.

## 주의사항

- 이 버전은 여전히 알파 릴리스입니다.
- 생성된 코드는 실행, 재사용, 재배포, 배포 전에 반드시 사람이 검토해야 합니다.
- import smoke check는 일부 런타임 문제를 잡아주지만, 생성된 애플리케이션의 전체 동작을 보장하지는 않습니다.
- profile별 런타임 데이터 스키마 검사는 아직 완성되지 않았습니다.

## 업그레이드 참고

- 이전 환경에서 설치했다면 의존성을 다시 설치하는 것을 권장합니다.
- 기존 `0.0.1-alpha` run 폴더는 그대로 보관해도 됩니다.
- 새 batch 실행 결과에는 active output run 폴더 안에 `batch_report.json`과 `batch_report.md`가 함께 생성됩니다.
