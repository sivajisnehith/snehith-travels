'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Bus } from '@/types';

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-zinc-500">Loading search results...</div>}>
      <SearchResultsContent />
    </Suspense>
  );
}

function SearchResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const fromCity = searchParams.get('from') || 'Hyderabad';
  const toCity = searchParams.get('to') || 'Vijayawada';
  const journeyDate = searchParams.get('journey_date') || new Date().toISOString().split('T')[0];
  const passengers = parseInt(searchParams.get('passengers') || '1', 10);

  const [buses, setBuses] = useState<Bus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [acFilter, setAcFilter] = useState<'all' | 'ac' | 'non-ac'>('all');
  const [typeFilter, setTypeFilter] = useState<'all' | 'sleeper' | 'seater'>('all');
  const [timeFilter, setTimeFilter] = useState<'all' | 'morning' | 'afternoon' | 'evening' | 'night'>('all');
  const [sortBy, setSortBy] = useState<'cheapest' | 'earliest_departure' | 'shortest_journey'>('cheapest');

  useEffect(() => {
    fetchBuses();
  }, [fromCity, toCity, journeyDate, passengers, acFilter, typeFilter, timeFilter, sortBy]);

  const fetchBuses = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.searchBuses({
        from: fromCity,
        to: toCity,
        journey_date: journeyDate,
        passengers,
        is_ac: acFilter === 'all' ? undefined : acFilter === 'ac',
        seat_type: typeFilter === 'all' ? undefined : typeFilter,
        departure_time: timeFilter === 'all' ? undefined : timeFilter,
        sort_by: sortBy,
      });
      setBuses(res);
    } catch (err: any) {
      setError(err.message || 'Error fetching available buses.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
      {/* Route Header Banner */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 mb-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-zinc-900">
              {fromCity} <span className="text-zinc-400 font-normal">to</span> {toCity}
            </h1>
            <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
              {buses.length} {buses.length === 1 ? 'Bus' : 'Buses'} Available
            </span>
          </div>
          <p className="text-xs text-zinc-500 mt-1">
            Journey Date: <span className="font-semibold text-zinc-700">{journeyDate}</span> • {passengers}{' '}
            {passengers === 1 ? 'Passenger' : 'Passengers'}
          </p>
        </div>

        <Link
          href="/"
          className="text-xs font-bold px-4 py-2 rounded-xl border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 text-zinc-700 transition"
        >
          Modify Search
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Filter Sidebar */}
        <aside className="lg:col-span-1 space-y-5">
          <div className="bg-white rounded-2xl border border-zinc-200 p-5 shadow-xs">
            <h2 className="text-sm font-bold text-zinc-900 uppercase tracking-wider mb-4 pb-2 border-b border-zinc-100">
              Filters
            </h2>

            {/* Sort Order */}
            <div className="mb-5">
              <label className="block text-xs font-bold text-zinc-600 mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full text-xs font-semibold px-3 py-2 rounded-xl border border-zinc-200 bg-zinc-50"
              >
                <option value="cheapest">Cheapest Fare</option>
                <option value="earliest_departure">Earliest Departure</option>
                <option value="shortest_journey">Shortest Duration</option>
              </select>
            </div>

            {/* AC Filter */}
            <div className="mb-5">
              <label className="block text-xs font-bold text-zinc-600 mb-2">Bus Climate</label>
              <div className="flex flex-col gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => setAcFilter('all')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    acFilter === 'all' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  All Buses
                </button>
                <button
                  type="button"
                  onClick={() => setAcFilter('ac')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    acFilter === 'ac' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  AC Only
                </button>
                <button
                  type="button"
                  onClick={() => setAcFilter('non-ac')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    acFilter === 'non-ac' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Non-AC Only
                </button>
              </div>
            </div>

            {/* Seat Type Filter */}
            <div className="mb-5">
              <label className="block text-xs font-bold text-zinc-600 mb-2">Seating Format</label>
              <div className="flex flex-col gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => setTypeFilter('all')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    typeFilter === 'all' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  All Formats
                </button>
                <button
                  type="button"
                  onClick={() => setTypeFilter('sleeper')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    typeFilter === 'sleeper' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Sleeper Berths
                </button>
                <button
                  type="button"
                  onClick={() => setTypeFilter('seater')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    typeFilter === 'seater' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Seater / Semi-Sleeper
                </button>
              </div>
            </div>

            {/* Departure Time */}
            <div>
              <label className="block text-xs font-bold text-zinc-600 mb-2">Departure Time</label>
              <div className="flex flex-col gap-1.5 text-xs">
                <button
                  type="button"
                  onClick={() => setTimeFilter('all')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    timeFilter === 'all' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Any Time
                </button>
                <button
                  type="button"
                  onClick={() => setTimeFilter('morning')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    timeFilter === 'morning' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Morning (06:00 - 12:00)
                </button>
                <button
                  type="button"
                  onClick={() => setTimeFilter('afternoon')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    timeFilter === 'afternoon' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Afternoon (12:00 - 17:00)
                </button>
                <button
                  type="button"
                  onClick={() => setTimeFilter('evening')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    timeFilter === 'evening' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Evening (17:00 - 21:00)
                </button>
                <button
                  type="button"
                  onClick={() => setTimeFilter('night')}
                  className={`text-left px-3 py-2 rounded-lg font-medium transition ${
                    timeFilter === 'night' ? 'bg-blue-50 text-blue-700 font-bold' : 'hover:bg-zinc-50'
                  }`}
                >
                  Night (21:00 onwards)
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Bus Results List */}
        <main className="lg:col-span-3 space-y-4">
          {loading && (
            <div className="bg-white rounded-2xl border border-zinc-200 p-12 text-center text-sm text-zinc-500">
              Fetching available buses for {fromCity} → {toCity}...
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl p-6 text-sm">
              <span className="font-bold">Error:</span> {error}
            </div>
          )}

          {!loading && !error && buses.length === 0 && (
            <div className="bg-white rounded-2xl border border-zinc-200 p-12 text-center space-y-3">
              <div className="text-3xl">🚌</div>
              <h3 className="font-bold text-zinc-900 text-base">No buses found for this route</h3>
              <p className="text-xs text-zinc-500">
                Try adjusting your filters or search another date or route like Hyderabad → Vijayawada.
              </p>
            </div>
          )}

          {!loading &&
            !error &&
            buses.map((bus) => (
              <div
                key={bus.bus_id}
                className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs hover:shadow-md transition group"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-100">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h3 className="text-lg font-black text-zinc-900 group-hover:text-blue-600 transition">
                        {bus.bus_name}
                      </h3>
                      <span className="px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700 text-xs font-semibold">
                        {bus.bus_type}
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold">
                        ★ {bus.rating}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 mt-0.5">Operator: {bus.operator}</p>
                  </div>

                  <div className="text-left sm:text-right">
                    <span className="text-xs text-zinc-400">Starting from</span>
                    <div className="text-2xl font-black text-zinc-900">₹{bus.starting_price}</div>
                  </div>
                </div>

                {/* Timings and Seats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-4 items-center">
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-base font-extrabold text-zinc-900">{bus.departure_time}</div>
                      <div className="text-xs text-zinc-500">{bus.origin}</div>
                    </div>
                    <div className="text-center flex-1 px-2">
                      <div className="text-[10px] text-zinc-400 font-medium">{bus.duration}</div>
                      <div className="w-full h-0.5 bg-zinc-200 relative my-1">
                        <div className="absolute -top-1 right-0 w-2 h-2 rounded-full bg-blue-600"></div>
                      </div>
                    </div>
                    <div>
                      <div className="text-base font-extrabold text-zinc-900">{bus.arrival_time}</div>
                      <div className="text-xs text-zinc-500">{bus.destination}</div>
                    </div>
                  </div>

                  {/* Available Seats Info */}
                  <div className="text-center sm:text-left">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                      <span>✓</span> {bus.available_seats} Seats Left
                    </span>
                    <span className="text-xs text-zinc-400 block mt-1">
                      Out of {bus.total_seats} total seats
                    </span>
                  </div>

                  {/* Select Seats Button */}
                  <div className="sm:text-right">
                    <button
                      type="button"
                      onClick={() =>
                        router.push(
                          `/bus/${bus.bus_id}?journey_date=${journeyDate}&passengers=${passengers}`
                        )
                      }
                      className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition"
                    >
                      Select Seats
                    </button>
                  </div>
                </div>

                {/* Amenities Badges */}
                {bus.amenities && bus.amenities.length > 0 && (
                  <div className="pt-3 border-t border-zinc-100 flex flex-wrap gap-1.5">
                    {bus.amenities.map((amenity, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-600"
                      >
                        {amenity}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
        </main>
      </div>
    </div>
  );
}
