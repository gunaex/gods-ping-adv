import { useEffect, useState } from 'react';
import { botAPI, API_BASE_URL } from '../api';
import { Activity, RefreshCw } from 'lucide-react';
import { colors, typography } from '../theme/colors';

export default function PaperTradingPerformance() {
  const [performance, setPerformance] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    loadPerformance();
    const interval = setInterval(loadPerformance, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadPerformance = async () => {
    try {
      const [perfRes, histRes] = await Promise.all([
        fetch(`${API_BASE_URL}/paper-trading/performance`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch(`${API_BASE_URL}/paper-trading/history?days=7`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (perfRes.ok) {
        const perfData = await perfRes.json();
        setPerformance(perfData);
      }

      if (histRes.ok) {
        const histData = await histRes.json();
        setHistory(histData.history || []);
      }
    } catch (error) {
      console.error('Failed to load paper trading performance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all paper trading history? This cannot be undone.')) {
      return;
    }
    setResetting(true);
    try {
      await botAPI.resetPaperTrading();
      await loadPerformance();
      alert('Paper trading history has been reset.');
    } catch (error: any) {
      alert('Failed to reset paper trading history: ' + (error.response?.data?.detail || error.message));
    } finally {
      setResetting(false);
    }
  };

  if (loading) {
    return <div className="section-card">Loading performance data...</div>;
  }

  if (!performance) {
    return (
      <div className="section-card">
        <div className="section-title">
          <Activity />
          Paper Trading Performance
        </div>
        <p style={{ textAlign: 'center', opacity: 0.7, padding: '40px 0' }}>
          No paper trading data available yet. Start Gods Hand to begin tracking performance.
        </p>
      </div>
    );
  }

  const isProfit = performance.total_pl >= 0;
  const plColor = isProfit ? colors.trading.buy.color : colors.trading.sell.color;

  return (
    <div className="section-card">
      <div className="section-title">
        <Activity />
        Paper Trading Performance (7 Day History)
        <button 
          onClick={handleReset} 
          disabled={resetting}
          style={{ 
            marginLeft: 'auto', 
            padding: '8px 12px',
            background: colors.status.error.bg,
            border: `1px solid ${colors.status.error.border}`,
            color: colors.status.error.color,
            borderRadius: typography.borderRadius.md,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <RefreshCw size={14} />
          {resetting ? 'Resetting...' : 'Reset History'}
        </button>
      </div>

      {/* Performance Summary */}
      <div className="grid grid-4" style={{ marginBottom: '24px' }}>
        {/* Starting Balance */}
        <div style={{
          padding: '20px',
          background: colors.background.card,
          borderRadius: typography.borderRadius.md,
          border: `1px solid ${colors.border.subtle}`,
        }}>
          <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '8px' }}>
            Starting Balance
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: colors.text.primary }}>
            ${performance.starting_balance?.toFixed(2)}
          </div>
        </div>

        {/* Current Balance */}
        <div style={{
          padding: '20px',
          background: colors.background.card,
          borderRadius: typography.borderRadius.md,
          border: `2px solid ${plColor}`,
        }}>
          <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '8px' }}>
            Current Balance
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: plColor }}>
            ${performance.current_balance?.toFixed(2)}
          </div>
        </div>

        {/* Total P/L */}
        <div style={{
          padding: '20px',
          background: isProfit ? colors.trading.buy.bg : colors.trading.sell.bg,
          borderRadius: typography.borderRadius.md,
          border: `2px solid ${plColor}`,
        }}>
          <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '8px' }}>
            Total P/L
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: plColor }}>
            {isProfit ? '+' : ''}${performance.total_pl?.toFixed(2)}
          </div>
          <div style={{ fontSize: '1.1rem', color: plColor, marginTop: '4px' }}>
            ({isProfit ? '+' : ''}{performance.pl_percent?.toFixed(2)}%)
          </div>
        </div>

        {/* Win Rate */}
        <div style={{
          padding: '20px',
          background: colors.background.card,
          borderRadius: typography.borderRadius.md,
          border: `1px solid ${colors.border.subtle}`,
        }}>
          <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '8px' }}>
            Win Rate
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: colors.primary.sage }}>
            {performance.win_rate?.toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.9rem', color: colors.text.secondary, marginTop: '4px' }}>
            {performance.winning_trades} / {performance.sell_trades} trades
          </div>
        </div>
      </div>

      {/* Position Details */}
      <div style={{
        padding: '20px',
        background: colors.background.secondary,
        borderRadius: typography.borderRadius.md,
        marginBottom: '24px',
        border: `1px solid ${colors.border.default}`,
      }}>
        <h3 style={{ marginBottom: '16px', color: colors.text.primary }}>Current Position</h3>
        <div className="grid grid-2">
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Quantity Held</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.text.primary }}>
              {performance.quantity_held?.toFixed(6)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Avg Buy Price</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.text.primary }}>
              ${performance.avg_buy_price?.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Current Price</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.text.primary }}>
              ${performance.current_price?.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Position Value</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.text.primary }}>
              ${performance.position_value?.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Trade Statistics */}
      <div style={{
        padding: '20px',
        background: colors.background.secondary,
        borderRadius: typography.borderRadius.md,
        border: `1px solid ${colors.border.default}`,
      }}>
        <h3 style={{ marginBottom: '16px', color: colors.text.primary }}>Trade Statistics</h3>
        <div className="grid grid-3">
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Total Trades</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: colors.text.primary }}>
              {performance.total_trades}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Realized P/L</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: performance.realized_pl >= 0 ? colors.trading.buy.color : colors.trading.sell.color }}>
              ${performance.realized_pl?.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>Unrealized P/L</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: performance.unrealized_pl >= 0 ? colors.trading.buy.color : colors.trading.sell.color }}>
              ${performance.unrealized_pl?.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Chart (Simple) */}
      {history.length > 0 && (
        <div style={{
          marginTop: '24px',
          padding: '20px',
          background: colors.background.secondary,
          borderRadius: typography.borderRadius.md,
          border: `1px solid ${colors.border.default}`,
        }}>
          <h3 style={{ marginBottom: '16px', color: colors.text.primary }}>7-Day Performance</h3>
          <div style={{ fontSize: '0.9rem', color: colors.text.secondary }}>
            {history.length} snapshots recorded
          </div>
        </div>
      )}
    </div>
  );
}
