# Sephiria Insight Agent

세피리아(Sephiria)의 플레이어 수 변화를 중심으로 가격, 패치, 허브 팔로워 데이터를 함께 분석하는 AI Agent 웹서비스입니다.

M1에서 수행한 패치 전후 플레이어 수 분석을 서비스 형태로 확장했습니다. 사용자는 분석 대시보드에서 주요 지표를 확인하고, 자연어로 질문해 AI의 해석을 받을 수 있습니다.

## 프로젝트 목표

일반적인 챗봇이 아니라 실제 분석 데이터를 참고해 답변하는 AI 분석 서비스를 만드는 것이 목표입니다.

- 플레이어 수 시계열 분석
- 가격 변경 시점과 플레이어 변화 비교
- 패치 전후 변화율 및 지속성 분석
- 허브 팔로워 추이 확인
- Firestore 기반 데이터 저장·조회
- 커스텀 OpenAI 호환 AI 제공자 연동
- Vercel 프론트엔드와 Render 백엔드 배포

## 데이터 구성

| 데이터 | 원본 파일 | 설명 |
|---|---|---|
| 플레이어 수 | `steamdb_Player_chart.csv` | 플레이어 수와 평균 플레이어 수 시계열 |
| 가격 | `steamdb_Price_chart.csv` | 가격이 변경된 시점의 스냅샷 |
| 패치 | `patch_analysis.csv` | 73개 패치일의 전후 변화 분석 |
| 패치 이벤트 | `event_analysis.csv` | 가까운 패치를 묶은 24개 이벤트 분석 |
| 허브 | `steamdb_Hub_chart.csv` | 일별 누적 팔로워 수 |

현재 원본 데이터 규모는 다음과 같습니다.

- 플레이어 원본 행: 2,108개
- 일별 평균 플레이어 값: 575개
- 가격 스냅샷: 21개
- 패치일: 73개
- 패치 이벤트: 24개
- 허브 데이터: 1,059개

M1 분석에서는 1.0 정식 출시 이후 플레이어 수가 이전 7일 평균보다 약 1,388% 증가한 것으로 관찰되었습니다. 다만 정식 출시, 홍보, 가격 변화가 함께 발생했을 수 있으므로 패치 자체의 인과 효과로 단정하지 않습니다.

## 시스템 구조

```text
Vercel
  └─ HTML / CSS / JavaScript frontend
          │
          │ POST /api/chat
          ▼
Render
  └─ FastAPI backend
       ├─ Firestore: players / prices / patches / events / hub
       ├─ 분석 요약 컨텍스트 생성
       └─ 커스텀 AI 제공자 호출
              │
              ▼
       https://copa.codyssey.kr/v1/chat/completions
```

## 폴더 구조

```text
M2/
├─ backend/
│  ├─ main.py
│  ├─ config.py
│  ├─ schemas.py
│  ├─ ai_service.py
│  ├─ data_service.py
│  ├─ firestore_service.py
│  ├─ firestore_summary.py
│  ├─ requirements.txt
│  ├─ .env.example
│  └─ README.md
├─ frontend/
│  ├─ index.html
│  ├─ styles.css
│  ├─ app.js
│  └─ README.md
├─ steamdb_Player_chart.csv
├─ steamdb_Price_chart.csv
├─ patch_analysis.csv
├─ event_analysis.csv
├─ steamdb_Hub_chart.csv
└─ M1_REPORT.md
```

## 로컬 실행

### 프론트엔드

프로젝트 루트에서 실행합니다.

```powershell
python -m http.server 5500
```

접속 주소:

```text
http://localhost:5500/frontend/
```

### 백엔드

`backend` 폴더에서 실행합니다.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`.env.example`을 복사해 `.env`를 만든 뒤 값을 입력합니다.

```powershell
Copy-Item .env.example .env
```

로컬 서버 실행:

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --port 8001
```

주요 주소:

- API 안내: `http://127.0.0.1:8001/`
- Health Check: `http://127.0.0.1:8001/api/health`
- Swagger UI: `http://127.0.0.1:8001/docs`
- 분석 요약: `http://127.0.0.1:8001/api/data/summary`

## 환경변수

```env
AI_BASE_URL=https://copa.codyssey.kr/v1
AI_API_KEY=커스텀_제공자_virtual_key
AI_MODEL=gpt-5-mini
AI_REQUEST_TIMEOUT_SECONDS=60
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
FIRESTORE_COLLECTION_PREFIX=
```

