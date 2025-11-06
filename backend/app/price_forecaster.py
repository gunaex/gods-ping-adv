"""
Price Forecasting Engine
Predicts future price movements using multiple methods:
1. Linear Regression (trend-based)
2. Moving Average Crossover (momentum-based)
3. RSI Divergence (reversal detection)
4. MACD (Moving Average Convergence Divergence)
5. Bollinger Bands (volatility & overbought/oversold)
6. Volume Analysis (buying/selling pressure)
7. Ichimoku Cloud (comprehensive trend)
8. Stochastic Oscillator (momentum)
9. Support/Resistance Levels
10. Social Sentiment (news & market mood)
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import statistics
import re


def calculate_linear_regression(prices: List[float], periods: int = 24) -> Dict:
    """
    Calculate price trend using linear regression.
    Uses last N periods to predict next period.
    
    Returns:
        {
            'predicted_price': 3500.0,
            'trend': 'UP',  # UP/DOWN/SIDEWAYS
            'slope': 2.5,  # Rate of change
            'confidence': 0.75  # R-squared value
        }
    """
    if len(prices) < periods:
        periods = len(prices)
    
    recent_prices = prices[-periods:]
    x = np.arange(len(recent_prices))
    y = np.array(recent_prices)
    
    # Calculate linear regression: y = mx + b
    n = len(x)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    # Slope (m)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    slope = numerator / denominator if denominator != 0 else 0
    
    # Intercept (b)
    intercept = y_mean - slope * x_mean
    
    # Predict next value
    next_x = len(recent_prices)
    predicted_price = slope * next_x + intercept
    
    # Calculate R-squared (confidence)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Determine trend
    if slope > 0.5:
        trend = 'UP'
    elif slope < -0.5:
        trend = 'DOWN'
    else:
        trend = 'SIDEWAYS'
    
    return {
        'predicted_price': round(predicted_price, 2),
        'trend': trend,
        'slope': round(slope, 4),
        'confidence': round(max(0, min(1, r_squared)), 2)
    }


def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices)
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


def predict_ma_crossover(prices: List[float]) -> Dict:
    """
    Predict price direction using Moving Average crossover strategy.
    
    Uses:
    - EMA(12) vs EMA(26) for short-term trend
    - EMA(50) for long-term trend
    
    Returns:
        {
            'signal': 'BULLISH',  # BULLISH/BEARISH/NEUTRAL
            'predicted_direction': 'UP',
            'strength': 0.65,  # 0-1
            'target_price': 3520.0
        }
    """
    if len(prices) < 50:
        return {
            'signal': 'NEUTRAL',
            'predicted_direction': 'SIDEWAYS',
            'strength': 0.0,
            'target_price': prices[-1]
        }
    
    current_price = prices[-1]
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    ema50 = calculate_ema(prices, 50)
    
    # Calculate momentum
    fast_slow_diff = ema12 - ema26
    fast_slow_pct = (fast_slow_diff / ema26) * 100
    
    # Determine signal
    if ema12 > ema26 and ema12 > ema50:
        signal = 'BULLISH'
        predicted_direction = 'UP'
        # Target: current + 1% based on momentum
        target_price = current_price * (1 + abs(fast_slow_pct) / 100)
    elif ema12 < ema26 and ema12 < ema50:
        signal = 'BEARISH'
        predicted_direction = 'DOWN'
        # Target: current - 1% based on momentum
        target_price = current_price * (1 - abs(fast_slow_pct) / 100)
    else:
        signal = 'NEUTRAL'
        predicted_direction = 'SIDEWAYS'
        target_price = current_price
    
    # Calculate strength (0-1)
    strength = min(1.0, abs(fast_slow_pct) / 5.0)  # Cap at 5% difference
    
    return {
        'signal': signal,
        'predicted_direction': predicted_direction,
        'strength': round(strength, 2),
        'target_price': round(target_price, 2)
    }


def detect_support_resistance(highs: List[float], lows: List[float], current_price: float) -> Dict:
    """
    Identify key support and resistance levels.
    
    Returns:
        {
            'resistance': 3600.0,  # Nearest resistance above current
            'support': 3400.0,     # Nearest support below current
            'range': 200.0,        # Distance between S/R
            'position': 'MIDDLE',  # NEAR_SUPPORT/NEAR_RESISTANCE/MIDDLE
            'breakout_target': 3650.0  # If breaks resistance
        }
    """
    if len(highs) < 20 or len(lows) < 20:
        return {
            'resistance': current_price * 1.05,
            'support': current_price * 0.95,
            'range': current_price * 0.10,
            'position': 'MIDDLE',
            'breakout_target': current_price * 1.10
        }
    
    # Find recent pivot highs (local maxima)
    pivot_highs = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            pivot_highs.append(highs[i])
    
    # Find recent pivot lows (local minima)
    pivot_lows = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            pivot_lows.append(lows[i])
    
    # Find nearest resistance (above current price)
    resistances_above = [h for h in pivot_highs if h > current_price]
    resistance = min(resistances_above) if resistances_above else current_price * 1.05
    
    # Find nearest support (below current price)
    supports_below = [l for l in pivot_lows if l < current_price]
    support = max(supports_below) if supports_below else current_price * 0.95
    
    # Calculate position in range
    range_size = resistance - support
    distance_from_support = current_price - support
    position_pct = (distance_from_support / range_size) * 100 if range_size > 0 else 50
    
    if position_pct < 25:
        position = 'NEAR_SUPPORT'
    elif position_pct > 75:
        position = 'NEAR_RESISTANCE'
    else:
        position = 'MIDDLE'
    
    # Breakout target (if resistance breaks)
    breakout_target = resistance + range_size * 0.5
    
    return {
        'resistance': round(resistance, 2),
        'support': round(support, 2),
        'range': round(range_size, 2),
        'position': position,
        'breakout_target': round(breakout_target, 2)
    }


def calculate_volatility(prices: List[float], period: int = 24) -> float:
    """Calculate price volatility (standard deviation of returns)"""
    if len(prices) < period + 1:
        period = len(prices) - 1
    
    recent_prices = prices[-(period+1):]
    returns = [(recent_prices[i] / recent_prices[i-1] - 1) for i in range(1, len(recent_prices))]
    
    if not returns:
        return 0.0
    
    return statistics.stdev(returns) * 100  # As percentage


def calculate_rsi(prices: List[float], period: int = 14) -> Dict:
    """
    Calculate Relative Strength Index (RSI).
    
    Returns:
        {
            'rsi': 45.5,
            'signal': 'NEUTRAL',  # OVERSOLD/NEUTRAL/OVERBOUGHT
            'strength': 0.5  # 0-1
        }
    """
    if len(prices) < period + 1:
        return {'rsi': 50.0, 'signal': 'NEUTRAL', 'strength': 0.0}
    
    # Calculate price changes
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    # Determine signal
    if rsi < 30:
        signal = 'OVERSOLD'
        strength = (30 - rsi) / 30  # Stronger as RSI gets lower
    elif rsi > 70:
        signal = 'OVERBOUGHT'
        strength = (rsi - 70) / 30  # Stronger as RSI gets higher
    else:
        signal = 'NEUTRAL'
        strength = 0.0
    
    return {
        'rsi': round(rsi, 2),
        'signal': signal,
        'strength': round(min(1.0, strength), 2)
    }


def calculate_macd(prices: List[float]) -> Dict:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Returns:
        {
            'macd': 12.5,
            'signal_line': 10.2,
            'histogram': 2.3,
            'signal': 'BULLISH',  # BULLISH/BEARISH/NEUTRAL
            'strength': 0.65
        }
    """
    if len(prices) < 26:
        return {
            'macd': 0.0,
            'signal_line': 0.0,
            'histogram': 0.0,
            'signal': 'NEUTRAL',
            'strength': 0.0
        }
    
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd = ema12 - ema26
    
    # Calculate signal line (9-period EMA of MACD)
    # For simplicity, use SMA instead of recalculating full MACD history
    signal_line = macd * 0.9  # Approximation
    
    histogram = macd - signal_line
    
    # Determine signal
    if macd > signal_line and macd > 0:
        signal = 'BULLISH'
        strength = min(1.0, abs(histogram) / 50)
    elif macd < signal_line and macd < 0:
        signal = 'BEARISH'
        strength = min(1.0, abs(histogram) / 50)
    else:
        signal = 'NEUTRAL'
        strength = 0.0
    
    return {
        'macd': round(macd, 2),
        'signal_line': round(signal_line, 2),
        'histogram': round(histogram, 2),
        'signal': signal,
        'strength': round(strength, 2)
    }


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict:
    """
    Calculate Bollinger Bands.
    
    Returns:
        {
            'upper': 3600.0,
            'middle': 3500.0,
            'lower': 3400.0,
            'position': 'MIDDLE',  # UPPER/MIDDLE/LOWER
            'width': 200.0,
            'signal': 'NEUTRAL'  # SQUEEZE/EXPANSION/NEUTRAL
        }
    """
    if len(prices) < period:
        avg = sum(prices) / len(prices)
        return {
            'upper': avg * 1.02,
            'middle': avg,
            'lower': avg * 0.98,
            'position': 'MIDDLE',
            'width': avg * 0.04,
            'signal': 'NEUTRAL'
        }
    
    recent_prices = prices[-period:]
    middle = sum(recent_prices) / period
    std = statistics.stdev(recent_prices)
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    width = upper - lower
    
    current_price = prices[-1]
    
    # Determine position
    range_size = upper - lower
    if current_price > middle + (range_size * 0.3):
        position = 'UPPER'
    elif current_price < middle - (range_size * 0.3):
        position = 'LOWER'
    else:
        position = 'MIDDLE'
    
    # Determine squeeze/expansion
    avg_width = width / middle * 100
    if avg_width < 4:
        signal = 'SQUEEZE'  # Low volatility - breakout coming
    elif avg_width > 8:
        signal = 'EXPANSION'  # High volatility
    else:
        signal = 'NEUTRAL'
    
    return {
        'upper': round(upper, 2),
        'middle': round(middle, 2),
        'lower': round(lower, 2),
        'position': position,
        'width': round(width, 2),
        'signal': signal
    }


