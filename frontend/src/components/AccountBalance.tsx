import { useEffect, useState } from 'react';
import { Wallet, TrendingUp, TrendingDown, DollarSign, RefreshCw } from 'lucide-react';
import { colors, patterns } from '../theme/colors';
import SettingsModal from './SettingsModal';
import { settingsAPI } from '../api';

interface AccountBalanceProps {
  symbol: string;
  fiatCurrency: string;
}

interface BalanceData {
  total_balance: number;
  available_balance: number;
  in_orders: number;
  total_pnl: number;
  total_pnl_percentage: number;
  daily_pnl: number;
  daily_pnl_percentage: number;
  fiat_currency?: string;
  exchange_rate?: number;
  assets: Array<{
    asset: string;
    free: number;
    locked: number;
    total: number;
    usd_value: number;
  }>;
  error?: string;
}

export default function AccountBalance({ symbol, fiatCurrency }: AccountBalanceProps) {
  const [balance, setBalance] = useState<BalanceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ ok: boolean; msg?: string; hint?: string } | null>(null);

  useEffect(() => {
    loadBalance();
  }, [symbol, fiatCurrency]);

  const loadBalance = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/account/balance?fiat_currency=${fiatCurrency}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }
      
      const data = await response.json();
      
      // Check if response contains an error message
      if (data.error) {
        setError(data.error);
      }
      
      setBalance(data);
    } catch (error: any) {
      console.error('Failed to load balance:', error);
      setError(error.message || 'Failed to load account balance');
    } finally {
      setLoading(false);
    }
  };

  const validateKeys = async () => {
    setValidating(true);
    setValidationResult(null);
    try {
      const res = await settingsAPI.validateKeys();
      const data = res.data;
      if (data.ok) {
        setValidationResult({ ok: true, msg: data.msg });
      } else {
        setValidationResult({ ok: false, msg: data.error, hint: data.hint });
      }
    } catch (e: any) {
      setValidationResult({ ok: false, msg: e.response?.data?.detail || 'Validation failed' });
    } finally {
      setValidating(false);
    }
  };

  const formatCurrency = (value: number) => {
    if (fiatCurrency === 'THB') {
      return `฿${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return colors.trading.buy.color;
    if (pnl < 0) return colors.trading.sell.color;
    return colors.trading.neutral.color;
  };

  const getPnLBg = (pnl: number) => {
    if (pnl > 0) return colors.trading.buy.bg;
    if (pnl < 0) return colors.trading.sell.bg;
    return colors.trading.neutral.bg;
  };

  const getPnLShape = (pnl: number) => {
    if (pnl > 0) return colors.trading.buy.shape;
    if (pnl < 0) return colors.trading.sell.shape;
    return colors.trading.neutral.shape;
  };

  const getPnLIcon = (pnl: number) => {
    if (pnl > 0) return <TrendingUp size={20} />;
    if (pnl < 0) return <TrendingDown size={20} />;
    return <DollarSign size={20} />;
  };

  return (
    <div className="section-card">
      <div className="section-title">
        <Wallet />
        Account Balance & P/L
        {balance?.exchange_rate && balance.exchange_rate !== 1 && (
          <span style={{ 
            fontSize: '0.85rem', 
            fontWeight: 'normal',
            marginLeft: '12px',
            padding: '4px 10px',
            background: colors.status.info.bg,
            color: colors.status.info.color,
            borderRadius: '6px',
            border: `1px solid ${colors.status.info.border}`
          }}>
            1 USD = {balance.exchange_rate.toFixed(2)} {fiatCurrency}
          </span>
        )}
        <button 
          onClick={loadBalance} 
          disabled={loading}
          style={{ 
            marginLeft: 'auto', 
            padding: '5px 15px',
            background: colors.status.info.bg,
            border: `1px solid ${colors.status.info.border}`,
            borderRadius: '6px',
            color: colors.status.info.color,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          <RefreshCw size={16} style={{ 
            animation: loading ? 'spin 1s linear infinite' : 'none',
            verticalAlign: 'middle'
          }} />
        </button>
      </div>

      {error && (
        <div style={{
          padding: '15px',
          background: colors.status.error.bg,
          border: `1px solid ${colors.status.error.border}`,
          borderRadius: '8px',
          color: colors.status.error.color,
          marginBottom: '15px',
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 320px' }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{patterns.error} Could not load balance</div>
              <div style={{ fontSize: '0.95rem' }}>{error}</div>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={validateKeys}
                disabled={validating}
                style={{ padding: '8px 12px' }}
              >
                {validating ? 'Validating…' : 'Validate Keys'}
              </button>
              <button
                onClick={() => setShowSettings(true)}
                style={{ padding: '8px 12px' }}
              >
                Fix in Settings
              </button>
            </div>
          </div>
          {validationResult && (
            <div
              style={{
                marginTop: 10,
                padding: '10px 12px',
                borderRadius: 8,
                border: `1px solid ${validationResult.ok ? 'rgba(123,170,109,0.6)' : 'rgba(217,119,87,0.6)'}`,
                background: validationResult.ok ? 'rgba(123,170,109,0.12)' : 'rgba(217,119,87,0.12)',
                color: validationResult.ok ? '#2D5D2A' : '#7A3A2C',
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 4 }}>
                {validationResult.ok ? 'API keys are valid ✅' : 'API keys invalid ❌'}
              </div>
              {validationResult.msg && <div style={{ fontSize: '0.9rem' }}>{validationResult.msg}</div>}
              {validationResult.hint && (
                <div style={{ fontSize: '0.85rem', opacity: 0.85, marginTop: 4 }}>{validationResult.hint}</div>
              )}
            </div>
          )}
        </div>
      )}

      {loading && !balance ? (
        <div style={{ textAlign: 'center', padding: '40px', color: colors.text.secondary }}>
          Loading balance...
        </div>
      ) : balance ? (
        <div>
          {/* Symbol-Specific Balance (if applicable) */}
          {symbol && (() => {
            // Extract base currency from symbol (e.g., BTC from BTC/USDT)
            const baseCurrency = symbol.split('/')[0];
            const quoteCurrency = symbol.split('/')[1] || 'USDT';
            
            // Find the asset for this trading pair
            const baseAsset = balance.assets?.find(a => a.asset === baseCurrency);
            const quoteAsset = balance.assets?.find(a => a.asset === quoteCurrency);
            
            if (baseAsset || quoteAsset) {
              return (
                <div style={{
                  padding: '20px',
                  background: `linear-gradient(135deg, ${colors.primary.sage}15 0%, ${colors.primary.coral}15 100%)`,
                  border: `2px solid ${colors.primary.sage}`,
                  borderRadius: '12px',
                  marginBottom: '20px'
                }}>
                  <div style={{
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    color: colors.text.primary,
                    marginBottom: '15px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    💰 {symbol} Balance
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: '12px'
                  }}>
                    {baseAsset && (
                      <div style={{
                        padding: '15px',
                        background: colors.background.card,
                        borderRadius: '8px',
                        border: `1px solid ${colors.border.default}`
                      }}>
                        <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '6px' }}>
                          {baseCurrency}
                        </div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: colors.primary.sage, marginBottom: '4px' }}>
                          {baseAsset.total.toFixed(8)}
                        </div>
                        <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>
                          {formatCurrency(baseAsset.usd_value)}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: colors.text.muted, marginTop: '4px' }}>
                          Free: {baseAsset.free.toFixed(8)}
                        </div>
                      </div>
                    )}
                    {quoteAsset && (
                      <div style={{
                        padding: '15px',
                        background: colors.background.card,
                        borderRadius: '8px',
                        border: `1px solid ${colors.border.default}`
                      }}>
                        <div style={{ fontSize: '0.85rem', color: colors.text.secondary, marginBottom: '6px' }}>
                          {quoteCurrency}
                        </div>
                        <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: colors.primary.coral, marginBottom: '4px' }}>
                          {quoteAsset.total.toFixed(2)}
                        </div>
                        <div style={{ fontSize: '0.85rem', color: colors.text.secondary }}>
                          {formatCurrency(quoteAsset.usd_value)}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: colors.text.muted, marginTop: '4px' }}>
                          Free: {quoteAsset.free.toFixed(2)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            }
            return null;
          })()}

          {/* Main Balance Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '15px',
            marginBottom: '20px'
          }}>
            {/* Total Balance */}
            <div style={{
              padding: '20px',
              background: colors.background.card,
              border: `1px solid ${colors.border.default}`,
              borderRadius: '12px',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = colors.background.cardHover;
              e.currentTarget.style.borderColor = colors.border.hover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = colors.background.card;
              e.currentTarget.style.borderColor = colors.border.default;
            }}
            >
              <div style={{ 
                fontSize: '0.85rem', 
                color: colors.text.secondary,
                marginBottom: '8px'
              }}>
                Total Balance
              </div>
              <div style={{ 
                fontSize: '1.8rem', 
                fontWeight: 'bold',
                color: colors.primary.coral
              }}>
                {formatCurrency(balance.total_balance)}
              </div>
            </div>

            {/* Available Balance */}
            <div style={{
              padding: '20px',
              background: colors.background.card,
              border: `1px solid ${colors.border.default}`,
              borderRadius: '12px',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = colors.background.cardHover;
              e.currentTarget.style.borderColor = colors.border.hover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = colors.background.card;
              e.currentTarget.style.borderColor = colors.border.default;
            }}
            >
              <div style={{ 
                fontSize: '0.85rem', 
                color: colors.text.secondary,
                marginBottom: '8px'
              }}>
                Available
              </div>
              <div style={{ 
                fontSize: '1.8rem', 
                fontWeight: 'bold',
                color: colors.primary.sage
              }}>
                {formatCurrency(balance.available_balance)}
              </div>
            </div>

            {/* In Orders */}
            <div style={{
              padding: '20px',
              background: colors.background.card,
              border: `1px solid ${colors.border.default}`,
              borderRadius: '12px',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = colors.background.cardHover;
              e.currentTarget.style.borderColor = colors.border.hover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = colors.background.card;
              e.currentTarget.style.borderColor = colors.border.default;
            }}
            >
              <div style={{ 
                fontSize: '0.85rem', 
                color: colors.text.secondary,
                marginBottom: '8px'
              }}>
                In Orders
              </div>
              <div style={{ 
                fontSize: '1.8rem', 
                fontWeight: 'bold',
                color: colors.primary.peach
              }}>
                {formatCurrency(balance.in_orders)}
              </div>
            </div>
          </div>

          {/* P/L Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '15px',
            marginBottom: '20px'
          }}>
            {/* Total P/L */}
            <div style={{
              padding: '20px',
              background: getPnLBg(balance.total_pnl),
              border: `2px solid ${getPnLColor(balance.total_pnl)}`,
              borderRadius: '12px',
            }}>
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '10px',
                color: colors.text.secondary
              }}>
                {getPnLIcon(balance.total_pnl)}
                <span style={{ fontSize: '0.85rem' }}>Total P/L</span>
              </div>
              <div style={{ 
                fontSize: '1.6rem', 
                fontWeight: 'bold',
                color: getPnLColor(balance.total_pnl),
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{ fontSize: '1.2rem' }}>{getPnLShape(balance.total_pnl)}</span>
                {formatCurrency(balance.total_pnl)}
              </div>
              <div style={{ 
                fontSize: '1rem',
                marginTop: '5px',
                color: getPnLColor(balance.total_pnl),
                fontWeight: '600'
              }}>
                {balance.total_pnl >= 0 ? '+' : ''}{balance.total_pnl_percentage.toFixed(2)}%
              </div>
            </div>

            {/* Daily P/L */}
            <div style={{
              padding: '20px',
              background: getPnLBg(balance.daily_pnl),
              border: `2px solid ${getPnLColor(balance.daily_pnl)}`,
              borderRadius: '12px',
            }}>
              <div style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '10px',
                color: colors.text.secondary
              }}>
                {getPnLIcon(balance.daily_pnl)}
                <span style={{ fontSize: '0.85rem' }}>Daily P/L</span>
              </div>
              <div style={{ 
                fontSize: '1.6rem', 
                fontWeight: 'bold',
                color: getPnLColor(balance.daily_pnl),
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{ fontSize: '1.2rem' }}>{getPnLShape(balance.daily_pnl)}</span>
                {formatCurrency(balance.daily_pnl)}
              </div>
              <div style={{ 
                fontSize: '1rem',
                marginTop: '5px',
                color: getPnLColor(balance.daily_pnl),
                fontWeight: '600'
              }}>
                {balance.daily_pnl >= 0 ? '+' : ''}{balance.daily_pnl_percentage.toFixed(2)}%
              </div>
            </div>
          </div>

          {/* Assets List */}
          {balance.assets && balance.assets.length > 0 && (
            <div>
              <div style={{
                fontSize: '0.9rem',
                color: colors.text.secondary,
                marginBottom: '10px',
                fontWeight: '600'
              }}>
                Assets Breakdown
              </div>
              <div style={{
                display: 'grid',
                gap: '8px'
              }}>
                {balance.assets
                  .filter(asset => asset.total > 0)
                  .sort((a, b) => b.usd_value - a.usd_value)
                  .map(asset => (
                  <div key={asset.asset} style={{
                    padding: '12px 15px',
                    background: colors.background.card,
                    border: `1px solid ${colors.border.default}`,
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        background: colors.primary.sage + '33',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        color: colors.primary.sage
                      }}>
                        {asset.asset.substring(0, 2)}
                      </div>
                      <div>
                        <div style={{ 
                          fontWeight: 'bold',
                          color: colors.text.primary,
                          fontSize: '1rem'
                        }}>
                          {asset.asset}
                        </div>
                        <div style={{ 
                          fontSize: '0.8rem',
                          color: colors.text.secondary
                        }}>
                          Free: {asset.free.toFixed(8)} | Locked: {asset.locked.toFixed(8)}
                        </div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ 
                        fontWeight: 'bold',
                        color: colors.text.primary
                      }}>
                        {asset.total.toFixed(8)}
                      </div>
                      <div style={{ 
                        fontSize: '0.85rem',
                        color: colors.text.secondary
                      }}>
                        {formatCurrency(asset.usd_value)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px',
          color: colors.text.secondary
        }}>
          No balance data available. Configure your API keys in Settings.
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}
