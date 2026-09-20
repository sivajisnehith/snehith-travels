'use client';

import { useState } from 'react';
import { VOICE_BOT_CONFIG, VOICE_BOT_LINES } from '@/lib/voiceBot';

interface VoiceBotModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function VoiceBotModal({ isOpen, onClose }: VoiceBotModalProps) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-xl bg-white rounded-3xl shadow-2xl border border-zinc-100 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with decorative gradient */}
        <div className="relative bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 text-white p-6 sm:p-7 shrink-0">
          <button
            onClick={onClose}
            className="absolute top-5 right-5 w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white flex items-center justify-center transition text-sm font-bold cursor-pointer"
            aria-label="Close"
          >
            ✕
          </button>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur border border-white/20 flex items-center justify-center text-2xl shadow-inner">
              🤖
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300 text-xs font-semibold border border-emerald-400/30 mb-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                Live Voice Agent
              </div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tight">
                Saarthi AI Phone Bot
              </h2>
            </div>
          </div>
          <p className="text-xs sm:text-sm text-blue-100 mt-1">
            Dial in from any phone to search buses, select seats, and book tickets through natural voice conversation.
          </p>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-zinc-800 text-sm">
          {/* Step 1 & 2: Available Phone Lines */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-zinc-600 flex items-center gap-1.5">
                <span>📞</span> Select a Line to Call &amp; Enter PIN
              </h3>
              <span className="text-[11px] text-zinc-500 font-medium">Available 24/7</span>
            </div>

            {VOICE_BOT_LINES.map((line) => {
              const isMain = line.isPrimary;
              return (
                <div
                  key={line.id}
                  className={`p-4 rounded-2xl border transition-all ${
                    isMain
                      ? 'bg-blue-50/90 border-blue-200 shadow-xs ring-1 ring-blue-500/20'
                      : 'bg-zinc-50/90 border-zinc-200'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-md ${
                          isMain
                            ? 'bg-blue-600 text-white'
                            : 'bg-zinc-200 text-zinc-700'
                        }`}
                      >
                        {line.badge}
                      </span>
                      <span className="text-xs font-bold text-zinc-900">{line.name}</span>
                    </div>
                    {isMain && (
                      <span className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 inline-block" /> Active
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-zinc-500 mb-3">{line.description}</p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 border-t border-zinc-200/60">
                    {/* Number */}
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">
                        Phone Number
                      </span>
                      <div className="flex items-center justify-between gap-2 bg-white px-3 py-2 rounded-xl border border-zinc-200">
                        <span className="font-mono font-black text-zinc-900 text-base">
                          {line.displayNumber}
                        </span>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => copyToClipboard(line.number, `num_${line.id}`)}
                            className="px-2 py-1 rounded bg-zinc-100 hover:bg-zinc-200 text-zinc-700 text-[11px] font-semibold transition"
                            title="Copy phone number"
                          >
                            {copiedKey === `num_${line.id}` ? '✓' : 'Copy'}
                          </button>
                          <a
                            href={`tel:${line.number}`}
                            className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-bold transition flex items-center gap-1"
                          >
                            Call
                          </a>
                        </div>
                      </div>
                    </div>

                    {/* PIN */}
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase text-purple-700 tracking-wider">
                        Dial-Pad PIN / Password
                      </span>
                      <div className="flex items-center justify-between gap-2 bg-white px-3 py-2 rounded-xl border border-purple-200">
                        <code className="font-mono font-black text-purple-900 text-base tracking-wider">
                          {line.pin}
                        </code>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(line.pin, `pin_${line.id}`)}
                          className="px-2.5 py-1 rounded bg-purple-100 hover:bg-purple-200 text-purple-800 text-[11px] font-bold transition"
                        >
                          {copiedKey === `pin_${line.id}` ? '✓ Copied' : 'Copy PIN'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Step 3: Talk & Book */}
          <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-200 space-y-1.5">
            <span className="text-xs font-extrabold uppercase tracking-wider text-zinc-700 flex items-center gap-1.5">
              <span className="w-5 h-5 rounded-full bg-zinc-700 text-white flex items-center justify-center text-[10px]">
                3
              </span>
              Speak Naturally
            </span>
            <p className="text-xs text-zinc-600 leading-relaxed">
              Speak in <strong>English, Hindi, or Telugu</strong>. Saarthi will search available buses, check live seats, hold your seat, and generate your booking in real time.
            </p>
          </div>

          {/* Critical Testing Restrictions & Delivery Rules */}
          <div className="space-y-2.5 pt-1">
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-zinc-500">
              Testing Delivery Notice
            </h4>

            {/* WhatsApp Restriction Box */}
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 flex gap-3 items-start">
              <span className="text-lg leading-none shrink-0 mt-0.5">⚠️</span>
              <div className="text-xs space-y-1">
                <p className="font-bold text-amber-900">
                  WhatsApp Delivery Restriction (Meta Cloud API Test Mode)
                </p>
                <p className="text-amber-800 leading-relaxed">
                  Due to Meta API sandbox restrictions, the Razorpay payment link and the digital WhatsApp ticket PDF will{' '}
                  <strong className="underline">only be delivered to {VOICE_BOT_CONFIG.restrictedWhatsAppDisplay}</strong>.
                  Please use or test with this WhatsApp number during voice bookings.
                </p>
              </div>
            </div>

            {/* Email Delivery Available Box */}
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 flex gap-3 items-start">
              <span className="text-lg leading-none shrink-0 mt-0.5">✉️</span>
              <div className="text-xs space-y-1">
                <p className="font-bold text-emerald-900">
                  Email Ticket Delivery Works for Everyone
                </p>
                <p className="text-emerald-800 leading-relaxed">
                  <strong>Any valid email address</strong> can receive the confirmed ticket PDF! Simply provide your email to Saarthi during the call.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-zinc-50 border-t border-zinc-200 flex items-center justify-between gap-3 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl border border-zinc-300 text-zinc-700 hover:bg-zinc-100 text-xs font-semibold transition cursor-pointer"
          >
            Close
          </button>
          <a
            href={`tel:${VOICE_BOT_CONFIG.phoneNumber}`}
            className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-md transition flex items-center gap-1.5"
          >
            <span>📞</span> Call Main Line ({VOICE_BOT_CONFIG.displayPhoneNumber})
          </a>
        </div>
      </div>
    </div>
  );
}
