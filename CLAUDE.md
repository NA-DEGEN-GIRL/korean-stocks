# 주식 분석 웹앱 (Stock Analyzer)

KOSPI/KOSDAQ 기업 분석 웹앱. 주간 단위 종목 발굴, 급등 원인 분석, 조기 발굴 기능 제공.

## 실행 방법

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # DART_API_KEY 입력 필요
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API 문서: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
앱: http://localhost:5173

## 기술 스택

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.x, SQLite (WAL), FinanceDataReader, OpenDartReader, APScheduler
- **Frontend**: Vite, React 18, TypeScript, Tailwind CSS v4, TradingView Lightweight Charts v5, @tanstack/react-query
- **배포**: Frontend → Vercel, Backend → Railway

## 프로젝트 구조

- `backend/app/models/` — SQLAlchemy ORM 모델 (stock, disclosure, news, analysis)
- `backend/app/schemas/` — Pydantic 요청/응답 스키마
- `backend/app/routers/` — FastAPI 라우트 (stocks, screener, analysis, disclosures, news, system)
- `backend/app/services/` — 비즈니스 로직 (market_data, screener, momentum, dart, news, analysis)
- `backend/app/jobs/` — APScheduler 스케줄 작업
- `frontend/src/pages/` — Dashboard, StockDetail, Screener, WeeklyDiscovery, Settings
- `frontend/src/components/` — Layout, PriceChart
- `frontend/src/api/` — Backend API 클라이언트 (stocks, screener, analysis, disclosures, news, system)

## 핵심 기능

1. **대시보드**: 급등주/급락주/거래량 급증 요약, 종목 검색
2. **종목 스크리너**: 급등/급락/거래량급증/신고가/모멘텀 5개 탭
3. **종목 상세**: 캔들차트, 투자지표, 공시, 뉴스, "왜 오르나?" 분석
4. **주간 발굴**: 주간 급등주, 거래량 급증, 신고가, 모멘텀 상위
5. **설정**: 시스템 상태, 스케줄러 관리, 수동 잡 실행, 과거 데이터 백필

## 데이터 수집 스케줄 (KST, 평일)

- 18:30 종목 동기화 (sync_stocks)
- 18:45 일별 가격 수집 (fetch_daily_prices)
- 19:00 거래량 급증 감지 (detect_volume_spikes)
- 19:30 DART 공시 수집 (fetch_disclosures)

## 코딩 컨벤션

### Python (Backend)
- snake_case (함수, 변수), PascalCase (클래스)
- 타입 힌트 필수
- FinanceDataReader 사용 (pykrx는 2026년 데이터 지원 안됨)

### TypeScript (Frontend)
- camelCase (함수, 변수), PascalCase (컴포넌트, 타입)
- 함수형 컴포넌트 + hooks
- @tanstack/react-query로 서버 상태 관리
- lightweight-charts v5 API: `chart.addSeries(CandlestickSeries, opts)`

## 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| DART_API_KEY | Y | Open DART API 인증키 |
| DATABASE_URL | N | SQLite 경로 (기본: sqlite:///./data/stocks.db) |
| CORS_ORIGINS | N | 허용 오리진 (기본: http://localhost:5173) |
| VITE_API_URL | N | 프론트엔드 빌드 시 API 주소 (배포용) |

## 주요 명령어

```bash
make dev          # Backend + Frontend 동시 실행
make backfill     # 과거 6개월 데이터 수집
make sync-stocks  # 종목 리스트 갱신
```

## API 엔드포인트

```
GET  /api/stocks                    종목 목록 (search, market, page, per_page)
GET  /api/stocks/{ticker}           종목 상세 + 펀더멘탈
GET  /api/stocks/{ticker}/prices    가격 히스토리 (자동 수집)
GET  /api/screener/top-gainers      급등주 (period, market, limit)
GET  /api/screener/top-losers       급락주
GET  /api/screener/volume-spikes    거래량 급증
GET  /api/screener/new-highs        52주 신고가
GET  /api/screener/momentum         모멘텀 랭킹
GET  /api/analysis/why-moving/{t}   왜 오르나? 종합 분석
GET  /api/disclosures               DART 공시 목록
POST /api/disclosures/fetch/{t}     공시 수집 트리거
GET  /api/news                      뉴스 목록
POST /api/news/fetch/{t}            뉴스 수집 트리거
GET  /api/system/status             시스템 상태
GET  /api/system/scheduler          스케줄러 상태
POST /api/system/run-job/{name}     수동 잡 실행
POST /api/system/backfill           과거 데이터 백필
```
