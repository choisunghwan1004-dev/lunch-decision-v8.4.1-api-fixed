# 점심·여행 자동 결정 + AI 지역 뉴스

Node.js·Express·MySQL 기반 점심·여행 시스템과, 이를 확장하는 두 가지 AI 지역 뉴스 브랜치를 관리하는 저장소입니다. 실제 실행 폴더는 **`v84_integrated/`**입니다.

**`main`에는 V8.4.1 점심·여행 기능이 있으며, 뉴스 기능은 아래 두 개발 브랜치에만 있습니다.** 뉴스 브랜치끼리도 구현·설치 방법이 다르므로 사용할 브랜치를 먼저 선택하세요.

## 1. 브랜치 비교

### 비교 기준

2026-10-19에 GitHub의 모든 브랜치 3개와 실제 파일 내용을 확인했습니다. 아래 커밋 수와 변경 파일 수는 **이 README 추가 전 `main@023788c`**을 기준으로 한 고정 기록입니다. 이후 문서 커밋이나 개발에 따라 GitHub의 현재 수치와 달라질 수 있습니다.

| 브랜치 | 확인한 HEAD | 기준 main 대비 커밋 | 변경 파일 | 용도 |
| --- | --- | --- | --- | --- |
| [main](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/tree/main) | `023788cf604b4d735a66f6c02bdc282f7ce0c3d5` | 기준 | 기준 | V8.4.1 점심·여행 |
| [feature/v8.5.1-ai-local-news](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/tree/feature/v8.5.1-ai-local-news) | `7f124334773efcc924aaee0f47f01f0682680553` | 추가 17 / 누락 0 | 15개: 추가 14, 수정 1 | 독립 실행형 뉴스 서비스 |
| [feature/v8.5.1-news-center](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/tree/feature/v8.5.1-news-center) | `d21fc0a3a8b39898b0cc41c04b31406a100e2ca4` | 추가 5 / 누락 0 | 21개: 추가 15, 수정 6 | 기존 관리자에 통합한 뉴스 센터 |

두 뉴스 브랜치는 같은 `main@023788c`에서 각각 갈라졌습니다. 서로의 변경이 포함되어 있지 않으므로 커밋 수만으로 최신판·완성판을 판단할 수 없습니다.

고정 커밋 비교: [main → 독립형](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/compare/023788cf604b4d735a66f6c02bdc282f7ce0c3d5...7f124334773efcc924aaee0f47f01f0682680553) · [main → 통합형](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/compare/023788cf604b4d735a66f6c02bdc282f7ce0c3d5...d21fc0a3a8b39898b0cc41c04b31406a100e2ca4)

### 기능·구조 비교

