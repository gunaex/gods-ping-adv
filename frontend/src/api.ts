import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  createUser: (username: string, password: string) =>
    api.post('/auth/create-user', { username, password }),
  
  getMe: () => api.get('/auth/me'),
};

export const marketAPI = {
  getTicker: (symbol: string) => api.get(`/market/ticker/${symbol}`),
  
  getCandles: (symbol: string, timeframe: string = '1h', limit: number = 100) =>
    api.get(`/market/candles/${symbol}`, { params: { timeframe, limit } }),
  
  getOrderbook: (symbol: string, limit: number = 20) =>
    api.get(`/market/orderbook/${symbol}`, { params: { limit } }),
};

export const aiAPI = {
  getRecommendation: (symbol: string) =>
    api.get(`/ai/recommendation/${symbol}`),
  
  getAnalysis: (symbol: string) =>
    api.get(`/ai/analysis/${symbol}`),
};

export const tradingAPI = {
  getPairs: () => api.get('/trading-pairs'),
  
  executeTrade: (symbol: string, side: string, amount: number, price?: number) =>
    api.post('/trade/execute', { symbol, side, amount, price }),
  
  getHistory: (limit: number = 50) =>
    api.get('/trade/history', { params: { limit } }),
};

export const botAPI = {
  getConfig: () => api.get('/settings/bot-config'),
  
  updateConfig: (config: any) => api.put('/settings/bot-config', config),
  
  startGrid: () => api.post('/bot/grid/start'),
  
  startDCA: () => api.post('/bot/dca/start'),
  
  startGodsHand: (continuous: boolean = true, intervalSeconds: number = 60) =>
    api.post('/bot/gods-hand/start', {}, { params: { continuous, interval_seconds: intervalSeconds } }),
  
  stopBot: (botType: string) => api.post(`/bot/${botType}/stop`),
  
  getStatus: () => api.get('/bot/status'),
  
  resetPaperTrading: (symbol?: string) => 
    api.post('/bot/paper-trading/reset', {}, { params: symbol ? { symbol } : {} }),
};

export const settingsAPI = {
  updateAPIKeys: (apiKey: string, apiSecret: string) =>
    api.post('/settings/api-keys', {
      binance_api_key: apiKey,
      binance_api_secret: apiSecret,
    }),
  validateKeys: () => api.get('/settings/validate-keys'),
};

export const systemAPI = {
  getServerInfo: () => axios.get('/'),
};

export default api;
