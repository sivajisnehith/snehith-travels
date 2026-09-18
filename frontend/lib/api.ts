import {
  AuthResponse,
  User,
  Bus,
  BusSeatsResponse,
  SeatRecommendationResponse,
  SeatHoldResponse,
  BookingResponse,
  BookingDetail,
  PaymentResponse,
  DigitalTicket,
  Route,
  BusCreateInput,
} from '@/types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL !== undefined
    ? process.env.NEXT_PUBLIC_API_URL
    : process.env.NODE_ENV === 'production'
    ? ''
    : 'http://localhost:8000';

export function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('snehith_token');
  }
  return null;
}

export function setAuthToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('snehith_token', token);
  }
}

export function removeAuthToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('snehith_token');
    localStorage.removeItem('snehith_user');
  }
}

export function getStoredUser(): User | null {
  if (typeof window !== 'undefined') {
    const data = localStorage.getItem('snehith_user');
    if (data) {
      try {
        return JSON.parse(data);
      } catch {
        return null;
      }
    }
  }
  return null;
}

export function setStoredUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('snehith_user', JSON.stringify(user));
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getAuthToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  async register(data: { name: string; email: string; password: string; phone?: string }): Promise<User> {
    return request<User>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async login(data: { email: string; password: string }): Promise<AuthResponse> {
    const res = await request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      setAuthToken(res.access_token);
      setStoredUser(res.user);
    }
    return res;
  },

  async getMe(): Promise<User> {
    const user = await request<User>('/api/auth/me');
    setStoredUser(user);
    return user;
  },

  logout(): void {
    removeAuthToken();
  },

  // Routes & Buses
  async getRoutes(): Promise<Route[]> {
    return request<Route[]>('/api/buses/routes');
  },

  async searchBuses(params: {
    from: string;
    to: string;
    journey_date: string;
    passengers?: number;
    bus_type?: string;
    is_ac?: boolean;
    seat_type?: string;
    price_min?: number;
    price_max?: number;
    departure_time?: string;
    sort_by?: string;
  }): Promise<Bus[]> {
    const query = new URLSearchParams();
    query.set('from', params.from);
    query.set('to', params.to);
    query.set('journey_date', params.journey_date);
    if (params.passengers) query.set('passengers', params.passengers.toString());
    if (params.bus_type) query.set('bus_type', params.bus_type);
    if (params.is_ac !== undefined) query.set('is_ac', params.is_ac.toString());
    if (params.seat_type) query.set('seat_type', params.seat_type);
    if (params.price_min) query.set('price_min', params.price_min.toString());
    if (params.price_max) query.set('price_max', params.price_max.toString());
    if (params.departure_time) query.set('departure_time', params.departure_time);
    if (params.sort_by) query.set('sort_by', params.sort_by);

    return request<Bus[]>(`/api/buses/search?${query.toString()}`);
  },

  async getBus(busId: number, journey_date?: string): Promise<Bus> {
    const query = journey_date ? `?journey_date=${journey_date}` : '';
    return request<Bus>(`/api/buses/${busId}${query}`);
  },

  async getBusSeats(busId: number, journey_date: string): Promise<BusSeatsResponse> {
    return request<BusSeatsResponse>(`/api/buses/${busId}/seats?journey_date=${journey_date}`);
  },

  async recommendSeats(
    busId: number,
    preferences: {
      journey_date: string;
      cheapest?: boolean;
      window?: boolean;
      aisle?: boolean;
      lower?: boolean;
      upper?: boolean;
      front?: boolean;
      rear?: boolean;
      sleeper?: boolean;
      seater?: boolean;
      maximum_budget?: number;
      limit?: number;
    }
  ): Promise<SeatRecommendationResponse> {
    return request<SeatRecommendationResponse>(`/api/buses/${busId}/recommend-seats`, {
      method: 'POST',
      body: JSON.stringify(preferences),
    });
  },

  // Seats Hold
  async holdSeats(busId: number, seatIds: number[], journey_date: string): Promise<SeatHoldResponse> {
    return request<SeatHoldResponse>('/api/seats/hold', {
      method: 'POST',
      body: JSON.stringify({
        bus_id: busId,
        seat_ids: seatIds,
        journey_date,
      }),
    });
  },

  async releaseSeats(holdToken: string, seatIds?: number[]): Promise<{ success: boolean; message: string }> {
    return request<{ success: boolean; message: string }>('/api/seats/hold', {
      method: 'DELETE',
      body: JSON.stringify({
        hold_token: holdToken,
        seat_ids: seatIds,
      }),
    });
  },

  // Bookings
  async createBooking(data: {
    bus_id: number;
    journey_date: string;
    boarding_point: string;
    dropping_point: string;
    passengers: {
      seat_id: number;
      name: string;
      age: number;
      gender: string;
    }[];
    hold_token?: string;
  }): Promise<BookingResponse> {
    return request<BookingResponse>('/api/bookings', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getBookings(): Promise<BookingDetail[]> {
    return request<BookingDetail[]>('/api/bookings');
  },

  async getBooking(bookingIdOrRef: string): Promise<BookingDetail> {
    return request<BookingDetail>(`/api/bookings/${bookingIdOrRef}`);
  },

  async cancelBooking(bookingId: number): Promise<{ booking_id: number; status: string; message: string }> {
    return request<{ booking_id: number; status: string; message: string }>(`/api/bookings/${bookingId}/cancel`, {
      method: 'POST',
    });
  },

  // Payments
  async createPayment(bookingId: number, paymentMethod: string = 'RAZORPAY_PAYMENT_LINK'): Promise<PaymentResponse> {
    return request<PaymentResponse>('/api/payments', {
      method: 'POST',
      body: JSON.stringify({
        booking_id: bookingId,
        payment_method: paymentMethod,
      }),
    });
  },

  async getPayment(paymentId: number): Promise<PaymentResponse> {
    return request<PaymentResponse>(`/api/payments/${paymentId}`);
  },

  async mockPaymentSuccess(paymentId: number): Promise<{ status: string; message: string; booking_reference: string; booking_status: string }> {
    return request(`/api/payments/${paymentId}/mock-success`, {
      method: 'POST',
    });
  },

  async mockPaymentFailure(paymentId: number): Promise<{ status: string; message: string; booking_reference: string; booking_status: string }> {
    return request(`/api/payments/${paymentId}/mock-failure`, {
      method: 'POST',
    });
  },

  async deliverPaymentLink(data: {
    booking_id?: number;
    payment_id?: number;
    channel?: string;
    destination: string;
  }): Promise<{
    delivery_status: string;
    channel: string;
    destination: string;
    payment_url: string;
    booking_reference: string;
    amount: number;
    message: string;
    message_id?: string;
  }> {
    return request('/api/payments/deliver-link', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Tickets
  async getTicket(bookingIdOrRef: string): Promise<DigitalTicket> {
    return request<DigitalTicket>(`/api/tickets/${bookingIdOrRef}`);
  },

  // Admin Fleet Management
  async getAllBusesAdmin(): Promise<Bus[]> {
    return request<Bus[]>('/api/buses/admin/all');
  },

  async createBus(busData: BusCreateInput): Promise<Bus> {
    return request<Bus>('/api/buses', {
      method: 'POST',
      body: JSON.stringify(busData),
    });
  },

  async deleteBus(busId: number): Promise<{ message: string }> {
    return request<{ message: string }>(`/api/buses/${busId}`, {
      method: 'DELETE',
    });
  },

  async seedFleetAdmin(): Promise<{ message: string; total_buses: number }> {
    return request<{ message: string; total_buses: number }>('/api/buses/admin/seed-fleet', {
      method: 'POST',
    });
  },

  async getAllBookingsAdmin(): Promise<BookingDetail[]> {
    return request<BookingDetail[]>('/api/bookings/admin/all');
  },
};
