import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Zap, Play, StopCircle, AlertTriangle, Settings } from 'lucide-react';
import { botAPI, API_BASE_URL } from '../api';
import { colors, typography } from '../theme/colors';

interface GodsHandProps {
  symbol: string;
}

export default function GodsHand({ symbol }: GodsHandProps) {
  const [config, setConfig] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [balance, setBalance] = useState<any>(null);
  const [continuous, setContinuous] = useState<boolean>(() => {
    const saved = localStorage.getItem('godsHand.continuous');
    return saved ? saved === 'true' : true;
  });
  const [intervalSeconds, setIntervalSeconds] = useState<number>(() => {
    const saved = localStorage.getItem('godsHand.intervalSeconds');
    const n = saved ? parseInt(saved) : 60;
    return isNaN(n) ? 60 : n;
  });

  useEffect(() => {
    loadConfig();
    loadStatus();
    loadBalance();
    
    // Auto-refresh status every 5 seconds
    const statusInterval = setInterval(() => {
      loadStatus();
      loadBalance();
    }, 5000);
    
    return () => clearInterval(statusInterval);
  }, [symbol]);

  // Sync symbol with Trading Pair Selector when bot is not running
  useEffect(() => {
    const syncSymbol = async () => {
      if (config && symbol !== config.symbol && status?.gods_hand !== 'running') {
        try {
          await botAPI.updateConfig({ symbol: symbol });
          await loadConfig(); // Reload to show updated symbol
        } catch (error) {
          console.error('Failed to sync symbol:', error);
        }
      }
    };
    syncSymbol();
  }, [symbol, config?.symbol, status?.gods_hand]);

  const loadConfig = async () => {
    try {
      const response = await botAPI.getConfig();
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load config');
    }
  };

  const loadStatus = async () => {
    try {
      const response = await botAPI.getStatus();
      console.log('Bot status response:', response.data);
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to load status');
    }
  };

  const loadBalance = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/account/balance?fiat_currency=USD`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBalance(data);
      }
    } catch (error) {
      console.error('Failed to load balance');
    }
  };

  const startGodsHand = async () => {
    console.log('Starting Gods Hand...', { continuous, intervalSeconds });
    setLoading(true);
    try {
      // Update symbol to match Trading Pair Selector before starting
      console.log('Updating config with symbol:', symbol);
      await botAPI.updateConfig({ 
        gods_hand_enabled: true,
        symbol: symbol  // Sync with Trading Pair Selector
      });
      console.log('Starting Gods Hand API call...');
      const response = await botAPI.startGodsHand(continuous, intervalSeconds);
      console.log('Gods Hand started successfully:', response.data);
      setResult(response.data);
      await loadConfig(); // Reload config to show updated symbol
      loadStatus();
    } catch (error: any) {
      console.error('Error starting Gods Hand:', error);
      alert(error.response?.data?.detail || 'Failed to start Gods Hand');
    } finally {
      setLoading(false);
    }
  };

  const stopGodsHand = async () => {
    try {
      const response = await botAPI.stopBot('gods-hand');
      alert(response.data.message);
      loadStatus();
      setResult(null);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to stop Gods Hand');
    }
  };

  return (
    <div className="section-card">
      <div className="section-title">
        <Zap />
        Gods Hand - AI Autonomous Trading
        <button 
          onClick={() => setShowSettings(true)}
          style={{ 
            marginLeft: 'auto',
            padding: '8px 16px',
            background: colors.background.card,
            border: `1px solid ${colors.border.default}`,
            borderRadius: typography.borderRadius.md,
            color: colors.text.primary
          }}
        >
          <Settings size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
          Settings
        </button>
      </div>

      <div className="grid grid-2" style={{ marginBottom: '20px' }}>
        {/* Current Symbol Balance */}
        {config && balance && (() => {
          const baseCurrency = symbol.split('/')[0];
          const quoteCurrency = symbol.split('/')[1] || 'USDT';
          const baseAsset = balance.assets?.find((a: any) => a.asset === baseCurrency);
          const quoteAsset = balance.assets?.find((a: any) => a.asset === quoteCurrency);
          
          return (
            <div style={{ 
              padding: '20px', 
              background: `linear-gradient(135deg, ${colors.primary.sage}15 0%, ${colors.primary.coral}15 100%)`,
              borderRadius: typography.borderRadius.md,
              border: `2px solid ${colors.primary.sage}`,
              boxShadow: colors.shadow.sm
            }}>
              <h3 style={{ 
                marginBottom: '15px', 
                fontSize: '1.1rem',
                color: colors.text.primary,
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                💰 {symbol} Balance
              </h3>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px'
              }}>
                {baseAsset ? (
                  <div style={{
                    padding: '12px',
                    background: colors.background.card,
                    borderRadius: '8px',
                    border: `1px solid ${colors.border.default}`
                  }}>
                    <div style={{ fontSize: '0.75rem', color: colors.text.secondary, marginBottom: '4px' }}>
                      {baseCurrency}
                    </div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.primary.sage, marginBottom: '2px' }}>
                      {baseAsset.total.toFixed(8)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: colors.text.muted }}>
                      Free: {baseAsset.free.toFixed(8)}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '12px',
                    background: colors.background.card,
                    borderRadius: '8px',
                    border: `1px solid ${colors.border.default}`,
                    textAlign: 'center',
                    color: colors.text.muted
                  }}>
                    <div style={{ fontSize: '0.75rem', marginBottom: '4px' }}>{baseCurrency}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>0.00000000</div>
                  </div>
                )}
                {quoteAsset ? (
                  <div style={{
                    padding: '12px',
                    background: colors.background.card,
                    borderRadius: '8px',
                    border: `1px solid ${colors.border.default}`
                  }}>
                    <div style={{ fontSize: '0.75rem', color: colors.text.secondary, marginBottom: '4px' }}>
                      {quoteCurrency}
                    </div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: colors.primary.coral, marginBottom: '2px' }}>
                      {quoteAsset.total.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: colors.text.muted }}>
                      Free: {quoteAsset.free.toFixed(2)}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '12px',
                    background: colors.background.card,
                    borderRadius: '8px',
                    border: `1px solid ${colors.border.default}`,
                    textAlign: 'center',
                    color: colors.text.muted
                  }}>
                    <div style={{ fontSize: '0.75rem', marginBottom: '4px' }}>{quoteCurrency}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>0.00</div>
                  </div>
                )}
              </div>
              <div style={{ 
                marginTop: '12px',
                paddingTop: '12px',
                borderTop: `1px solid ${colors.border.subtle}`,
                fontSize: '0.85rem',
                color: colors.text.secondary
              }}>
                Budget: <strong style={{ color: colors.primary.clay }}>${config.budget.toFixed(2)}</strong>
                <span style={{ marginLeft: '12px' }}>
                  {config.paper_trading ? '📝 PAPER' : '💰 REAL'}
                </span>
              </div>
            </div>
          );
        })()}

        {/* Current Config */}
        {config && (
          <div style={{ 
            padding: '20px', 
            background: colors.background.card, 
            borderRadius: typography.borderRadius.md,
            border: `1px solid ${colors.border.subtle}`,
            boxShadow: colors.shadow.sm
          }}>
            <h3 style={{ 
              marginBottom: '15px', 
              fontSize: '1.1rem',
              color: colors.text.primary,
              fontWeight: 700
            }}>
              Current Configuration
            </h3>
            <div style={{ fontSize: '0.95rem', lineHeight: '2', color: colors.text.secondary }}>
              <div>Symbol: <strong style={{ color: colors.text.primary }}>{config.symbol}</strong></div>
              <div>Risk Level: <strong style={{ color: colors.text.primary }}>{config.risk_level}</strong></div>
              <div>Min Confidence: <strong style={{ color: colors.text.primary }}>{(config.min_confidence * 100).toFixed(0)}%</strong></div>
              <div>Entry Step: <strong style={{ color: colors.text.primary }}>{config.entry_step_percent}%</strong></div>
              <div>Exit Step: <strong style={{ color: colors.text.primary }}>{config.exit_step_percent}%</strong></div>
            </div>
          </div>
        )}

        {/* Last Result (moved to second row if both balance and config exist) */}
        {result && (
          <div style={{ 
            padding: '20px', 
            background: colors.background.card,
            borderRadius: typography.borderRadius.md,
            border: `1px solid ${colors.border.subtle}`,
            boxShadow: colors.shadow.sm
          }}>
            <h3 style={{ 
              marginBottom: '15px', 
              fontSize: '1.1rem',
              color: colors.text.primary,
              fontWeight: 700
            }}>
              Last Action
            </h3>
            <div style={{
              padding: '20px',
              background: result.action === 'HOLD' ? colors.trading.neutral.bg :
                         result.action === 'BUY' ? colors.trading.buy.bg :
                         colors.trading.sell.bg,
              borderRadius: typography.borderRadius.md,
              border: `2px solid ${
                result.action === 'HOLD' ? colors.trading.neutral.border :
                result.action === 'BUY' ? colors.trading.buy.border : 
                colors.trading.sell.border
              }`,
            }}>
              <div style={{ 
                fontSize: '1.8rem', 
                fontWeight: 'bold',
                  color: (result.action || (result.status === 'hold' ? 'HOLD' : result?.recommendation?.action)) === 'HOLD' ? colors.trading.neutral.color :
                         (result.action || (result.status === 'hold' ? 'HOLD' : result?.recommendation?.action)) === 'BUY' ? colors.trading.buy.color : 
                         colors.trading.sell.color,
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                  {(result.action || (result.status === 'hold' ? 'HOLD' : result?.recommendation?.action)) === 'BUY' && colors.trading.buy.shape}
                  {(result.action || (result.status === 'hold' ? 'HOLD' : result?.recommendation?.action)) === 'SELL' && colors.trading.sell.shape}
                  {(result.action || (result.status === 'hold' ? 'HOLD' : result?.recommendation?.action)) === 'HOLD' && colors.trading.neutral.shape}
                  {result.action || (result.status === 'hold' ? 'HOLD' : (result?.recommendation?.action || 'HOLD'))}
              </div>
                <div style={{ fontSize: '0.95rem', color: colors.text.secondary, marginTop: '8px' }}>
                  {(() => {
                    const conf = typeof result.confidence === 'number' ? result.confidence : (result?.recommendation?.confidence);
                    const text = typeof conf === 'number' ? `${(conf * 100).toFixed(0)}%` : '-';
                    return (<span>Confidence: {text}</span>);
                  })()}
                </div>
              <div style={{ fontSize: '0.95rem', marginTop: '12px', color: colors.text.primary }}>
                {result.message}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div style={{
        padding: '24px',
        background: colors.background.secondary,
        borderRadius: typography.borderRadius.md,
        display: 'flex',
        gap: '15px',
        alignItems: 'center',
        justifyContent: 'space-between',
        border: `1px solid ${colors.border.default}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '14px',
            height: '14px',
            borderRadius: typography.borderRadius.round,
            background: status?.gods_hand === 'running' ? colors.trading.buy.color : colors.text.muted,
            boxShadow: status?.gods_hand === 'running' ? `0 0 12px ${colors.trading.buy.color}` : 'none',
          }} />
          <span style={{ fontSize: '1rem', color: colors.text.primary, fontWeight: 600 }}>
            Status: {status?.gods_hand || 'stopped'}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button 
            onClick={startGodsHand} 
            disabled={loading || status?.gods_hand === 'running'}
            onMouseEnter={() => console.log('Execute Now - disabled?', loading || status?.gods_hand === 'running', 'status:', status?.gods_hand)}
          >
            <Play size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
            Execute Now
          </button>
          <button 
            onClick={stopGodsHand} 
            disabled={status?.gods_hand !== 'running'}
            onMouseEnter={() => console.log('Stop - disabled?', status?.gods_hand !== 'running', 'status:', status?.gods_hand)}
            style={{
              background: `linear-gradient(135deg, ${colors.status.error.color} 0%, ${colors.primary.warmRed} 100%)`,
            }}
          >
            <StopCircle size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
            Stop
          </button>
        </div>
      </div>

      {config?.paper_trading && (
        <div style={{
          marginTop: '15px',
          padding: '16px',
          background: colors.status.warning.bg,
          borderRadius: typography.borderRadius.md,
          border: `1.5px solid ${colors.status.warning.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <AlertTriangle size={20} color={colors.status.warning.color} />
          <span style={{ fontSize: '1rem', color: colors.text.primary, fontWeight: 600 }}>
            📝 Paper Trading Mode Active - No real trades will be executed
          </span>
        </div>
      )}

      {/* Settings Modal */}
      {showSettings && createPortal(
        <GodsHandSettingsModal
          config={config}
          continuous={continuous}
          intervalSeconds={intervalSeconds}
          onClose={() => setShowSettings(false)}
          onSave={async (newConfig: any) => {
            try {
              await botAPI.updateConfig(newConfig);
              await loadConfig();
              setShowSettings(false);
            } catch (error) {
              alert('Failed to save settings');
            }
          }}
          onSaveRunSettings={(cont: boolean, interval: number) => {
            setContinuous(cont);
            setIntervalSeconds(interval);
            localStorage.setItem('godsHand.continuous', String(cont));
            localStorage.setItem('godsHand.intervalSeconds', String(interval));
          }}
        />,
        document.body
      )}
    </div>
  );
}

// Settings Modal Component
function GodsHandSettingsModal({ config, onClose, onSave, onSaveRunSettings, continuous, intervalSeconds }: any) {
  const [settings, setSettings] = useState({
    paper_trading: config?.paper_trading || false,
    budget: config?.budget || 1000,
    risk_level: config?.risk_level || 'medium',
    min_confidence: config?.min_confidence || 0.7,
    gods_hand_enabled: config?.gods_hand_enabled || false,
  });

  const [runSettings, setRunSettings] = useState({
    continuous: typeof continuous === 'boolean' ? continuous : true,
    intervalSeconds: intervalSeconds || 60,
  });

  const [resetting, setResetting] = useState(false);

  const handleResetPaperTrading = async () => {
    if (!confirm('⚠️ This will delete ALL paper trading history!\n\nAre you sure you want to reset?')) {
      return;
    }
    
    setResetting(true);
    try {
      const response = await botAPI.resetPaperTrading();
      alert(`✅ ${response.data.message}\n\nDeleted ${response.data.deleted_trades} trades and ${response.data.deleted_snapshots} snapshots.`);
    } catch (error: any) {
      alert(`❌ Failed to reset: ${error.response?.data?.detail || error.message}`);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: colors.background.overlay,
        backdropFilter: 'blur(8px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 99999,
        padding: '20px',
        overflow: 'auto'
      }}
      onClick={(e) => {
        // Close when clicking backdrop
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div style={{
        background: `linear-gradient(135deg, ${colors.background.primary} 0%, ${colors.background.secondary} 100%)`,
        borderRadius: typography.borderRadius.xl,
        width: '100%',
        maxWidth: '600px',
        padding: '32px',
        boxShadow: colors.shadow.lg,
        border: `1px solid ${colors.border.default}`,
        position: 'relative',
        zIndex: 100000
      }}
      onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ 
          margin: '0 0 24px 0', 
          fontSize: '1.8rem',
          color: colors.text.primary,
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <Settings size={28} color={colors.primary.warmRed} />
          Gods Hand Settings
        </h2>

        {/* Paper Trading Toggle */}
        <div style={{
          padding: '20px',
          background: settings.paper_trading ? colors.status.warning.bg : colors.trading.buy.bg,
          border: `2px solid ${settings.paper_trading ? colors.status.warning.border : colors.trading.buy.border}`,
          borderRadius: typography.borderRadius.md,
          marginBottom: '20px',
          cursor: 'pointer',
        }}
        onClick={() => setSettings({ ...settings, paper_trading: !settings.paper_trading })}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: colors.text.primary, marginBottom: '6px' }}>
                {settings.paper_trading ? '📝 Paper Trading' : '💰 Real Trading'}
              </div>
              <div style={{ fontSize: '0.9rem', color: colors.text.secondary }}>
                {settings.paper_trading 
                  ? 'Simulate trades without real money'
                  : 'Execute real trades with your funds'}
              </div>
            </div>
            <div style={{
              width: '60px',
              height: '32px',
              background: settings.paper_trading ? colors.status.warning.color : colors.trading.buy.color,
              borderRadius: '16px',
              position: 'relative',
              transition: 'all 0.3s ease',
            }}>
              <div style={{
                width: '28px',
                height: '28px',
                background: colors.background.primary,
                borderRadius: '50%',
                position: 'absolute',
                top: '2px',
                left: settings.paper_trading ? '2px' : '30px',
                transition: 'all 0.3s ease',
                boxShadow: colors.shadow.sm
              }} />
            </div>
          </div>
        </div>

        {/* Budget */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '10px',
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '1rem'
          }}>
            Trading Budget ($)
          </label>
          <input 
            type="number"
            value={settings.budget}
            onChange={(e) => setSettings({ ...settings, budget: parseFloat(e.target.value) })}
          />
        </div>

        {/* Risk Level */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '10px',
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '1rem'
          }}>
            Risk Level
          </label>
          <select
            value={settings.risk_level}
            onChange={(e) => setSettings({ ...settings, risk_level: e.target.value })}
          >
            <option value="low">🛡️ Low - Conservative</option>
            <option value="medium">⚖️ Medium - Balanced</option>
            <option value="high">⚡ High - Aggressive</option>
          </select>
        </div>

        {/* Min Confidence */}
        <div style={{ marginBottom: '28px' }}>
          <label style={{ 
            display: 'block', 
            marginBottom: '10px',
            color: colors.text.primary,
            fontWeight: 600,
            fontSize: '1rem'
          }}>
            Minimum Confidence: {(settings.min_confidence * 100).toFixed(0)}%
          </label>
          <input 
            type="range"
            min="0.5"
            max="0.95"
            step="0.05"
            value={settings.min_confidence}
            onChange={(e) => setSettings({ ...settings, min_confidence: parseFloat(e.target.value) })}
            style={{
              width: '100%',
              height: '8px',
              borderRadius: '4px',
              background: `linear-gradient(to right, ${colors.trading.sell.color} 0%, ${colors.status.warning.color} 50%, ${colors.trading.buy.color} 100%)`,
              cursor: 'pointer'
            }}
          />
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            fontSize: '0.85rem',
            color: colors.text.secondary,
            marginTop: '6px'
          }}>
            <span>50% - Risky</span>
            <span>95% - Very Safe</span>
          </div>
        </div>

        {/* Continuous Mode & Interval */}
        <div style={{
          padding: '16px',
          background: colors.background.secondary,
          borderRadius: typography.borderRadius.md,
          border: `1px solid ${colors.border.subtle}`,
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ color: colors.text.primary, fontWeight: 600 }}>Continuous Mode</div>
            <input
              type="checkbox"
              checked={runSettings.continuous}
              onChange={(e) => setRunSettings({ ...runSettings, continuous: e.target.checked })}
            />
          </div>

          <div>
            <label style={{
              display: 'block', marginBottom: '8px', color: colors.text.secondary
            }}>
              Interval (seconds)
            </label>
            <select
              value={runSettings.intervalSeconds}
              onChange={(e) => setRunSettings({ ...runSettings, intervalSeconds: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            >
              <option value={30}>30</option>
              <option value={60}>60</option>
              <option value={120}>120</option>
              <option value={300}>300</option>
            </select>
          </div>
        </div>

        {/* Reset Paper Trading */}
        {settings.paper_trading && (
          <div style={{
            padding: '16px',
            background: colors.status.warning.bg,
            borderRadius: typography.borderRadius.md,
            border: `2px solid ${colors.status.warning.border}`,
            marginBottom: '20px'
          }}>
            <div style={{ 
              color: colors.text.primary, 
              fontWeight: 700, 
              marginBottom: '8px',
              fontSize: '1rem'
            }}>
              🔄 Reset Paper Trading
            </div>
            <div style={{ 
              color: colors.text.secondary, 
              fontSize: '0.9rem',
              marginBottom: '12px'
            }}>
              Clear all paper trading history and start fresh. This cannot be undone.
            </div>
            <button
              onClick={handleResetPaperTrading}
              disabled={resetting}
              style={{
                width: '100%',
                padding: '12px',
                background: colors.status.error.bg,
                color: colors.status.error.color,
                border: `2px solid ${colors.status.error.border}`,
                borderRadius: typography.borderRadius.md,
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: resetting ? 'not-allowed' : 'pointer',
                opacity: resetting ? 0.6 : 1
              }}
            >
              {resetting ? '⏳ Resetting...' : '🗑️ Reset All Paper Trading Data'}
            </button>
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={onClose}
            style={{
              flex: 1,
              padding: '14px',
              background: colors.background.secondary,
              color: colors.text.primary,
              border: `1.5px solid ${colors.border.default}`,
              borderRadius: typography.borderRadius.md,
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => { onSave(settings); onSaveRunSettings(runSettings.continuous, runSettings.intervalSeconds); }}
            style={{
              flex: 1,
              padding: '14px',
              borderRadius: typography.borderRadius.md,
              fontSize: '1rem',
              fontWeight: 600
            }}
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}
