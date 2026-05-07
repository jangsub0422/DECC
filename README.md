# DECC

DECC is an AI-assisted code generation pipeline that decomposes a natural-language program request into structured module blueprints, generates Python modules in batch, validates them, and links them into a runnable application.

Current release status: `0.0.1-alpha`

## English

### Overview

DECC is a local-first AI software pipeline designed around a biologically inspired workflow.  
Its architecture is motivated by protein expression and SDS-PAGE-style verification:

- natural-language specification as the upstream input
- plasmid-style JSON blueprints as structured design artifacts
- module-by-module code generation as expression
- syntax and contract checks as validation gates
- integration into a runnable application as final assembly

### What DECC Does

- Accepts a natural-language specification
- Decomposes the request into `plasmid_*.json` module blueprints
- Generates Python modules from those blueprints
- Validates syntax and profile-based contracts
- Integrates valid outputs into a runnable `final_app.py`

### Current Scope

DECC currently includes profile-aware normalization for:

- `cli_crud`
- `file_transformer`
- `data_analysis`

This is still an alpha release. Generated code may be incomplete, inconsistent, or unsuitable for production use without review.

### Disclaimer

This project uses AI-assisted generation in multiple stages, including decomposition, code generation, validation feedback, and integration guidance.

Because this project includes AI-generated code, users should review outputs carefully before execution, reuse, redistribution, or deployment.

- Outputs may contain bugs, omissions, security issues, or incorrect assumptions
- The generated results are not guaranteed to be correct, complete, or production-ready
- Human review and testing are strongly recommended before real use
- Extra caution is required for security-sensitive, legal, medical, financial, or privacy-sensitive workflows

### Project Structure

```text
architect.py
-> plasmids_batch/runs/<run_name>/plasmid_*.json
-> run_batch.py
-> outputs/runs/<run_name>/*.py
-> integration.py
-> outputs/runs/<run_name>/final_app.py
-> root final_app.py
```

Important directories:

- `plasmids_batch/runs/`: generated blueprint runs
- `outputs/runs/`: generated Python runs
- `code_pipeline/`: contracts, assay, protocol, connectors, run-path helpers
- `web_app.py`: Streamlit wrapper UI

### Requirements

- Python 3.11+ recommended
- Python packages from `requirements.txt`
- Ollama installed and running for the recommended local-model workflow
- Optional API key only if you intentionally use a hosted API path

Install dependencies:

```bash
pip install -r requirements.txt
```

Notes:

- `requirements.txt` installs Python packages only
- Ollama is a separate local service and must be installed manually
- Hosted APIs are supported, but they are not the recommended default path for this project

### Recommended Runtime Path

The recommended way to use DECC is the local-first path:

- local Python environment
- local Streamlit wrapper
- local Ollama service for local-model workflows

Hosted APIs such as Gemini, OpenAI, and Claude are supported for both architect decomposition and module code generation, but they are optional and may introduce recurring usage cost.

### Running With The Web Wrapper

Quick launchers:

```text
Windows: start_decc_windows.bat
Linux:   start_decc_linux.sh
```

You can also run Streamlit directly:

```bash
streamlit run web_app.py
```

Recommended flow:

1. Enter a program specification
2. Enter a run name / project name
3. Choose the architect host and model
4. Generate plasmids
5. Review the current plasmids
6. Run batch generation
7. Run integration
8. Test `final_app.py`

### Running From The CLI

Generate plasmids through `architect.py`, then run:

```bash
python run_batch.py
python integration.py
python final_app.py
```

If your environment uses a different launcher, use that launcher instead of `python`.

### Versioning

This repository currently targets:

- `0.0.1-alpha`: first public alpha milestone

Version metadata is stored in:

- `VERSION.txt`
- `code_pipeline/__init__.py`

### Included Documentation

- `USER_GUIDE_KO.txt`
- `USER_GUIDE_EN.txt`
- `THIRD_PARTY_NOTICES.md`
- `RELEASE_NOTES_0.0.1-alpha.md`
- `RELEASE_NOTES_0.0.1-alpha_KO.md`

### Known Alpha Limitations

- Generated modules may still fail contract checks
- Entry modules may still require prompt tuning for some use cases
- Profile coverage is limited
- End-to-end output quality depends heavily on the selected model
- Hosted API-based generation may increase cost and operational variability
- The pipeline is designed for experimentation, not guaranteed production delivery

### Third-Party Note

This repository references third-party Python packages through `requirements.txt`.  
Those dependencies remain subject to their own licenses and, where applicable, their own service terms.

See `THIRD_PARTY_NOTICES.md` for a basic notice summary.

## 한국어

### 개요

DECC는 자연어 프로그램 요구사항을 구조화된 모듈 명세로 분해하고,
각 명세를 기반으로 Python 모듈을 생성한 뒤,
검증과 통합 과정을 거쳐 실행 가능한 결과물로 연결하는 로컬 우선 AI 코드 생성 파이프라인입니다.

이 프로젝트는 생물학적 단백질 발현 과정과 SDS-PAGE 기반 검증 흐름을 모티브로 설계되었습니다.

- 자연어 요구사항을 upstream 입력으로 사용하고
- plasmid 형태의 JSON 명세를 구조화된 설계 산출물로 만들며
- 모듈 단위 코드 생성을 발현 과정처럼 다루고
- 문법 및 contract 검증을 검증 관문처럼 사용하며
- 최종 실행 가능한 프로그램으로의 연결을 최종 조립 단계처럼 다룹니다

