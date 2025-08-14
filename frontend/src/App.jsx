import { useEffect } from 'react'
import MACDTrading from './screens/MACD'
import heartbeatService from './services/heartbeat'

function App() {
  useEffect(() => {
    // Get API URL from environment variables
    const API_URL = import.meta.env.VITE_API_URL || 'https://mytradingbot-project.onrender.com';
    
    // Set the API URL for the heartbeat service
    heartbeatService.setApiUrl(API_URL);
    
    // Start the heartbeat service when the app loads
    heartbeatService.start();

    // Cleanup function to stop heartbeat when component unmounts
    return () => {
      heartbeatService.stop();
    };
  }, []);

  return (
    <div className="app">
        <div className="content">
          <MACDTrading />
        </div>
      </div>
  );
}

export default App