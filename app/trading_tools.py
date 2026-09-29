# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


def search_ticker(company_or_query: str) -> Dict[str, Any]:
    """Searches for a stock ticker symbol given a company name or query string.

    Args:
        company_or_query: The name of the company or query (e.g. 'Apple', 'Tesla', 'Microsoft', 'NVDA').

    Returns:
        A dictionary with matched tickers including symbol, company name, exchange, and quote type.
    """
    clean_query = company_or_query.strip()
    encoded = urllib.parse.quote(clean_query)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={encoded}&quotesCount=5&newsCount=0"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            quotes = data.get("quotes", [])
            results = []
            for q in quotes:
                symbol = q.get("symbol")
                name = q.get("shortname") or q.get("longname")
                exchange = q.get("exchange")
                quote_type = q.get("quoteType")
                if symbol and (quote_type in ("EQUITY", "ETF", None)):
                    results.append({
                        "symbol": symbol,
                        "name": name,
                        "exchange": exchange,
                        "type": quote_type
                    })
            if not results and quotes:
                for q in quotes[:3]:
                    results.append({
                        "symbol": q.get("symbol"),
                        "name": q.get("shortname") or q.get("longname"),
                        "exchange": q.get("exchange"),
                        "type": q.get("quoteType")
                    })
            
            best_match = results[0]["symbol"] if results else clean_query.upper()
            return {
                "query": clean_query,
                "best_match_symbol": best_match,
                "matches": results
            }
    except Exception as e:
        return {
            "query": clean_query,
            "best_match_symbol": clean_query.upper(),
            "matches": [],
            "error": str(e)
        }


def _calculate_sma(prices: List[float], window: int) -> List[Optional[float]]:
    """Calculates Simple Moving Average for a list of prices."""
    smas: List[Optional[float]] = []
    for i in range(len(prices)):
        if i + 1 < window:
            smas.append(None)
        else:
            avg = sum(prices[i + 1 - window : i + 1]) / window
            smas.append(round(avg, 2))
    return smas


