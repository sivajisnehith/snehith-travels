'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { BookingDetail, PaymentResponse } from '@/types';

export default function PaymentPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-sm text-zinc-500">Loading payment checkout...</div>}>
      <PaymentPageContent />
    </Suspense>
  );
}

function PaymentPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingId = searchParams.get('booking_id') || '';

  const [booking, setBooking] = useState<BookingDetail | null>(null);
  const [payment, setPayment] = useState<PaymentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [generatingLink, setGeneratingLink] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initializedRef = React.useRef(false);

  useEffect(() => {
    if (!bookingId) {
      setError('Missing booking reference.');
      setLoading(false);
      return;
    }
    if (initializedRef.current) return;
    initializedRef.current = true;
    initializeCheckout();
  }, [bookingId]);

  const initializeCheckout = async () => {
    setLoading(true);
    setError(null);
    try {
      const b = await api.getBooking(bookingId);
      setBooking(b);

      if (b.status === 'CONFIRMED') {
        setLoading(false);
        return;
      }

      // Automatically generate or retrieve Razorpay Payment Link
      setGeneratingLink(true);
      const p = await api.createPayment(b.id, 'RAZORPAY_PAYMENT_LINK');
      setPayment(p);

      // If already paid according to authoritative backend
      if (p.status === 'PAID' || p.status === 'SUCCESS') {
        const updatedBooking = await api.getBooking(bookingId);
        setBooking(updatedBooking);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to initialize payment.');
    } finally {
      setGeneratingLink(false);
      setLoading(false);
    }
  };

  const handleGenerateLink = async () => {
    if (!booking) return;
    setGeneratingLink(true);
    setError(null);
    try {
      const p = await api.createPayment(booking.id, 'RAZORPAY_PAYMENT_LINK');
      setPayment(p);
    } catch (err: any) {
      setError(err.message || 'Could not generate Razorpay payment link.');
    } finally {
      setGeneratingLink(false);
    }
  };

  const handleCheckStatus = async () => {
    if (!payment && !booking) return;
    const payId = payment?.id || booking?.payment_id;
    if (!payId) {
      // Re-fetch booking
      if (bookingId) {
        const b = await api.getBooking(bookingId);
        setBooking(b);
      }
      return;
    }

    setVerifying(true);
    setError(null);
    try {
      const authoritativePayment = await api.getPayment(payId);
      setPayment(authoritativePayment);

      const updatedBooking = await api.getBooking(bookingId);
      setBooking(updatedBooking);

      if (authoritativePayment.status === 'PAID' || updatedBooking.status === 'CONFIRMED') {
        // Confirmed!
      } else if (authoritativePayment.status === 'PENDING') {
        setError('Payment is still being verified by the provider webhook. If you just completed payment, please check again in a few seconds.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to verify payment status.');
    } finally {
      setVerifying(false);
    }
  };

  const handlePayNow = () => {
    if (payment?.payment_url) {
      // Open Razorpay hosted payment link
      window.location.href = payment.payment_url;
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-sm text-zinc-500">
        Setting up Razorpay Test Mode checkout...
      </div>
    );
  }

  const isPaid =
    payment?.status === 'PAID' ||
    payment?.status === 'SUCCESS' ||
    booking?.status === 'CONFIRMED';
  const isFailed = payment?.status === 'FAILED';
  const isExpired = payment?.status === 'EXPIRED' || booking?.status === 'EXPIRED';
  const isPending = !isPaid && !isFailed && !isExpired;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12 w-full flex-1">
      <div className="bg-white rounded-3xl border border-zinc-200 p-8 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between pb-6 border-b border-zinc-100">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 text-xs font-bold border border-blue-200 mb-2">
              <span>🛡️</span> Razorpay Sandbox (Test Mode)
            </div>
            <h1 className="text-2xl font-black text-zinc-900">Snehith Travels</h1>
            <p className="text-xs text-zinc-500 mt-0.5">Secure Hosted Payment Link</p>
          </div>

          {booking && (
            <div className="text-right">
              <span className="text-xs text-zinc-400">Total Due</span>
              <div className="text-3xl font-black text-zinc-900">₹{booking.total_amount}</div>
            </div>
          )}
        </div>

        {error && (
          <div className="my-4 p-4 rounded-xl bg-amber-50 text-amber-800 text-xs border border-amber-200 font-medium">
            {error}
          </div>
        )}

        {/* Booking Details Summary */}
        {booking && (
          <div className="my-6 p-5 rounded-2xl bg-zinc-50 border border-zinc-100 space-y-2.5 text-xs text-zinc-600">
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-500">Booking Reference</span>
              <span className="font-mono font-bold text-zinc-900">{booking.booking_reference}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-500">Route</span>
              <span className="font-semibold text-zinc-800">
                {booking.origin} → {booking.destination}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-500">Journey Date</span>
              <span className="font-semibold text-zinc-800">
                {booking.journey_date} ({booking.departure_time})
              </span>
            </div>
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-500">Seats</span>
              <span className="font-bold text-blue-600">{booking.seat_numbers.join(', ')}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-semibold text-zinc-500">Passenger(s)</span>
              <span className="font-semibold text-zinc-800">
                {booking.passengers.map((p) => p.name).join(', ')}
              </span>
            </div>
          </div>
        )}

        {/* STATE 1: PAID */}
        {isPaid && (
          <div className="my-6 p-6 rounded-2xl bg-emerald-50 border border-emerald-200 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xl font-bold mx-auto">
              ✓
            </div>
            <h2 className="text-lg font-black text-emerald-900">Payment Successful</h2>
            <p className="text-xs text-emerald-700">
              Booking confirmed! Reference:{' '}
              <span className="font-mono font-bold">{booking?.booking_reference}</span>
            </p>

            <div className="pt-2">
              <Link
                href={`/booking/${booking?.booking_reference}`}
                className="inline-block px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md transition"
              >
                View Digital Ticket & QR Code →
              </Link>
            </div>
          </div>
        )}

        {/* STATE 2: FAILED */}
        {isFailed && (
          <div className="my-6 p-6 rounded-2xl bg-red-50 border border-red-200 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-red-600 text-white flex items-center justify-center text-xl font-bold mx-auto">
              ✗
            </div>
            <h2 className="text-lg font-black text-red-900">Payment Failed</h2>
            <p className="text-xs text-red-700">
              Your test transaction was not completed. Please try generating a new payment link.
            </p>

            <button
              type="button"
              onClick={handleGenerateLink}
              disabled={generatingLink}
              className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs transition"
            >
              {generatingLink ? 'Regenerating...' : 'Try Payment Again'}
            </button>
          </div>
        )}

        {/* STATE 3: EXPIRED */}
        {isExpired && (
          <div className="my-6 p-6 rounded-2xl bg-amber-50 border border-amber-200 text-center space-y-3">
            <div className="text-2xl">⌛</div>
            <h2 className="text-lg font-black text-amber-900">Payment Link Expired</h2>
            <p className="text-xs text-amber-700">
              The 10-minute reservation window expired and the held seats have been released.
            </p>
            <Link
              href="/"
              className="inline-block px-5 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white font-bold text-xs transition"
            >
              Search Buses Again
            </Link>
          </div>
        )}

        {/* STATE 4: PENDING PAYMENT */}
        {isPending && (
          <div className="space-y-4">
            {payment?.payment_url && (
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={handlePayNow}
                  className="w-full py-4 px-6 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-sm shadow-md transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>💳</span> Pay ₹{booking?.total_amount} via Razorpay Hosted Page
                </button>

                <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1 px-1">
                  <span>Provider: Razorpay Sandbox</span>
                  <button
                    type="button"
                    disabled={verifying}
                    onClick={handleCheckStatus}
                    className="font-bold text-blue-600 hover:underline cursor-pointer"
                  >
                    {verifying ? 'Verifying with backend...' : 'I have completed payment (Verify)'}
                  </button>
                </div>
              </div>
            )}

            <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200 text-[11px] text-zinc-600 space-y-1 mt-4">
              <div className="font-bold text-zinc-800">ℹ️ Secure Payment with Razorpay:</div>
              <p>
                Click <strong>Pay via Razorpay Hosted Page</strong> above to complete your booking securely using UPI, Credit/Debit Cards, Net Banking, or Wallets. Once payment is confirmed, your booking will be confirmed automatically and your digital boarding pass will be generated.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
