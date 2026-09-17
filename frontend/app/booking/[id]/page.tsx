'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { DigitalTicket } from '@/types';

export default function TicketConfirmationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = React.use(params);
  const bookingRef = resolvedParams.id;

  const [ticket, setTicket] = useState<DigitalTicket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTicket();
  }, [bookingRef]);

  const loadTicket = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTicket(bookingRef);
      setTicket(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load ticket.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center text-sm text-zinc-500">
        Generating your verified digital ticket...
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <div className="p-4 rounded-2xl bg-red-50 text-red-700 text-sm border border-red-200">
          {error || 'Ticket could not be found.'}
        </div>
        <Link href="/" className="text-xs font-bold text-blue-600 hover:underline">
          Return to search
        </Link>
      </div>
    );
  }

  const isConfirmed = ticket.status === 'CONFIRMED';

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10 w-full flex-1">
      {/* Top Banner */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <span
            className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
              isConfirmed
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-amber-100 text-amber-800'
            }`}
          >
            {isConfirmed ? '✓ Booking Confirmed' : `Status: ${ticket.status}`}
          </span>
          <h1 className="text-2xl font-black text-zinc-900 mt-1">E-Ticket & Boarding Pass</h1>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={handlePrint}
            className="px-4 py-2 rounded-xl border border-zinc-300 bg-white hover:bg-zinc-50 text-xs font-bold text-zinc-700 transition"
          >
            🖨️ Print Ticket
          </button>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-bold text-white transition"
          >
            My Trips
          </Link>
        </div>
      </div>

      {/* Ticket Card */}
      <div className="bg-white rounded-3xl border border-zinc-200 shadow-xl overflow-hidden print:border-none print:shadow-none">
        {/* Ticket Header */}
        <div className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white p-6 sm:p-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs font-bold tracking-widest text-blue-200 uppercase">
              Snehith Travels Boarding Pass
            </div>
            <div className="text-2xl font-black mt-1">{ticket.bus_name}</div>
            <div className="text-xs text-blue-100 mt-0.5">
              {ticket.bus_type} • Operator: {ticket.operator}
            </div>
          </div>

          <div className="text-left sm:text-right bg-white/10 backdrop-blur px-4 py-2.5 rounded-2xl border border-white/20">
            <span className="text-[10px] uppercase font-bold text-blue-200 block">
              Booking Reference
            </span>
            <span className="font-mono text-xl font-black tracking-wider text-white">
              {ticket.booking_reference}
            </span>
          </div>
        </div>

        {/* Journey Details Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 p-6 sm:p-8 border-b border-zinc-100 bg-zinc-50/50">
          <div>
            <span className="text-[10px] uppercase font-bold text-zinc-400">Departure</span>
            <div className="text-lg font-black text-zinc-900 mt-0.5">{ticket.departure_time}</div>
            <div className="text-xs font-bold text-zinc-700">{ticket.origin}</div>
            <div className="text-[11px] text-zinc-500 mt-1">Boarding: {ticket.boarding_point}</div>
          </div>

          <div className="text-center flex flex-col items-center justify-center">
            <span className="text-[10px] uppercase font-mono text-zinc-400">{ticket.duration}</span>
            <div className="w-full h-0.5 bg-zinc-300 relative my-2">
              <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-blue-600"></div>
            </div>
            <span className="text-xs font-semibold text-zinc-600">{ticket.journey_date}</span>
          </div>

          <div className="sm:text-right">
            <span className="text-[10px] uppercase font-bold text-zinc-400">Arrival</span>
            <div className="text-lg font-black text-zinc-900 mt-0.5">{ticket.arrival_time}</div>
            <div className="text-xs font-bold text-zinc-700">{ticket.destination}</div>
            <div className="text-[11px] text-zinc-500 mt-1">Dropping: {ticket.dropping_point}</div>
          </div>
        </div>

        {/* Passenger & QR Code Section */}
        <div className="p-6 sm:p-8 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {/* Passenger List */}
          <div className="md:col-span-2 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400">
              Passenger(s) Details
            </h3>

            <div className="space-y-2">
              {ticket.passengers.map((p, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-zinc-200 bg-white shadow-xs"
                >
                  <div>
                    <div className="text-sm font-bold text-zinc-900">{p.name}</div>
                    <div className="text-xs text-zinc-500">
                      Age: {p.age} • Gender: {p.gender}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-zinc-400 block">Seat</span>
                    <span className="font-mono text-base font-black text-blue-600">
                      {p.seat_number}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-between items-center text-xs">
              <span className="text-zinc-500">Total Paid (Mock Gateway)</span>
              <span className="text-lg font-black text-zinc-900">₹{ticket.total_amount}</span>
            </div>
          </div>

          {/* Dynamic QR Code */}
          <div className="flex flex-col items-center justify-center p-4 bg-zinc-50 rounded-2xl border border-zinc-200 text-center">
            {ticket.qr_code && (
              <img
                src={ticket.qr_code}
                alt="Ticket QR Code"
                className="w-36 h-36 rounded-xl border border-zinc-300 shadow-xs bg-white p-1"
              />
            )}
            <span className="text-[10px] font-mono text-zinc-500 mt-2">
              Scan for safe booking verification
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
