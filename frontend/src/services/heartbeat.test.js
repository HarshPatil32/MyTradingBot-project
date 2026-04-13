import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';

vi.mock('axios');

// Re-import a fresh instance of the service for each test
async function freshService() {
  vi.resetModules();
  const mod = await import('./heartbeat.js');
  return mod.default;
}

describe('HeartbeatService', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    axios.get.mockResolvedValue({ status: 200, data: { timestamp: '2026-04-12T00:00:00' } });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('has a 4-minute interval', async () => {
    const service = await freshService();
    expect(service.heartbeatInterval).toBe(4 * 60 * 1000);
  });

  it('calls GET /heartbeat with the correct URL', async () => {
    const service = await freshService();
    service.setApiUrl('https://api.example.com');

    await service.sendHeartbeat();

    expect(axios.get).toHaveBeenCalledOnce();
    expect(axios.get).toHaveBeenCalledWith(
      'https://api.example.com/heartbeat',
      expect.objectContaining({ timeout: 10000 })
    );
  });

  it('sends an immediate heartbeat when started', async () => {
    const service = await freshService();
    service.setApiUrl('https://api.example.com');

    service.start();
    await Promise.resolve(); // flush the async sendHeartbeat call

    expect(axios.get).toHaveBeenCalledOnce();
  });

  it('sends heartbeats repeatedly at the 4-minute interval', async () => {
    const service = await freshService();
    service.setApiUrl('https://api.example.com');

    service.start();
    await Promise.resolve(); // flush the immediate call

    // Advance by one interval -> should trigger one more call
    await vi.advanceTimersByTimeAsync(4 * 60 * 1000);
    expect(axios.get).toHaveBeenCalledTimes(2);

    // Advance by another interval -> one more call
    await vi.advanceTimersByTimeAsync(4 * 60 * 1000);
    expect(axios.get).toHaveBeenCalledTimes(3);

    service.stop();
  });

  it('stops calling GET /heartbeat after stop()', async () => {
    const service = await freshService();
    service.setApiUrl('https://api.example.com');

    service.start();
    await Promise.resolve(); // flush the immediate call

    service.stop();
    await vi.advanceTimersByTimeAsync(4 * 60 * 1000);

    // Only the single initial call; no interval calls after stop
    expect(axios.get).toHaveBeenCalledTimes(1);
  });

  it('skips the request when no API URL is set', async () => {
    const service = await freshService();

    const result = await service.sendHeartbeat();

    expect(result).toBe(false);
    expect(axios.get).not.toHaveBeenCalled();
  });
});
