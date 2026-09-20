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

  // Admin WhatsApp Payment Delivery State
  const [isAdminUser, setIsAdminUser] = useState(false);
  const [showAdminWhatsAppModal, setShowAdminWhatsAppModal] = useState(false);
  const [createdBooking, setCreatedBooking] = useState<any | null>(null);
  const [whatsAppPhone, setWhatsAppPhone] = useState('');
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [dispatchingWhatsApp, setDispatchingWhatsApp] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<{
    success: boolean;
    delivery_status?: string;
    message: string;
    payment_url?: string;
    message_id?: string;
  } | null>(null);

  const validateIndianPhone = (raw: string): { isValid: boolean; normalized: string; error?: string } => {
    let cleaned = raw.trim();
    if (cleaned.toLowerCase().startsWith('whatsapp:')) cleaned = cleaned.slice(9).trim();
    cleaned = cleaned.replace(/[\s\-\(\)\.]/g, '');
    let digits = cleaned;
    if (cleaned.startsWith('+91')) digits = cleaned.slice(3);
    else if (cleaned.startsWith('91') && cleaned.length === 12) digits = cleaned.slice(2);
    else if (cleaned.startsWith('0') && cleaned.length === 11) digits = cleaned.slice(1);

    if (!/^[6-9]\d{9}$/.test(digits)) {
      return {
        isValid: false,
        normalized: '',
        error: 'Please enter a valid 10-digit Indian mobile number (starting with 6, 7, 8, or 9).',
      };
    }
    return { isValid: true, normalized: `91${digits}` };
  };

  useEffect(() => {
    const storedUser = getStoredUser();
    setIsAdminUser(storedUser?.role === 'admin');

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

      if (isAdminUser) {
        setCreatedBooking(booking);
        setShowAdminWhatsAppModal(true);
      } else {
        // Regular user proceeds directly to checkout
        router.push(`/payment?booking_id=${booking.id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to reserve booking.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendWhatsAppDelivery = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!createdBooking) return;

    const validation = validateIndianPhone(whatsAppPhone);
    if (!validation.isValid) {
      setPhoneError(validation.error || 'Invalid Indian mobile number.');
      return;
    }

    setPhoneError(null);
    setDispatchingWhatsApp(true);
    setDispatchResult(null);

    try {
      const res = await api.deliverPaymentLink({
        booking_id: createdBooking.id,
        channel: 'WHATSAPP',
        destination: validation.normalized,
      });

      setDispatchResult({
        success: res.delivery_status === 'SENT',
        delivery_status: res.delivery_status,
        message: res.message,
        payment_url: res.payment_url,
        message_id: res.message_id,
      });
    } catch (err: any) {
      setDispatchResult({
        success: false,
        message: err.message || 'Failed to dispatch payment link via WhatsApp.',
      });
    } finally {
      setDispatchingWhatsApp(false);
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
                    className="w-full text-xs font-semibold px-3 py-2.5 rounded-xl border border-zinc-200 bg-zinc-50 text-zinc-900 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
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
                    className="w-full text-xs font-semibold px-3 py-2.5 rounded-xl border border-zinc-200 bg-zinc-50 text-zinc-900 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
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
                        className="w-full text-xs font-semibold px-3 py-2 rounded-lg border border-zinc-200 bg-white text-zinc-900 placeholder:text-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
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
                        className="w-full text-xs font-semibold px-3 py-2 rounded-lg border border-zinc-200 bg-white text-zinc-900 placeholder:text-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-[11px] font-semibold text-zinc-600 mb-1">
                        Gender
                      </label>
                      <select
                        value={p.gender}
                        onChange={(e) => handlePassengerChange(idx, 'gender', e.target.value)}
                        className="w-full text-xs font-semibold px-3 py-2 rounded-lg border border-zinc-200 bg-white text-zinc-900 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
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

      {/* Admin WhatsApp Payment Delivery Modal */}
      {showAdminWhatsAppModal && createdBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200 overflow-y-auto">
          <div className="bg-white rounded-3xl border border-zinc-200 shadow-2xl max-w-lg w-full p-5 sm:p-7 relative max-h-[90vh] overflow-y-auto my-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-zinc-100">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl font-bold border border-emerald-100">
                  📱
                </div>
                <div>
                  <h3 className="text-base font-black text-zinc-900">Send Payment Link via WhatsApp</h3>
                  <p className="text-xs text-zinc-500 font-medium">Meta WhatsApp Cloud API Integration</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAdminWhatsAppModal(false)}
                className="w-8 h-8 rounded-full text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 flex items-center justify-center transition text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Booking Summary Card */}
            <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200 text-xs space-y-2 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-zinc-500 font-medium">Booking Reference</span>
                <span className="font-mono font-bold text-zinc-900 bg-white px-2.5 py-0.5 rounded-md border border-zinc-200">
                  {createdBooking.booking_reference}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-500 font-medium">Bus & Route</span>
                <span className="font-semibold text-zinc-800">
                  {bus?.bus_name} ({bus?.origin} → {bus?.destination})
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-500 font-medium">Selected Seats</span>
                <span className="font-bold text-blue-600">
                  {selectedSeats.map((s) => s.seat_number).join(', ')}
                </span>
              </div>
              <div className="flex justify-between items-center pt-1.5 border-t border-zinc-200">
                <span className="font-bold text-zinc-700">Total Fare Due</span>
                <span className="text-base font-black text-zinc-900">₹{createdBooking.total_amount}</span>
              </div>
            </div>

            {/* Direct Payment Link Card */}
            <div className="p-3.5 rounded-2xl bg-blue-50/70 border border-blue-200 mb-4">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold text-blue-900 flex items-center gap-1.5">
                  <span>🔗</span> Direct Payment Link:
                </span>
                <button
                  type="button"
                  onClick={() => {
                    const url = dispatchResult?.payment_url || (typeof window !== 'undefined' ? `${window.location.origin}/payment?booking_id=${createdBooking.id}` : '');
                    navigator.clipboard.writeText(url);
                    setCopiedLink(true);
                    setTimeout(() => setCopiedLink(false), 2000);
                  }}
                  className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition cursor-pointer"
                >
                  {copiedLink ? '✓ Copied!' : '📋 Copy Link'}
                </button>
              </div>
              <p className="font-mono text-[11px] text-blue-800 break-all bg-white/90 p-2 rounded-lg border border-blue-100 select-all">
                {dispatchResult?.payment_url || (typeof window !== 'undefined' ? `${window.location.origin}/payment?booking_id=${createdBooking.id}` : '')}
              </p>
            </div>

            {/* Notification Result Banner */}
            {dispatchResult && (
              <div
                className={`mb-4 p-3.5 rounded-2xl text-xs font-semibold border flex items-start gap-2.5 ${
                  dispatchResult.success
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-amber-50 text-amber-900 border-amber-200'
                }`}
              >
                <span className="text-base">{dispatchResult.success ? '✅' : '⚠️'}</span>
                <div className="flex-1">
                  <p className="font-bold leading-snug">{dispatchResult.message}</p>
                  {dispatchResult.message_id && (
                    <p className="text-[10px] font-mono text-zinc-500 mt-0.5">
                      Meta Message ID: {dispatchResult.message_id}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Phone Input & Action Buttons */}
            <form onSubmit={handleSendWhatsAppDelivery} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-zinc-700 mb-1.5">
                  Traveler WhatsApp Number <span className="text-blue-600 font-semibold">(Indian Mobile Only)</span>
                </label>
                <div className="relative flex items-center">
                  <span className="absolute left-3.5 text-xs font-bold text-zinc-600 flex items-center gap-1 select-none">
                    <span>🇮🇳</span> +91
                  </span>
                  <input
                    type="tel"
                    required
                    autoFocus
                    placeholder="e.g. 98765 43210"
                    value={whatsAppPhone}
                    onChange={(e) => {
                      setWhatsAppPhone(e.target.value);
                      if (phoneError) setPhoneError(null);
                    }}
                    className={`w-full text-xs font-semibold pl-16 pr-3.5 py-3 rounded-xl border bg-zinc-50 text-zinc-900 placeholder:text-zinc-400 focus:bg-white focus:outline-hidden focus:ring-2 ${
                      phoneError
                        ? 'border-red-300 focus:ring-red-500'
                        : 'border-zinc-200 focus:ring-blue-600'
                    }`}
                  />
                </div>
                {phoneError && (
                  <p className="text-[11px] text-red-600 font-semibold mt-1 flex items-center gap-1">
                    <span>⚠️</span> {phoneError}
                  </p>
                )}
                <p className="text-[11px] text-zinc-400 mt-1">
                  10-digit Indian mobile number. Standardized to E.164 (+91).
                </p>
              </div>

              {/* Action Buttons */}
              <div className="pt-1 space-y-2.5">
                {/* 1. Send via Meta WhatsApp Cloud API */}
                <button
                  type="submit"
                  disabled={dispatchingWhatsApp}
                  className="w-full py-3.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {dispatchingWhatsApp ? (
                    <>
                      <span className="animate-spin">🔄</span>
                      <span>Dispatching via Meta WhatsApp API...</span>
                    </>
                  ) : (
                    <>
                      <span className="text-sm">⚡</span>
                      <span>Send Payment Link via Meta WhatsApp</span>
                    </>
                  )}
                </button>

                {/* 2. Direct 1-Click WhatsApp (wa.me) */}
                {(() => {
                  const rawDigits = whatsAppPhone.replace(/\D/g, '');
                  const cleanDigits = rawDigits.startsWith('91') && rawDigits.length === 12 ? rawDigits.slice(2) : rawDigits.slice(-10);
                  const validNumber = /^[6-9]\d{9}$/.test(cleanDigits);
                  const paymentUrl = dispatchResult?.payment_url || (typeof window !== 'undefined' ? `${window.location.origin}/payment?booking_id=${createdBooking.id}` : '');
                  const textPayload = `🚌 *Snehith Travels - Payment Link*\n\nDear Customer,\nYour booking reservation *${createdBooking.booking_reference}* is ready.\n\n• *Bus:* ${bus?.bus_name || 'Express'} (${bus?.origin} → ${bus?.destination})\n• *Seats:* ${selectedSeats.map((s) => s.seat_number).join(', ')}\n• *Amount Due:* ₹${createdBooking.total_amount}\n\n👉 *Pay Securely Here:* ${paymentUrl}\n\nPlease click the link above to complete your payment.\nThank you!`;
                  const waHref = validNumber ? `https://wa.me/91${cleanDigits}?text=${encodeURIComponent(textPayload)}` : '#';

                  return (
                    <a
                      href={validNumber ? waHref : undefined}
                      target={validNumber ? '_blank' : undefined}
                      rel="noopener noreferrer"
                      onClick={(e) => {
                        if (!validNumber) {
                          e.preventDefault();
                          setPhoneError('Please enter a valid 10-digit Indian number above first.');
                        }
                      }}
                      className={`w-full py-2.5 px-4 rounded-xl border border-emerald-600/30 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold text-xs transition flex items-center justify-center gap-2 text-center cursor-pointer ${
                        !validNumber ? 'opacity-70' : ''
                      }`}
                    >
                      <span>💬</span>
                      <span>Or Open in WhatsApp Web / App (Direct 1-Click)</span>
                    </a>
                  );
                })()}

                {/* 3. View Checkout Button */}
                <button
                  type="button"
                  onClick={() => router.push(`/payment?booking_id=${createdBooking.id}`)}
                  className="w-full py-2.5 px-4 rounded-xl border border-zinc-200 text-zinc-600 hover:bg-zinc-50 font-bold text-xs transition text-center cursor-pointer"
                >
                  View Checkout Page →
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