| 항목 | main | ai-local-news: 독립형 | news-center: 관리자 통합형 |
| --- | --- | --- | --- |
| Node 패키지 버전 | 8.4.1 | 8.4.1 유지 | 8.5.1 |
| 점심·여행 사용자 화면 | 제공 | main과 동일 | main과 동일 |
| 뉴스 코드 폴더 | 없음 | `news-service/`: 하이픈 | `news_service/`: 밑줄 |
| 뉴스 화면 진입 | 없음 | 관리자 메뉴 → 별도 탭, `http://127.0.0.1:8000/` | 기존 `http://127.0.0.1:3100/admin` 안의 뉴스 메뉴 |
| 뉴스 인증 | 해당 없음 | 별도 HTTP Basic 계정 | 기존 Express 관리자 세션 + 서버 간 내부 토큰 |
| 뉴스 API 연결 | 없음 | 브라우저 → FastAPI 8000 | 브라우저 → `/api/news` → 내부 FastAPI 8001 |
| 지역 입력 | 점심·여행용 연쇄 선택 | 뉴스 화면에서 `districts.id` 직접 입력 | DB의 시·군·구 목록에서 선택 |
| 뉴스 DB 설정 | 없음 | 뉴스 폴더의 별도 `.env`, `NEWS_DB_*` | 상위 `.env`의 기존 `DB_*`·`V83_DB_NAME` 공유 |
| Python MySQL 드라이버 | 해당 없음 | PyMySQL | mysql-connector-python |
| 출처 중복 방지 | 해당 없음 | 출처 URL 중복 차단 없음 | 같은 주제의 URL 해시 중복 차단 |
| Fact 검증 | 해당 없음 | 출처 메타정보 확인 후 검증 처리 | 근거 연결 + 원문 대조 확인 + 검증 의견 필수 |
| Fact 수정·삭제 | 해당 없음 | API 제공, 수정 시 검증 해제 | API 제공, 수정 시 검증 해제; 기사에 사용된 Fact 삭제 차단 |
| 초안 생성 | 없음 | 검증 Fact로 텍스트 생성·저장 | 검증 Fact로 JSON 생성·검사, 초안 개정 번호 저장 |
| 문장별 근거 저장 | 없음 | 테이블만 준비, 생성 API에서 저장하지 않음 | `news_claims`·`news_claim_facts`에 저장; 문장은 `unverified` |
| OpenAI 사용 기록 | 없음 | 테이블만 준비, 생성 API에서 기록하지 않음 | 성공한 생성의 요청 ID·입출력/캐시 토큰 저장 |
| 사람 검수 결과 | 없음 | 수치·지역/날짜·인과·출처 4종 체크 저장, 실패 시 수정 요청 | 초안·근거 조회 제공; 검수 결과 저장 API 미구현 |
| 최종 승인·사용자 게시 | 없음 | 미구현; 승인 요청 HTTP 409 | 미구현; 승인·게시 API 없음 |

두 뉴스 구현 모두 OpenAI Responses API를 사용하며 기본 모델 설정은 `gpt-4.1-mini`입니다. 독립형은 `OPENAI_MODEL`, 통합형은 `OPENAI_NEWS_MODEL`로 변경합니다. 모델이 생성한 내용의 사실 여부는 사람이 원문과 대조해야 합니다.

Fact 수정 API는 두 브랜치에 있지만, 현재 뉴스 화면에는 Fact 수정 입력 UI가 없습니다. 테이블 존재만으로 승인·게시·검수 기능이 완성된 것은 아닙니다.

### 기존 코드 보존 여부와 변경 파일

확인한 두 뉴스 HEAD에서 다음 파일의 Git blob SHA가 `main@023788c`과 동일합니다.

- `public/index.html`, `public/script.js`, `public/style.css`
- `routes/api.js`, `db.js`
- `sql/01_schema.sql`, `sql/02_v84_extensions.sql`

독립형은 `news-service/`의 14개 파일을 추가하고 `public/admin.html`에 뉴스 메뉴·별도 탭 링크를 추가했습니다. `server.js`와 `package.json`은 기존과 같습니다.

통합형은 `news_service/`, `routes/news-proxy.js`, `public/news-admin.js`·`news-admin.css`, `scripts/news-setup.js`, `sql/03_news_v851.sql` 등을 추가했습니다. `server.js`에는 뉴스 프록시를 연결하고, 관리자 화면·패키지 스크립트·환경설정 예시를 확장했습니다.

## 2. main의 점심·여행 기능

- 국가 → 시·도 → 시·군·구 → 읍·면·동 → 상권 연쇄 선택, 행정·법정구역 연결 검사
- 회원가입·로그인, 개인 조건 저장, 점심 추천·선택/거절/방문 피드백·이력
- 예산·평점·음식 선호·최근 30일 이력을 반영한 규칙 기반 추천
- 관리자 지역·음식점·관광지·카페·숙박 등록 및 목록 조회
- 등록 장소를 이용한 관광 → 점심 → 카페 → 관광 → 저녁 → 숙박 코스 구성
- OpenWeather 날씨 조회, OSRM 자동차 이동 경로·시간 조회
- 기존 DB 읽기 전용 백업·이관, 신규 DB 검증, API 연결 진단

