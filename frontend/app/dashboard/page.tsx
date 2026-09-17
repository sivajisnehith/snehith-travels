'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, getAuthToken, getStoredUser } from '@/lib/api';
import { BookingDetail, User } from '@/types';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [adminViewAll, setAdminViewAll] = useState(false);

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      router.push('/login?redirect=/dashboard');
      return;
    }
    const currentUser = getStoredUser();
    setUser(currentUser);
    loadBookings(false);
  }, []);

  const loadBookings = async (viewAll: boolean = adminViewAll) => {
    setLoading(true);
    setError(null);
    try {
      const data = viewAll ? await api.getAllBookingsAdmin() : await api.getBookings();
      setBookings(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch bookings.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (bookingId: number) => {
    if (!confirm('Are you sure you want to cancel this booking? This will release your seats.')) {
      return;
    }
    try {
      await api.cancelBooking(bookingId);
      loadBookings(adminViewAll);
    } catch (err: any) {
      alert(err.message || 'Could not cancel booking.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 mb-8 border-b border-zinc-200">
        <div>
          <h1 className="text-2xl font-black text-zinc-900">Passenger Dashboard</h1>
          <p className="text-xs text-zinc-500 mt-1">
            Welcome back, <span className="font-bold text-zinc-800">{user?.name || 'Traveler'}</span> ({user?.email})
          </p>
        </div>

        <Link
          href="/"
          className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition"
        >
          + Book New Journey
        </Link>
      </div>

      {user?.role === 'admin' && (
        <div className="mb-6 p-4 rounded-2xl bg-purple-50 border border-purple-200 flex flex-wrap items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚡</span>
            <div>
              <h4 className="text-xs font-bold text-purple-900">Administrator Access Enabled</h4>
              <p className="text-[11px] text-purple-700">You have full fleet permissions to deploy new buses, set timings, and manage routes.</p>
            </div>
          </div>
          <Link
            href="/admin"
            className="px-4 py-2 rounded-xl bg-purple-700 hover:bg-purple-800 text-white font-bold text-xs shadow-xs transition"
          >
            Open Fleet Manager & Deploy Buses →
          </Link>
        </div>
      )}

      {user?.role === 'admin' && (
        <div className="flex items-center gap-3 mb-6">
          <button
            type="button"
            onClick={() => {
              setAdminViewAll(false);
              loadBookings(false);
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
              !adminViewAll
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-white text-zinc-600 border border-zinc-200 hover:bg-zinc-50'
            }`}
          >
            👤 My Personal Bookings
          </button>
          <button
            type="button"
            onClick={() => {
              setAdminViewAll(true);
              loadBookings(true);
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
              adminViewAll
                ? 'bg-purple-700 text-white shadow-xs'
                : 'bg-white text-purple-700 border border-purple-200 hover:bg-purple-50'
            }`}
          >
            <span>👑</span> All Platform Bookings ({bookings.length})
          </button>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200 font-medium">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-16 text-center text-sm text-zinc-500">Loading your travel history...</div>
      ) : bookings.length === 0 ? (
        <div className="bg-white rounded-3xl border border-zinc-200 p-12 text-center space-y-4 shadow-xs">
          <div className="text-4xl">🎫</div>
          <h2 className="text-lg font-bold text-zinc-900">No bookings yet</h2>
          <p className="text-xs text-zinc-500 max-w-sm mx-auto">
            You haven't made any bus reservations yet. Search our routes and experience seamless travel!
          </p>
          <Link
            href="/"
            className="inline-block px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition"
          >
            Find Buses
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((b) => {
            const isConfirmed = b.status === 'CONFIRMED';
            const isPending = b.status === 'PENDING_PAYMENT';
            const isCancelled = b.status === 'CANCELLED';

            return (
              <div
                key={b.id}
                className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs hover:shadow-md transition"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-100">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-black text-zinc-900">
                        {b.booking_reference}
                      </span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          isConfirmed
                            ? 'bg-emerald-100 text-emerald-800'
                            : isPending
                            ? 'bg-amber-100 text-amber-800'
                            : isCancelled
                            ? 'bg-red-100 text-red-800'
                            : 'bg-zinc-100 text-zinc-800'
                        }`}
                      >
                        {b.status}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-500 mt-1 font-medium">
                      {b.bus_name} • {b.bus_type}
                    </div>
                  </div>

                  <div className="text-left sm:text-right">
                    <span className="text-xs text-zinc-400">Total Amount</span>
                    <div className="text-xl font-black text-zinc-900">₹{b.total_amount}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-4 text-xs">
                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase font-bold">Route & Date</span>
                    <div className="font-bold text-zinc-800 text-sm mt-0.5">
                      {b.origin} → {b.destination}
                    </div>
                    <div className="text-zinc-500 mt-0.5">
                      Date: {b.journey_date} ({b.departure_time})
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase font-bold">Seats & Boarding</span>
                    <div className="font-bold text-blue-600 text-sm mt-0.5">
                      Seats: {b.seat_numbers.join(', ')}
                    </div>
                    <div className="text-zinc-500 mt-0.5 truncate">
                      Boarding: {b.boarding_point}
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] text-zinc-400 uppercase font-bold">Passengers</span>
                    <div className="font-medium text-zinc-800 mt-0.5">
                      {b.passengers.map((p) => p.name).join(', ')}
                    </div>
                  </div>
                </div>

                {/* Actions Bar */}
                <div className="pt-3 border-t border-zinc-100 flex flex-wrap items-center justify-between gap-3">
                  <div className="text-[11px] text-zinc-400">
                    Booked on {new Date(b.created_at).toLocaleDateString()}
                  </div>

                  <div className="flex gap-2">
                    {isPending && (
                      <Link
                        href={`/payment?booking_id=${b.id}`}
                        className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs transition"
                      >
                        Complete Payment
                      </Link>
                    )}

                    {isConfirmed && (
                      <Link
                        href={`/booking/${b.booking_reference}`}
                        className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition"
                      >
                        View E-Ticket & QR
                      </Link>
                    )}

                    {!isCancelled && (
                      <button
                        type="button"
                        onClick={() => handleCancel(b.id)}
                        className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition"
                      >
                        Cancel Booking
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