def _calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculates Relative Strength Index for the most recent period."""
    if len(prices) < period + 1:
        return None
    
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


def get_crossover_signals(symbol: str) -> Dict[str, Any]:
    """Fetches 1 year of daily historical prices for a stock ticker and computes swing trading crossover indicators.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA', 'NVDA').

    Returns:
        A dictionary containing current price, 1-year high/low, SMA 20, SMA 50, SMA 200, RSI 14,
        recent crossover status, and algorithmic swing trade recommendation (BUY, SELL, or HOLD).
    """
    clean_sym = symbol.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_sym}?range=1y&interval=1d"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data["chart"]["result"][0]
            meta = result.get("meta", {})
            quote = result["indicators"]["quote"][0]
            
            raw_closes = quote.get("close", [])
            raw_highs = quote.get("high", [])
            raw_lows = quote.get("low", [])
            timestamps = result.get("timestamp", [])
            
            valid_points = []
            for t, c, h, l in zip(timestamps, raw_closes, raw_highs, raw_lows):
                if c is not None and h is not None and l is not None:
                    valid_points.append({"ts": t, "close": float(c), "high": float(h), "low": float(l)})
            
            if len(valid_points) < 50:
                return {
                    "symbol": clean_sym,
                    "error": f"Insufficient historical data points ({len(valid_points)}) to calculate 50-day crossover."
                }
            
            closes = [p["close"] for p in valid_points]
            highs = [p["high"] for p in valid_points]
            lows = [p["low"] for p in valid_points]
            
            current_price = round(closes[-1], 2)
            year_high = round(max(highs), 2)
            year_low = round(min(lows), 2)
            
            sma20_series = _calculate_sma(closes, 20)
            sma50_series = _calculate_sma(closes, 50)
            sma200_series = _calculate_sma(closes, 200) if len(closes) >= 200 else None
            
            sma20_curr = sma20_series[-1]
            sma50_curr = sma50_series[-1]
            sma200_curr = sma200_series[-1] if sma200_series and sma200_series[-1] else None
            rsi14 = _calculate_rsi(closes, 14)
            
            recent_cross = "None"
            cross_days_ago = None
            lookback = min(15, len(sma20_series) - 1)
            
            for i in range(1, lookback):
                prev_sma20 = sma20_series[-i - 1]
                prev_sma50 = sma50_series[-i - 1]
                curr_sma20 = sma20_series[-i]
                curr_sma50 = sma50_series[-i]
                
                if prev_sma20 and prev_sma50 and curr_sma20 and curr_sma50:
                    if prev_sma20 <= prev_sma50 and curr_sma20 > curr_sma50:
                        recent_cross = "BULLISH_CROSSOVER (SMA 20 crossed ABOVE SMA 50)"
                        cross_days_ago = i - 1
                        break
                    elif prev_sma20 >= prev_sma50 and curr_sma20 < curr_sma50:
                        recent_cross = "BEARISH_CROSSOVER (SMA 20 crossed BELOW SMA 50)"
                        cross_days_ago = i - 1
                        break
            
            sma20_vs_sma50 = "BULLISH (SMA 20 > SMA 50)" if (sma20_curr and sma50_curr and sma20_curr > sma50_curr) else "BEARISH (SMA 20 < SMA 50)"
            
            macro_trend = "UNKNOWN"
            if sma200_curr:
                macro_trend = "UPTREND (Price > SMA 200)" if current_price > sma200_curr else "DOWNTREND (Price < SMA 200)"
            
            score = 0
            if sma20_curr and sma50_curr:
                if sma20_curr > sma50_curr:
                    score += 2
                else:
                    score -= 2
            
            if "BULLISH" in recent_cross:
                score += 3
            elif "BEARISH" in recent_cross:
                score -= 3
                
            if sma200_curr:
                if current_price > sma200_curr:
                    score += 1
                else:
                    score -= 1
                    
            rsi_condition = "NEUTRAL"
            if rsi14 is not None:
                if rsi14 > 70:
                    rsi_condition = "OVERBOUGHT (>70)"
                    score -= 1
                elif rsi14 < 30:
                    rsi_condition = "OVERSOLD (<30)"
                    score += 1
                else:
                    rsi_condition = f"NORMAL ({rsi14})"
            
            if score >= 3:
                action_call = "BUY"
                reasoning = "Strong bullish crossover alignment: SMA 20 is above SMA 50 and price supports upward momentum."
            elif score <= -3:
                action_call = "SELL"
                reasoning = "Bearish crossover alignment: SMA 20 is below SMA 50 indicating downward swing pressure."
            else:
                action_call = "HOLD / NEUTRAL"
                reasoning = "Mixed or consolidated signals. The fast and slow moving averages are not offering a high-conviction breakout."
            
            recent_lows = lows[-20:]
            recent_highs = highs[-20:]
            recent_support = round(min(recent_lows), 2)
            recent_resistance = round(max(recent_highs), 2)
            
            stop_loss = round(min(recent_support, current_price * 0.95), 2) if action_call == "BUY" else round(max(recent_resistance, current_price * 1.05), 2)
            profit_target = round(current_price * 1.08, 2) if action_call == "BUY" else round(current_price * 0.92, 2)

            return {
                "symbol": clean_sym,
                "currency": meta.get("currency", "USD"),
                "current_price": current_price,
                "52_week_high": year_high,
                "52_week_low": year_low,
                "indicators": {
                    "sma_20": sma20_curr,
                    "sma_50": sma50_curr,
                    "sma_200": sma200_curr,
                    "rsi_14": rsi14,
                    "rsi_condition": rsi_condition
                },
                "crossover_analysis": {
                    "current_alignment": sma20_vs_sma50,
                    "recent_crossover_event": recent_cross,
                    "crossover_days_ago": cross_days_ago,
                    "macro_trend_200sma": macro_trend
                },
                "swing_strategy_verdict": {
                    "action": action_call,
                    "conviction_score": score,
                    "rationale": reasoning,
                    "key_levels": {
                        "entry_reference_price": current_price,
                        "support_level": recent_support,
                        "resistance_level": recent_resistance,
                        "suggested_stop_loss": stop_loss,
                        "suggested_take_profit_target": profit_target
                    }
                }
            }
    except Exception as e:
        return {
            "symbol": clean_sym,
            "error": f"Failed to retrieve or analyze data for {clean_sym}: {str(e)}"
        }


def get_company_news_sentiment(symbol: str) -> Dict[str, Any]:
    """Fetches recent news headlines for a stock symbol to assess catalyst risk and market sentiment.

    Args:
        symbol: The stock ticker symbol (e.g. 'AAPL', 'NVDA', 'TSLA').

    Returns:
        A dictionary containing recent news headlines, publication dates, and a sentiment summary.
    """
    clean_sym = symbol.strip().upper()
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={clean_sym}&region=US&lang=en-US"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    try:
        import xml.etree.ElementTree as ET
        with urllib.request.urlopen(req, timeout=8) as resp:
            root = ET.fromstring(resp.read())
            items = root.findall(".//item")
            headlines = []
            for item in items[:5]:
                title = item.findtext("title", "").strip()
                pub_date = item.findtext("pubDate", "").strip()
                link = item.findtext("link", "").strip()
                if title:
                    headlines.append({"title": title, "published": pub_date, "link": link})
            
            return {
                "symbol": clean_sym,
                "headlines_count": len(headlines),
                "news": headlines
            }
    except Exception as e:
        return {
            "symbol": clean_sym,
            "news": [],
            "error": f"Failed to fetch news headlines: {str(e)}"
        }

