// Heartbeat service to keep the backend alive on Render's free tier
import axios from 'axios';

class HeartbeatService {
  constructor(apiUrl = null) {
    this.apiUrl = apiUrl;
    this.intervalId = null;
    this.isRunning = false;
    this.heartbeatInterval = 4 * 60 * 1000; // 4 minutes in milliseconds
  }

  // Method to set or update the API URL
  setApiUrl(apiUrl) {
    this.apiUrl = apiUrl;
    console.log(`Heartbeat service API URL set to: ${apiUrl}`);
  }

  async sendHeartbeat() {
    if (!this.apiUrl) {
      console.warn('Heartbeat skipped: API URL not set');
      return false;
    }

    try {
      console.log(`Sending heartbeat to backend: ${this.apiUrl}/heartbeat`);
      const response = await axios.get(`${this.apiUrl}/heartbeat`, {
        timeout: 10000, // 10 second timeout
        headers: {
          'Accept': 'application/json',
        }
      });

      if (response.status === 200) {
        const data = response.data;
        console.log('Heartbeat successful:', data.timestamp);
        return true;
      } else {
        console.warn('Heartbeat failed with status:', response.status);
        return false;
      }
    } catch (error) {
      console.error('Heartbeat error:', error.message);
      return false;
    }
  }

  start() {
    if (this.isRunning) {
      console.log('Heartbeat service is already running');
      return;
    }

    console.log('Starting heartbeat service...');
    this.isRunning = true;

    // Send initial heartbeat
    this.sendHeartbeat();

    // Set up interval for regular heartbeats
    this.intervalId = setInterval(() => {
      this.sendHeartbeat();
    }, this.heartbeatInterval);

    console.log(`Heartbeat service started - will ping every ${this.heartbeatInterval / 60000} minutes`);
  }

  stop() {
    if (!this.isRunning) {
      console.log('Heartbeat service is not running');
      return;
    }

    console.log('Stopping heartbeat service...');
    this.isRunning = false;

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    console.log('Heartbeat service stopped');
  }

  getStatus() {
    return {
      isRunning: this.isRunning,
      intervalMinutes: this.heartbeatInterval / 60000,
      nextHeartbeat: this.intervalId ? new Date(Date.now() + this.heartbeatInterval) : null
    };
  }
}

// Create a singleton instance
const heartbeatService = new HeartbeatService();

export default heartbeatService;
