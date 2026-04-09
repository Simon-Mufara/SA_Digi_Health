import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

type UserRole = 'doctor' | 'clinician' | 'admin' | 'security_officer' | 'researcher';

const rolePathMap: Record<UserRole, string> = {
  doctor: '/dashboard/doctor',
  clinician: '/dashboard/clinician',
  admin: '/dashboard/admin',
  security_officer: '/dashboard/security',
  researcher: '/dashboard/research',
};

const pathRoleMap: Record<string, UserRole> = {
  '/dashboard/doctor': 'doctor',
  '/dashboard/clinician': 'clinician',
  '/dashboard/admin': 'admin',
  '/dashboard/security': 'security_officer',
  '/dashboard/research': 'researcher',
};

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Only protect dashboard routes
  if (!pathname.startsWith('/dashboard')) {
    return NextResponse.next();
  }
  
  const token = request.cookies.get('access_token')?.value;
  
  // No token - redirect to login
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  try {
    // Verify JWT (using HS256 for now)
    const secret = new TextEncoder().encode(process.env.JWT_SECRET || 'replace-with-strong-secret');
    const { payload } = await jwtVerify(token, secret, {
      algorithms: ['HS256'],
    });
    
    const userRole = payload.role as UserRole;
    
    // Check if user is accessing correct role path
    const expectedPath = rolePathMap[userRole];
    
    // If at /dashboard root, redirect to their role dashboard
    if (pathname === '/dashboard' || pathname === '/dashboard/') {
      return NextResponse.redirect(new URL(expectedPath, request.url));
    }
    
    // Find which role path they're trying to access
    const attemptedRole = Object.entries(pathRoleMap).find(([path]) => 
      pathname.startsWith(path)
    )?.[1];
    
    // If trying to access wrong role's path, redirect to their own
    if (attemptedRole && attemptedRole !== userRole) {
      return NextResponse.redirect(new URL(expectedPath, request.url));
    }
    
    // Add user info to headers for server components
    const response = NextResponse.next();
    response.headers.set('x-staff-id', payload.sub as string);
    response.headers.set('x-staff-role', userRole);
    
    return response;
  } catch (error) {
    // Invalid token - redirect to login
    console.error('Token verification failed:', error);
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
