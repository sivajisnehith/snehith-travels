'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getStoredUser, removeAuthToken } from '@/lib/api';
import { User } from '@/types';

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
    const handleStorage = () => setUser(getStoredUser());
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const handleLogout = () => {
    removeAuthToken();
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-200 bg-white/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 sm:gap-2.5 shrink-0">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-lg sm:text-xl shadow-sm">
            ST
          </div>
          <div>
            <span className="text-base sm:text-xl font-extrabold tracking-tight text-zinc-900">Snehith</span>{' '}
            <span className="text-base sm:text-xl font-bold text-blue-600">Travels</span>
            <span className="hidden md:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              Demo Platform
            </span>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-2 sm:gap-5 shrink-0">
          <Link
            href="/"
            className="hidden md:inline-block text-xs sm:text-sm font-medium text-zinc-600 hover:text-blue-600 transition-colors"
          >
            Search Buses
          </Link>
          <Link
            href="/dashboard"
            className="hidden sm:inline-block text-xs sm:text-sm font-medium text-zinc-600 hover:text-blue-600 transition-colors"
          >
            My Bookings
          </Link>

          {user?.role === 'admin' && (
            <Link
              href="/admin"
              className="text-xs font-bold px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-lg bg-purple-100 text-purple-800 hover:bg-purple-200 border border-purple-300 transition flex items-center gap-1 sm:gap-1.5 shadow-xs"
            >
              <span>⚙️</span> Fleet Manager
            </Link>
          )}

          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden md:flex flex-col text-right">
                <span className="text-xs font-semibold text-zinc-900">{user.name}</span>
                <span className="text-[10px] text-zinc-500">{user.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="text-xs font-medium px-3 py-1.5 rounded-lg border border-zinc-300 text-zinc-700 hover:bg-zinc-100 transition"
              >
                Sign out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="text-sm font-medium px-3 py-1.5 rounded-lg text-zinc-700 hover:bg-zinc-100 transition"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="text-sm font-medium px-3.5 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition"
              >
                Register
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
