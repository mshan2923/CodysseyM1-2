# Sephiria Insight Backend

커스텀 OpenAI 호환 API를 호출하고, Firestore에 분석 데이터를 저장·조회하는 FastAPI 백엔드입니다.

## 1. 가상환경 및 설치

`backend` 폴더에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. 환경변수

```powershell
Copy-Item .env.example .env
```

그 다음 `.env`의 `AI_API_KEY`에 실제 virtual-key를 입력합니다. `.env`는 Git에 커밋하지 않습니다.

Firebase 콘솔에서 서비스 계정 키 JSON을 내려받아 `backend/firebase-service-account.json`으로 저장하고, `.env`의 `FIREBASE_SERVICE_ACCOUNT_PATH`가 그 파일을 가리키게 합니다. JSON 키 파일도 Git에 커밋하지 않습니다.

## 3. 실행

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

- Health: http://localhost:8000/api/health
- Summary: http://localhost:8000/api/data/summary
- Swagger: http://localhost:8000/docs

## 4. Firestore 데이터

운영 서버는 CSV에 의존하지 않고 Firestore만 사용합니다. 분석 데이터는 `data` 컬렉션에 수동 입력할 수 있고, 기존 source별 컬렉션(`players`, `prices`, `patches`, `events`, `hub`)도 읽을 수 있습니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/data/summary
Invoke-RestMethod 'http://127.0.0.1:8000/api/data?source=patches&limit=10'
```

## 5. 데이터 CRUD 및 채팅 테스트

```powershell
Invoke-RestMethod http://localhost:8000/api/chat `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"message":"가장 효과가 컸던 패치는 뭐야?"}'
```

프론트엔드는 `/api/data`, `/api/data/summary`, `/api/chat`을 호출하며, 채팅 컨텍스트와 대시보드 수치는 모두 Firestore에서 읽습니다.
