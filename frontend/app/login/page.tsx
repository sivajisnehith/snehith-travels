'use client';

import React, { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-zinc-500">Loading sign in...</div>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get('redirect') || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login({ email, password });
      window.location.href = redirectUrl;
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoCustomer = () => {
    setEmail('demo@snehithtravels.com');
    setPassword('DemoPassword123!');
  };

  const fillDemoAdmin = () => {
    setEmail('admin@snehithtravels.com');
    setPassword('AdminPassword123!');
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16 w-full flex-1 flex flex-col justify-center">
      <div className="bg-white rounded-3xl border border-zinc-200 p-8 shadow-xl">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center font-bold text-2xl mx-auto shadow-md mb-3">
            ST
          </div>
          <h1 className="text-2xl font-black text-zinc-900">Sign in to Snehith Travels</h1>
          <p className="text-xs text-zinc-500 mt-1">
            Access your bus bookings, ticket QR codes, and profile
          </p>
        </div>

        {/* Demo Fast Logins */}
        <div className="mb-6 p-4 rounded-2xl bg-zinc-50 border border-zinc-200/80">
          <span className="block text-[11px] font-bold text-zinc-600 uppercase tracking-wider mb-2">
            Hackathon Demo Quick Fill:
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={fillDemoCustomer}
              className="flex-1 text-xs font-semibold py-2 px-2.5 rounded-lg border border-zinc-300 bg-white hover:bg-zinc-100 text-zinc-700 transition"
            >
              Demo Customer
            </button>
            <button
              type="button"
              onClick={fillDemoAdmin}
              className="flex-1 text-xs font-semibold py-2 px-2.5 rounded-lg border border-zinc-300 bg-white hover:bg-zinc-100 text-zinc-700 transition"
            >
              Demo Admin
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200 font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-zinc-700 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-zinc-200 bg-zinc-50 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-zinc-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-zinc-200 bg-zinc-50 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-zinc-500 mt-6">
          Don't have an account?{' '}
          <Link href="/register" className="font-bold text-blue-600 hover:underline">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}
