'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { getStoredUser, removeAuthToken } from '@/lib/api';
import { User } from '@/types';
import VoiceBotModal from '@/components/VoiceBotModal';

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const [showVoiceModal, setShowVoiceModal] = useState(false);

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
    <>
      {/* AWS Hackathon Top Announcement Bar */}
      <div className="w-full bg-gradient-to-r from-amber-600 via-indigo-700 to-purple-800 text-white text-[11px] sm:text-xs py-1.5 px-4 font-semibold text-center flex flex-wrap items-center justify-center gap-2 shadow-xs">
        <span className="bg-amber-400 text-zinc-950 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider">
          🏆 AWS Hackathon Featured Project
        </span>
        <span className="hidden sm:inline">
          Meet <strong>Saarthi AI</strong>: Autonomous voice travel agent powered by <strong>Amazon Bedrock</strong>.
        </span>
        <button
          type="button"
          onClick={() => setShowVoiceModal(true)}
          className="inline-flex items-center gap-1 underline text-amber-200 hover:text-white font-bold transition cursor-pointer ml-1"
        >
          <span>📞 Call &amp; Test Live Phone Bot</span>
          <span>→</span>
        </button>
      </div>

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
              <span className="hidden md:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
                ⚡ AWS Hackathon
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-2 sm:gap-3 shrink-0">
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

            {/* Saarthi AI - AWS Hackathon Highlighted Button */}
            <button
              type="button"
              onClick={() => setShowVoiceModal(true)}
              className="relative flex items-center gap-2 px-3 sm:px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 via-indigo-600 to-purple-700 text-white text-xs sm:text-sm font-black hover:from-amber-600 hover:to-purple-800 shadow-md transition transform hover:scale-[1.03] active:scale-[0.98] ring-2 ring-amber-400/80 cursor-pointer"
              title="AWS Hackathon Project: Call Saarthi AI Voice Bot"
            >
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-80"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
              </span>
              <span className="flex items-center gap-1.5">
                <span>🎙️ Saarthi AI</span>
                <span className="hidden lg:inline-block px-1.5 py-0.2 rounded bg-amber-400/25 text-amber-200 text-[10px] font-black uppercase tracking-wider border border-amber-300/30">
                  AWS Agent
                </span>
              </span>
            </button>

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

      {/* Voice Bot Instructions Modal */}
      <VoiceBotModal
        isOpen={showVoiceModal}
        onClose={() => setShowVoiceModal(false)}
      />
    </>
  );
}
