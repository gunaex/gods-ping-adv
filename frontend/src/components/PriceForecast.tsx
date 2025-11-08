import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../api';
import { TrendingUp, Target, AlertCircle, Activity } from 'lucide-react';

interface ForecastProps {
  symbol: string;
}

interface Forecast {
  timestamp: string;
  current_price: number;
  forecasts: Array<{
    hour: number;
    predicted_price: number;
    confidence: number;
  }>;
  trend_analysis: {
    short_term: string;
    medium_term: string;
    long_term: string;
  };
  price_targets: {
    optimistic: number;
    realistic: number;
    pessimistic: number;
    '6h_average': number;
  };
  key_levels: {
    resistance: number;
    support: number;
    range: number;
    position: string;
    breakout_target: number;
  };
  risk_metrics: {
    volatility: number;
    confidence: number;
    reliability: string;
    trend_strength: number;
    signal_strength: number;
    bullish_signals: number;
    bearish_signals: number;
  };
  technical_indicators?: {
    rsi: {
      rsi: number;
      signal: string;
      strength: number;
    };
    macd: {
      macd: number;
      signal_line: number;
      histogram: number;
      signal: string;
      strength: number;
    };
    volume: {
      pressure: string;
      volume_trend: string;
      strength: number;
    };
  };
  social_sentiment?: {
    sentiment: string;
    sentiment_score: number;
    fear_greed_index: number;
    news_mentions: number;
    social_volume: string;
    trending: boolean;
  };
  trading_recommendation: {
    action: string;
    timing: string;
    reasoning: string;
  };
  summary?: string;
}

