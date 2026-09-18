'use client';

import React, { useState } from 'react';
import { Seat } from '@/types';

interface SeatMapProps {
  seats: Seat[];
  selectedSeatIds: number[];
  onSeatToggle: (seat: Seat) => void;
  maxSelectable?: number;
}

export default function SeatMap({
  seats,
  selectedSeatIds,
  onSeatToggle,
  maxSelectable = 6,
}: SeatMapProps) {
  const [activeDeck, setActiveDeck] = useState<'lower' | 'upper'>('lower');

  const isSleeper = seats.some((s) => s.seat_type === 'sleeper');

  // Filter seats by deck if sleeper
  const displayedSeats = isSleeper
    ? seats.filter((s) => s.upper_lower === activeDeck)
    : seats;

  // Group by rows
  const rows = Array.from(new Set(displayedSeats.map((s) => s.row))).sort((a, b) => a - b);

  return (
    <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-zinc-200">
        <div>
          <h3 className="text-lg font-bold text-zinc-900">Select Your Seats</h3>
          <p className="text-xs text-zinc-500 mt-0.5">
            Click on available seats to select (Max {maxSelectable} seats)
          </p>
        </div>

        {/* Sleeper Deck Selector */}
        {isSleeper && (
          <div className="inline-flex rounded-lg bg-zinc-100 p-1 border border-zinc-200">
            <button
              type="button"
              onClick={() => setActiveDeck('lower')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-md transition ${
                activeDeck === 'lower'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              Lower Deck
            </button>
            <button
              type="button"
              onClick={() => setActiveDeck('upper')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-md transition ${
                activeDeck === 'upper'
                  ? 'bg-white text-blue-600 shadow-xs'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              Upper Deck
            </button>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-6 py-4 border-b border-zinc-100 text-xs text-zinc-600">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded border border-emerald-500 bg-emerald-50 inline-block"></span>
          <span>Available</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded bg-blue-600 border border-blue-600 inline-block"></span>
          <span className="font-semibold text-zinc-900">Selected</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded bg-zinc-200 border border-zinc-300 inline-block"></span>
          <span>Booked</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded bg-amber-100 border border-amber-300 inline-block"></span>
          <span>Held</span>
        </div>
      </div>

      {/* Bus Interior Box */}
      <div className="w-full overflow-x-auto pb-2 my-6">
        <div className="min-w-[320px] max-w-md mx-auto p-4 sm:p-6 rounded-3xl border-2 border-zinc-200 bg-zinc-50/50 shadow-inner">
        {/* Front of the bus indicator */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-dashed border-zinc-300 text-xs text-zinc-400 font-mono">
          <span>FRONT</span>
          <span className="p-1 rounded-full bg-zinc-200 text-zinc-600 text-[10px] font-bold">
            STEERING WHEEL
          </span>
        </div>

        {/* Seat Grid */}
        <div className="space-y-3">
          {rows.map((rowNum) => {
            const rowSeats = displayedSeats.filter((s) => s.row === rowNum);

            if (isSleeper) {
              // Sleeper 2+1 layout:
              // Left: Single berth (col 1)
              // Center: Aisle
              // Right: Double berth (col 3, col 4)
              const singleSeat = rowSeats.find((s) => s.column === 1);
              const doubleAisle = rowSeats.find((s) => s.column === 3);
              const doubleWindow = rowSeats.find((s) => s.column === 4);

              return (
                <div key={rowNum} className="flex items-center justify-between gap-4">
                  {/* Single Berth */}
                  <div className="w-24">
                    {singleSeat ? (
                      <SeatItem
                        seat={singleSeat}
                        isSelected={selectedSeatIds.includes(singleSeat.id)}
                        onToggle={() => onSeatToggle(singleSeat)}
                      />
                    ) : (
                      <div className="w-24 h-12"></div>
                    )}
                  </div>

                  {/* Aisle */}
                  <div className="flex-1 text-center">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-300">
                      AISLE
                    </span>
                  </div>

                  {/* Double Berth */}
                  <div className="flex gap-2 w-48">
                    {doubleAisle && (
                      <SeatItem
                        seat={doubleAisle}
                        isSelected={selectedSeatIds.includes(doubleAisle.id)}
                        onToggle={() => onSeatToggle(doubleAisle)}
                      />
                    )}
                    {doubleWindow && (
                      <SeatItem
                        seat={doubleWindow}
                        isSelected={selectedSeatIds.includes(doubleWindow.id)}
                        onToggle={() => onSeatToggle(doubleWindow)}
                      />
                    )}
                  </div>
                </div>
              );
            } else {
              // Seater 2+2 layout: Col 1, Col 2 | Aisle | Col 3, Col 4
              const c1 = rowSeats.find((s) => s.column === 1);
              const c2 = rowSeats.find((s) => s.column === 2);
              const c3 = rowSeats.find((s) => s.column === 3);
              const c4 = rowSeats.find((s) => s.column === 4);

              return (
                <div key={rowNum} className="flex items-center justify-between gap-4">
                  <div className="flex gap-2">
                    {c1 && (
                      <SeatItem
                        seat={c1}
                        isSelected={selectedSeatIds.includes(c1.id)}
                        onToggle={() => onSeatToggle(c1)}
                      />
                    )}
                    {c2 && (
                      <SeatItem
                        seat={c2}
                        isSelected={selectedSeatIds.includes(c2.id)}
                        onToggle={() => onSeatToggle(c2)}
                      />
                    )}
                  </div>

                  <div className="flex-1 text-center">
                    <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-300">
                      AISLE
                    </span>
                  </div>

                  <div className="flex gap-2">
                    {c3 && (
                      <SeatItem
                        seat={c3}
                        isSelected={selectedSeatIds.includes(c3.id)}
                        onToggle={() => onSeatToggle(c3)}
                      />
                    )}
                    {c4 && (
                      <SeatItem
                        seat={c4}
                        isSelected={selectedSeatIds.includes(c4.id)}
                        onToggle={() => onSeatToggle(c4)}
                      />
                    )}
                  </div>
                </div>
              );
            }
          })}
        </div>

        {/* Rear indicator */}
        <div className="pt-4 mt-4 border-t border-dashed border-zinc-300 text-center text-xs text-zinc-400 font-mono">
          REAR
        </div>
      </div>
      </div>
    </div>
  );
}

function SeatItem({
  seat,
  isSelected,
  onToggle,
}: {
  seat: Seat;
  isSelected: boolean;
  onToggle: () => void;
}) {
  const isAvailable = seat.status === 'available';
  const isBooked = seat.status === 'booked';
  const isHeld = seat.status === 'held';

  let btnClasses =
    'relative flex flex-col items-center justify-center transition rounded-xl font-medium cursor-pointer ';

  if (seat.seat_type === 'sleeper') {
    btnClasses += 'w-24 h-14 text-xs ';
  } else {
    btnClasses += 'w-12 h-12 text-xs ';
  }

  if (isSelected) {
    btnClasses += 'bg-blue-600 text-white shadow-md ring-2 ring-blue-400 font-bold';
  } else if (isBooked) {
    btnClasses += 'bg-zinc-200 text-zinc-400 cursor-not-allowed opacity-60 border border-zinc-300';
  } else if (isHeld) {
    btnClasses += 'bg-amber-50 text-amber-600 border border-dashed border-amber-300 cursor-not-allowed';
  } else {
    btnClasses +=
      'bg-white border-2 border-emerald-400 text-zinc-800 hover:border-emerald-600 hover:bg-emerald-50/50 shadow-xs';
  }

  return (
    <button
      type="button"
      disabled={!isAvailable && !isSelected}
      onClick={onToggle}
      className={btnClasses}
      title={`${seat.seat_number} - ₹${seat.price} (${seat.seat_type}, ${seat.upper_lower}, ${
        seat.window ? 'Window' : 'Aisle'
      }, ${seat.status})`}
    >
      <span className="text-[11px] font-bold">{seat.seat_number}</span>
      <span className="text-[9px] opacity-80">₹{seat.price}</span>

      {seat.window && (
        <span
          className={`absolute top-0.5 right-1 text-[8px] px-1 rounded ${
            isSelected ? 'bg-blue-800 text-white' : 'text-emerald-700 bg-emerald-100'
          }`}
        >
          W
        </span>
      )}
    </button>
  );
}
