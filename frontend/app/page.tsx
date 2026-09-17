'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const POPULAR_CITIES = ['Hyderabad', 'Vijayawada', 'Bangalore', 'Chennai'];

export default function Home() {
  const router = useRouter();
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

  const [fromCity, setFromCity] = useState('Hyderabad');
  const [toCity, setToCity] = useState('Vijayawada');
  const [journeyDate, setJourneyDate] = useState(tomorrow);
  const [passengers, setPassengers] = useState(1);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fromCity || !toCity) return;
    router.push(
      `/search?from=${encodeURIComponent(fromCity)}&to=${encodeURIComponent(
        toCity
      )}&journey_date=${journeyDate}&passengers=${passengers}`
    );
  };

  const handleSwap = () => {
    const temp = fromCity;
    setFromCity(toCity);
    setToCity(temp);
  };

  const quickRoutes = [
    { from: 'Hyderabad', to: 'Vijayawada', time: '5.5h', price: '₹599' },
    { from: 'Hyderabad', to: 'Bangalore', time: '9h', price: '₹899' },
    { from: 'Bangalore', to: 'Chennai', time: '6h', price: '₹649' },
    { from: 'Vijayawada', to: 'Hyderabad', time: '5.5h', price: '₹549' },
  ];

  return (
    <div className="flex flex-col flex-1">
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-blue-700 via-blue-800 to-indigo-900 text-white py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/30 text-blue-100 text-xs font-semibold backdrop-blur border border-blue-400/30">
            <span>✨</span> Next-Gen Bus Booking & AI Integration Platform
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Travel Comfortably with <span className="text-blue-300">Snehith Travels</span>
          </h1>
          <p className="text-sm sm:text-base text-blue-100 max-w-2xl mx-auto">
            Book premium AC Sleepers, Semi-sleepers, and Seaters across Andhra Pradesh, Telangana, Karnataka & Tamil Nadu.
          </p>

          {/* Search Card */}
          <div className="bg-white text-zinc-900 rounded-3xl p-6 sm:p-8 shadow-2xl mt-8 text-left border border-zinc-100">
            <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
              {/* From */}
              <div className="md:col-span-3">
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5">
                  From (Origin)
                </label>
                <select
                  value={fromCity}
                  onChange={(e) => setFromCity(e.target.value)}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-3 text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-blue-600"
                >
                  {POPULAR_CITIES.map((c) => (
                    <option key={c} value={c} disabled={c === toCity}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Swap button */}
              <div className="hidden md:flex md:col-span-1 items-center justify-center pb-2">
                <button
                  type="button"
                  onClick={handleSwap}
                  className="p-2 rounded-full border border-zinc-200 bg-zinc-100 hover:bg-zinc-200 text-zinc-600 transition"
                  title="Swap Origin and Destination"
                >
                  ⇄
                </button>
              </div>

              {/* To */}
              <div className="md:col-span-3">
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5">
                  To (Destination)
                </label>
                <select
                  value={toCity}
                  onChange={(e) => setToCity(e.target.value)}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-3 text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-blue-600"
                >
                  {POPULAR_CITIES.map((c) => (
                    <option key={c} value={c} disabled={c === fromCity}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Journey Date */}
              <div className="md:col-span-3">
                <label className="block text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5">
                  Journey Date
                </label>
                <input
                  type="date"
                  value={journeyDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setJourneyDate(e.target.value)}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-3 text-sm font-semibold focus:outline-hidden focus:ring-2 focus:ring-blue-600"
                />
              </div>

              {/* Passengers & Submit */}
              <div className="md:col-span-2 flex flex-col gap-2">
                <button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-md transition flex items-center justify-center gap-1.5 text-sm"
                >
                  Search Buses
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Quick Routes Section */}
      <section className="max-w-6xl mx-auto px-4 py-12 w-full">
        <h2 className="text-xl font-bold text-zinc-900 mb-6">Popular Demo Routes</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickRoutes.map((r, i) => (
            <button
              key={i}
              onClick={() => {
                setFromCity(r.from);
                setToCity(r.to);
                router.push(
                  `/search?from=${encodeURIComponent(r.from)}&to=${encodeURIComponent(
                    r.to
                  )}&journey_date=${journeyDate}&passengers=1`
                );
              }}
              className="text-left p-5 rounded-2xl bg-white border border-zinc-200 hover:border-blue-500 hover:shadow-md transition group"
            >
              <div className="flex items-center justify-between text-xs text-zinc-400 font-semibold mb-2">
                <span>Direct Route</span>
                <span>{r.time}</span>
              </div>
              <div className="font-bold text-zinc-900 text-base group-hover:text-blue-600 transition flex items-center gap-1.5">
                {r.from} <span className="text-zinc-400">→</span> {r.to}
              </div>
              <div className="mt-3 text-xs text-zinc-500 flex items-center justify-between">
                <span>Starting from</span>
                <span className="font-extrabold text-blue-600 text-sm">{r.price}</span>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Feature Highlights Section */}
      <section className="bg-zinc-100/60 border-t border-zinc-200 py-12 px-4">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 bg-white rounded-2xl border border-zinc-200">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-lg mb-3">
              🤖
            </div>
            <h3 className="font-bold text-zinc-900 text-base">Saarthi AI Ready</h3>
            <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
              Every backend API endpoint is designed to be cleanly invoked as deterministic tools by the upcoming Saarthi AI voice travel agent.
            </p>
          </div>

          <div className="p-6 bg-white rounded-2xl border border-zinc-200">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-lg mb-3">
              ⏱️
            </div>
            <h3 className="font-bold text-zinc-900 text-base">Instant Seat Holds</h3>
            <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
              Transactional concurrency protection with 10-minute temporary seat holding prevents race conditions and double bookings.
            </p>
          </div>

          <div className="p-6 bg-white rounded-2xl border border-zinc-200">
            <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-lg mb-3">
              🎟️
            </div>
            <h3 className="font-bold text-zinc-900 text-base">Digital QR Ticket</h3>
            <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
              Automatic generation of digital bus tickets with safe verification QR codes and detailed passenger and boarding point data.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
