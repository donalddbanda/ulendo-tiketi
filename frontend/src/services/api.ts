// API service for Python backend integration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
    const token = localStorage.getItem('auth_token');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication
  async login(email: string, password: string): Promise<{ user: User; token: string }> {
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
  }): Promise<{ user: User; token: string }> {
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
    return this.request('/schedules/search', {
      method: 'POST',
      body: JSON.stringify(params),
    });
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
}

export const apiService = new ApiService();