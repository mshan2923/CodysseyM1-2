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

## 4. Firestore에 CSV 업로드

서버가 실행 중일 때 다음 요청으로 현재 CSV 데이터를 한 번 업로드합니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/admin/seed -Method Post
```

데이터는 각각 `players`, `prices`, `patches`, `events`, `hub` 컬렉션에 저장됩니다. 기존에 사용하던 `analysis_data` 컬렉션은 삭제하지 않습니다.

예상 결과는 플레이어, 가격, 패치, 이벤트, 허브별 업로드 건수입니다. 업로드 후 아래 API는 Firestore 데이터를 우선 읽습니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/data/summary
Invoke-RestMethod 'http://127.0.0.1:8000/api/data?source=patches&limit=10'
```

## 5. 채팅 테스트

```powershell
Invoke-RestMethod http://localhost:8000/api/chat `
  -Method Post `
  -ContentType 'application/json' `
  -Body '{"message":"가장 효과가 컸던 패치는 뭐야?"}'
```

프론트엔드는 `/api/chat`을 호출하며, 채팅 컨텍스트의 분석 요약도 Firestore를 우선 사용합니다.
