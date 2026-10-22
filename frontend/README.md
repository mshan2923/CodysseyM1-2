# Sephiria Insight 로컬 프론트엔드

대시보드, AI 분석 대화, 데이터 탐색, 대화 기록 화면을 포함합니다. AI 질문은 로컬 FastAPI의 `/api/chat`으로 전송됩니다.

## 실행

프로젝트 루트(`M2`)에서 다음 명령을 실행합니다.

```powershell
python -m http.server 5500
```

브라우저에서 [http://localhost:5500/frontend/](http://localhost:5500/frontend/)를 엽니다.

`frontend/app.js`의 `API_BASE_URL`은 기본적으로 `http://127.0.0.1:8001`입니다. FastAPI를 먼저 실행한 뒤 질문을 보내야 합니다.
