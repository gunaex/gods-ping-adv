import { useState, useEffect } from 'react';
import { 
  X, FileText, AlertCircle, User, Brain, Zap, 
  Settings, TrendingUp, Bot, Server, Filter, RefreshCw, Trash2
} from 'lucide-react';
import { formatLocalDateTime } from '../utils/timeUtils';
import { API_BASE_URL } from '../api';
import { colors, patterns } from '../theme/colors';

interface LogEntry {
  id: number;
  timestamp: string;
  category: string;
  level: string;
  message: string;
  details?: string;
  user_id?: number;
  symbol?: string;
  bot_type?: string;
  ai_recommendation?: string;
  ai_confidence?: string;
  ai_executed?: string;
  execution_reason?: string;
}

interface LogsModalProps {
  onClose: () => void;
}

export default function LogsModal({ onClose }: LogsModalProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'logs' | 'ai-comparison'>('logs');

  const categories = [
    { value: 'all', label: 'All Logs', icon: FileText, color: colors.text.secondary },
    { value: 'error', label: `${colors.logs.error.icon} Errors`, icon: AlertCircle, color: colors.logs.error.color },
    { value: 'user', label: `${colors.logs.user.icon} User Actions`, icon: User, color: colors.logs.user.color },
    { value: 'ai_thinking', label: `${colors.logs.ai_thinking.icon} AI Thinking`, icon: Brain, color: colors.logs.ai_thinking.color },
    { value: 'ai_action', label: `${colors.logs.ai_action.icon} AI Actions`, icon: Zap, color: colors.logs.ai_action.color },
    { value: 'trading', label: `${colors.logs.trading.icon} Trading`, icon: TrendingUp, color: colors.logs.trading.color },
    { value: 'config', label: `${colors.logs.config.icon} Config Changes`, icon: Settings, color: colors.logs.config.color },
    { value: 'bot', label: `${colors.logs.bot.icon} Bot Operations`, icon: Bot, color: colors.logs.bot.color },
    { value: 'system', label: `${colors.logs.system.icon} System`, icon: Server, color: colors.logs.system.color }
  ];

  useEffect(() => {
    loadLogs();
  }, [selectedCategory]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = selectedCategory !== 'all' ? `?category=${selectedCategory}&limit=200` : '?limit=200';
      const response = await fetch(`${API_BASE_URL}/logs${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = async () => {
    if (!confirm(`Clear ${selectedCategory === 'all' ? 'ALL' : selectedCategory} logs?`)) return;
    
    try {
      const params = selectedCategory !== 'all' ? `?category=${selectedCategory}` : '';
      await fetch(`${API_BASE_URL}/logs/clear${params}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      loadLogs();
    } catch (error) {
      alert('Failed to clear logs');
    }
  };

  const getLevelColor = (level: string) => {
    // Text color mapping per request:
    // - info: white
    // - warning: light blue
    // - error/critical: orange/red
    switch (level) {
      case 'error':
      case 'critical':
        return colors.status.error.color; // warm orange-red
      case 'warning':
        return colors.status.info.color; // use soft teal-blue as light blue
      case 'info':
        return '#ffffff'; // white
      case 'debug':
        return colors.text.muted;
      default:
        return '#ffffff';
    }
  };

  const getCategoryIcon = (category: string) => {
    const cat = categories.find(c => c.value === category);
    return cat ? cat.icon : FileText;
  };

  const getCategoryColor = (category: string) => {
    const cat = categories.find(c => c.value === category);
    return cat ? cat.color : colors.text.secondary;
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(5px)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        borderRadius: '16px',
        width: '95%',
        maxWidth: '1400px',
        height: '90vh',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 30px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <FileText size={28} />
            <div>
              <h2 style={{ margin: 0, fontSize: '1.5rem' }}>System Logs</h2>
              <p style={{ margin: '5px 0 0 0', opacity: 0.7, fontSize: '0.9rem' }}>
                Monitor all system activities and AI decisions
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'transparent',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            padding: '8px'
          }}>
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: '10px',
          padding: '15px 30px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <button
            onClick={() => setActiveTab('logs')}
            style={{
              padding: '10px 20px',
              background: activeTab === 'logs' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
              border: activeTab === 'logs' ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            <FileText size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            All Logs
          </button>
          <button
            onClick={() => setActiveTab('ai-comparison')}
            style={{
              padding: '10px 20px',
              background: activeTab === 'ai-comparison' ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
              border: activeTab === 'ai-comparison' ? '1px solid #8b5cf6' : '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            <Brain size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            AI Thinking vs Actions
          </button>
        </div>

        {activeTab === 'logs' && (
          <>
            {/* Category Filter */}
            <div style={{
              padding: '15px 30px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              gap: '10px',
              flexWrap: 'wrap',
              alignItems: 'center'
            }}>
              <Filter size={18} style={{ opacity: 0.7 }} />
              {categories.map(cat => {
                const Icon = cat.icon;
                return (
                  <button
                    key={cat.value}
                    onClick={() => setSelectedCategory(cat.value)}
                    style={{
                      padding: '8px 16px',
                      background: selectedCategory === cat.value ? 
                        `${cat.color}33` : 'rgba(255, 255, 255, 0.05)',
                      border: selectedCategory === cat.value ? 
                        `1px solid ${cat.color}` : '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '20px',
                      color: selectedCategory === cat.value ? cat.color : 'white',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <Icon size={14} />
                    {cat.label}
                  </button>
                );
              })}
              <div style={{ flex: 1 }} />
              <button onClick={loadLogs} style={{
                padding: '8px 16px',
                background: 'rgba(59, 130, 246, 0.2)',
                border: '1px solid #3b82f6',
                borderRadius: '8px',
                color: 'white',
                cursor: 'pointer'
              }}>
                <RefreshCw size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                Refresh
              </button>
              <button onClick={clearLogs} style={{
                padding: '8px 16px',
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #ef4444',
                borderRadius: '8px',
                color: 'white',
                cursor: 'pointer'
              }}>
                <Trash2 size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                Clear
              </button>
            </div>

            {/* Logs List */}
            <div style={{
              flex: 1,
              overflow: 'auto',
              padding: '20px 30px'
            }}>
              {loading ? (
                <div style={{ textAlign: 'center', padding: '40px', opacity: 0.7 }}>
                  Loading logs...
                </div>
              ) : logs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', opacity: 0.7 }}>
                  No logs found
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {logs.map(log => {
                    const Icon = getCategoryIcon(log.category);
                    const categoryColor = getCategoryColor(log.category);
                    
                    return (
                      <div
                        key={log.id}
                        style={{
                          background: 'rgba(255, 255, 255, 0.03)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          borderLeft: `4px solid ${categoryColor}`,
                          borderRadius: '8px',
                          padding: '15px',
                          transition: 'all 0.2s'
                        }}
                      >
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginBottom: '8px'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Icon size={16} style={{ color: categoryColor }} />
                            <span style={{
                              fontSize: '0.85rem',
                              color: categoryColor,
                              fontWeight: 'bold'
                            }}>
                              {log.category.replace('_', ' ').toUpperCase()}
                            </span>
                            <span style={{
                              fontSize: '0.8rem',
                              padding: '2px 8px',
                              background: getLevelColor(log.level) + '33',
                              color: getLevelColor(log.level),
                              borderRadius: '4px'
                            }}>
                              {log.level.toUpperCase()}
                            </span>
                            {log.symbol && (
                              <span style={{
                                fontSize: '0.8rem',
                                padding: '2px 8px',
                                background: 'rgba(255, 255, 255, 0.1)',
                                borderRadius: '4px'
                              }}>
                            {log.symbol}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: '0.85rem', opacity: 0.6, color: '#ffffff' }}>
                        {formatLocalDateTime(log.timestamp)}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '0.95rem', marginBottom: '5px', color: getLevelColor(log.level) }}>
                      {log.message}
                    </div>
                    
                    {/* AI-specific fields */}
                    {log.ai_recommendation && (
                      <div style={{
                        fontSize: '0.85rem',
                        color: '#ffffff',
                        marginTop: '8px',
                        display: 'flex',
                        gap: '15px',
                        flexWrap: 'wrap'
                      }}>
                        <span style={{
                          padding: '4px 10px',
                          background: log.ai_recommendation === 'BUY' ? colors.trading.buy.bg :
                                     log.ai_recommendation === 'SELL' ? colors.trading.sell.bg :
                                     colors.trading.neutral.bg,
                          color: log.ai_recommendation === 'BUY' ? colors.trading.buy.color :
                                 log.ai_recommendation === 'SELL' ? colors.trading.sell.color : 
                                 colors.trading.neutral.color,
                          borderRadius: '4px',
                          fontWeight: 'bold'
                        }}>
                          {log.ai_recommendation === 'BUY' && `${colors.trading.buy.shape} `}
                          {log.ai_recommendation === 'SELL' && `${colors.trading.sell.shape} `}
                          {log.ai_recommendation}
                        </span>
                        {log.ai_confidence && (
                          <span>Confidence: {(parseFloat(log.ai_confidence) * 100).toFixed(0)}%</span>
                        )}
                        {log.ai_executed && (
                          <span style={{
                            color: log.ai_executed === 'yes' ? colors.status.success.color : colors.status.error.color
                          }}>
                            {log.ai_executed === 'yes' ? patterns.success : patterns.error} Executed: {log.ai_executed.toUpperCase()}
                          </span>
                        )}
                      </div>
                    )}
                    
                    {log.execution_reason && (
                      <div style={{
                        fontSize: '0.85rem',
                        color: '#ffffff',
                        marginTop: '5px',
                        fontStyle: 'italic'
                      }}>
                        Reason: {log.execution_reason}
                      </div>
                    )}
                        
                    {log.details && (
                      <details style={{ marginTop: '8px', fontSize: '0.85rem', color: '#ffffff' }}>
                        <summary style={{ cursor: 'pointer' }}>Details</summary>
                        <pre style={{
                          marginTop: '8px',
                          padding: '10px',
                          background: 'rgba(0, 0, 0, 0.3)',
                          borderRadius: '4px',
                          overflow: 'auto',
                          color: '#ffffff'
                        }}>
                          {JSON.stringify(JSON.parse(log.details), null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                );
              })}
            </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'ai-comparison' && (
          <AIComparisonTab />
        )}
      </div>
    </div>
  );
}

function AIComparisonTab() {
  const [comparisons, setComparisons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Match text color behavior from main Logs tab
  const getLevelColor = (level?: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return colors.status.error.color; // warm orange-red
      case 'warning':
        return colors.status.info.color; // soft teal-blue as light blue
      case 'info':
        return '#ffffff'; // white
      case 'debug':
        return colors.text.muted;
      default:
        return '#ffffff';
    }
  };

  useEffect(() => {
    loadComparisons();
  }, []);

  const loadComparisons = async () => {
    try {
      const response = await fetch('/api/logs/ai-actions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setComparisons(data.comparisons || []);
    } catch (error) {
      console.error('Failed to load AI comparisons:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      flex: 1,
      overflow: 'auto',
      padding: '20px 30px'
    }}>
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', opacity: 0.7 }}>
          Loading AI comparisons...
        </div>
      ) : comparisons.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', opacity: 0.7 }}>
          No AI actions recorded yet
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {comparisons.map((comp, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '20px'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '15px'
              }}>
                <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '1.1rem',
                    fontWeight: 'bold',
                    color: '#ffffff'
                  }}>
                    {comp.symbol}
                  </span>
                  <span style={{ fontSize: '0.9rem', opacity: 0.6, color: '#ffffff' }}>
                    {formatLocalDateTime(comp.timestamp)}
                  </span>
                </div>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '20px'
              }}>
                {/* AI Thinking */}
                <div style={{
                  background: 'rgba(139, 92, 246, 0.1)',
                  border: '1px solid rgba(139, 92, 246, 0.3)',
                  borderRadius: '8px',
                  padding: '15px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '10px'
                  }}>
                    <Brain size={18} style={{ color: '#8b5cf6' }} />
                    <strong style={{ color: '#8b5cf6' }}>AI Thinking</strong>
                  </div>
                  <div style={{ fontSize: '0.9rem', marginBottom: '8px', color: getLevelColor(comp.thinking_level) }}>
                    {comp.thinking_message}
                  </div>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{
                      padding: '4px 10px',
                      background: comp.ai_recommendation === 'BUY' ? colors.trading.buy.bg :
                                 comp.ai_recommendation === 'SELL' ? colors.trading.sell.bg :
                                 colors.trading.neutral.bg,
                      color: comp.ai_recommendation === 'BUY' ? colors.trading.buy.color :
                             comp.ai_recommendation === 'SELL' ? colors.trading.sell.color : 
                             colors.trading.neutral.color,
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      fontWeight: 'bold'
                    }}>
                      {comp.ai_recommendation === 'BUY' && `${colors.trading.buy.shape} `}
                      {comp.ai_recommendation === 'SELL' && `${colors.trading.sell.shape} `}
                      {comp.ai_recommendation}
                    </span>
                    {comp.ai_confidence && (
                      <span style={{ fontSize: '0.85rem', color: '#ffffff' }}>
                        Confidence: {(parseFloat(comp.ai_confidence) * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>

                {/* Actual Action */}
                <div style={{
                  background: comp.action_taken === 'yes' ? 
                    colors.status.success.bg : colors.status.error.bg,
                  border: comp.action_taken === 'yes' ? 
                    `1px solid ${colors.status.success.border}` : `1px solid ${colors.status.error.border}`,
                  borderRadius: '8px',
                  padding: '15px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    marginBottom: '10px'
                  }}>
                    <Zap size={18} style={{ 
                      color: comp.action_taken === 'yes' ? colors.status.success.color : colors.status.error.color
                    }} />
                    <strong style={{ 
                      color: comp.action_taken === 'yes' ? colors.status.success.color : colors.status.error.color
                    }}>
                      {comp.action_taken === 'yes' ? `${patterns.success} Action Executed` : 
                       comp.action_taken === 'no' ? `${patterns.error} Action Skipped` : 'No Action'}
                    </strong>
                  </div>
                  {comp.action_message && (
                    <div style={{ fontSize: '0.9rem', marginBottom: '8px', color: getLevelColor(comp.action_level) }}>
                      {comp.action_message}
                    </div>
                  )}
                  {comp.action_reason && (
                    <div style={{ fontSize: '0.85rem', opacity: 0.85, fontStyle: 'italic', color: getLevelColor(comp.action_level) }}>
                      {comp.action_reason}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
