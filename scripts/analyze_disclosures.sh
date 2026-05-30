#!/bin/bash
# 미분석 공시를 Claude Code MCP를 통해 자동 분석하는 스크립트
# crontab: */10 * * * * /root/stocks/scripts/analyze_disclosures.sh >> /root/stocks/scripts/analyze.log 2>&1

export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node/ 2>/dev/null | tail -1)/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

cd /root/stocks

PROMPT='미분석 공시를 확인하고 모두 분석해줘. 미분석이 0건이 될 때까지 반복해야 한다.

작업 순서:
1. fetch_new_disclosures로 최신 공시 수집
2. get_unanalyzed_disclosures(limit=20)로 미분석 목록 확인
3. 각 공시에 대해 get_stock_context로 종목 맥락 파악 후 submit_analysis로 분석 결과 저장
   - ai_summary: 한국어 2-3문장
   - ai_impact: 긍정/부정/중립
   - 정형적 공시(투자설명서, 일괄신고, 기업집단현황 등)는 간략히 중립 처리
   - 핵심 공시(실적변경, 시설투자, 합병, 유상증자 등)는 상세 분석
4. 20건 처리 후 다시 get_unanalyzed_disclosures로 확인
5. 미분석이 남아있으면 3-4를 반복. 0건이 되면 종료.

중요: 반드시 미분석 0건이 될 때까지 반복할 것. 한 번만 돌고 끝내지 말 것.'

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting disclosure analysis..."
claude -p "$PROMPT" --allowedTools "mcp__stocks-analyzer__*"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Analysis complete."
