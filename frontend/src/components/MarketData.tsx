import { useEffect, useState, useRef } from 'react';
import { BarChart3 } from 'lucide-react';
import { createChart, ColorType } from 'lightweight-charts';
import { marketAPI } from '../api';

interface MarketDataProps {
  symbol: string;
}

export default function MarketData({ symbol }: MarketDataProps) {
  const [ticker, setTicker] = useState<any>(null);
  const [candles, setCandles] = useState<any[]>([]);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);

  // Load market data when symbol changes
  useEffect(() => {
    const loadMarketData = async () => {
      try {
        const [tickerRes, candlesRes] = await Promise.all([
          marketAPI.getTicker(symbol),
          marketAPI.getCandles(symbol, '1h', 100),
        ]);
        setTicker(tickerRes.data);
        setCandles(candlesRes.data.candles);
      } catch (error) {
        console.error('Failed to load market data:', error);
      }
    };

    loadMarketData();
    const interval = setInterval(loadMarketData, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, [symbol]);

  // Initialize chart on mount / symbol change
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Dispose previous chart if any
    if (chartRef.current) {
      try { chartRef.current.remove(); } catch {}
      chartRef.current = null;
      seriesRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        // Set X and Y axis text (tick labels) to dark gray
        textColor: '#6b7280', // dark gray
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.1)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.1)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(107, 114, 128, 0.4)', // subtle dark gray axis line
      },
      timeScale: {
        borderColor: 'rgba(107, 114, 128, 0.4)', // subtle dark gray axis line
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#4ade80',
      downColor: '#f87171',
      borderVisible: false,
      wickUpColor: '#4ade80',
      wickDownColor: '#f87171',
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        try { chartRef.current.remove(); } catch {}
        chartRef.current = null;
        seriesRef.current = null;
      }
    };
  }, [symbol]);

  // Update series data when candles change
  useEffect(() => {
    if (!seriesRef.current) return;
    const formattedCandles = candles.map(c => ({
      time: c.timestamp / 1000,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    try {
      seriesRef.current.setData(formattedCandles);
      chartRef.current?.timeScale().fitContent();
    } catch (e) {
      // Ignore updates if chart was disposed between renders
      console.warn('Chart update skipped:', e);
    }
  }, [candles]);

  // Removed renderChart; chart lifecycle handled in effects above

  return (
    <div className="section-card">
      <div className="section-title">
        <BarChart3 />
        Market Data & Candlestick Chart
      </div>

      {ticker && (
        <div className="grid grid-3" style={{ marginBottom: '20px' }}>
          <div style={{
            padding: '15px',
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '8px',
          }}>
            <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>Last Price</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
              ${ticker.last?.toFixed(2)}
            </div>
          </div>

          <div style={{
            padding: '15px',
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '8px',
          }}>
            <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>24h Change</div>
            <div style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: ticker.change_24h >= 0 ? '#4ade80' : '#f87171',
            }}>
              {ticker.change_24h >= 0 ? '+' : ''}{ticker.change_24h?.toFixed(2)}%
            </div>
          </div>

          <div style={{
            padding: '15px',
            background: 'rgba(0, 0, 0, 0.2)',
            borderRadius: '8px',
          }}>
            <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>24h Volume</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
              {ticker.volume?.toFixed(0)}
            </div>
          </div>
        </div>
      )}

      <div ref={chartContainerRef} className="chart-container" />
    </div>
  );
}
