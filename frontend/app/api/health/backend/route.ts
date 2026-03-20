import { NextResponse } from 'next/server';

const API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      cache: 'no-store',
    });

    if (!response.ok) {
      return NextResponse.json(
        {
          status: 'failed',
          apiBaseUrl: API_BASE_URL,
          safeSummary: 'The frontend could not validate the configured API health endpoint.',
        },
        { status: 503 },
      );
    }

    return NextResponse.json({
      status: 'ok',
      apiBaseUrl: API_BASE_URL,
      safeSummary: 'The frontend can reach the configured API health endpoint.',
    });
  } catch {
    return NextResponse.json(
      {
        status: 'failed',
        apiBaseUrl: API_BASE_URL,
        safeSummary: 'The frontend could not reach the configured API health endpoint.',
      },
      { status: 503 },
    );
  }
}
