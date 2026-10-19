# V8.5.1 — AI 지역 뉴스 제작 센터

지역 축제·관광 정보를 뉴스로 작성하는 관리자 전용 모듈입니다. 기존 V8.4.1 점심·여행 기능은 그대로 유지합니다.

## 구현 범위
1. 기존 MySQL districts를 사용하여 뉴스 지역과 주제 선택
2. 출처 URL/기관/제목 수동 등록, 중복 차단
3. Fact Sheet 등록·조회·수정·삭제, 같은 주제의 출처 근거 연결
4. 관리자의 원문 대조 확인과 검증 의견을 거쳐 verified 처리
5. verified Fact만 OpenAI Responses API (`gpt-4.1-mini`)에 전송해 JSON 초안 생성
6. news_drafts / news_claims / news_ai_usage 저장; 생성 문장은 항상 unverified
7. **최종 기사 승인·사용자 게시는 V8.5.2에서 구현. 이 버전은 자동 게시 금지**

## Windows 설치
```powershell
cd v84_integrated
npm install
npm run backup
Copy-Item .env.example .env   # 기존 .env가 있다면 복사하지 말고 기존 내용을 유지
notepad .env
python -m pip install -r news_service/requirements.txt
npm run news:setup
```

.env에 `NEWS_INTERNAL_TOKEN`(64자리 hex), `OPENAI_API_KEY`, `OPENAI_NEWS_MODEL=gpt-4.1-mini`를 설정합니다.
키 생성: `python -c "import secrets; print(secrets.token_hex(32))"`.

PowerShell 창 A: `npm run news:run` (내부 포트 8001)
PowerShell 창 B: `npm start` (웹 포트 3100)
브라우저: `http://127.0.0.1:3100/admin` → 뉴스 메뉴.

오프라인 테스트: `npm run news:test`.
실제 MySQL + 실제 OpenAI(호출 비용 발생): 두 서버 실행 후 `npm run news:test:real`.
`diagnostics/news-real-test.json`의 결과가 passed일 때만 실통합 성공입니다.

## 보안
기존 Express 관리자 세션을 통과한 요청만 Node 내부 프록시를 통해 FastAPI에 전달됩니다.
FastAPI는 로컬호스트 전용, NEWS_INTERNAL_TOKEN은 서버 간 인증에 사용합니다.
.env, API 키 및 백업 파일을 GitHub에 업로드하지 않습니다.
실제 원문 수집 자동화, 언론 기사 3건의 Notion 등록, 예약 실행은 미구현입니다.

[실제 V8.4 상세 README](README.md) · [노션 AI사업계획서 V8.5.1](https://app.notion.com/p/3fe28cb9cfd78112ae1ed0702416cc25)
