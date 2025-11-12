// API service for Python backend integration
// Normalize base URL: ensure it contains the `/api` prefix and no trailing slash
const RAW_API = import.meta.env.VITE_API_URL || 'http://localhost:5000';
const API_BASE_URL = RAW_API.replace(/\/$/, '') + '/api';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'passenger' | 'company' | 'admin';
  phone?: string;
}

export interface Schedule {
  id: string;
  departure_time: string;
  arrival_time: string;
  price: number;
  available_seats: number;
  bus: {
    bus_number: string;
    bus_type: string;
    amenities: string[];
    company: {
      name: string;
      logo_url: string | null;
    };
  };
  route: {
    origin: string;
    destination: string;
    distance_km: number;
    estimated_duration_minutes: number;
  };
}

export interface Booking {
  id: string;
  booking_reference: string;
  seat_number: number;
  status: string;
  created_at: string;
  passenger_name: string;
  passenger_phone: string;
  passenger_email: string;
  schedule: Schedule;
}

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // If backend uses session cookies (flask-login), include credentials
    const config: RequestInit = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication
  async login(email: string, password: string): Promise<any> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(userData: {
    email: string;
    password: string;
    full_name: string;
    role: 'passenger' | 'company';
    phone?: string;
  }): Promise<any> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // Schedules and Search
  async searchSchedules(params: {
    origin: string;
    destination: string;
    date: string;
  }): Promise<Schedule[]> {
    // Backend exposes search under GET /api/search/schedules
    const qs = new URLSearchParams();
    if (params.origin) qs.set('origin', params.origin);
    if (params.destination) qs.set('destination', params.destination);
    if (params.date) qs.set('date', params.date);

    const queryString = qs.toString();
    const endpoint = `/search/schedules${queryString ? `?${queryString}` : ''}`;
    const resp: any = await this.request(endpoint, { method: 'GET' });
    // Backend returns { count, schedules: [...] } -- normalize to array
    if (Array.isArray(resp)) return resp as Schedule[];
    if (resp && Array.isArray(resp.schedules)) return resp.schedules as Schedule[];
    return [];
  }

  // Bookings
  async createBooking(bookingData: {
    schedule_id: string;
    seat_number: number;
    passenger_name: string;
    passenger_phone: string;
    passenger_email: string;
  }): Promise<Booking> {
    return this.request('/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData),
    });
  }

  async getUserBookings(): Promise<Booking[]> {
    return this.request('/bookings/my-bookings');
  }

  async cancelBooking(bookingId: string): Promise<void> {
    return this.request(`/bookings/${bookingId}/cancel`, {
      method: 'POST',
    });
  }

  // GIS Integration
  async calculateRoute(routeData: {
    origin: string;
    destination: string;
    waypoints?: string[];
  }): Promise<any> {
    return this.request('/gis/calculate-route', {
      method: 'POST',
      body: JSON.stringify(routeData),
    });
  }

  async getLiveLocation(busId: string): Promise<any> {
    return this.request(`/gis/buses/${busId}/location`);
  }

  // Authentication helper for session-based auth
  async whoami(): Promise<any> {
    return this.request('/auth/whoami', { method: 'GET' });
  }
}

export const apiService = new ApiService();