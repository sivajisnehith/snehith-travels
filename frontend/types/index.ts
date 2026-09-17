export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Route {
  id: number;
  origin: string;
  destination: string;
  distance_km: number;
  estimated_duration_hours: number;
}

export interface Bus {
  bus_id: number;
  operator: string;
  bus_name: string;
  bus_type: string;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  starting_price: number;
  available_seats: number;
  total_seats: number;
  amenities: string[];
  rating: number;
  boarding_points: string[];
  dropping_points: string[];
}

export interface Seat {
  id: number;
  seat_number: string;
  row: number;
  column: number;
  seat_type: 'sleeper' | 'seater';
  window: boolean;
  aisle: boolean;
  upper_lower: 'lower' | 'upper' | 'seater';
  front_rear: 'front' | 'middle' | 'rear';
  price: number;
  status: 'available' | 'held' | 'booked';
}

export interface BusSeatsResponse {
  bus_id: number;
  bus_name: string;
  bus_type: string;
  journey_date: string;
  total_seats: number;
  available_seats: number;
  seats: Seat[];
}

export interface RankedSeat {
  seat_id: number;
  seat_number: string;
  score: number;
  reasons: string[];
  price: number;
  seat_type: string;
  upper_lower: string;
  window: boolean;
  aisle: boolean;
  front_rear: string;
}

export interface SeatRecommendationResponse {
  bus_id: number;
  journey_date: string;
  recommended_seats: RankedSeat[];
}

export interface SeatHoldResponse {
  hold_token: string;
  bus_id: number;
  journey_date: string;
  held_seats: {
    seat_id: number;
    seat_number: string;
    price: number;
  }[];
  expires_at: string;
  duration_minutes: number;
  message: string;
}

export interface PassengerInput {
  seat_id: number;
  seat_number: string;
  name: string;
  age: number;
  gender: 'M' | 'F' | 'Other';
}

export interface BookingResponse {
  id: number;
  booking_reference: string;
  user_id: number;
  bus_id: number;
  journey_date: string;
  boarding_point: string;
  dropping_point: string;
  total_amount: number;
  status: string;
  created_at: string;
  updated_at: string;
  seat_numbers: string[];
}

export interface PassengerDetail {
  id: number;
  seat_id: number;
  seat_number: string;
  name: string;
  age: number;
  gender: string;
}

export interface BookingDetail extends BookingResponse {
  bus_name: string;
  operator: string;
  bus_type: string;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  passengers: PassengerDetail[];
  payment_status?: string;
  payment_id?: number;
}

export interface PaymentResponse {
  id: number;
  payment_id?: number;
  booking_id: number;
  booking_reference: string;
  amount: number;
  currency?: string;
  payment_url?: string;
  provider?: string;
  provider_payment_link_id?: string;
  provider_payment_id?: string;
  payment_method: string;
  transaction_reference: string;
  status: string;
  expires_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface DigitalTicket {
  booking_reference: string;
  booking_id: number;
  status: string;
  bus_name: string;
  operator: string;
  bus_type: string;
  origin: string;
  destination: string;
  journey_date: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  boarding_point: string;
  dropping_point: string;
  passengers: {
    name: string;
    age: number;
    gender: string;
    seat_number: string;
  }[];
  seats: string[];
  total_amount: number;
  qr_code: string;
  qr_content: string;
}

export interface BusCreateInput {
  origin: string;
  destination: string;
  operator: string;
  bus_name: string;
  bus_type: string;
  is_ac: boolean;
  is_sleeper: boolean;
  departure_time: string;
  arrival_time: string;
  duration?: string;
  starting_price: number;
  rating?: number;
  amenities: string[];
  boarding_points: string[];
  dropping_points: string[];
}
