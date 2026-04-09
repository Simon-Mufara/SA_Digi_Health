import { cookies } from 'next/headers';
import { jwtVerify } from 'jose';

const JWT_PUBLIC_KEY = process.env.YARA_JWT_PUBLIC_KEY || '';
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8010';

export type UserRole = 'doctor' | 'clinician' | 'admin' | 'security_officer' | 'researcher';

export interface AuthUser {
  staffId: string;
  role: UserRole;
  exp: number;
}

export async function getAuthFromCookie(): Promise<AuthUser | null> {
  const cookieStore = cookies();
  const token = cookieStore.get('access_token')?.value;
  
  if (!token) return null;
  
  try {
    // For HS256, use the secret directly
    const secret = new TextEncoder().encode(process.env.JWT_SECRET || 'replace-with-strong-secret');
    const { payload } = await jwtVerify(token, secret, {
      algorithms: ['HS256'],
    });
    
    return {
      staffId: payload.sub as string,
      role: payload.role as UserRole,
      exp: payload.exp as number,
    };
  } catch (e) {
    console.error('JWT verification failed:', e);
    return null;
  }
}

export async function verifyRole(allowedRoles: UserRole[]): Promise<AuthUser | null> {
  const user = await getAuthFromCookie();
  if (!user) return null;
  if (!allowedRoles.includes(user.role)) return null;
  return user;
}

export function getRoleColor(role: UserRole): string {
  const colors: Record<UserRole, string> = {
    doctor: '#8b5cf6',
    clinician: '#06b6d4',
    admin: '#f59e0b',
    security_officer: '#ef4444',
    researcher: '#10b981',
  };
  return colors[role] || '#6b7280';
}

export function getRoleLabel(role: UserRole): string {
  const labels: Record<UserRole, string> = {
    doctor: 'Doctor',
    clinician: 'Clinician',
    admin: 'Admin',
    security_officer: 'Security',
    researcher: 'Researcher',
  };
  return labels[role] || role;
}

export function getRolePath(role: UserRole): string {
  const paths: Record<UserRole, string> = {
    doctor: '/dashboard/doctor',
    clinician: '/dashboard/clinician',
    admin: '/dashboard/admin',
    security_officer: '/dashboard/security',
    researcher: '/dashboard/research',
  };
  return paths[role] || '/login';
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const cookieStore = cookies();
  const token = cookieStore.get('access_token')?.value;
  
  const res = await fetch(`${API_URL}/api/v1${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    cache: 'no-store',
  });
  
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || error.detail || 'API request failed');
  }
  
  return res.json();
}
