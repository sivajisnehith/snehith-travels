'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, getAuthToken, getStoredUser } from '@/lib/api';
import { Bus, BusCreateInput, User, BookingDetail } from '@/types';

const POPULAR_CITIES = ['Hyderabad', 'Vijayawada', 'Bangalore', 'Chennai', 'Visakhapatnam'];

const COMMON_OPERATORS = [
  'Snehith Travels',
  'Orange Tours & Travels',
  'Kaveri Travels',
  'IntrCity SmartBus',
  'Zingbus Plus',
  'TSRTC Garuda Plus',
  'APSRTC Amaravathi',
  'Morning Star Travels',
  'VRL Travels',
  'Greenline Travels',
];

const AMENITY_OPTIONS = [
  'AC',
  'WiFi',
  'Charging Port',
  'Blanket',
  'Pillow',
  'Water Bottle',
  'Snack Pack',
  'Reading Light',
  'Movie Screen',
  'Live GPS',
];

export default function AdminFleetPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [buses, setBuses] = useState<Bus[]>([]);
  const [bookings, setBookings] = useState<BookingDetail[]>([]);
  const [activeTab, setActiveTab] = useState<'fleet' | 'bookings'>('fleet');
  const [loading, setLoading] = useState(true);
  const [loadingBookings, setLoadingBookings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Search & Filter (Fleet)
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterTime, setFilterTime] = useState('all');

  // Search & Filter (Bookings)
  const [bookingSearchQuery, setBookingSearchQuery] = useState('');
  const [bookingStatusFilter, setBookingStatusFilter] = useState('all');

  // Deploy Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState<BusCreateInput>({
    origin: 'Hyderabad',
    destination: 'Bangalore',
    operator: 'Snehith Travels',
    bus_name: '',
    bus_type: 'AC Sleeper',
    is_ac: true,
    is_sleeper: true,
    departure_time: '21:30',
    arrival_time: '06:30',
    starting_price: 1199,
    rating: 4.8,
    amenities: ['AC', 'WiFi', 'Charging Port', 'Blanket', 'Water Bottle'],
    boarding_points: ['Gachibowli (21:00)', 'Ameerpet (21:30)', 'LB Nagar (22:15)'],
    dropping_points: ['Hebbal (05:45)', 'Majestic (06:15)', 'Silk Board (06:30)'],
  });

  const [boardingInput, setBoardingInput] = useState('Gachibowli (21:00), Ameerpet (21:30), LB Nagar (22:15)');
  const [droppingInput, setDroppingInput] = useState('Hebbal (05:45), Majestic (06:15), Silk Board (06:30)');

  useEffect(() => {
    const token = getAuthToken();
    const storedUser = getStoredUser();

    if (!token || !storedUser) {
      router.push('/login?redirect=/admin');
      return;
    }

    if (storedUser.role !== 'admin') {
      router.push('/dashboard');
      return;
    }

    setUser(storedUser);
    loadFleet();
    loadBookings();
  }, []);

  const loadFleet = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAllBusesAdmin();
      setBuses(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch fleet inventory.');
    } finally {
      setLoading(false);
    }
  };

  const loadBookings = async () => {
    setLoadingBookings(true);
    try {
      const data = await api.getAllBookingsAdmin();
      setBookings(data);
    } catch (err: any) {
      console.error('Failed to load platform bookings:', err);
    } finally {
      setLoadingBookings(false);
    }
  };

  const handleCancelBooking = async (bookingId: number) => {
    if (!confirm('Are you sure you want to cancel this booking? This will release the seats.')) {
      return;
    }
    try {
      await api.cancelBooking(bookingId);
      setSuccessMsg('Booking cancelled successfully.');
      loadBookings();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to cancel booking.');
    }
  };

  const handleDecommission = async (busId: number, busName: string) => {
    if (!confirm(`Are you sure you want to decommission "${busName}" (ID: ${busId}) from service?`)) {
      return;
    }
    try {
      await api.deleteBus(busId);
      setSuccessMsg(`Bus "${busName}" successfully decommissioned.`);
      setBuses((prev) => prev.filter((b) => b.bus_id !== busId));
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Could not decommission bus.');
    }
  };

  const handleSeedFleet = async () => {
    if (!confirm('This will seed/refresh the comprehensive AbhiBus 24-hour fleet across all 12 major routes. Proceed?')) {
      return;
    }
    setLoading(true);
    try {
      const res = await api.seedFleetAdmin();
      setSuccessMsg(`Fleet successfully synced! Total active buses: ${res.total_buses}`);
      loadFleet();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to seed fleet.');
      setLoading(false);
    }
  };

  const handleAmenityToggle = (amenity: string) => {
    setFormData((prev) => {
      const exists = prev.amenities.includes(amenity);
      const updated = exists
        ? prev.amenities.filter((a) => a !== amenity)
        : [...prev.amenities, amenity];
      return { ...prev, amenities: updated };
    });
  };

  const handleTypeChange = (type: string) => {
    const isSleeper = type.includes('Sleeper');
    const isAc = !type.includes('Non-AC');
    setFormData((prev) => ({
      ...prev,
      bus_type: type,
      is_sleeper: isSleeper,
      is_ac: isAc,
    }));
  };

  const handleDeploySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.bus_name.trim()) {
      alert('Please provide a bus service name.');
      return;
    }

    setSubmitting(true);
    try {
      const boardingArr = boardingInput
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      const droppingArr = droppingInput
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const payload: BusCreateInput = {
        ...formData,
        boarding_points: boardingArr.length > 0 ? boardingArr : ['Main Stand'],
        dropping_points: droppingArr.length > 0 ? droppingArr : ['City Drop'],
      };

      const newBus = await api.createBus(payload);
      setSuccessMsg(`🚀 Bus "${newBus.bus_name}" deployed successfully with all seats created!`);
      setIsModalOpen(false);
      // Reset form
      setFormData((prev) => ({
        ...prev,
        bus_name: '',
      }));
      loadFleet();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to deploy bus.');
    } finally {
      setSubmitting(false);
    }
  };

  // Filtered buses
  const filteredBuses = buses.filter((b) => {
    const matchesQuery =
      searchQuery === '' ||
      b.bus_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.operator.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.origin.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.destination.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType =
      filterType === 'all' ||
      (filterType === 'sleeper' && b.bus_type.includes('Sleeper')) ||
      (filterType === 'seater' && (b.bus_type.includes('Seater') || b.bus_type.includes('Semi-sleeper')));

    let matchesTime = true;
    if (filterTime !== 'all') {
      const depHour = parseInt(b.departure_time.split(':')[0], 10);
      if (filterTime === 'morning') matchesTime = depHour >= 5 && depHour < 12;
      else if (filterTime === 'afternoon') matchesTime = depHour >= 12 && depHour < 17;
      else if (filterTime === 'evening') matchesTime = depHour >= 17 && depHour < 21;
      else if (filterTime === 'night') matchesTime = depHour >= 21 || depHour < 5;
    }

    return matchesQuery && matchesType && matchesTime;
  });

  // Filtered bookings
  const filteredBookings = bookings.filter((b) => {
    const q = bookingSearchQuery.toLowerCase();
    const matchesQuery =
      q === '' ||
      b.booking_reference.toLowerCase().includes(q) ||
      b.bus_name.toLowerCase().includes(q) ||
      b.operator.toLowerCase().includes(q) ||
      b.origin.toLowerCase().includes(q) ||
      b.destination.toLowerCase().includes(q) ||
      b.passengers.some((p) => p.name.toLowerCase().includes(q)) ||
      b.seat_numbers.some((s) => s.toLowerCase().includes(q));

    const matchesStatus =
      bookingStatusFilter === 'all' || b.status === bookingStatusFilter;

    return matchesQuery && matchesStatus;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 mb-6 border-b border-zinc-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs font-bold uppercase tracking-wider">
              Administrator Console
            </span>
          </div>
          <h1 className="text-3xl font-black text-zinc-900 mt-1">Fleet Management Hub</h1>
          <p className="text-xs text-zinc-500 mt-0.5">
            Deploy scheduled buses across any hour, configure seat layouts, manage routes, and inspect real-time platform inventory.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSeedFleet}
            className="px-4 py-2.5 rounded-xl border border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-700 font-bold text-xs shadow-xs transition flex items-center gap-1.5"
            title="Sync comprehensive 24-hour AbhiBus schedules"
          >
            <span>⚡</span> 1-Click Sync AbhiBus Fleet
          </button>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition flex items-center gap-1.5"
          >
            <span>+</span> Deploy New Bus Service
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200 flex items-center gap-2 shadow-xs">
          <span>✅</span> {successMsg}
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-50 text-red-700 text-xs font-semibold border border-red-200 flex items-center gap-2 shadow-xs">
          <span>⚠️</span> {error}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-3 mb-8">
        <button
          type="button"
          onClick={() => setActiveTab('fleet')}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'fleet'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'bg-white text-zinc-600 border border-zinc-200 hover:bg-zinc-50'
          }`}
        >
          <span>🚌</span> Fleet Inventory & Schedules ({buses.length})
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab('bookings');
            loadBookings();
          }}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'bookings'
              ? 'bg-purple-700 text-white shadow-xs'
              : 'bg-white text-purple-700 border border-purple-200 hover:bg-purple-50'
          }`}
        >
          <span>🎫</span> All Platform Bookings & Travelers ({bookings.length})
        </button>
      </div>

      {activeTab === 'fleet' ? (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Total Buses</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">{buses.length}</div>
              <span className="text-[11px] text-emerald-600 font-semibold">Active in fleet</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Active Routes</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">
                {new Set(buses.map((b) => `${b.origin}->${b.destination}`)).size}
              </div>
              <span className="text-[11px] text-blue-600 font-semibold">Connecting South India</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Operators</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">
                {new Set(buses.map((b) => b.operator)).size}
              </div>
              <span className="text-[11px] text-purple-600 font-semibold">Live travel brands</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Total Seats Managed</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">
                {buses.reduce((acc, b) => acc + (b.total_seats || 30), 0)}
              </div>
              <span className="text-[11px] text-zinc-500 font-semibold">Pre-configured layouts</span>
            </div>
          </div>

          {/* Filter and Search Bar */}
          <div className="bg-white p-4 rounded-2xl border border-zinc-200 mb-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
            <div className="flex-1 min-w-[240px]">
              <input
                type="text"
                placeholder="Search by bus name, operator, or city..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-2 text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-blue-600"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Type Filter */}
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs font-semibold text-zinc-700"
              >
                <option value="all">All Bus Types</option>
                <option value="sleeper">Sleepers (2+1)</option>
                <option value="seater">Seaters / Semi-Sleepers</option>
              </select>

              {/* Time Filter */}
              <select
                value={filterTime}
                onChange={(e) => setFilterTime(e.target.value)}
                className="bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs font-semibold text-zinc-700"
              >
                <option value="all">Any Departure Time</option>
                <option value="morning">🌅 Morning (05:00 - 12:00)</option>
                <option value="afternoon">☀️ Afternoon (12:00 - 17:00)</option>
                <option value="evening">🌆 Evening (17:00 - 21:00)</option>
                <option value="night">🌙 Night (21:00 - 05:00)</option>
              </select>
            </div>
          </div>

          {/* Bus Inventory Grid */}
          {loading ? (
            <div className="p-16 text-center text-sm text-zinc-500">Loading fleet inventory...</div>
          ) : filteredBuses.length === 0 ? (
            <div className="bg-white rounded-2xl border border-zinc-200 p-12 text-center space-y-3">
              <div className="text-3xl">🚌</div>
              <h3 className="text-base font-bold text-zinc-800">No buses matching your filters</h3>
              <p className="text-xs text-zinc-500">Try clearing your search query or click "Deploy New Bus Service".</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredBuses.map((bus) => (
                <div
                  key={bus.bus_id}
                  className="bg-white rounded-2xl border border-zinc-200 p-5 shadow-xs hover:border-zinc-300 transition flex flex-col justify-between"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 pb-3 border-b border-zinc-100">
                      <div>
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                          {bus.operator}
                        </span>
                        <h3 className="text-base font-black text-zinc-900 leading-snug">{bus.bus_name}</h3>
                      </div>
                      <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 text-[11px] font-bold shrink-0">
                        {bus.bus_type}
                      </span>
                    </div>

                    {/* Route & Timings */}
                    <div className="py-3 space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold text-zinc-800">
                        <span>{bus.origin}</span>
                        <span className="text-zinc-400 font-normal">→</span>
                        <span>{bus.destination}</span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-zinc-500">
                        <span className="font-semibold text-zinc-700">Dep: {bus.departure_time}</span>
                        <span className="px-1.5 py-0.5 rounded-sm bg-zinc-100 text-[10px]">{bus.duration}</span>
                        <span className="font-semibold text-zinc-700">Arr: {bus.arrival_time}</span>
                      </div>

                      <div className="flex items-center justify-between pt-1">
                        <span className="text-xs font-black text-emerald-700">₹{bus.starting_price}</span>
                        <span className="text-xs font-bold text-zinc-600">★ {bus.rating}</span>
                        <span className="text-[11px] text-zinc-400">{bus.total_seats} seats</span>
                      </div>

                      {/* Amenities preview */}
                      {bus.amenities && bus.amenities.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {bus.amenities.slice(0, 3).map((a) => (
                            <span key={a} className="px-1.5 py-0.5 rounded-sm bg-zinc-100 text-[10px] text-zinc-600">
                              {a}
                            </span>
                          ))}
                          {bus.amenities.length > 3 && (
                            <span className="px-1.5 py-0.5 rounded-sm bg-zinc-100 text-[10px] text-zinc-400">
                              +{bus.amenities.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-zinc-100 flex items-center justify-between gap-2">
                    <Link
                      href={`/bus/${bus.bus_id}`}
                      className="px-3 py-1.5 rounded-lg border border-zinc-200 hover:bg-zinc-50 text-zinc-700 font-bold text-xs transition"
                    >
                      View Layout
                    </Link>
                    <button
                      type="button"
                      onClick={() => handleDecommission(bus.bus_id, bus.bus_name)}
                      className="px-3 py-1.5 rounded-lg text-red-600 hover:bg-red-50 text-xs font-bold transition"
                    >
                      Decommission
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <>
          {/* Bookings Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Total Reservations</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">{bookings.length}</div>
              <span className="text-[11px] text-zinc-500 font-semibold">Platform-wide</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Confirmed Bookings</span>
              <div className="text-2xl font-black text-emerald-600 mt-1">
                {bookings.filter((b) => b.status === 'CONFIRMED').length}
              </div>
              <span className="text-[11px] text-emerald-600 font-semibold">Paid & Ticketed</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Gross Platform Revenue</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">
                ₹{bookings.filter((b) => b.status === 'CONFIRMED').reduce((acc, b) => acc + b.total_amount, 0).toLocaleString('en-IN')}
              </div>
              <span className="text-[11px] text-purple-600 font-semibold">Captured revenue</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-zinc-200 shadow-xs">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Total Seats Booked</span>
              <div className="text-2xl font-black text-zinc-900 mt-1">
                {bookings.reduce((acc, b) => acc + (b.seat_numbers?.length || 0), 0)}
              </div>
              <span className="text-[11px] text-blue-600 font-semibold">Passengers served</span>
            </div>
          </div>

          {/* Bookings Filter and Search Bar */}
          <div className="bg-white p-4 rounded-2xl border border-zinc-200 mb-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
            <div className="flex-1 min-w-[240px]">
              <input
                type="text"
                placeholder="Search by passenger name, booking ref (e.g. ST-), bus name, or route..."
                value={bookingSearchQuery}
                onChange={(e) => setBookingSearchQuery(e.target.value)}
                className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-2 text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-purple-600"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <select
                value={bookingStatusFilter}
                onChange={(e) => setBookingStatusFilter(e.target.value)}
                className="bg-zinc-50 border border-zinc-200 rounded-xl px-3 py-2 text-xs font-semibold text-zinc-700"
              >
                <option value="all">All Statuses ({bookings.length})</option>
                <option value="CONFIRMED">CONFIRMED</option>
                <option value="PENDING_PAYMENT">PENDING_PAYMENT</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>

              <button
                type="button"
                onClick={loadBookings}
                disabled={loadingBookings}
                className="px-3.5 py-2 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-700 font-bold text-xs shadow-xs transition"
              >
                {loadingBookings ? 'Refreshing...' : '🔄 Refresh Bookings'}
              </button>
            </div>
          </div>

          {/* Bookings Content */}
          {loadingBookings ? (
            <div className="p-16 text-center text-sm text-zinc-500">Loading all platform bookings...</div>
          ) : filteredBookings.length === 0 ? (
            <div className="bg-white rounded-2xl border border-zinc-200 p-12 text-center space-y-3 shadow-xs">
              <div className="text-3xl">🎫</div>
              <h3 className="text-base font-bold text-zinc-800">No bookings found</h3>
              <p className="text-xs text-zinc-500">
                {bookings.length === 0
                  ? 'No customer has made a reservation yet. Platform bookings will automatically appear here in real time.'
                  : 'No bookings match your current search or filter criteria.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredBookings.map((b) => {
                const isConfirmed = b.status === 'CONFIRMED';
                const isPending = b.status === 'PENDING_PAYMENT';
                const isCancelled = b.status === 'CANCELLED';

                return (
                  <div
                    key={b.id}
                    className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-xs hover:border-purple-200 transition"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-100">
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-sm font-black text-zinc-900 bg-zinc-100 px-2.5 py-1 rounded-lg">
                            {b.booking_reference}
                          </span>
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                              isConfirmed
                                ? 'bg-emerald-100 text-emerald-800'
                                : isPending
                                ? 'bg-amber-100 text-amber-800'
                                : isCancelled
                                ? 'bg-red-100 text-red-800'
                                : 'bg-zinc-100 text-zinc-800'
                            }`}
                          >
                            {b.status}
                          </span>
                          <span className="text-[11px] text-zinc-400">
                            Booked on {new Date(b.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="text-xs font-semibold text-zinc-700 mt-1.5">
                          {b.operator} • <span className="font-bold text-zinc-900">{b.bus_name}</span> ({b.bus_type})
                        </div>
                      </div>

                      <div className="text-left sm:text-right">
                        <span className="text-xs text-zinc-400">Total Fare</span>
                        <div className="text-xl font-black text-zinc-900">₹{b.total_amount}</div>
                        {b.payment_status && (
                          <span className="text-[10px] font-bold text-zinc-500 uppercase">
                            Payment: {b.payment_status}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-4 text-xs">
                      <div>
                        <span className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider">Journey</span>
                        <div className="font-bold text-zinc-800 text-sm mt-0.5">
                          {b.origin} → {b.destination}
                        </div>
                        <div className="text-zinc-500 mt-0.5">
                          Date: <span className="font-semibold text-zinc-700">{b.journey_date}</span> ({b.departure_time})
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider">Seats & Boarding</span>
                        <div className="font-bold text-purple-700 text-sm mt-0.5">
                          Seats: {b.seat_numbers.join(', ')} ({b.seat_numbers.length} {b.seat_numbers.length === 1 ? 'seat' : 'seats'})
                        </div>
                        <div className="text-zinc-500 mt-0.5 truncate">
                          Boarding: {b.boarding_point}
                        </div>
                        {b.dropping_point && (
                          <div className="text-zinc-400 mt-0.5 truncate">
                            Dropping: {b.dropping_point}
                          </div>
                        )}
                      </div>

                      <div>
                        <span className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider">
                          Passengers ({b.passengers?.length || 0})
                        </span>
                        <div className="space-y-1 mt-1">
                          {b.passengers?.map((p, idx) => (
                            <div key={idx} className="flex items-center gap-1.5 text-zinc-700 font-medium">
                              <span className="font-bold text-zinc-900">{p.name}</span>
                              <span className="text-zinc-400">({p.age}y, {p.gender})</span>
                              <span className="text-[10px] font-bold px-1.5 py-0.2 bg-zinc-100 rounded-sm text-zinc-600">
                                {p.seat_number}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Actions Bar */}
                    <div className="pt-3 border-t border-zinc-100 flex flex-wrap items-center justify-between gap-3">
                      <div className="text-[11px] text-zinc-400">
                        Customer User ID: #{b.user_id}
                      </div>

                      <div className="flex items-center gap-2">
                        {isConfirmed && (
                          <Link
                            href={`/booking/${b.booking_reference}`}
                            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition"
                          >
                            View E-Ticket & QR
                          </Link>
                        )}

                        {isPending && (
                          <Link
                            href={`/payment?booking_id=${b.id}`}
                            className="px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs transition"
                          >
                            Complete Payment
                          </Link>
                        )}

                        {!isCancelled && (
                          <button
                            type="button"
                            onClick={() => handleCancelBooking(b.id)}
                            className="px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition"
                          >
                            Cancel Reservation
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Deploy Bus Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 sm:p-8 shadow-2xl border border-zinc-100 my-8">
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-zinc-100">
              <div>
                <h2 className="text-xl font-black text-zinc-900">Deploy New Bus Service</h2>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Creates the service and automatically generates the complete sleeper or seater layout.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleDeploySubmit} className="space-y-4 text-xs">
              {/* Route */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Origin City</label>
                  <input
                    type="text"
                    required
                    list="origin-cities"
                    value={formData.origin}
                    onChange={(e) => setFormData({ ...formData, origin: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                  <datalist id="origin-cities">
                    {POPULAR_CITIES.map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </div>

                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Destination City</label>
                  <input
                    type="text"
                    required
                    list="dest-cities"
                    value={formData.destination}
                    onChange={(e) => setFormData({ ...formData, destination: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                  <datalist id="dest-cities">
                    {POPULAR_CITIES.map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </div>
              </div>

              {/* Operator & Bus Name */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Operator Brand</label>
                  <input
                    type="text"
                    required
                    list="operators"
                    value={formData.operator}
                    onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                  <datalist id="operators">
                    {COMMON_OPERATORS.map((op) => (
                      <option key={op} value={op} />
                    ))}
                  </datalist>
                </div>

                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Bus Service Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Garuda Plus Volvo B11R"
                    value={formData.bus_name}
                    onChange={(e) => setFormData({ ...formData, bus_name: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>
              </div>

              {/* Type, Pricing, and Timings */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Bus Model / Type</label>
                  <select
                    value={formData.bus_type}
                    onChange={(e) => handleTypeChange(e.target.value)}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-semibold text-zinc-700"
                  >
                    <option value="AC Sleeper">AC Sleeper (2+1, 30 Seats)</option>
                    <option value="Non-AC Sleeper">Non-AC Sleeper (2+1, 30 Seats)</option>
                    <option value="Semi-sleeper">Semi-sleeper (2+2, 32 Seats)</option>
                    <option value="AC Seater">AC Seater (2+2, 32 Seats)</option>
                    <option value="Electric AC Luxury">Electric AC Luxury (2+1, 30 Seats)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Departure Time (24h)</label>
                  <input
                    type="time"
                    required
                    value={formData.departure_time}
                    onChange={(e) => setFormData({ ...formData, departure_time: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>

                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Arrival Time (24h)</label>
                  <input
                    type="time"
                    required
                    value={formData.arrival_time}
                    onChange={(e) => setFormData({ ...formData, arrival_time: e.target.value })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>
              </div>

              {/* Price & Rating */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Starting Ticket Price (₹)</label>
                  <input
                    type="number"
                    required
                    min={100}
                    max={5000}
                    value={formData.starting_price}
                    onChange={(e) => setFormData({ ...formData, starting_price: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-bold focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>

                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Rating (Stars)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="1.0"
                    max="5.0"
                    value={formData.rating}
                    onChange={(e) => setFormData({ ...formData, rating: parseFloat(e.target.value) || 4.5 })}
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-bold focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>
              </div>

              {/* Boarding and Dropping Points */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Boarding Points (Comma-separated)</label>
                  <input
                    type="text"
                    value={boardingInput}
                    onChange={(e) => setBoardingInput(e.target.value)}
                    placeholder="e.g. Miyapur (21:00), Ameerpet (21:30)"
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>

                <div>
                  <label className="block font-bold text-zinc-700 mb-1">Dropping Points (Comma-separated)</label>
                  <input
                    type="text"
                    value={droppingInput}
                    onChange={(e) => setDroppingInput(e.target.value)}
                    placeholder="e.g. Hebbal (05:45), Majestic (06:15)"
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-3.5 py-2.5 font-medium focus:ring-2 focus:ring-blue-600 focus:outline-hidden"
                  />
                </div>
              </div>

              {/* Amenities */}
              <div>
                <label className="block font-bold text-zinc-700 mb-2">Amenities Included</label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {AMENITY_OPTIONS.map((a) => {
                    const isChecked = formData.amenities.includes(a);
                    return (
                      <button
                        type="button"
                        key={a}
                        onClick={() => handleAmenityToggle(a)}
                        className={`px-3 py-2 rounded-xl text-left font-semibold border transition ${
                          isChecked
                            ? 'bg-blue-50 text-blue-700 border-blue-300'
                            : 'bg-zinc-50 text-zinc-600 border-zinc-200 hover:bg-zinc-100'
                        }`}
                      >
                        {isChecked ? '✓ ' : '+ '}
                        {a}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Form Buttons */}
              <div className="pt-4 border-t border-zinc-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2.5 rounded-xl border border-zinc-200 text-zinc-600 font-bold hover:bg-zinc-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold transition shadow-sm"
                >
                  {submitting ? 'Deploying Bus & Seats...' : '🚀 Deploy Bus to Fleet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