export default function PriceForecast({ symbol }: ForecastProps) {
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadForecast = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const token = localStorage.getItem('token');
        const response = await fetch(
          `${API_BASE_URL}/market/forecast/${symbol}?forecast_hours=6`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load forecast');
        }

        const data = await response.json();
        setForecast(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadForecast();
    const interval = setInterval(loadForecast, 300000); // Update every 5 minutes
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading) {
    return (
      <div className="section-card">
        <div className="section-title">
          <TrendingUp />
          Price Forecast (6 Hours)
        </div>
        <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
          Loading forecast...
        </div>
      </div>
    );
  }

  if (error || !forecast) {
    return (
      <div className="section-card">
        <div className="section-title">
          <TrendingUp />
          Price Forecast (6 Hours)
        </div>
        <div style={{ padding: '20px', textAlign: 'center', color: '#f87171' }}>
          <AlertCircle style={{ display: 'inline-block', marginBottom: '8px' }} />
          <div>{error || 'No forecast data available'}</div>
        </div>
      </div>
    );
  }

  const changePct = ((forecast.price_targets['6h_average'] - forecast.current_price) / forecast.current_price) * 100;
  const isUp = changePct > 0;

  // Get reliability color
  const reliabilityColor = 
    forecast.risk_metrics.reliability === 'HIGH' ? '#4ade80' :
    forecast.risk_metrics.reliability === 'MEDIUM' ? '#fbbf24' : '#f87171';

  // Get action color
  const actionColor = 
    forecast.trading_recommendation.action === 'BUY' ? '#4ade80' :
    forecast.trading_recommendation.action === 'SELL' ? '#f87171' : '#9ca3af';

  return (
    <div className="section-card">
      <div className="section-title">
        <TrendingUp />
        🔮 AI Price Forecast (Next 6 Hours)
      </div>

      {/* Summary Stats */}
      <div className="grid grid-3" style={{ marginBottom: '20px' }}>
        <div style={{
          padding: '15px',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '4px' }}>Current Price</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            ${forecast.current_price.toLocaleString()}
          </div>
        </div>

        <div style={{
          padding: '15px',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '4px' }}>6h Forecast</div>
          <div style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: isUp ? '#4ade80' : '#f87171',
          }}>
            ${forecast.price_targets['6h_average'].toLocaleString()}
          </div>
          <div style={{ fontSize: '0.9rem', opacity: 0.9, marginTop: '2px' }}>
            {isUp ? '📈' : '📉'} {changePct > 0 ? '+' : ''}{changePct.toFixed(2)}%
          </div>
        </div>

        <div style={{
          padding: '15px',
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
        }}>
          <div style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '4px' }}>Confidence</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {(forecast.risk_metrics.confidence * 100).toFixed(0)}%
          </div>
          <div style={{ 
            fontSize: '0.9rem', 
            marginTop: '2px',
            color: reliabilityColor
          }}>
            {forecast.risk_metrics.reliability}
          </div>
        </div>
      </div>

      {/* Hourly Forecasts */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '20px',
      }}>
        <div style={{ 
          fontSize: '0.9rem', 
          fontWeight: 'bold', 
          marginBottom: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Activity size={16} />
          Hourly Predictions
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '10px' }}>
          {forecast.forecasts.map((f) => {
            const hourChange = ((f.predicted_price - forecast.current_price) / forecast.current_price) * 100;
            return (
              <div key={f.hour} style={{
                padding: '10px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                textAlign: 'center',
              }}>
                <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>+{f.hour}h</div>
                <div style={{ 
                  fontSize: '1rem', 
                  fontWeight: 'bold',
                  color: hourChange > 0 ? '#4ade80' : '#f87171',
                  margin: '4px 0'
                }}>
                  ${f.predicted_price.toLocaleString()}
                </div>
                <div style={{ fontSize: '0.7rem', opacity: 0.6 }}>
                  {hourChange > 0 ? '+' : ''}{hourChange.toFixed(1)}%
                </div>
                <div style={{ 
                  fontSize: '0.65rem', 
                  opacity: 0.5,
                  marginTop: '2px'
                }}>
                  {(f.confidence * 100).toFixed(0)}% conf
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Price Targets */}
      <div className="grid grid-2" style={{ marginBottom: '20px' }}>
        <div style={{
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
          padding: '15px',
        }}>
          <div style={{ 
            fontSize: '0.9rem', 
            fontWeight: 'bold', 
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Target size={16} />
            Price Targets
          </div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Optimistic:</span>
              <span style={{ fontWeight: 'bold', color: '#4ade80' }}>
                ${forecast.price_targets.optimistic.toLocaleString()}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Realistic:</span>
              <span style={{ fontWeight: 'bold' }}>
                ${forecast.price_targets.realistic.toLocaleString()}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Pessimistic:</span>
              <span style={{ fontWeight: 'bold', color: '#f87171' }}>
                ${forecast.price_targets.pessimistic.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        <div style={{
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: '8px',
          padding: '15px',
        }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '12px' }}>
            Key Levels
          </div>
          <div style={{ display: 'grid', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Resistance:</span>
              <span style={{ fontWeight: 'bold', color: '#f87171' }}>
                ${forecast.key_levels.resistance.toLocaleString()}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Support:</span>
              <span style={{ fontWeight: 'bold', color: '#4ade80' }}>
                ${forecast.key_levels.support.toLocaleString()}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ opacity: 0.7 }}>Position:</span>
              <span style={{ fontWeight: 'bold' }}>
                {forecast.key_levels.position.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Social Sentiment & Technical Indicators */}
      {(forecast.social_sentiment || forecast.technical_indicators) && (
        <div className="grid grid-2" style={{ marginBottom: '20px' }}>
          {/* Social Sentiment */}
          {forecast.social_sentiment && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '8px',
              padding: '15px',
            }}>
              <div style={{ 
                fontSize: '0.9rem', 
                fontWeight: 'bold', 
                marginBottom: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                🌐 Social Sentiment
                {forecast.social_sentiment.trending && (
                  <span style={{
                    fontSize: '0.7rem',
                    padding: '2px 6px',
                    background: '#4ade80',
                    color: '#000',
                    borderRadius: '4px',
                    fontWeight: 'bold'
                  }}>
                    TRENDING
                  </span>
                )}
              </div>
              <div style={{ display: 'grid', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ opacity: 0.7 }}>Market Mood:</span>
                  <span style={{ 
                    fontWeight: 'bold',
                    color: forecast.social_sentiment.sentiment === 'BULLISH' ? '#4ade80' :
                           forecast.social_sentiment.sentiment === 'BEARISH' ? '#f87171' : '#9ca3af'
                  }}>
                    {forecast.social_sentiment.sentiment}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.7 }}>Fear & Greed:</span>
                  <span style={{ fontWeight: 'bold' }}>
                    {forecast.social_sentiment.fear_greed_index}/100
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.7 }}>News Mentions:</span>
                  <span style={{ fontWeight: 'bold' }}>
                    {forecast.social_sentiment.news_mentions}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.7 }}>Social Volume:</span>
                  <span style={{ 
                    fontWeight: 'bold',
                    color: forecast.social_sentiment.social_volume === 'HIGH' ? '#4ade80' :
                           forecast.social_sentiment.social_volume === 'LOW' ? '#f87171' : '#fbbf24'
                  }}>
                    {forecast.social_sentiment.social_volume}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Technical Indicators */}
          {forecast.technical_indicators && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '8px',
              padding: '15px',
            }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '12px' }}>
                📊 Technical Indicators
              </div>
              <div style={{ display: 'grid', gap: '8px' }}>
                {forecast.technical_indicators.rsi && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ opacity: 0.7 }}>RSI:</span>
                    <span style={{ 
                      fontWeight: 'bold',
                      color: forecast.technical_indicators.rsi.signal === 'OVERSOLD' ? '#4ade80' :
                             forecast.technical_indicators.rsi.signal === 'OVERBOUGHT' ? '#f87171' : '#9ca3af'
                    }}>
                      {forecast.technical_indicators.rsi.rsi.toFixed(0)} ({forecast.technical_indicators.rsi.signal})
                    </span>
                  </div>
                )}
                {forecast.technical_indicators.macd && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ opacity: 0.7 }}>MACD:</span>
                    <span style={{ 
                      fontWeight: 'bold',
                      color: forecast.technical_indicators.macd.signal === 'BULLISH' ? '#4ade80' :
                             forecast.technical_indicators.macd.signal === 'BEARISH' ? '#f87171' : '#9ca3af'
                    }}>
                      {forecast.technical_indicators.macd.signal}
                    </span>
                  </div>
                )}
                {forecast.technical_indicators.volume && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ opacity: 0.7 }}>Volume Pressure:</span>
                    <span style={{ 
                      fontWeight: 'bold',
                      color: forecast.technical_indicators.volume.pressure === 'BUYING' ? '#4ade80' :
                             forecast.technical_indicators.volume.pressure === 'SELLING' ? '#f87171' : '#9ca3af'
                    }}>
                      {forecast.technical_indicators.volume.pressure}
                    </span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.7 }}>Signal Strength:</span>
                  <span style={{ fontWeight: 'bold' }}>
                    {(forecast.risk_metrics.signal_strength * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trend Analysis */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.2)',
        borderRadius: '8px',
        padding: '15px',
        marginBottom: '20px',
      }}>
        <div style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '12px' }}>
          Trend Analysis
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>Short-term</div>
            <div style={{ 
              fontSize: '1rem', 
              fontWeight: 'bold',
              color: forecast.trend_analysis.short_term === 'UP' ? '#4ade80' : 
                     forecast.trend_analysis.short_term === 'DOWN' ? '#f87171' : '#9ca3af'
            }}>
              {forecast.trend_analysis.short_term}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>Medium-term</div>
            <div style={{ 
              fontSize: '1rem', 
              fontWeight: 'bold',
              color: forecast.trend_analysis.medium_term === 'UP' ? '#4ade80' : 
                     forecast.trend_analysis.medium_term === 'DOWN' ? '#f87171' : '#9ca3af'
            }}>
              {forecast.trend_analysis.medium_term}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.7 }}>Long-term</div>
            <div style={{ 
              fontSize: '1rem', 
              fontWeight: 'bold',
              color: forecast.trend_analysis.long_term === 'UP' ? '#4ade80' : 
                     forecast.trend_analysis.long_term === 'DOWN' ? '#f87171' : '#9ca3af'
            }}>
              {forecast.trend_analysis.long_term}
            </div>
          </div>
        </div>
      </div>

      {/* Trading Recommendation */}
      <div style={{
        background: `linear-gradient(135deg, ${actionColor}20, ${actionColor}10)`,
        border: `2px solid ${actionColor}`,
        borderRadius: '8px',
        padding: '15px',
      }}>
        <div style={{ 
          fontSize: '1.1rem', 
          fontWeight: 'bold', 
          marginBottom: '8px',
          color: actionColor,
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {forecast.trading_recommendation.action === 'BUY' ? '📈' : 
           forecast.trading_recommendation.action === 'SELL' ? '📉' : '⏸️'}
          {forecast.trading_recommendation.action}
          <span style={{ 
            fontSize: '0.8rem', 
            opacity: 0.8,
            marginLeft: 'auto'
          }}>
            Timing: {forecast.trading_recommendation.timing}
          </span>
        </div>
        <div style={{ fontSize: '0.9rem', opacity: 0.9, lineHeight: '1.5' }}>
          {forecast.trading_recommendation.reasoning}
        </div>
        <div style={{ 
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: `1px solid ${actionColor}40`,
          fontSize: '0.8rem',
          opacity: 0.7
        }}>
          Volatility: {forecast.risk_metrics.volatility.toFixed(2)}% | 
          Trend Strength: {forecast.risk_metrics.trend_strength}/3 | 
          Updated: {new Date(forecast.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