점심 추천과 여행 코스는 현재 규칙 기반입니다. 뉴스의 OpenAI 기사 생성과 별개이며, 여행 일정 전체를 날씨·예산·영업시간에 맞춰 최적화하는 엔진은 구현되어 있지 않습니다.

## 3. main 설치와 실행

### 공통 준비

- Node.js: `package.json`의 최소 요구 버전 `18.18.0` 이상
- MySQL 8.x 및 DB 생성·테이블 준비 권한
- 뉴스 브랜치 사용 시 Python 3.10 이상과 해당 브랜치의 `requirements.txt`
- 뉴스 생성 시 유효한 `OPENAI_API_KEY`와 사용 가능한 API 잔액

Windows PowerShell에서 저장소를 받습니다.

```powershell
git clone https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed.git
cd lunch-decision-v8.4.1-api-fixed
git switch main
cd v84_integrated
npm ci

# 이미 .env가 있다면 기존 설정을 유지합니다.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

다음 항목을 실제 환경에 맞게 설정합니다.

```env
PORT=3100
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=실제_MYSQL_비밀번호
OLD_DB_NAME=lunch_decision
V83_DB_NAME=lunch_decision_v83
SESSION_SECRET=32자_이상의_충분히_긴_임의값
ADMIN_USERNAME=admin
ADMIN_PASSWORD=본인만_아는_관리자_암호
OPENWEATHER_API_KEY=
GOOGLE_MAPS_API_KEY=
```

`OLD_DB_NAME`과 `V83_DB_NAME`은 서로 달라야 합니다. 현재 `setup`은 신규 DB 이름으로 **`lunch_decision_v83`만 허용**합니다.

### DB 준비

기존 데이터가 있으면 먼저 백업합니다.

```powershell
npm run backup
```

`backup`은 기존 DB 연결에 실패하면 중단됩니다. `lunch_decision` 등 이전 DB가 전혀 없는 신규 설치라면 백업할 원본이 없으므로 아래 새 DB 준비부터 시작합니다. 이미 사용 중인 DB가 있을 때는 백업 오류를 해결한 뒤 진행하세요.

```powershell
npm run setup
npm run seed:demo
npm run verify
npm run doctor
npm start
```

사용자 화면: `http://127.0.0.1:3100/` · 관리자: `http://127.0.0.1:3100/admin`

`seed:demo`는 시연용 지역·장소 데이터를 추가합니다. 실제 영업·가격·행사 정보로 사용하지 마세요. 기존 데이터를 옮길 때는 [기존 상세 README](v84_integrated/README.md)의 `migrate:plan` → 보고서 확인 → `migrate:apply` 절차를 따르세요.

### 점검 명령

```powershell
npm run check
npm run test:ui
npm run test:api
```

`test:ui`는 Node 자동 검사이며 실제 브라우저 조작 테스트가 아닙니다. `test:api`는 설정된 포트의 서버를 확인하고, 필요하면 서버를 자동 시작한 뒤 자신이 시작한 서버만 종료합니다. DB가 준비되어 있어야 합니다.

## 4. 뉴스 브랜치별 실행

아래 절차는 **점심·여행 DB가 준비된 환경**을 전제로 합니다. 브랜치 선택은 저장소 최상위에서 실행하고, 실행 중인 서버를 먼저 종료하세요. 뉴스 브랜치를 교체하기 전에는 5절의 DB 호환성을 확인하세요.

### A. 독립형: feature/v8.5.1-ai-local-news

저장소 최상위에서:

```powershell
git fetch origin
git switch feature/v8.5.1-ai-local-news
cd v84_integrated
npm ci
npm start
```

별도 PowerShell 창에서 `v84_integrated/news-service` 폴더로 이동합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

이 폴더의 `.env`에 `NEWS_DB_HOST`·`NEWS_DB_PORT`·`NEWS_DB_USER`·`NEWS_DB_PASSWORD`·`NEWS_DB_NAME`, `NEWS_ADMIN_USERNAME`·`NEWS_ADMIN_PASSWORD`, `OPENAI_API_KEY`·`OPENAI_MODEL`을 설정합니다. 뉴스 DB는 기존 지역 테이블이 있는 DB를 지정해야 하며, 기본값은 `lunch_decision_v83`입니다.

