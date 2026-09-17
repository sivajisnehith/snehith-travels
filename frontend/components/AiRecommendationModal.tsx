'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { RankedSeat } from '@/types';

interface AiRecommendationModalProps {
  busId: number;
  journeyDate: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectSeat: (seatNumber: string) => void;
}

export default function AiRecommendationModal({
  busId,
  journeyDate,
  isOpen,
  onClose,
  onSelectSeat,
}: AiRecommendationModalProps) {
  const [windowPref, setWindowPref] = useState(true);
  const [lowerPref, setLowerPref] = useState(true);
  const [frontPref, setFrontPref] = useState(false);
  const [cheapestPref, setCheapestPref] = useState(false);
  const [budget, setBudget] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<RankedSeat[]>([]);

  if (!isOpen) return null;

  const handleRecommend = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.recommendSeats(busId, {
        journey_date: journeyDate,
        window: windowPref,
        lower: lowerPref,
        front: frontPref,
        cheapest: cheapestPref,
        maximum_budget: budget ? parseFloat(budget) : undefined,
        limit: 5,
      });
      setRecommendations(res.recommended_seats);
    } catch (err: any) {
      setError(err.message || 'Failed to get recommendations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-zinc-200 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between pb-4 border-b border-zinc-100">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-purple-100 text-purple-700 text-sm">🤖</span>
            <div>
              <h3 className="font-bold text-zinc-900 text-base">Saarthi AI Seat Advisor</h3>
              <p className="text-xs text-zinc-500">Deterministic seat scoring algorithm</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600 rounded-lg p-1 text-lg font-bold"
          >
            &times;
          </button>
        </div>

        {/* Preference Controls */}
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-zinc-200 hover:bg-zinc-50 cursor-pointer">
              <input
                type="checkbox"
                checked={windowPref}
                onChange={(e) => setWindowPref(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-zinc-800">Window Preference</span>
            </label>
            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-zinc-200 hover:bg-zinc-50 cursor-pointer">
              <input
                type="checkbox"
                checked={lowerPref}
                onChange={(e) => setLowerPref(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-zinc-800">Lower Berth / Seat</span>
            </label>
            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-zinc-200 hover:bg-zinc-50 cursor-pointer">
              <input
                type="checkbox"
                checked={frontPref}
                onChange={(e) => setFrontPref(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-zinc-800">Front Rows</span>
            </label>
            <label className="flex items-center gap-2 p-2.5 rounded-xl border border-zinc-200 hover:bg-zinc-50 cursor-pointer">
              <input
                type="checkbox"
                checked={cheapestPref}
                onChange={(e) => setCheapestPref(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-zinc-800">Cheapest Fare</span>
            </label>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-700 mb-1">
              Max Budget (Optional, in ₹)
            </label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="e.g. 1200"
              className="w-full text-xs px-3 py-2 rounded-xl border border-zinc-200 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="button"
            onClick={handleRecommend}
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs shadow-xs transition flex items-center justify-center gap-2"
          >
            {loading ? 'Analyzing Bus Layout...' : 'Calculate Best Seats'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200">
            {error}
          </div>
        )}

        {/* Results */}
        {recommendations.length > 0 && (
          <div className="mt-5 space-y-2.5 max-h-56 overflow-y-auto pr-1">
            <h4 className="text-xs font-bold text-zinc-700 uppercase tracking-wider">
              Top Ranked Seats ({recommendations.length})
            </h4>
            {recommendations.map((rec, idx) => (
              <div
                key={rec.seat_id}
                className="flex items-center justify-between p-3 rounded-xl border border-zinc-200 bg-zinc-50 hover:bg-white hover:border-purple-300 transition"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-zinc-900 text-sm">{rec.seat_number}</span>
                    <span className="px-1.5 py-0.5 rounded-full bg-purple-100 text-purple-700 text-[10px] font-bold">
                      Score: {rec.score}
                    </span>
                    <span className="text-xs font-semibold text-zinc-700">₹{rec.price}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {rec.reasons.map((r, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-200/70 text-zinc-700 font-medium"
                      >
                        ✓ {r}
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    onSelectSeat(rec.seat_number);
                    onClose();
                  }}
                  className="text-xs font-bold px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Select
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