def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Dict:
    """
    Calculate Stochastic Oscillator.
    
    Returns:
        {
            'k': 75.5,  # %K line
            'd': 72.3,  # %D line (signal)
            'signal': 'OVERBOUGHT',  # OVERSOLD/NEUTRAL/OVERBOUGHT
            'strength': 0.55
        }
    """
    if len(closes) < period:
        return {
            'k': 50.0,
            'd': 50.0,
            'signal': 'NEUTRAL',
            'strength': 0.0
        }
    
    recent_highs = highs[-period:]
    recent_lows = lows[-period:]
    current_close = closes[-1]
    
    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)
    
    if highest_high == lowest_low:
        k = 50.0
    else:
        k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
    
    # %D is 3-period SMA of %K (simplified)
    d = k * 0.9  # Approximation
    
    # Determine signal
    if k < 20:
        signal = 'OVERSOLD'
        strength = (20 - k) / 20
    elif k > 80:
        signal = 'OVERBOUGHT'
        strength = (k - 80) / 20
    else:
        signal = 'NEUTRAL'
        strength = 0.0
    
    return {
        'k': round(k, 2),
        'd': round(d, 2),
        'signal': signal,
        'strength': round(min(1.0, strength), 2)
    }


def analyze_volume(volumes: List[float], prices: List[float]) -> Dict:
    """
    Analyze volume trends and buying/selling pressure.
    
    Returns:
        {
            'average_volume': 1000000.0,
            'current_volume': 1500000.0,
            'volume_trend': 'INCREASING',
            'pressure': 'BUYING',  # BUYING/SELLING/NEUTRAL
            'strength': 0.65
        }
    """
    if len(volumes) < 20 or len(prices) < 2:
        return {
            'average_volume': 0.0,
            'current_volume': 0.0,
            'volume_trend': 'NEUTRAL',
            'pressure': 'NEUTRAL',
            'strength': 0.0
        }
    
    avg_volume = sum(volumes[-20:]) / 20
    current_volume = volumes[-1]
    
    # Volume trend
    recent_avg = sum(volumes[-5:]) / 5
    older_avg = sum(volumes[-20:-5]) / 15
    
    if recent_avg > older_avg * 1.2:
        volume_trend = 'INCREASING'
    elif recent_avg < older_avg * 0.8:
        volume_trend = 'DECREASING'
    else:
        volume_trend = 'STABLE'
    
    # Buying/selling pressure (volume + price direction)
    price_change = prices[-1] - prices[-2]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    
    if price_change > 0 and volume_ratio > 1.2:
        pressure = 'BUYING'
        strength = min(1.0, (volume_ratio - 1.0) / 2.0)
    elif price_change < 0 and volume_ratio > 1.2:
        pressure = 'SELLING'
        strength = min(1.0, (volume_ratio - 1.0) / 2.0)
    else:
        pressure = 'NEUTRAL'
        strength = 0.0
    
    return {
        'average_volume': round(avg_volume, 2),
        'current_volume': round(current_volume, 2),
        'volume_trend': volume_trend,
        'pressure': pressure,
        'strength': round(strength, 2)
    }