배포 환경에서는 Firebase JSON 파일을 저장소에 올리지 말고 `FIREBASE_SERVICE_ACCOUNT_JSON` 환경변수에 서비스 계정 JSON 전체를 저장합니다.

API 키, Firebase 서비스 계정 JSON, `.env` 파일은 GitHub나 프론트엔드 코드에 포함하지 않습니다.

## Firestore 데이터 업로드

현재 CSV 데이터는 다음 컬렉션으로 분리해 저장합니다.

```text
players/
prices/
patches/
events/
hub/
```

서버가 실행 중일 때 최초 1회 업로드합니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/admin/seed -Method Post
```

업로드 후 조회합니다.

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/data/summary
Invoke-RestMethod "http://127.0.0.1:8001/api/data?source=patches&limit=10"
```

## API

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/` | API 안내 |
| `GET` | `/api/health` | 서버와 AI 설정 확인 |
| `GET` | `/api/data/summary` | Firestore 분석 요약 |
| `GET` | `/api/data?source=patches` | 특정 데이터 컬렉션 조회 |
| `POST` | `/api/admin/seed` | CSV를 Firestore에 업로드 |
| `POST` | `/api/chat` | 분석 컨텍스트 기반 AI 질문 |

채팅 요청 예시:

```json
{
  "message": "가장 효과가 컸던 패치는 뭐야?",
  "conversation": []
}
```

## AI 응답 흐름

```text
사용자 질문
  ↓
FastAPI /api/chat
  ↓
Firestore 분석 요약 조회
  ↓
시스템 프롬프트 + 분석 컨텍스트 구성
  ↓
커스텀 AI API 호출
  ↓
AI 답변 반환
```

AI는 플레이어 수, 가격, 패치, 허브 데이터를 함께 참고하지만, 관찰된 동시 변화와 인과관계를 구분하도록 설계했습니다.

## 배포

### Render 백엔드

Render Web Service 설정:

```text
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check Path: /api/health
```

Render 환경변수에는 다음을 입력합니다.

```text
AI_BASE_URL
AI_API_KEY
AI_MODEL
ALLOWED_ORIGINS
FIREBASE_SERVICE_ACCOUNT_JSON
FIRESTORE_COLLECTION_PREFIX
```

### Vercel 프론트엔드

Vercel Project 설정:

```text
Root Directory: frontend
Framework Preset: Other
Build Command: 비워두기
Output Directory: .
```

배포 전에 `frontend/app.js`의 `API_BASE_URL`을 Render 백엔드 주소로 설정합니다.

```javascript
const API_BASE_URL = 'https://your-backend.onrender.com';
```

Render의 `ALLOWED_ORIGINS`에는 Vercel 도메인을 넣고, 두 서비스를 각각 재배포해야 합니다.

## 현재 구현 상태

- [x] 로컬 프론트엔드 대시보드
- [x] AI 채팅 UI
- [x] FastAPI 서버
- [x] 커스텀 OpenAI 호환 AI 제공자 연결
- [x] CSV 분석 요약
- [x] Firebase Admin SDK 연결
- [x] Firestore 컬렉션 분리 저장
- [x] Firestore 데이터 조회
- [x] Render 배포 설정
- [x] Vercel 배포용 API 주소 설정
- [ ] 대화 기록 Firestore 저장 API
- [ ] 데이터 CRUD UI 및 API
- [ ] Function Calling 또는 MCP 연동
- [ ] 배포 환경 최종 통합 테스트

## 검증 체크리스트

- `/api/health`가 200을 반환하는가
- `/api/data/summary`의 데이터 출처가 Firestore인가
- `/api/data?source=patches`가 패치 컬렉션을 조회하는가
- `/api/chat`이 커스텀 AI 응답을 반환하는가
- Vercel 프론트엔드가 Render API를 호출하는가
- CORS 오류가 발생하지 않는가
- API 키와 Firebase 서비스 계정 키가 프론트엔드에 노출되지 않는가
- 패치 효과를 인과관계로 과장하지 않는가

## 참고 자료

- `M1_REPORT.md`: 세피리아 패치 전후 플레이어 수 분석
- `미션 - AI 응용 학습2.pdf`: AI Agent 서비스 구현 요구사항
