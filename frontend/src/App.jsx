import { useEffect, useState } from 'react'
import MACDTrading from './screens/legacy/MACD'
import BacktestUpload from './screens/BacktestUpload'
import Home from './screens/Home'
import heartbeatService from './services/heartbeat'
import { API_URL } from './config'

function App() {
  const [activeTab, setActiveTab] = useState('home')

  useEffect(() => {
    heartbeatService.setApiUrl(API_URL);
    heartbeatService.start();
    return () => heartbeatService.stop();
  }, []);

  return (
    <>
      {activeTab === 'home' ? (
        <Home onAnalyze={() => setActiveTab('backtest')} />
      ) : (
        <div className="app">
          <nav className="flex gap-2 p-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('home')}
              className="px-4 py-2 rounded text-sm font-medium text-gray-600 hover:bg-gray-100"
            >
              Home
            </button>
            <button
              onClick={() => setActiveTab('backtest')}
              className={`px-4 py-2 rounded text-sm font-medium ${
                activeTab === 'backtest' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              Backtest Upload
            </button>
            <button
              onClick={() => setActiveTab('macd')}
              className={`px-4 py-2 rounded text-sm font-medium ${
                activeTab === 'macd' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              MACD Strategy
            </button>
          </nav>
          <div className="content">
            {activeTab === 'backtest' && <BacktestUpload />}
            {activeTab === 'macd' && <MACDTrading />}
          </div>
        </div>
      )}
    </>
  );
}

export default App