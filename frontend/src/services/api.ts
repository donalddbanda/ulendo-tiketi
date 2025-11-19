// API service for Python backend integration
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
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
  async login(emailOrPhone: string, password: string): Promise<any> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: emailOrPhone, password }),
    });
  }

  async register(emailOrPhone: string, password: string, fullName: string, role: 'passenger' | 'company', phone?: string): Promise<any> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: emailOrPhone,
        password,
        full_name: fullName,
        role,
        phone: phone || emailOrPhone,
      }),
    });
  }

  async whoami(): Promise<any> {
    return this.request('/auth/whoami', { method: 'GET' });
  }

  // --- Admin / Company Management ---

  // Fetch all bus companies (admin)
  async getCompanies(): Promise<any> {
    return this.request('/companies/get', { method: 'GET' });
  }

  // Approve or reject a company
  async reviewCompany(id: number, action: 'approve' | 'reject'): Promise<any> {
    return this.request(`/companies/review/${id}/${action}`, { method: 'POST' });
  }

  // Send password reset link for a company
  async sendPasswordReset(email: string): Promise<any> {
    return this.request('/companies/send-reset', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  // Admin: register a new bus company (admin-only)
  async registerCompany(companyData: {
    name: string;
    description: string;
    phone_numbers: string[];
    email?: string;
    bank_name?: string;
    bank_account_number?: string;
    bank_account_name?: string;
  }): Promise<any> {
    return this.request('/companies/register', {
      method: 'POST',
      body: JSON.stringify(companyData),
    });
  }

  // --- Schedules and Search ---
  async searchSchedules(params: { origin: string; destination: string; date: string }): Promise<Schedule[]> {
    const qs = new URLSearchParams();
    if (params.origin) qs.set('origin', params.origin);
    if (params.destination) qs.set('destination', params.destination);
    if (params.date) qs.set('date', params.date);

    const queryString = qs.toString();
    const endpoint = `/search/schedules${queryString ? `?${queryString}` : ''}`;
    const resp: any = await this.request(endpoint, { method: 'GET' });
    if (Array.isArray(resp)) return resp as Schedule[];
    if (resp && Array.isArray(resp.schedules)) return resp.schedules as Schedule[];
    return [];
  }

  // Bookings
  async getSchedule(scheduleId: string): Promise<Schedule> {
    return this.request(`/schedules/${scheduleId}`);
  }

  async createBooking(bookingData: { schedule_id: string; seat_number: number }): Promise<any> {
    return this.request('/bookings/book', {
      method: 'POST',
      body: JSON.stringify(bookingData),
    });
  }

  async getBooking(bookingId: string): Promise<Booking> {
    return this.request(`/bookings/get/${bookingId}`);
  }

  async getUserBookings(): Promise<Booking[]> {
    const resp: any = await this.request('/bookings/get');
    if (Array.isArray(resp)) return resp as Booking[];
    if (resp && Array.isArray(resp.bookings)) return resp.bookings as Booking[];
    return [];
  }

  async cancelBooking(bookingId: string): Promise<void> {
    return this.request(`/bookings/cancel/${bookingId}`, { method: 'POST' });
  }

  async getQRCode(bookingId: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/bookings/qr-code/${bookingId}`, { credentials: 'include' });
    if (!response.ok) throw new Error('Failed to download QR code');
    return response.blob();
  }

  async validateQRCode(bookingId: string): Promise<any> {
    return this.request(`/bookings/validate-qr/${bookingId}`, { method: 'POST' });
  }

  async scanQRCode(qrReference: string, busId: string): Promise<any> {
    return this.request('/bookings/scan-qr', {
      method: 'POST',
      body: JSON.stringify({ qr_reference: qrReference, bus_id: busId }),
    });
  }

  // --- Buses ---
  async getCompanyBuses(): Promise<any> {
    return this.request('/buses/company');
  }

  async createBus(busData: { bus_number: string; seating_capacity: number }): Promise<any> {
    return this.request('/buses/add', { method: 'POST', body: JSON.stringify(busData) });
  }

  async getBus(busId: string): Promise<any> {
    return this.request(`/buses/${busId}`);
  }

  async updateBus(busId: string, busData: any): Promise<any> {
    return this.request(`/buses/${busId}/update`, { method: 'PUT', body: JSON.stringify(busData) });
  }

  async deleteBus(busId: string): Promise<void> {
    return this.request(`/buses/${busId}/delete`, { method: 'DELETE' });
  }

  // --- Schedules ---
  async getCompanySchedules(): Promise<any> {
    return this.request('/schedules/company/schedules');
  }

  async createSchedule(scheduleData: { bus_id: string; route_id: string; departure_time: string; arrival_time: string; price: number; available_seats: number }): Promise<any> {
    return this.request('/schedules/create', { method: 'POST', body: JSON.stringify(scheduleData) });
  }

  async getScheduleById(scheduleId: string): Promise<any> {
    return this.request(`/schedules/${scheduleId}`);
  }

  async cancelSchedule(scheduleId: string): Promise<void> {
    return this.request(`/schedules/${scheduleId}/cancel`, { method: 'POST' });
  }

  // --- Route & GIS ---
  async calculateRoute(routeData: { origin: string; destination: string; waypoints?: string[] }): Promise<any> {
    return this.request('/gis/calculate-route', { method: 'POST', body: JSON.stringify(routeData) });
  }

  async getLiveLocation(busId: string): Promise<any> {
    return this.request(`/gis/buses/${busId}/location`);
  }
}

export const apiService = new ApiService();
