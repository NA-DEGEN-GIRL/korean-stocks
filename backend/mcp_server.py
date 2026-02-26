"""MCP Server for Korean Stock Analyzer.

Provides tools for Claude to fetch disclosures, analyze them,
and submit analysis results to the Railway backend.

Usage:
    Registered in ~/.mcp.json and launched automatically by Claude Code.

Environment variables:
    STOCK_API_URL: Railway backend URL (default: https://korean-stocks-production.up.railway.app)
    STOCK_ADMIN_KEY: Admin key for write operations
"""

import json
import os
import urllib.request
import urllib.error

from mcp.server.fastmcp import FastMCP

server = FastMCP("stocks-analyzer")

API_URL = os.environ.get("STOCK_API_URL", "https://korean-stocks-production.up.railway.app")
ADMIN_KEY = os.environ.get("STOCK_ADMIN_KEY", "")


def _api_get(path: str) -> dict | list:
    """Make a GET request to the stock API."""
    url = f"{API_URL}{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _api_post(path: str, data: dict | None = None) -> dict:
    """Make a POST request to the stock API."""
    url = f"{API_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    if ADMIN_KEY:
        req.add_header("X-Admin-Key", ADMIN_KEY)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


@server.tool()
def get_unanalyzed_disclosures(limit: int = 20) -> str:
    """미분석 공시 목록을 가져옵니다. AI 요약이 아직 없는 공시들을 반환합니다.

    Args:
        limit: 가져올 최대 공시 수 (기본 20)

    Returns:
        미분석 공시 목록 (id, ticker, corp_name, report_nm, rcept_dt, disclosure_url)
    """
    try:
        result = _api_get(f"/api/disclosures/unanalyzed?limit={limit}")
        items = result.get("items", [])
        if not items:
            return "미분석 공시가 없습니다."

        lines = [f"미분석 공시 {len(items)}건:\n"]
        for d in items:
            lines.append(
                f"- [ID:{d['id']}] {d.get('corp_name', '?')} ({d.get('ticker', '?')}) "
                f"| {d.get('report_nm', '?')} "
                f"| {d.get('rcept_dt', '?')} "
                f"| {d.get('disclosure_url', '')}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"오류: {e}"


@server.tool()
def get_stock_context(ticker: str) -> str:
    """종목의 맥락 정보를 가져옵니다 (기본정보 + 최근 주가 + 최근 뉴스).

    Args:
        ticker: 종목 코드 (예: 005930)

    Returns:
        종목 기본정보, 최근 5일 주가, 최근 뉴스 5건
    """
    try:
        parts = []

        # 기본 정보
        try:
            stock = _api_get(f"/api/stocks/{ticker}")
            parts.append(
                f"종목: {stock.get('name', '?')} ({ticker})\n"
                f"시장: {stock.get('market', '?')} | 섹터: {stock.get('sector', '?')}\n"
                f"시가총액: {stock.get('market_cap', '?')} | PER: {stock.get('per', '?')} | PBR: {stock.get('pbr', '?')}"
            )
        except Exception:
            parts.append(f"종목 기본정보 조회 실패: {ticker}")

        # 최근 주가
        try:
            prices = _api_get(f"/api/stocks/{ticker}/prices?limit=5")
            if prices:
                parts.append("\n최근 주가:")
                for p in prices[:5]:
                    parts.append(
                        f"  {p.get('date', '?')}: 종가 {p.get('close', '?'):,}원 "
                        f"(변동 {p.get('change_pct', 0):+.2f}%) "
                        f"거래량 {p.get('volume', 0):,}"
                    )
        except Exception:
            parts.append("\n주가 데이터 없음")

        # 최근 뉴스
        try:
            news = _api_get(f"/api/news?ticker={ticker}&limit=5")
            news_items = news.get("items", news) if isinstance(news, dict) else news
            if news_items:
                parts.append("\n최근 뉴스:")
                for n in news_items[:5]:
                    parts.append(f"  - {n.get('title', '?')} ({n.get('published_at', '?')})")
        except Exception:
            parts.append("\n뉴스 없음")

        return "\n".join(parts)
    except Exception as e:
        return f"오류: {e}"


@server.tool()
def submit_analysis(disclosure_id: int, ai_summary: str, ai_impact: str) -> str:
    """공시에 대한 AI 분석 결과를 저장합니다.

    Args:
        disclosure_id: 공시 ID
        ai_summary: AI 분석 요약 (한국어, 2-3문장)
        ai_impact: 주가 영향 판단 ("긍정", "부정", "중립" 중 하나)

    Returns:
        저장 결과
    """
    if ai_impact not in ("긍정", "부정", "중립"):
        return f"오류: ai_impact는 '긍정', '부정', '중립' 중 하나여야 합니다. 입력값: {ai_impact}"

    try:
        result = _api_post(
            f"/api/disclosures/{disclosure_id}/analysis",
            {"ai_summary": ai_summary, "ai_impact": ai_impact},
        )
        return f"분석 저장 완료: 공시 ID {disclosure_id}, 영향: {ai_impact}"
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return f"오류 ({e.code}): {body}"
    except Exception as e:
        return f"오류: {e}"


@server.tool()
def fetch_new_disclosures() -> str:
    """백엔드에서 최신 DART 공시를 수집하도록 트리거합니다.

    Returns:
        수집 시작 상태
    """
    try:
        result = _api_post("/api/system/run-job/fetch_disclosures")
        return f"공시 수집 시작됨: {result}"
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return f"오류 ({e.code}): {body}"
    except Exception as e:
        return f"오류: {e}"


if __name__ == "__main__":
    server.run()
