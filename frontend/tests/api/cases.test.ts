/**
 * Tests for the cases API client.
 * 
 * Verifies type-safe API integration with backend endpoints.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { casesApi, ApiError } from '../../shared/api/cases';
import type { CaseCreateResponse, CaseDetail } from '../../shared/types/cases';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Cases API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  describe('createCase', () => {
    it('successfully creates a case', async () => {
      const mockResponse: CaseCreateResponse = {
        transpositionCaseId: 'case-123',
        status: 'new',
        caseSummary: {
          id: 'case-123',
          status: 'new',
          instrumentIdentity: 'trumpet-bb',
          scoreCount: 0,
          createdAt: '2024-01-15T10:00:00Z',
          updatedAt: '2024-01-15T10:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await casesApi.createCase({
        instrument_identity: 'trumpet-bb',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/cases',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ instrument_identity: 'trumpet-bb' }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('throws ApiError on validation failure (422)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ detail: 'instrument_identity is required' }),
      });

      const request = casesApi.createCase({ instrument_identity: '' });

      await expect(request).rejects.toThrow(ApiError);
      await expect(request).rejects.toMatchObject({
        status: 422,
        message: 'instrument_identity is required',
      });
    });

    it('throws ApiError on server error (500)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      await expect(
        casesApi.createCase({ instrument_identity: 'trumpet' })
      ).rejects.toMatchObject({
        status: 500,
        message: 'Internal server error',
      });
    });
  });

  describe('getCase', () => {
    it('successfully retrieves a case', async () => {
      const mockResponse: CaseDetail = {
        id: 'case-123',
        status: 'ready_for_upload',
        instrumentIdentity: 'trumpet-bb',
        scoreCount: 2,
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-15T12:00:00Z',
        constraints: {
          highest_playable_tone: 'C6',
          lowest_playable_tone: 'F#3',
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: null,
          comfort_range_max: null,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await casesApi.getCase('case-123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/cases/case-123',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
      expect(result.constraints.highest_playable_tone).toBe('C6');
    });

    it('throws ApiError on not found (404)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Case with id not-found not found' }),
      });

      await expect(casesApi.getCase('not-found')).rejects.toMatchObject({
        status: 404,
        message: 'Case with id not-found not found',
      });
    });
  });

  describe('listCases', () => {
    it('successfully lists all cases', async () => {
      const mockResponse = [
        {
          id: 'case-1',
          status: 'new',
          instrumentIdentity: 'trumpet-bb',
          scoreCount: 0,
          createdAt: '2024-01-15T10:00:00Z',
          updatedAt: '2024-01-15T10:00:00Z',
        },
        {
          id: 'case-2',
          status: 'ready_for_upload',
          instrumentIdentity: 'flute',
          scoreCount: 3,
          createdAt: '2024-01-14T09:00:00Z',
          updatedAt: '2024-01-14T15:00:00Z',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await casesApi.listCases();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/cases',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        })
      );
      expect(result).toHaveLength(2);
      expect(result[0].instrumentIdentity).toBe('trumpet-bb');
    });

    it('returns empty array when no cases exist', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      const result = await casesApi.listCases();

      expect(result).toEqual([]);
    });

    it('throws ApiError with a stable message when the backend cannot be reached', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      await expect(casesApi.listCases()).rejects.toMatchObject({
        status: 0,
        message: 'Could not reach the backend service. Please make sure the backend is running and try again.',
      });
    });
  });

  describe('deleteCase', () => {
    it('successfully deletes a case through the provisional cleanup route', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => undefined,
      });

      await expect(casesApi.deleteCase('case-123')).resolves.toBeUndefined();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/cases/case-123',
        expect.objectContaining({
          method: 'DELETE',
          headers: {
            'Accept': 'application/json',
          },
        })
      );
    });

    it('throws ApiError when deleting an unknown case', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Case with id missing-case not found.' }),
      });

      await expect(casesApi.deleteCase('missing-case')).rejects.toMatchObject({
        status: 404,
        message: 'Case with id missing-case not found.',
      });
    });
  });

  describe('updateCase', () => {
    it('updates an existing case through the patch endpoint', async () => {
      const mockResponse: CaseDetail = {
        id: 'case-123',
        status: 'ready_for_upload',
        instrumentIdentity: 'flute',
        scoreCount: 0,
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-15T12:00:00Z',
        latestScoreDocumentId: null,
        constraints: {
          highest_playable_tone: null,
          lowest_playable_tone: null,
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: 'A3',
          comfort_range_max: 'E5',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await casesApi.updateCase('case-123', {
        instrumentIdentity: 'flute',
        constraints: {
          highest_playable_tone: null,
          lowest_playable_tone: null,
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: 'A3',
          comfort_range_max: 'E5',
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/cases/case-123',
        expect.objectContaining({
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('resetCase', () => {
    it('resets an existing case through the explicit reset endpoint', async () => {
      const mockResponse: CaseDetail = {
        id: 'case-123',
        status: 'new',
        instrumentIdentity: 'trumpet-bb',
        scoreCount: 0,
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-15T12:00:00Z',
        latestScoreDocumentId: null,
        constraints: {
          highest_playable_tone: null,
          lowest_playable_tone: null,
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: null,
          comfort_range_max: null,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await casesApi.resetCase('case-123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/cases/case-123/reset',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Accept': 'application/json',
          },
        })
      );
      expect(result.status).toBe('new');
    });
  });

  describe('ApiError', () => {
    it('creates error with status and message', () => {
      const error = new ApiError('Test error', 400, 'VALIDATION_ERROR');
      
      expect(error.name).toBe('ApiError');
      expect(error.message).toBe('Test error');
      expect(error.status).toBe(400);
      expect(error.code).toBe('VALIDATION_ERROR');
    });

    it('works without error code', () => {
      const error = new ApiError('Simple error', 500);
      
      expect(error.status).toBe(500);
      expect(error.code).toBeUndefined();
    });
  });
});
