# Proposal: LLM Integration (Gemini) for Trading Bot

This document outlines a strategy to integrate Google Gemini LLM into the existing trading bot architecture.

## Objectives
1.  **Enhance Decision Making**: Use LLM reasoning to validate technical signals (Sanity Check).
2.  **Market Sentiment Analysis**: Analyze external data (news, social) to adjust strategy bias.
3.  **Dynamic Parameter Tuning**: Use LLM to suggest weight adjustments based on recent market conditions.
4.  **Explainability**: Generate human-readable explanations for trade entries/exits.

---

## Integration Architecture

We propose a **Hybrid Approach**: The core execution remains rule-based (UNUM Score), while the LLM acts as a high-level analyst/advisor.

### 1. Level 1: The "Sanity Check" (Recommended Starting Point)
Before entering a trade based on UNUM Score, the bot sends a snapshot of technical data to Gemini.

*   **Input**: JSON containing current price, RSI, MACD, ADX, Support/Resistance levels, and the tentative UNUM decision (e.g., "Strong Buy").
*   **Prompt**: "You are a senior crypto trader. Review these technical indicators. The algorithm suggests a BUY. Do you see any major contradictions or risks? Reply with CONFIRM or REJECT and a 1-sentence reason."
*   **Output**: `{"decision": "CONFIRM", "confidence": 0.9, "reason": "RSI is not yet overbought and MACD just crossed up."}`
*   **Action**: If "REJECT" or low confidence, skip the trade or reduce position size.

### 2. Level 2: Dynamic Weight Adjustment (Meta-Strategy)
Use Gemini to analyze the "Market Regime" and adjust the weights in `SignalAggregator`.

*   **Trigger**: Every 4 hours (on candle close).
*   **Input**: Normalized values of volatility (ATR), trend strength (ADX), and recent price action.
*   **Prompt**: "Analyze the current market regime (Trending vs Ranging vs Choppy). Suggest optimal weights for Trend, Volume, and Momentum signals."
*   **Output**: `{"trend_w": 0.6, "vol_w": 0.1, "mom_w": 0.3}`
*   **Action**: Update `self.weights` in `strategy.py`.

### 3. Level 3: Sentiment Analysis (Requires External Data)
Integrate news APIs (e.g., CryptoPanic, Twitter) to feed text into Gemini.

*   **Input**: Headlines and summaries from the last hour.
*   **analysis**: "Sentiment Score" (-1.0 to +1.0).
*   **Action**: Add `sentiment_score` as a 4th component to the UNUM calculations.

---

## Technical Implementation Plan

### Step 1: Gemini Client Setup
*   Create `backend/src/core/llm.py`.
*   Implement `GeminiClient` class using `google-generativeai` library.
*   Securely handle API Key via `.env`.

### Step 2: Prompt Engineering
*   Design and test prompts for "Technical Analysis" and "Market Regime".
*   Ensure outputs are strictly JSON for parsing.

### Step 3: Integration in `strategy.py`
*   Add `ask_llm_confirmation()` method to `SignalAggregator`.
*   Call this method only when `abs(unum_score) > threshold` to save API credits and latency.

### Step 4: UI Updates
*   Add a "Gemini Insight" panel to the Dashboard.
*   Show the LLM's explanation for the last signal.

## Risks & Mitigations
*   **Latency**: LLM calls are slow (1-3s). *Mitigation*: Run async; only use for 4h timeframe (plenty of time).
*   **Hallucinations**: LLM might invent patterns. *Mitigation*: Provide strict context (only provided numbers); use it as a filter (confirmer), not a generator.
*   **Cost/Rate Limits**: *Mitigation*: Cache responses; limit calls to high-conviction setups.

---

## Next Steps
1.  Approve this proposal.
2.  Obtain Google Gemini API Key.
3.  Begin with **Level 1 (Sanity Check)** implementation.
