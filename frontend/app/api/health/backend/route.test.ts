import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { GET } from './route';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Frontend Backend Health Probe', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('reports ok when the configured backend health endpoint responds', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
    });

    const response = await GET();
    const payload = await response.json();

    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/health', {
      cache: 'no-store',
    });
    expect(response.status).toBe(200);
    expect(payload.status).toBe('ok');
  });

  it('reports failure when the configured backend health endpoint is unreachable', async () => {
    mockFetch.mockRejectedValueOnce(new Error('unreachable'));

    const response = await GET();
    const payload = await response.json();

    expect(response.status).toBe(503);
    expect(payload.status).toBe('failed');
  });
});
