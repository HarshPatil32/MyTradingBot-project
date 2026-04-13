import { useEffect } from 'react'
import MACDTrading from './screens/MACD'
import heartbeatService from './services/heartbeat'
import { API_URL } from './config'

function App() {
  useEffect(() => {
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