### DECC가 하는 일

- 자연어 프로그램 요구사항을 입력으로 받습니다
- 요구사항을 `plasmid_*.json` 모듈 명세로 분해합니다
- 각 명세를 바탕으로 Python 모듈을 생성합니다
- 문법과 profile 기반 contract를 검증합니다
- 유효한 결과물을 `final_app.py`로 연결합니다

### 현재 범위

현재 DECC는 다음 profile에 대해 정규화 규칙을 포함합니다.

- `cli_crud`
- `file_transformer`
- `data_analysis`

현재는 알파 단계이므로 생성 결과는 불완전하거나 일관되지 않을 수 있으며, 검토 없이 바로 실사용하는 것을 권장하지 않습니다.

### 면책 및 주의사항

이 프로젝트는 분해, 코드 생성, 검증 피드백, integration 단계 전반에 걸쳐 AI 보조 생성을 사용합니다.

이 프로젝트에는 AI 생성 코드가 포함될 수 있으므로, 사용자는 실행, 재사용, 재배포, 배포 전에 결과물을 주의 깊게 검토해야 합니다.

- 생성 결과에는 버그, 누락, 보안 문제, 잘못된 가정이 포함될 수 있습니다
- 생성 결과의 정확성, 완전성, 생산 환경 적합성은 보장되지 않습니다
- 실사용 전에는 반드시 사람이 직접 검토하고 테스트해야 합니다
- 보안, 법률, 의료, 재무, 개인정보 처리와 같은 민감한 목적에는 특히 추가 검토가 필요합니다

### 프로젝트 구조

```text
architect.py
-> plasmids_batch/runs/<run_name>/plasmid_*.json
-> run_batch.py
-> outputs/runs/<run_name>/*.py
-> integration.py
-> outputs/runs/<run_name>/final_app.py
-> 루트 final_app.py
```

주요 디렉터리:

- `plasmids_batch/runs/`: 생성된 plasmid run 기록
- `outputs/runs/`: 생성된 Python 결과 run 기록
- `code_pipeline/`: contracts, assay, protocol, connectors, run-path helpers
- `web_app.py`: Streamlit 기반 wrapper UI

### 요구 사항

- Python 3.11 이상 권장
- `requirements.txt`에 포함된 Python 패키지
- 권장 로컬 워크플로우를 위한 Ollama 설치 및 실행
- 상용 API 경로를 사용할 경우에만 선택적으로 API 키 필요

의존성 설치:

```bash
pip install -r requirements.txt
```

참고:

- `requirements.txt`는 Python 패키지만 설치합니다
- Ollama는 별도 설치가 필요한 로컬 서비스입니다
- 상용 API도 지원하지만, 이 프로젝트의 기본 권장 경로는 아닙니다

### 권장 실행 경로

DECC의 기본 권장 사용 방식은 로컬 우선 경로입니다.

- 로컬 Python 환경
- 로컬 Streamlit wrapper
- 로컬 Ollama 서비스 기반 코드 생성 워크플로우

Gemini, OpenAI, Claude 같은 상용 API는 architect 분해 단계와 모듈 코드 생성 단계 모두에서 사용할 수 있지만,
선택 사항이며 사용량 비용이 발생할 수 있습니다.

### 웹 Wrapper 실행

빠른 실행 파일:

```text
Windows: start_decc_windows.bat
Linux:   start_decc_linux.sh
```

직접 실행:

```bash
streamlit run web_app.py
```

권장 사용 순서:

1. 프로그램 요구사항 입력
2. Run name / project name 입력
3. Architect host와 model 선택
4. plasmid 생성
5. Current Plasmids 검토
6. run_batch 실행
7. integration 실행
8. `final_app.py` 테스트

### CLI 실행

plasmid를 생성한 뒤 다음 순서로 실행합니다.

```bash
python run_batch.py
python integration.py
python final_app.py
```

환경에 따라 `python` 대신 다른 실행 명령을 사용해도 됩니다.

### 버전 정책

현재 저장소 버전:

- `0.0.1-alpha`: 첫 공개 알파 마일스톤

버전 정보 위치:

- `VERSION.txt`
- `code_pipeline/__init__.py`

### 포함 문서

- `USER_GUIDE_KO.txt`
- `USER_GUIDE_EN.txt`
- `THIRD_PARTY_NOTICES.md`
- `RELEASE_NOTES_0.0.1-alpha.md`
- `RELEASE_NOTES_0.0.1-alpha_KO.md`

### 현재 알파 단계 한계

- 생성 모듈이 contract 검사를 통과하지 못할 수 있습니다
- 일부 entry module prompt는 추가 조정이 필요할 수 있습니다
- 지원하는 profile 범위는 아직 제한적입니다
- 생성 결과 품질은 선택한 모델에 크게 영향을 받습니다
- API 기반 생성은 비용과 운영 변동성을 높일 수 있습니다
- 이 프로젝트는 실험용 알파 단계이며, 생산 환경용 완성품은 아닙니다

### 서드파티 고지

이 저장소는 `requirements.txt`를 통해 서드파티 Python 패키지를 참조합니다.  
해당 의존성은 각자의 라이선스와, 필요한 경우 각자의 서비스 약관을 따릅니다.

자세한 요약은 `THIRD_PARTY_NOTICES.md`를 참고하세요.
