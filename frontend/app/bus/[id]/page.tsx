'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Bus, Seat } from '@/types';
import SeatMap from '@/components/SeatMap';
import AiRecommendationModal from '@/components/AiRecommendationModal';

export default function BusPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = React.use(params);
  const busId = parseInt(resolvedParams.id, 10);

  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-zinc-500">Loading seat layout...</div>}>
      <BusPageContent busId={busId} />
    </Suspense>
  );
}

function BusPageContent({ busId }: { busId: number }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const journeyDate = searchParams.get('journey_date') || new Date().toISOString().split('T')[0];
  const maxSelectableSeats = 6; // Standard maximum seats per booking

  const [bus, setBus] = useState<Bus | null>(null);
  const [seats, setSeats] = useState<Seat[]>([]);
  const [selectedSeatIds, setSelectedSeatIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [holding, setHolding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);

  useEffect(() => {
    loadBusAndSeats();
  }, [busId, journeyDate]);

  const loadBusAndSeats = async () => {
    setLoading(true);
    setError(null);
    try {
      const [busData, seatsData] = await Promise.all([
        api.getBus(busId, journeyDate),
        api.getBusSeats(busId, journeyDate),
      ]);
      setBus(busData);
      setSeats(seatsData.seats);
    } catch (err: any) {
      setError(err.message || 'Failed to load bus seat layout.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeatToggle = (seat: Seat) => {
    if (seat.status !== 'available' && !selectedSeatIds.includes(seat.id)) {
      return;
    }

    if (selectedSeatIds.includes(seat.id)) {
      setSelectedSeatIds((prev) => prev.filter((id) => id !== seat.id));
    } else {
      if (selectedSeatIds.length >= maxSelectableSeats) {
        alert(`You can select at most ${maxSelectableSeats} seats per booking.`);
        return;
      }
      setSelectedSeatIds((prev) => [...prev, seat.id]);
    }
  };

  const handleAiSelectSeat = (seatNumber: string) => {
    const seatObj = seats.find((s) => s.seat_number === seatNumber);
    if (seatObj && seatObj.status === 'available') {
      if (!selectedSeatIds.includes(seatObj.id)) {
        if (selectedSeatIds.length < maxSelectableSeats) {
          setSelectedSeatIds((prev) => [...prev, seatObj.id]);
        }
      }
    }
  };

  const selectedSeats = seats.filter((s) => selectedSeatIds.includes(s.id));
  const totalPrice = selectedSeats.reduce((acc, s) => acc + s.price, 0);

  const handleProceedToBooking = async () => {
    if (selectedSeatIds.length === 0) {
      alert('Please select at least one seat to proceed.');
      return;
    }

    setHolding(true);
    setError(null);
    try {
      // Call backend temporary hold API
      const holdRes = await api.holdSeats(busId, selectedSeatIds, journeyDate);
      
      // Navigate to booking page with hold token and seat IDs
      const seatIdsParam = selectedSeatIds.join(',');
      router.push(
        `/booking?bus_id=${busId}&journey_date=${journeyDate}&hold_token=${holdRes.hold_token}&seats=${seatIdsParam}`
      );
    } catch (err: any) {
      setError(err.message || 'Could not hold seats. Another passenger may have just reserved them.');
      // Refresh seats to show updated status
      loadBusAndSeats();
    } finally {
      setHolding(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-sm text-zinc-500">
        Loading bus and interactive seat map...
      </div>
    );
  }

  if (error && !bus) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="p-4 rounded-2xl bg-red-50 text-red-700 text-sm border border-red-200">
          {error}
        </div>
        <Link href="/" className="text-xs font-bold text-blue-600 hover:underline">
          Return to search
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
      {/* Bus Header Card */}
      {bus && (
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 mb-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-zinc-900">{bus.bus_name}</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
                {bus.bus_type}
              </span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                ★ {bus.rating}
              </span>
            </div>
            <p className="text-xs text-zinc-500 mt-1">
              {bus.origin} → {bus.destination} • Journey Date: <span className="font-semibold text-zinc-700">{journeyDate}</span> • Departure:{' '}
              <span className="font-semibold text-zinc-700">{bus.departure_time}</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsAiModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 text-xs font-bold transition flex items-center gap-1.5 shadow-xs"
            >
              <span>🤖</span> Saarthi AI Seat Advisor
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 text-amber-800 text-xs border border-amber-200 font-medium">
          ⚠️ {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Seat Map */}
        <div className="lg:col-span-2">
          <SeatMap
            seats={seats}
            selectedSeatIds={selectedSeatIds}
            onSeatToggle={handleSeatToggle}
            maxSelectable={maxSelectableSeats}
          />
        </div>

        {/* Selected Summary Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs">
            <h3 className="text-base font-bold text-zinc-900 pb-3 border-b border-zinc-100">
              Booking Summary
            </h3>

            <div className="py-4 space-y-3 text-xs">
              <div className="flex justify-between text-zinc-600">
                <span>Selected Seats ({selectedSeats.length})</span>
                <span className="font-bold text-zinc-900">
                  {selectedSeats.length > 0
                    ? selectedSeats.map((s) => s.seat_number).join(', ')
                    : 'None'}
                </span>
              </div>

              {selectedSeats.map((s) => (
                <div
                  key={s.id}
                  className="flex justify-between items-center bg-zinc-50 px-3 py-2 rounded-lg border border-zinc-100"
                >
                  <span className="font-semibold text-zinc-800">
                    Seat {s.seat_number} ({s.seat_type}, {s.upper_lower})
                  </span>
                  <span className="font-bold text-zinc-900">₹{s.price}</span>
                </div>
              ))}

              <div className="pt-3 border-t border-zinc-100 flex justify-between items-center text-sm">
                <span className="font-bold text-zinc-700">Total Amount</span>
                <span className="text-xl font-black text-blue-600">₹{totalPrice}</span>
              </div>
            </div>

            <button
              type="button"
              disabled={selectedSeatIds.length === 0 || holding}
              onClick={handleProceedToBooking}
              className={`w-full py-3.5 px-4 rounded-xl font-bold text-xs shadow-md transition ${
                selectedSeatIds.length === 0 || holding
                  ? 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {holding ? 'Holding Seats (10m)...' : `Hold & Continue (₹${totalPrice})`}
            </button>

            <p className="text-[10px] text-zinc-400 text-center mt-2.5">
              Seats will be temporarily held for 10 minutes to prevent double booking.
            </p>
          </div>

          {/* Quick AI Prompt Box */}
          <div className="p-5 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100 text-xs space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-purple-900">
              <span>💡</span> AI Integration Ready
            </div>
            <p className="text-purple-700 leading-relaxed text-[11px]">
              The future voice agent Saarthi AI uses the same backend recommendation algorithm to suggest window and lower berths according to traveler voice prompts.
            </p>
          </div>
        </div>
      </div>

      {/* AI Recommendation Modal */}
      <AiRecommendationModal
        busId={busId}
        journeyDate={journeyDate}
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        onSelectSeat={handleAiSelectSeat}
      />
    </div>
  );
}
