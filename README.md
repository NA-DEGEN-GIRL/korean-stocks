# 📊 Korean Stock Analyzer

KOSPI/KOSDAQ 종목 분석 웹앱. 급등주 발굴, 주가 변동 원인 분석, 공시/뉴스 연동을 제공합니다.

![Dashboard](https://img.shields.io/badge/React-18-blue) ![Backend](https://img.shields.io/badge/FastAPI-0.115-green) ![Python](https://img.shields.io/badge/Python-3.10+-yellow) ![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)

## 주요 기능

### 대시보드
- 오늘의 급등주 / 급락주 / 거래량 급증 요약
- 전체 종목 검색 (KOSPI / KOSDAQ 필터)

### 종목 스크리너
- **급등주 / 급락주** — 일간, 주간, 월간 기간별 등락률 랭킹
- **거래량 급증** — 20일 평균 대비 거래량 급증 종목
- **52주 신고가** — 신고가 근접 종목 탐지
- **모멘텀** — 7개 지표 기반 종합 모멘텀 점수 (0~100)

### 종목 상세
- TradingView 캔들스틱 차트 + 거래량
- 투자 지표 (시가총액, PER, PBR, EPS, 배당수익률)
- DART 공시 목록 (자동 수집)
- Naver Finance 뉴스 (자동 스크래핑)
- **"왜 오르나?"** — 가격 변동 + 공시 + 뉴스 + 섹터 비교 종합 분석

### 주간 발굴
- 주간 급등주, 급락주, 거래량 급증, 신고가, 모멘텀 상위 종목

### 설정
- 시스템 상태 모니터링 (데이터 수량, 최신 날짜)
- 스케줄러 관리 (4개 자동 수집 잡)
- 수동 작업 실행 (종목 동기화, 가격 수집)
- 과거 데이터 백필

## 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy 2.x, SQLite (WAL), APScheduler |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS v4, TradingView Lightweight Charts v5 |
| **데이터** | FinanceDataReader (주가), OpenDartReader (공시), Naver Finance (뉴스) |
| **상태관리** | @tanstack/react-query |

## 시작하기

### 사전 요구사항
- Python 3.10+
- Node.js 18+
- [Open DART API Key](https://opendart.fss.or.kr/) (무료 발급)

### 설치

```bash
# 레포 클론
git clone https://github.com/NA-DEGEN-GIRL/korean-stocks.git
cd korean-stocks

# Backend 설정
cd backend
pip install -r requirements.txt
cp .env.example .env
# .env 파일에서 DART_API_KEY 입력

# Frontend 설정
cd ../frontend
npm install
```

### 실행

```bash
# Backend (터미널 1)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (터미널 2)
cd frontend
npm run dev
```

- 앱: http://localhost:5173
- API 문서: http://localhost:8000/docs

### 초기 데이터 수집

앱 실행 후 설정 페이지(http://localhost:5173/settings)에서:

1. **종목 목록 동기화** — KOSPI/KOSDAQ 전체 종목 수집
2. **오늘 가격 수집** — 당일 OHLCV 데이터 수집
3. **과거 데이터 백필** (선택) — 과거 N개월 데이터 일괄 수집

또는 터미널에서:

```bash
# 종목 동기화
curl -X POST http://localhost:8000/api/system/sync-stocks

# 오늘 가격
curl -X POST http://localhost:8000/api/system/fetch-prices

# 과거 3개월 백필 (시간 소요)
curl -X POST 'http://localhost:8000/api/system/backfill?start_date=2025-12-01'
```

## 자동 수집 스케줄 (KST, 평일)

| 시간 | 작업 |
|------|------|
| 18:30 | 종목 목록 동기화 |
| 18:45 | 일별 가격(OHLCV) 수집 |
| 19:00 | 거래량 급증 감지 |
| 19:30 | DART 공시 수집 |

## 프로젝트 구조

```
korean-stocks/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── config.py            # 환경변수 설정
│   │   ├── database.py          # SQLite + SQLAlchemy
│   │   ├── models/              # DB 모델 (stock, disclosure, news, analysis)
│   │   ├── schemas/             # Pydantic 스키마
│   │   ├── routers/             # API 엔드포인트
│   │   ├── services/            # 비즈니스 로직
│   │   └── jobs/                # APScheduler 스케줄러
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── pages/               # Dashboard, StockDetail, Screener, ...
    │   ├── components/          # Layout, PriceChart
    │   ├── api/                 # API 클라이언트
    │   ├── hooks/               # React Query hooks
    │   └── types/               # TypeScript 타입
    ├── package.json
    └── vite.config.ts
```

## 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `DART_API_KEY` | Yes | Open DART API 인증키 |
| `DATABASE_URL` | No | SQLite 경로 (기본: `sqlite:///./data/stocks.db`) |
| `CORS_ORIGINS` | No | 허용 오리진 (기본: `http://localhost:5173`) |
| `VITE_API_URL` | No | 프론트엔드 배포 시 API 주소 |

## 라이선스

MIT
