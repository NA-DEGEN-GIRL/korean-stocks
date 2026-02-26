#!/bin/bash
# 미분석 공시를 Claude Code MCP를 통해 자동 분석하는 스크립트
# crontab 예시: 30 20 * * 1-5 /root/stocks/scripts/analyze_disclosures.sh >> /root/stocks/scripts/analyze.log 2>&1

cd /root/stocks

PROMPT='미분석 공시를 확인하고 모두 분석해줘.
1. fetch_new_disclosures로 최신 공시 수집
2. get_unanalyzed_disclosures로 미분석 목록 확인
3. 각 공시에 대해 get_stock_context로 종목 맥락 파악
4. submit_analysis로 분석 결과 저장 (ai_summary: 한국어 2-3문장, ai_impact: 긍정/부정/중립)
5. 정형적 공시(투자설명서, 일괄신고 등)는 간략히 중립 처리
6. 핵심 공시(실적변경, 시설투자, 합병 등)는 상세 분석'

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting disclosure analysis..."
claude -p "$PROMPT" --allowedTools "mcp__stocks-analyzer__*"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Analysis complete."
