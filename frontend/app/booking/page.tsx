'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api, getAuthToken, getStoredUser } from '@/lib/api';
import { Bus, Seat, PassengerInput } from '@/types';

export default function BookingPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-zinc-500">Loading booking checkout...</div>}>
      <BookingPageContent />
    </Suspense>
  );
}

function BookingPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const busId = parseInt(searchParams.get('bus_id') || '0', 10);
  const journeyDate = searchParams.get('journey_date') || '';
  const holdToken = searchParams.get('hold_token') || '';
  const seatIdsParam = searchParams.get('seats') || '';

  const seatIds = seatIdsParam
    .split(',')
    .map((id) => parseInt(id, 10))
    .filter((id) => !isNaN(id));

  const [bus, setBus] = useState<Bus | null>(null);
  const [selectedSeats, setSelectedSeats] = useState<Seat[]>([]);
  const [passengers, setPassengers] = useState<PassengerInput[]>([]);
  const [boardingPoint, setBoardingPoint] = useState<string>('');
  const [droppingPoint, setDroppingPoint] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication
    const token = getAuthToken();
    if (!token) {
      // If not logged in, direct user to login with return path
      const currentUrl = window.location.pathname + window.location.search;
      router.push(`/login?redirect=${encodeURIComponent(currentUrl)}`);
      return;
    }

    loadBookingData();
  }, [busId, journeyDate, seatIdsParam]);

  const loadBookingData = async () => {
    if (!busId || seatIds.length === 0) {
      setError('Invalid booking parameters. Please select seats from the search results.');
      setLoading(false);
      return;
    }

    try {
      const [busData, seatsData] = await Promise.all([
        api.getBus(busId, journeyDate),
        api.getBusSeats(busId, journeyDate),
      ]);
      setBus(busData);

      const matchedSeats = seatsData.seats.filter((s) => seatIds.includes(s.id));
      setSelectedSeats(matchedSeats);

      if (busData.boarding_points?.length > 0) {
        setBoardingPoint(busData.boarding_points[0]);
      }
      if (busData.dropping_points?.length > 0) {
        setDroppingPoint(busData.dropping_points[0]);
      }

      // Prepopulate passenger fields
      const user = getStoredUser();
      const initialPassengers: PassengerInput[] = matchedSeats.map((s, idx) => ({
        seat_id: s.id,
        seat_number: s.seat_number,
        name: idx === 0 && user ? user.name : '',
        age: 28,
        gender: 'M',
      }));
      setPassengers(initialPassengers);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize booking session.');
    } finally {
      setLoading(false);
    }
  };

  const handlePassengerChange = (
    index: number,
    field: keyof PassengerInput,
    value: any
  ) => {
    setPassengers((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleCreateBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate passengers
    for (const p of passengers) {
      if (!p.name.trim()) {
        setError(`Please provide a name for seat ${p.seat_number}.`);
        return;
      }
      if (p.age < 1 || p.age > 120) {
        setError(`Please enter a valid age for passenger ${p.name}.`);
        return;
      }
    }

    if (!boardingPoint || !droppingPoint) {
      setError('Please select both boarding and dropping points.');
      return;
    }

    setSubmitting(true);
    try {
      const booking = await api.createBooking({
        bus_id: busId,
        journey_date: journeyDate,
        boarding_point: boardingPoint,
        dropping_point: droppingPoint,
        hold_token: holdToken || undefined,
        passengers: passengers.map((p) => ({
          seat_id: p.seat_id,
          name: p.name.trim(),
          age: p.age,
          gender: p.gender,
        })),
      });

      // Redirect to mock payment page
      router.push(`/payment?booking_id=${booking.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to reserve booking.');
    } finally {
      setSubmitting(false);
    }
  };

  const totalAmount = selectedSeats.reduce((sum, s) => sum + s.price, 0);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-sm text-zinc-500">
        Preparing your passenger checkout...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
      <div className="mb-6">
        <h1 className="text-2xl font-black text-zinc-900">Passenger & Journey Details</h1>
        <p className="text-xs text-zinc-500 mt-1">
          Review your selection and enter traveler details to complete booking.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200 font-medium">
          {error}
        </div>
      )}

      {bus && (
        <form onSubmit={handleCreateBooking} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Passenger Input Fields */}
          <div className="lg:col-span-2 space-y-6">
            {/* Boarding and Dropping Points */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs space-y-4">
              <h2 className="text-sm font-bold text-zinc-900 pb-2 border-b border-zinc-100">
                Boarding & Dropping Points
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-zinc-600 mb-1.5">
                    Boarding Point ({bus.origin})
                  </label>
                  <select
                    value={boardingPoint}
                    onChange={(e) => setBoardingPoint(e.target.value)}
                    className="w-full text-xs font-semibold px-3 py-2.5 rounded-xl border border-zinc-200 bg-zinc-50"
                  >
                    {bus.boarding_points?.map((bp, idx) => (
                      <option key={idx} value={bp}>
                        {bp}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-zinc-600 mb-1.5">
                    Dropping Point ({bus.destination})
                  </label>
                  <select
                    value={droppingPoint}
                    onChange={(e) => setDroppingPoint(e.target.value)}
                    className="w-full text-xs font-semibold px-3 py-2.5 rounded-xl border border-zinc-200 bg-zinc-50"
                  >
                    {bus.dropping_points?.map((dp, idx) => (
                      <option key={idx} value={dp}>
                        {dp}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Passenger Forms */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs space-y-6">
              <h2 className="text-sm font-bold text-zinc-900 pb-2 border-b border-zinc-100">
                Passenger Details ({passengers.length})
              </h2>

              {passengers.map((p, idx) => (
                <div
                  key={p.seat_id}
                  className="p-4 rounded-xl border border-zinc-200 bg-zinc-50/70 space-y-3"
                >
                  <div className="flex items-center justify-between text-xs font-bold text-zinc-700">
                    <span>Passenger {idx + 1}</span>
                    <span className="px-2.5 py-0.5 rounded-md bg-blue-100 text-blue-700">
                      Seat: {p.seat_number}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
                    <div className="sm:col-span-6">
                      <label className="block text-[11px] font-semibold text-zinc-600 mb-1">
                        Full Name
                      </label>
                      <input
                        type="text"
                        required
                        value={p.name}
                        onChange={(e) => handlePassengerChange(idx, 'name', e.target.value)}
                        placeholder="e.g. Ramesh Kumar"
                        className="w-full text-xs px-3 py-2 rounded-lg border border-zinc-200 bg-white"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-[11px] font-semibold text-zinc-600 mb-1">
                        Age
                      </label>
                      <input
                        type="number"
                        required
                        min="1"
                        max="120"
                        value={p.age}
                        onChange={(e) =>
                          handlePassengerChange(idx, 'age', parseInt(e.target.value, 10) || 1)
                        }
                        className="w-full text-xs px-3 py-2 rounded-lg border border-zinc-200 bg-white"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-[11px] font-semibold text-zinc-600 mb-1">
                        Gender
                      </label>
                      <select
                        value={p.gender}
                        onChange={(e) => handlePassengerChange(idx, 'gender', e.target.value)}
                        className="w-full text-xs px-3 py-2 rounded-lg border border-zinc-200 bg-white"
                      >
                        <option value="M">Male</option>
                        <option value="F">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fare Summary Sidebar */}
          <div>
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs space-y-4 sticky top-24">
              <h3 className="text-base font-bold text-zinc-900 pb-3 border-b border-zinc-100">
                Fare Summary
              </h3>

              <div className="text-xs space-y-2 text-zinc-600">
                <div className="flex justify-between">
                  <span>Bus</span>
                  <span className="font-semibold text-zinc-900">{bus.bus_name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Route</span>
                  <span className="font-semibold text-zinc-900">
                    {bus.origin} → {bus.destination}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Journey Date</span>
                  <span className="font-semibold text-zinc-900">{journeyDate}</span>
                </div>
                <div className="flex justify-between">
                  <span>Departure Time</span>
                  <span className="font-semibold text-zinc-900">{bus.departure_time}</span>
                </div>
                <div className="flex justify-between">
                  <span>Seats</span>
                  <span className="font-bold text-blue-600">
                    {selectedSeats.map((s) => s.seat_number).join(', ')}
                  </span>
                </div>

                <div className="pt-3 border-t border-zinc-100 flex justify-between items-center text-sm">
                  <span className="font-bold text-zinc-700">Total Fare</span>
                  <span className="text-2xl font-black text-zinc-900">₹{totalAmount}</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-md transition"
              >
                {submitting ? 'Confirming Reservation...' : 'Proceed to Payment'}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