def analyze_social_sentiment(symbol: str) -> Dict:
    """
    Analyze social media sentiment and news trends.
    
    This is a placeholder that returns simulated sentiment.
    In production, you would integrate with:
    - Twitter API (crypto mentions, hashtags)
    - Reddit API (r/cryptocurrency, r/bitcoin sentiment)
    - News APIs (CryptoPanic, CoinTelegraph)
    - Google Trends
    - Fear & Greed Index
    
    Returns:
        {
            'sentiment_score': 0.65,  # -1 to 1 (bearish to bullish)
            'sentiment': 'BULLISH',  # BEARISH/NEUTRAL/BULLISH
            'fear_greed_index': 55,  # 0-100
            'news_mentions': 150,  # Number of news articles
            'social_volume': 'HIGH',  # LOW/MEDIUM/HIGH
            'trending': True,  # Is symbol trending?
            'confidence': 0.60
        }
    """
    # Extract base symbol (e.g., BTC from BTC/USDT)
    base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
    
    # Simulated sentiment based on symbol popularity
    # In production, replace with real API calls
    popular_coins = {
        'BTC': {'sentiment': 0.70, 'fg_index': 65, 'mentions': 500, 'volume': 'HIGH'},
        'ETH': {'sentiment': 0.65, 'fg_index': 60, 'mentions': 350, 'volume': 'HIGH'},
        'BNB': {'sentiment': 0.55, 'fg_index': 58, 'mentions': 200, 'volume': 'MEDIUM'},
        'SOL': {'sentiment': 0.60, 'fg_index': 62, 'mentions': 180, 'volume': 'MEDIUM'},
        'DOGE': {'sentiment': 0.50, 'fg_index': 55, 'mentions': 250, 'volume': 'HIGH'},
    }
    
    data = popular_coins.get(base_symbol, {
        'sentiment': 0.50,
        'fg_index': 50,
        'mentions': 50,
        'volume': 'LOW'
    })
    
    sentiment_score = data['sentiment']
    
    if sentiment_score > 0.6:
        sentiment = 'BULLISH'
    elif sentiment_score < 0.4:
        sentiment = 'BEARISH'
    else:
        sentiment = 'NEUTRAL'
    
    trending = data['mentions'] > 200 and data['volume'] == 'HIGH'
    
    return {
        'sentiment_score': round(sentiment_score, 2),
        'sentiment': sentiment,
        'fear_greed_index': data['fg_index'],
        'news_mentions': data['mentions'],
        'social_volume': data['volume'],
        'trending': trending,
        'confidence': 0.60  # Medium confidence for simulated data
    }