```powershell
.\.venv\Scripts\python.exe setup.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

뉴스 화면: `http://127.0.0.1:8000/`. 기존 관리자 뉴스 메뉴에서도 이 주소를 새 탭으로 엽니다. 뉴스 관리자 계정으로 한 번 더 인증합니다.

같은 폴더의 `live_check.py`는 MySQL의 뉴스 테이블 10개와 지역 테이블을 확인합니다. `--openai` 옵션을 붙이면 별도의 유료 모델 요청도 실행합니다. 결과는 `news-service/diagnostics/news-live-check.json`에 저장됩니다. 이 점검만으로 기사 생성 전체 흐름을 검증한 것은 아닙니다.

구현 근거: [뉴스 README](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/7f124334773efcc924aaee0f47f01f0682680553/v84_integrated/news-service/README.md) · [API·검수 로직](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/7f124334773efcc924aaee0f47f01f0682680553/v84_integrated/news-service/app.py)

### B. 관리자 통합형: feature/v8.5.1-news-center

저장소 최상위에서:

```powershell
git fetch origin
git switch feature/v8.5.1-news-center
cd v84_integrated
npm ci
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r news_service/requirements.txt
notepad .env
```

기존 `.env`의 DB·관리자 설정을 유지하고 다음을 추가합니다. `.env`가 없는 새 환경이라면 3절의 공통 설정을 먼저 진행하세요.

```env
NEWS_INTERNAL_TOKEN=64자리_임의_hex_값
OPENAI_API_KEY=본인의_API_키
OPENAI_NEWS_MODEL=gpt-4.1-mini
```

토큰 생성: `.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"`

DB 백업과 스키마 호환성 확인 후 뉴스 테이블을 준비합니다.

```powershell
npm run backup
npm run news:setup
.\.venv\Scripts\python.exe -m pytest -q news_service/tests
```

PowerShell 창 A, `v84_integrated`에서 내부 뉴스 서버를 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn news_service.app:app --host 127.0.0.1 --port 8001
```

PowerShell 창 B, 같은 폴더에서 `npm start`를 실행합니다. `http://127.0.0.1:3100/admin`에 로그인하고 뉴스 메뉴를 엽니다. 8001은 내부 API이며 별도 뉴스 홈 화면이 아닙니다.

패키지에는 `news:run`·`news:test`·`news:test:real`도 있습니다. 이 명령은 PATH의 `python`을 사용하므로 가상환경을 활성화하거나 위처럼 `.\.venv\Scripts\python.exe`를 직접 지정하세요.

실제 DB·OpenAI 통합 점검은 아래 명령입니다. **가상 주제·출처·Fact·초안을 DB에 저장하고, 유료 모델 요청을 실행합니다.** 테스트 데이터는 자동 삭제되지 않습니다.

```powershell
.\.venv\Scripts\python.exe news_service/tests/real_integration.py --run-live
```

결과: `diagnostics/news-real-test.json`의 `phase: "passed"`, `real_db: true`, `real_openai: true`. 이 스크립트는 내부 FastAPI를 직접 점검하므로 Express 로그인·프록시·화면 동작은 별도 확인해야 합니다.

구현 근거: [V8.5.1 안내](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/d21fc0a3a8b39898b0cc41c04b31406a100e2ca4/v84_integrated/README_V8.5.1.md) · [내부 API](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/d21fc0a3a8b39898b0cc41c04b31406a100e2ca4/v84_integrated/news_service/app.py) · [관리자 프록시](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/d21fc0a3a8b39898b0cc41c04b31406a100e2ca4/v84_integrated/routes/news-proxy.js)

## 5. 뉴스 DB 호환성과 브랜치 전환

두 뉴스 브랜치는 아래 **같은 이름의 테이블 10개에 서로 다른 스키마**를 사용합니다.

