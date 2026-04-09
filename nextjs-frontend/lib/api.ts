const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

// Client-side API helper
export async function clientApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || error.detail || 'API request failed');
  }
  
  return res.json();
}

export async function clientApiForm<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${endpoint}`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || error.detail || 'API request failed');
  }
  
  return res.json();
}

export function getWebSocketUrl(path: string): string {
  const wsBase = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
  return `${wsBase}${path}`;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`, { cache: 'no-store' });
    return res.ok;
  } catch {
    return false;
  }
}