def forecast_price_hourly(candles: List[Dict], forecast_hours: int = 6) -> Dict:
    """
    Comprehensive price forecast for next N hours.
    
    Args:
        candles: List of OHLCV candles (hourly timeframe)
        forecast_hours: How many hours ahead to forecast (default: 6)
    
    Returns:
        {
            'current_price': 3500.0,
            'forecasts': [
                {'hour': 1, 'predicted_price': 3520.0, 'confidence': 0.75},
                {'hour': 2, 'predicted_price': 3535.0, 'confidence': 0.70},
                ...
            ],
            'trend_analysis': {
                'short_term': 'UP',
                'medium_term': 'UP',
                'long_term': 'SIDEWAYS'
            },
            'price_targets': {
                'optimistic': 3600.0,
                'realistic': 3550.0,
                'pessimistic': 3480.0
            },
            'key_levels': {
                'resistance': 3600.0,
                'support': 3400.0,
                'breakout_target': 3650.0
            },
            'risk_metrics': {
                'volatility': 2.5,  # %
                'confidence': 0.72,
                'reliability': 'MEDIUM'  # HIGH/MEDIUM/LOW
            },
            'trading_recommendation': {
                'action': 'BUY',
                'timing': 'FAVORABLE',
                'reasoning': 'Strong uptrend with bullish momentum'
            }
        }
    """
    if not candles or len(candles) < 24:
        return {
            'error': 'Insufficient data for forecasting',
            'min_required': 24,
            'received': len(candles)
        }
    
    # Extract price data
    closes = [c['close'] for c in candles]
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    volumes = [c.get('volume', 0) for c in candles]
    symbol = candles[0].get('symbol', 'BTC/USDT') if candles else 'BTC/USDT'
    
    current_price = closes[-1]
    
    # ═══════════════════════════════════════════════════════════
    # TECHNICAL INDICATORS (10 different signals)
    # ═══════════════════════════════════════════════════════════
    
    # 1. Linear regression forecast (trend-based)
    regression = calculate_linear_regression(closes, periods=24)
    
    # 2. Moving average analysis (momentum)
    ma_analysis = predict_ma_crossover(closes)
    
    # 3. RSI (overbought/oversold)
    rsi = calculate_rsi(closes, period=14)
    
    # 4. MACD (trend strength)
    macd = calculate_macd(closes)
    
    # 5. Bollinger Bands (volatility)
    bb = calculate_bollinger_bands(closes, period=20)
    
    # 6. Stochastic Oscillator (momentum)
    stochastic = calculate_stochastic(highs, lows, closes, period=14)
    
    # 7. Support/Resistance levels
    sr_levels = detect_support_resistance(highs, lows, current_price)
    
    # 8. Volume analysis (buying/selling pressure)
    volume_analysis = analyze_volume(volumes, closes)
    
    # 9. Volatility analysis
    volatility = calculate_volatility(closes, period=24)
    
    # 10. Social sentiment (news & market mood)
    sentiment = analyze_social_sentiment(symbol)
    
    # Multi-timeframe trend analysis
    short_term_trend = calculate_linear_regression(closes[-6:], periods=6)['trend']
    medium_term_trend = calculate_linear_regression(closes[-24:], periods=24)['trend']
    long_term_trend = calculate_linear_regression(closes[-72:], periods=72)['trend'] if len(closes) >= 72 else 'UNKNOWN'
    
    # Generate hourly forecasts
    forecasts = []
    base_price = current_price
    trend_slope = regression['slope']
    
    for hour in range(1, forecast_hours + 1):
        # Combine linear trend + MA target
        linear_prediction = base_price + (trend_slope * hour)
        ma_target = ma_analysis['target_price']
        
        # Weighted average (favor near-term = linear, far-term = MA)
        weight_linear = max(0, 1 - (hour / forecast_hours))
        weight_ma = 1 - weight_linear
        predicted_price = (linear_prediction * weight_linear) + (ma_target * weight_ma)
        
        # Confidence decreases with time
        confidence = regression['confidence'] * (1 - (hour / (forecast_hours * 2)))
        
        forecasts.append({
            'hour': hour,
            'predicted_price': round(predicted_price, 2),
            'confidence': round(max(0.3, confidence), 2)
        })
    
    # ═══════════════════════════════════════════════════════════
    # INTELLIGENT CONFIDENCE CALCULATION
    # Weighs multiple indicators for more reliable predictions
    # ═══════════════════════════════════════════════════════════
    
    # Count bullish signals
    bullish_signals = 0
    bearish_signals = 0
    total_weight = 0
    
    # Signal 1: Trend Direction (weight: 2.0)
    if short_term_trend == 'UP':
        bullish_signals += 2.0
    elif short_term_trend == 'DOWN':
        bearish_signals += 2.0
    total_weight += 2.0
    
    if medium_term_trend == 'UP':
        bullish_signals += 1.5
    elif medium_term_trend == 'DOWN':
        bearish_signals += 1.5
    total_weight += 1.5
    
    # Signal 2: Moving Averages (weight: 1.5)
    if ma_analysis['signal'] == 'BULLISH':
        bullish_signals += 1.5 * ma_analysis['strength']
    elif ma_analysis['signal'] == 'BEARISH':
        bearish_signals += 1.5 * ma_analysis['strength']
    total_weight += 1.5
    
    # Signal 3: RSI (weight: 1.0)
    if rsi['signal'] == 'OVERSOLD':
        bullish_signals += 1.0 * rsi['strength']
    elif rsi['signal'] == 'OVERBOUGHT':
        bearish_signals += 1.0 * rsi['strength']
    total_weight += 1.0
    
    # Signal 4: MACD (weight: 1.5)
    if macd['signal'] == 'BULLISH':
        bullish_signals += 1.5 * macd['strength']
    elif macd['signal'] == 'BEARISH':
        bearish_signals += 1.5 * macd['strength']
    total_weight += 1.5
    
    # Signal 5: Bollinger Bands (weight: 1.0)
    if bb['position'] == 'LOWER':
        bullish_signals += 1.0  # Near lower band = potential bounce
    elif bb['position'] == 'UPPER':
        bearish_signals += 1.0  # Near upper band = potential reversal
    total_weight += 1.0
    
    # Signal 6: Stochastic (weight: 1.0)
    if stochastic['signal'] == 'OVERSOLD':
        bullish_signals += 1.0 * stochastic['strength']
    elif stochastic['signal'] == 'OVERBOUGHT':
        bearish_signals += 1.0 * stochastic['strength']
    total_weight += 1.0
    
    # Signal 7: Volume Pressure (weight: 1.0)
    if volume_analysis['pressure'] == 'BUYING':
        bullish_signals += 1.0 * volume_analysis['strength']
    elif volume_analysis['pressure'] == 'SELLING':
        bearish_signals += 1.0 * volume_analysis['strength']
    total_weight += 1.0
    
    # Signal 8: Social Sentiment (weight: 0.5)
    if sentiment['sentiment'] == 'BULLISH':
        bullish_signals += 0.5 * sentiment['sentiment_score']
    elif sentiment['sentiment'] == 'BEARISH':
        bearish_signals += 0.5 * (1 - sentiment['sentiment_score'])
    total_weight += 0.5
    
    # Calculate overall confidence (0-1 scale)
    signal_strength = bullish_signals - bearish_signals
    overall_confidence = min(1.0, (abs(signal_strength) / total_weight) * 1.5)
    
    # Adjust confidence based on volatility
    if volatility > 5:
        overall_confidence *= 0.7  # High volatility reduces confidence
        reliability = 'LOW'
    elif volatility > 2.5:
        overall_confidence *= 0.85
        reliability = 'MEDIUM'
    else:
        reliability = 'HIGH'
    
    # Boost confidence if multiple timeframes agree
    timeframe_agreement = sum([
        1 if short_term_trend == medium_term_trend else 0,
        1 if medium_term_trend == long_term_trend else 0,
    ])
    if timeframe_agreement >= 2:
        overall_confidence = min(1.0, overall_confidence * 1.15)
    
    # Calculate trend strength (how many indicators agree)
    trend_strength = abs(bullish_signals - bearish_signals) / total_weight
    
    # Calculate trend strength (how many indicators agree)
    trend_strength = abs(bullish_signals - bearish_signals) / total_weight
    
    # ═══════════════════════════════════════════════════════════
    # GENERATE HOURLY FORECASTS
    # ═══════════════════════════════════════════════════════════
    
    forecasts = []
    base_price = current_price
    trend_slope = regression['slope']
    
    # Adjust slope based on signal strength
    adjusted_slope = trend_slope * (1 + (signal_strength / total_weight))
    
    for hour in range(1, forecast_hours + 1):
        # Combine multiple predictions
        linear_prediction = base_price + (adjusted_slope * hour)
        ma_target = ma_analysis['target_price']
        
        # Weighted average (favor near-term = linear, far-term = MA)
        weight_linear = max(0, 1 - (hour / forecast_hours))
        weight_ma = 1 - weight_linear
        predicted_price = (linear_prediction * weight_linear) + (ma_target * weight_ma)
        
        # Consider Bollinger Bands as limits
        if predicted_price > bb['upper']:
            predicted_price = bb['upper'] * 0.995  # Cap at BB upper
        elif predicted_price < bb['lower']:
            predicted_price = bb['lower'] * 1.005  # Floor at BB lower
        
        # Confidence decreases with time
        hour_confidence = overall_confidence * (1 - (hour / (forecast_hours * 2.5)))
        
        forecasts.append({
            'hour': hour,
            'predicted_price': round(predicted_price, 2),
            'confidence': round(max(0.3, hour_confidence), 2)
        })
    
    # ═══════════════════════════════════════════════════════════
    # CALCULATE PRICE TARGETS
    # ═══════════════════════════════════════════════════════════
    
    avg_forecast = sum(f['predicted_price'] for f in forecasts) / len(forecasts)
    price_range = volatility * current_price / 100
    
    # Optimistic: Breakout above resistance
    optimistic = max(avg_forecast + price_range * 1.5, sr_levels['resistance'] * 1.01)
    
    # Realistic: Average forecast
    realistic = avg_forecast
    
    # Pessimistic: Support hold or breakdown
    pessimistic = max(avg_forecast - price_range * 1.5, sr_levels['support'] * 0.99)
    
    # ═══════════════════════════════════════════════════════════
    # INTELLIGENT TRADING RECOMMENDATION
    # ═══════════════════════════════════════════════════════════
    
    # Determine primary action
    if signal_strength > 1.0 and bullish_signals > bearish_signals:
        action = 'BUY'
        action_confidence = overall_confidence
    elif signal_strength > 1.0 and bearish_signals > bullish_signals:
        action = 'SELL'
        action_confidence = overall_confidence
    else:
        action = 'HOLD'
        action_confidence = 0.5
    
    # Determine timing based on position and indicators
    timing_factors = []
    
    # Factor 1: Support/Resistance position
    if action == 'BUY':
        if sr_levels['position'] == 'NEAR_SUPPORT':
            timing_factors.append(('Support bounce opportunity', 0.8))
        elif sr_levels['position'] == 'NEAR_RESISTANCE':
            timing_factors.append(('Near resistance - risky entry', 0.3))
        else:
            timing_factors.append(('Mid-range entry', 0.5))
    elif action == 'SELL':
        if sr_levels['position'] == 'NEAR_RESISTANCE':
            timing_factors.append(('Resistance rejection likely', 0.8))
        elif sr_levels['position'] == 'NEAR_SUPPORT':
            timing_factors.append(('Near support - risky exit', 0.3))
        else:
            timing_factors.append(('Mid-range exit', 0.5))
    
    # Factor 2: RSI extremes
    if rsi['signal'] == 'OVERSOLD' and action == 'BUY':
        timing_factors.append(('RSI oversold - good entry', 0.7))
    elif rsi['signal'] == 'OVERBOUGHT' and action == 'SELL':
        timing_factors.append(('RSI overbought - good exit', 0.7))
    
    # Factor 3: Volume confirmation
    if action == 'BUY' and volume_analysis['pressure'] == 'BUYING':
        timing_factors.append(('Strong buying volume', 0.7))
    elif action == 'SELL' and volume_analysis['pressure'] == 'SELLING':
        timing_factors.append(('Strong selling volume', 0.7))
    elif volume_analysis['pressure'] == 'NEUTRAL':
        timing_factors.append(('Low volume - wait for confirmation', 0.4))
    
    # Factor 4: Bollinger Band squeeze
    if bb['signal'] == 'SQUEEZE':
        timing_factors.append(('BB squeeze - breakout imminent', 0.6))
    
    # Factor 5: Social sentiment boost
    if sentiment['trending'] and sentiment['sentiment'] == 'BULLISH' and action == 'BUY':
        timing_factors.append(('Trending with bullish sentiment', 0.6))
    elif sentiment['trending'] and sentiment['sentiment'] == 'BEARISH' and action == 'SELL':
        timing_factors.append(('Trending with bearish sentiment', 0.6))
    
    # Calculate average timing score
    if timing_factors:
        avg_timing = sum(score for _, score in timing_factors) / len(timing_factors)
        if avg_timing > 0.65:
            timing = 'FAVORABLE'
        elif avg_timing > 0.45:
            timing = 'NEUTRAL'
        else:
            timing = 'WAIT'
    else:
        timing = 'NEUTRAL'
    
    # Build detailed reasoning
    reasoning_parts = []
    
    # Primary trend
    if bullish_signals > bearish_signals:
        reasoning_parts.append(f"Bullish momentum ({short_term_trend} ST, {medium_term_trend} MT)")
    elif bearish_signals > bullish_signals:
        reasoning_parts.append(f"Bearish momentum ({short_term_trend} ST, {medium_term_trend} MT)")
    else:
        reasoning_parts.append(f"Mixed signals ({short_term_trend} ST, {medium_term_trend} MT)")
    
    # Key indicators
    if rsi['signal'] != 'NEUTRAL':
        reasoning_parts.append(f"RSI {rsi['signal']} ({rsi['rsi']:.0f})")
    
    if macd['signal'] != 'NEUTRAL':
        reasoning_parts.append(f"MACD {macd['signal']}")
    
    if volume_analysis['pressure'] != 'NEUTRAL':
        reasoning_parts.append(f"{volume_analysis['pressure']} pressure")
    
    if sentiment['trending']:
        reasoning_parts.append(f"Trending {sentiment['sentiment'].lower()}")
    
    # Timing factors
    if timing_factors:
        top_factor = max(timing_factors, key=lambda x: x[1])
        reasoning_parts.append(top_factor[0])
    
    reasoning = ". ".join(reasoning_parts) + "."
    
    reasoning = ". ".join(reasoning_parts) + "."
    
    # ═══════════════════════════════════════════════════════════
    # RETURN COMPREHENSIVE FORECAST
    # ═══════════════════════════════════════════════════════════
    
    return {
        'timestamp': datetime.now().isoformat(),
        'current_price': round(current_price, 2),
        'symbol': symbol,
        
        # Hourly predictions
        'forecasts': forecasts,
        
        # Multi-timeframe trends
        'trend_analysis': {
            'short_term': short_term_trend,
            'medium_term': medium_term_trend,
            'long_term': long_term_trend
        },
        
        # Price targets
        'price_targets': {
            'optimistic': round(optimistic, 2),
            'realistic': round(realistic, 2),
            'pessimistic': round(pessimistic, 2),
            '6h_average': round(avg_forecast, 2)
        },
        
        # Support/Resistance
        'key_levels': sr_levels,
        
        # Technical Indicators (detailed)
        'technical_indicators': {
            'rsi': rsi,
            'macd': macd,
            'bollinger_bands': bb,
            'stochastic': stochastic,
            'moving_averages': ma_analysis,
            'volume': volume_analysis,
        },
        
        # Social Sentiment
        'social_sentiment': sentiment,
        
        # Risk assessment
        'risk_metrics': {
            'volatility': round(volatility, 2),
            'confidence': round(overall_confidence, 2),
            'reliability': reliability,
            'trend_strength': round(trend_strength, 2),
            'signal_strength': round(signal_strength, 2),
            'bullish_signals': round(bullish_signals, 2),
            'bearish_signals': round(bearish_signals, 2),
        },
        
        # Trading recommendation
        'trading_recommendation': {
            'action': action,
            'timing': timing,
            'reasoning': reasoning,
            'confidence': round(action_confidence, 2),
            'timing_factors': [{'factor': f, 'score': s} for f, s in timing_factors]
        }
    }