`news_topics`, `news_sources`, `news_facts`, `news_fact_evidence`, `news_drafts`, `news_claims`, `news_claim_facts`, `news_reviews`, `news_publications`, `news_ai_usage`

예를 들어 통합형은 `news_topics.is_demo`, `news_sources.source_url_sha256`, `news_drafts.revision_no` 등을 요구하지만 독립형 스키마에는 없습니다. `news_reviews`도 독립형의 `check_passed/comment`와 통합형의 `action/reason`으로 다릅니다.

양쪽 설치 스크립트의 `CREATE TABLE IF NOT EXISTS`는 기존 테이블의 컬럼을 변환하지 않습니다. 따라서 **독립형 DB에 통합형 setup을 실행하는 것만으로 전환되지 않으며, API에서 컬럼 오류가 발생할 수 있습니다.**

- 두 구현을 비교 실행할 때는 각각 분리된 MySQL 시험 환경 또는 검증된 DB 복제본을 사용하세요. 통합형 설치 SQL은 `lunch_decision_v83` 이름을 사용합니다.
- 기존 뉴스 데이터를 유지하며 전환하는 자동 마이그레이션은 없습니다. 백업과 컬럼·데이터 매핑 계획이 먼저 필요합니다.
- `git switch`는 소스만 바꿉니다. DB 데이터·스키마·로컬 `.env`를 이전 상태로 되돌리지 않습니다.
- 두 브랜치를 함께 병합하려면 뉴스 폴더·API·관리자 화면·인증·스키마를 하나로 정리해야 합니다. 이 README 작성에서는 병합하거나 DB를 변경하지 않았습니다.

스키마 비교: [독립형 SQL](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/7f124334773efcc924aaee0f47f01f0682680553/v84_integrated/news-service/sql/01_news_schema.sql) · [통합형 SQL](https://github.com/choisunghwan1004-dev/lunch-decision-v8.4.1-api-fixed/blob/d21fc0a3a8b39898b0cc41c04b31406a100e2ca4/v84_integrated/sql/03_news_v851.sql)

## 6. 현재 제한과 확인할 동작

- Google Places 자동 동기화는 세 브랜치 모두 HTTP 501로 비활성화되어 있습니다. 관리자 수동 등록은 별도 기능입니다.
- 여행 샘플은 실제 영업 정보를 보장하지 않습니다. 경로 조회 실패나 좌표 누락 시 이동시간은 미확인입니다.
- 두 뉴스 브랜치 모두 원문 자동 수집, Notion 자동 등록, 예약 실행, 최종 승인·사용자 공개가 구현되어 있지 않습니다.
- 통합형의 `package.json`은 8.5.1이지만 기존 `/health`·`/api/health` 응답과 서버 시작 문구는 V8.4.1로 남아 있습니다. 브랜치 확인은 `git branch --show-current`와 뉴스 파일 존재 여부를 함께 보세요.
- 뉴스 API 키·관리자 암호·내부 토큰이 포함된 `.env`와 백업 파일은 Git에 올리지 마세요. 현재 실행 명령은 로컬 개발 환경을 전제로 합니다.

브라우저에서는 ① 지역 선택 → 점심 추천·여행 코스, ② 선택한 뉴스 브랜치에서 출처 → Fact → 검증 → 초안 생성 흐름을 확인하세요. 독립형은 4종 검수 저장, 통합형은 초안의 문장별 Fact 연결도 확인합니다.

**이 문서는 소스와 Git 비교 결과를 설명합니다. 실제 MySQL·OpenAI·브라우저 통합 실행 성공을 보증하는 테스트 보고서가 아닙니다.** 기존 설치·이관·복구 세부 절차는 [v84_integrated/README.md](v84_integrated/README.md), 기존 DB 관계는 [ERD-V8.3](v84_integrated/ERD-V8.3.md)·[ERD-V8.4](v84_integrated/ERD-V8.4.md)를 참고하세요.
