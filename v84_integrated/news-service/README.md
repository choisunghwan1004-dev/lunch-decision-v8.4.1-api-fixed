# V8.5.1 AI 지역 뉴스 제작 센터

기존 점심·여행 **Node.js V8.4.1을 유지**하고 뉴스 제작만 FastAPI 서비스로 별도 실행합니다. 관리자 메뉴 `📰 AI 지역 뉴스`에서 새 모듈로 이동합니다.

## 구현 기능
- 종로구 등 기존 `districts.id` 기준 뉴스 주제 등록
- 공식 원본 자료 URL/발행일과 연결된 Fact Sheet 등록·조회·수정·삭제
- 관리자가 출처를 확인한 사실만 `verified` 처리
- OpenAI Responses API `gpt-4.1-mini` 검증 Fact 전용 기사 초안 생성
- 기자 검수 체크리스트 4종과 반려 처리
- **V8.5.1 승인·게시 미구현: 승인 요청은 409 오류**

## Windows 11 설치
```powershell
cd v84_integrated\news-service
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python setup.py
python -m pytest -q tests
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
`.env`에는 MySQL 비밀번호, 관리자 암호, OpenAI API 키를 입력하고 GitHub에 업로드하지 않습니다. `python setup.py`는 기존 `lunch_decision_v83`에 뉴스 전용 테이블만 추가합니다. 반드시 DB를 백업하고 실행하세요.

Node.js 점심·여행 서버는 기존대로 `npm start`로 3100 포트에서 실행합니다. **뉴스 제작 화면:** http://127.0.0.1:8000 (개발용 HTTP Basic 인증).

## 검증 상태
- 순수 Fact Sheet 검증 및 승인 차단 로직: 자동 테스트 가능
- 사용자 PC의 실제 MySQL 생성/CRUD: 별도 실행 필요
- OpenAI 유료 API 실제 요청: `OPENAI_API_KEY` 입력 후 테스트 필요
- 온라인 운영 서비스 공개: 현재 불가. HTTPS, 통합 관리자 세션, CSRF 방어·요청 제한은 정식 배포 전에 추가해야 함

## 평가 양식 대응
- 문제 1-1: 기획/기능/화면/DB/데이터 출처/개발환경 설계
- 문제 1-2: FastAPI + MySQL CRUD + Fact Sheet + 초안 생성
- 문제 1-3: 수치/지역·시각/인과/출처 체크리스트, 실패 시 승인 차단
- 문제 2: Notion 원본 기사 3건 수집/생성 기사 작성/지침 변경 비교/오전 9시 자동화는 **별도 후속 과제**이며 실행됐다고 기재하지 않음

## 수정 파일만 업로드
```powershell
git checkout feature/v8.5.1-ai-local-news
git add v84_integrated/public/admin.html v84_integrated/news-service/
git diff --cached --stat
git commit -m "feat(news): incremental V8.5.1 update"
git push origin feature/v8.5.1-ai-local-news
```
기존 소스를 통째로 교체하지 않습니다. 브랜치 PR 검토 후 `main`에 병합할 수 있습니다.
