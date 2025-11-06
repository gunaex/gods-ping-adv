import { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import { botAPI, settingsAPI, authAPI } from '../api';
import { useStore } from '../store';

interface SettingsModalProps {
  onClose: () => void;
}

export default function SettingsModal({ onClose }: SettingsModalProps) {
  const { user } = useStore();
  const [config, setConfig] = useState<any>(null);
  const [apiKeys, setApiKeys] = useState({ api_key: '', api_secret: '' });
  const [newUser, setNewUser] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ ok: boolean; msg?: string; hint?: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await botAPI.getConfig();
      setConfig(response.data);
    } catch (error) {
      console.error('Failed to load config');
    }
  };

  const saveConfig = async () => {
    setLoading(true);
    try {
      await botAPI.updateConfig(config);
      alert('Settings saved successfully!');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const saveAPIKeys = async () => {
    setLoading(true);
    try {
      await settingsAPI.updateAPIKeys(apiKeys.api_key, apiKeys.api_secret);
      alert('API keys saved successfully!');
      setApiKeys({ api_key: '', api_secret: '' });
      setValidationResult(null);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to save API keys');
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
    } catch (err: any) {
      setValidationResult({ ok: false, msg: err.response?.data?.detail || 'Validation failed' });
    } finally {
      setValidating(false);
    }
  };

  const createUser = async () => {
    setLoading(true);
    try {
      await authAPI.createUser(newUser.username, newUser.password);
      alert('User created successfully!');
      setNewUser({ username: '', password: '' });
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  if (!config) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.8rem' }}>Settings</h2>
          <button onClick={onClose} style={{ padding: '5px 10px' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          {/* Trading Settings */}
          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '15px' }}>Trading Settings</h3>
            

            <div className="grid grid-2" style={{ marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Fiat Currency
                </label>
                <select
                  value={config.fiat_currency}
                  onChange={(e) => setConfig({...config, fiat_currency: e.target.value})}
                  style={{ width: '100%' }}
                >
                  <option value="USD">USD</option>
                  <option value="THB">THB (฿)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-2" style={{ marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Budget ($)
                </label>
                <input
                  type="number"
                  value={config.budget}
                  onChange={(e) => setConfig({...config, budget: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Paper Trading
                </label>
                <select
                  value={config.paper_trading ? 'true' : 'false'}
                  onChange={(e) => setConfig({...config, paper_trading: e.target.value === 'true'})}
                  style={{ width: '100%' }}
                >
                  <option value="true">ON (Recommended)</option>
                  <option value="false">OFF (Live Trading)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Risk Management */}
          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '15px' }}>Risk Management</h3>
            
            <div className="grid grid-3" style={{ marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Risk Level
                </label>
                <select
                  value={config.risk_level}
                  onChange={(e) => setConfig({...config, risk_level: e.target.value})}
                  style={{ width: '100%' }}
                >
                  <option value="conservative">Conservative</option>
                  <option value="moderate">Moderate</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Min Confidence (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={(config.min_confidence * 100).toFixed(0)}
                  onChange={(e) => setConfig({...config, min_confidence: parseFloat(e.target.value) / 100})}
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Max Daily Loss (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={config.max_daily_loss}
                  onChange={(e) => setConfig({...config, max_daily_loss: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                Position Size Ratio (%)
                <span style={{ marginLeft: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
                  Maximum % of budget to use per trade
                </span>
              </label>
              <input
                type="number"
                min="10"
                max="100"
                step="5"
                value={(config.position_size_ratio * 100).toFixed(0)}
                onChange={(e) => setConfig({...config, position_size_ratio: parseFloat(e.target.value) / 100})}
                style={{ width: '100%' }}
              />
              <div style={{ marginTop: '6px', fontSize: '0.8rem', opacity: 0.6, lineHeight: 1.4 }}>
                Example with ${config.budget?.toLocaleString() || '0'} budget and {config.risk_level} risk:
                <br />
                Max Position = ${(config.budget * (config.position_size_ratio || 0.95)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                &nbsp;→&nbsp;
                Actual = ${(config.budget * (config.position_size_ratio || 0.95) * (config.risk_level === 'conservative' ? 0.5 : config.risk_level === 'moderate' ? 0.75 : 1.0)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
            </div>

            <div className="grid grid-2" style={{ marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Entry Step (%)
                  <span style={{ marginLeft: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
                    How much to buy per BUY signal
                  </span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  step="1"
                  value={config.entry_step_percent || 10}
                  onChange={(e) => setConfig({...config, entry_step_percent: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
                <div style={{ marginTop: '4px', fontSize: '0.75rem', opacity: 0.6 }}>
                  10% = accumulate position gradually (DCA)
                </div>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Exit Step (%)
                  <span style={{ marginLeft: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
                    How much to sell per SELL signal
                  </span>
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  step="1"
                  value={config.exit_step_percent || 10}
                  onChange={(e) => setConfig({...config, exit_step_percent: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
                <div style={{ marginTop: '4px', fontSize: '0.75rem', opacity: 0.6 }}>
                  10% = exit position gradually (reduce risk)
                </div>
              </div>
            </div>

            <div className="grid grid-2" style={{ marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Trailing Take Profit (%)
                  <span style={{ marginLeft: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
                    Lock in profits when price drops
                  </span>
                </label>
                <input
                  type="number"
                  min="0.5"
                  max="20"
                  step="0.5"
                  value={config.trailing_take_profit_percent || 2.5}
                  onChange={(e) => setConfig({...config, trailing_take_profit_percent: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
                <div style={{ marginTop: '4px', fontSize: '0.75rem', opacity: 0.6 }}>
                  Sell when profit ≥ {config.trailing_take_profit_percent || 2.5}%
                </div>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Hard Stop Loss (%)
                  <span style={{ marginLeft: '8px', fontSize: '0.85rem', opacity: 0.7 }}>
                    Exit all if loss exceeds
                  </span>
                </label>
                <input
                  type="number"
                  min="0.5"
                  max="20"
                  step="0.5"
                  value={config.hard_stop_loss_percent || 3.0}
                  onChange={(e) => setConfig({...config, hard_stop_loss_percent: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
                <div style={{ marginTop: '4px', fontSize: '0.75rem', opacity: 0.6 }}>
                  Close position if loss ≥ {config.hard_stop_loss_percent || 3.0}%
                </div>
              </div>
            </div>
          </div>

          {/* API Keys */}
          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '15px' }}>Binance API Keys</h3>
            
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                API Key
              </label>
              <input
                type="text"
                value={apiKeys.api_key}
                onChange={(e) => setApiKeys({...apiKeys, api_key: e.target.value})}
                placeholder="Enter your Binance API Key"
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                API Secret
              </label>
              <input
                type="password"
                value={apiKeys.api_secret}
                onChange={(e) => setApiKeys({...apiKeys, api_secret: e.target.value})}
                placeholder="Enter your Binance API Secret"
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <button onClick={saveAPIKeys} disabled={loading || !apiKeys.api_key || !apiKeys.api_secret}>
                <Save size={16} />
                Save API Keys
              </button>
              <button type="button" onClick={validateKeys} disabled={validating} style={{ padding: '8px 12px' }}>
                {validating ? 'Validating…' : 'Validate Keys'}
              </button>
            </div>

            {validationResult && (
              <div
                style={{
                  marginTop: 12,
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
                {validationResult.msg && (
                  <div style={{ fontSize: '0.9rem' }}>{validationResult.msg}</div>
                )}
                {validationResult.hint && (
                  <div style={{ fontSize: '0.85rem', opacity: 0.85, marginTop: 4 }}>{validationResult.hint}</div>
                )}
              </div>
            )}
          </div>

          {/* Create User (Admin Only) */}
          {user?.is_admin && (
            <div style={{ marginBottom: '25px' }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '15px' }}>Create Additional User</h3>
              
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Username
                </label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                  placeholder="New username"
                  style={{ width: '100%' }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                  placeholder="New password"
                  style={{ width: '100%' }}
                />
              </div>

              <button onClick={createUser} disabled={loading || !newUser.username || !newUser.password}>
                Create User
              </button>
            </div>
          )}

          {/* Notification Settings */}
          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '15px' }}>Email Notifications</h3>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                Notification Email Address
              </label>
              <input
                type="email"
                value={config.notification_email || ''}
                onChange={(e) => setConfig({...config, notification_email: e.target.value})}
                placeholder="your@email.com"
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                Gmail Sender Address
              </label>
              <input
                type="email"
                value={config.gmail_user || ''}
                onChange={(e) => setConfig({...config, gmail_user: e.target.value})}
                placeholder="sender@gmail.com"
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontSize: '0.9rem' }}>
                Gmail App Password
              </label>
              <input
                type="password"
                value={config.gmail_app_password || ''}
                onChange={(e) => setConfig({...config, gmail_app_password: e.target.value})}
                placeholder="your app password"
                style={{ width: '100%' }}
              />
              <small style={{ color: '#888' }}>Generate at: myaccount.google.com/apppasswords</small>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={!!config.notify_on_action}
                  onChange={e => setConfig({...config, notify_on_action: e.target.checked})}
                />
                Notify when AI buys or sells (multiple times)
              </label>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={!!config.notify_on_position_size}
                  onChange={e => setConfig({...config, notify_on_position_size: e.target.checked})}
                />
                Notify when Position Size Ratio is reached (once per day)
              </label>
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={!!config.notify_on_failure}
                  onChange={e => setConfig({...config, notify_on_failure: e.target.checked})}
                />
                Notify when AI failure/skipped action (once per hour)
              </label>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.2)' }}>
          <button onClick={saveConfig} disabled={loading} style={{ width: '100%' }}>
            <Save size={20} />
            Save All Settings
          </button>
        </div>
      </div>
    </div>
  );
}