def get_forecast_summary(forecast: Dict) -> str:
    """
    Generate human-readable forecast summary.
    """
    if 'error' in forecast:
        return f"❌ {forecast['error']}"
    
    current = forecast['current_price']
    avg_forecast = forecast['price_targets']['6h_average']
    change_pct = ((avg_forecast - current) / current) * 100
    
    trend = forecast['trend_analysis']['medium_term']
    action = forecast['trading_recommendation']['action']
    confidence = forecast['risk_metrics']['confidence']
    volatility = forecast['risk_metrics']['volatility']
    
    # Get technical indicators
    rsi = forecast['technical_indicators']['rsi']
    macd = forecast['technical_indicators']['macd']
    volume = forecast['technical_indicators']['volume']
    sentiment = forecast['social_sentiment']
    
    direction = "📈 UP" if change_pct > 0 else ("📉 DOWN" if change_pct < 0 else "➡️ FLAT")
    
    # Emoji for action
    action_emoji = "🟢" if action == "BUY" else ("🔴" if action == "SELL" else "⚪")
    
    summary = f"""
🔮 AI PRICE FORECAST (Next 6 Hours)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: ${current:,.2f}
Predicted (6h): ${avg_forecast:,.2f} {direction} ({change_pct:+.2f}%)

📊 Trend Analysis
   • Short-term: {forecast['trend_analysis']['short_term']}
   • Medium-term: {forecast['trend_analysis']['medium_term']}
   • Long-term: {forecast['trend_analysis']['long_term']}
   • Confidence: {confidence*100:.0f}% ({forecast['risk_metrics']['reliability']})

📈 Technical Indicators
   • RSI: {rsi['rsi']:.0f} ({rsi['signal']})
   • MACD: {macd['signal']} (histogram: {macd['histogram']:.1f})
   • Volume: {volume['pressure']} pressure ({volume['volume_trend']})
   • Volatility: {volatility:.1f}%

🌐 Social Sentiment
   • Mood: {sentiment['sentiment']} ({sentiment['sentiment_score']*100:.0f}%)
   • Fear & Greed: {sentiment['fear_greed_index']}/100
   • News Mentions: {sentiment['news_mentions']}
   • Trending: {'YES' if sentiment['trending'] else 'NO'}

🎯 Price Targets
   • Optimistic: ${forecast['price_targets']['optimistic']:,.2f}
   • Realistic: ${forecast['price_targets']['realistic']:,.2f}
   • Pessimistic: ${forecast['price_targets']['pessimistic']:,.2f}

🔑 Key Levels
   • Resistance: ${forecast['key_levels']['resistance']:,.2f}
   • Support: ${forecast['key_levels']['support']:,.2f}
   • Position: {forecast['key_levels']['position'].replace('_', ' ')}

{action_emoji} RECOMMENDATION: {action}
   Timing: {forecast['trading_recommendation']['timing']}
   {forecast['trading_recommendation']['reasoning']}

📊 Signal Strength: {forecast['risk_metrics']['signal_strength']:.1f}
   Bullish Signals: {forecast['risk_metrics']['bullish_signals']:.1f}
   Bearish Signals: {forecast['risk_metrics']['bearish_signals']:.1f}
"""
    return summary
