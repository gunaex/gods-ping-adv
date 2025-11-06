import { useEffect, useState } from 'react';
import { 
  LogOut, Settings, Clock, FileText 
} from 'lucide-react';
import { useStore } from '../store';
import { tradingAPI } from '../api';
import TradingPairSelector from './TradingPairSelector';
import AIRecommendation from './AIRecommendation';
import AccountBalance from './AccountBalance';
import MarketData from './MarketData';
import BotsPanel from './BotsPanel';
import AdvancedAnalysis from './AdvancedAnalysis';
import GodsHand from './GodsHand';
import PaperTradingPerformance from './PaperTradingPerformance';
import SettingsModal from './SettingsModal';
import LogsModal from './LogsModal';
import { formatLocalDateTime, getUserTimezone, getUTCOffset } from '../utils/timeUtils';

export default function ShichiFukujin() {
  const { user, logout, selectedSymbol, fiatCurrency } = useStore();
  const [showSettings, setShowSettings] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [tradingPairs, setTradingPairs] = useState<any[]>([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    loadTradingPairs();
    
    // Update time every second
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const loadTradingPairs = async () => {
    try {
      const response = await tradingAPI.getPairs();
      setTradingPairs(response.data.pairs);
    } catch (error) {
      console.error('Failed to load trading pairs:', error);
    }
  };

  return (
    <div className="container">
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '30px',
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        padding: '20px',
        borderRadius: '12px',
        border: '1px solid rgba(255, 255, 255, 0.2)',
      }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '5px' }}>
            Gods Ping
          </h1>
          <p style={{ opacity: 0.8 }}>七福神 Shichi-Fukujin Trading Platform</p>
          <p style={{ 
            opacity: 0.7, 
            fontSize: '0.9rem', 
            marginTop: '5px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Clock size={16} />
            {formatLocalDateTime(currentTime)}
            <span style={{ opacity: 0.6, marginLeft: '5px' }}>
              ({getUserTimezone()} • {getUTCOffset()})
            </span>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span style={{ opacity: 0.8 }}>Welcome, {user?.username}</span>
          <button onClick={() => setShowLogs(true)}>
            <FileText size={20} />
            Logs
          </button>
          <button onClick={() => setShowSettings(true)}>
            <Settings size={20} />
            Settings
          </button>
          <button onClick={logout}>
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-2">
        {/* Section 1: Trading Pair Selector */}
        <TradingPairSelector 
          pairs={tradingPairs} 
          selectedSymbol={selectedSymbol}
        />

        {/* Section 2: AI Recommendation */}
        <AIRecommendation symbol={selectedSymbol} />
      </div>

      {/* Section 3: Account Balance & P/L */}
      <AccountBalance symbol={selectedSymbol} fiatCurrency={fiatCurrency} />

  {/* Section 4: Market Data & Chart */}
  <MarketData key={selectedSymbol} symbol={selectedSymbol} />

      <div className="grid grid-2">
        {/* Section 5: Grid Bot & DCA Bot */}
        <BotsPanel />

        {/* Section 6: Advanced AI Analysis */}
        <AdvancedAnalysis symbol={selectedSymbol} />
      </div>

      {/* Section 7: Gods Hand */}
      <GodsHand symbol={selectedSymbol} />

      {/* Section 8: Paper Trading Performance */}
      <PaperTradingPerformance />

  {/* Logs Modal */}
      {showLogs && (
        <LogsModal onClose={() => setShowLogs(false)} />
      )}

      {/* Settings Modal */}
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} />
      )}
    </div>
  );
}
