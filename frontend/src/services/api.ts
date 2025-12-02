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
    // Public registration should not include role selection (backend allows passenger public registers)
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: emailOrPhone,
        password,
        full_name: fullName,
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

  // Send password reset (public endpoint)
  async sendPasswordReset(email: string): Promise<any> {
    return this.request('/auth/request/password-reset/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  // Admin: register a new bus company (admin-only)
  async registerCompany(payload: {
    company: { name: string; description: string; email?: string; phone_numbers: string[] };
    owner: { full_name: string; email: string; phone_number: string; password: string };
    bank_account?: { bank_name: string; account_number: string; account_name: string };
  }): Promise<any> {
    return this.request('/companies/register', {
      method: 'POST',
      body: JSON.stringify(payload),
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

  // QR validation — use scan endpoint which accepts { qr_data }
  async validateQRCode(qrData: string): Promise<any> {
    return this.request('/bookings/scan-qr', {
      method: 'POST',
      body: JSON.stringify({ qr_data: qrData }),
    });
  }

  // Conductor scan helper (alias)
  async scanQRCode(qrData: string): Promise<any> {
    return this.validateQRCode(qrData);
  }

  // Logout - call server then rely on session cookie cleared server-side
  async logout(): Promise<any> {
    return this.request('/auth/logout', { method: 'POST' });
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

  // Accounts / Payouts
  async getCompanyBalance(): Promise<any> {
    // returns { company: { balance: number, ... } }
    return this.request('/companies/whoami', { method: 'GET' });
  }

  async requestPayout(amount: number): Promise<any> {
    return this.request('/payouts/request', { method: 'POST', body: JSON.stringify({ amount }) });
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

  // --- Branches ---
  async createBranch(data: { name: string; company_id: number; manager_id?: number }): Promise<any> {
    return this.request('/branches/create', { method: 'POST', body: JSON.stringify(data) });
  }

  async listBranches(): Promise<any> {
    return this.request('/branches/list', { method: 'GET' });
  }

  async getBranch(branchId: string): Promise<any> {
    return this.request(`/branches/${branchId}`, { method: 'GET' });
  }

  async updateBranch(branchId: string, data: any): Promise<any> {
    return this.request(`/branches/${branchId}/update`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteBranch(branchId: string): Promise<any> {
    return this.request(`/branches/${branchId}/delete`, { method: 'DELETE' });
  }

  async getBranchEmployees(branchId: string): Promise<any> {
    return this.request(`/branches/${branchId}/employees`, { method: 'GET' });
  }

  async getBranchBuses(branchId: string): Promise<any> {
    return this.request(`/branches/${branchId}/buses`, { method: 'GET' });
  }

  // --- Employees ---
  async inviteEmployee(payload: { email: string; phone_number: string; full_name: string; role: string; branch_id?: number }): Promise<any> {
    return this.request('/employees/invite', { method: 'POST', body: JSON.stringify(payload) });
  }

  async acceptEmployeeInvitation(payload: { invitation_code: string; password: string; confirm_password: string }): Promise<any> {
    return this.request('/employees/accept-invitation', { method: 'POST', body: JSON.stringify(payload) });
  }

  async listInvitations(): Promise<any> {
    return this.request('/employees/invitations', { method: 'GET' });
  }

  async cancelInvitation(invitationId: string): Promise<any> {
    return this.request(`/employees/invitations/${invitationId}/cancel`, { method: 'DELETE' });
  }

  async listEmployees(): Promise<any> {
    return this.request('/employees/list', { method: 'GET' });
  }

  async getEmployee(employeeId: string): Promise<any> {
    return this.request(`/employees/${employeeId}`, { method: 'GET' });
  }

  async updateEmployee(employeeId: string, data: any): Promise<any> {
    return this.request(`/employees/${employeeId}/update`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async removeEmployee(employeeId: string): Promise<any> {
    return this.request(`/employees/${employeeId}/remove`, { method: 'DELETE' });
  }

  async assignBusToEmployee(employeeId: string, payload: { bus_id: number }): Promise<any> {
    return this.request(`/employees/${employeeId}/assign-bus`, { method: 'POST', body: JSON.stringify(payload) });
  }

  async unassignBusFromEmployee(employeeId: string, payload: { bus_id: number }): Promise<any> {
    return this.request(`/employees/${employeeId}/unassign-bus`, { method: 'POST', body: JSON.stringify(payload) });
  }

  // --- Banks ---
  async getBankAccount(): Promise<any> {
    return this.request('/banks/account', { method: 'GET' });
  }

  async deleteBankAccount(): Promise<any> {
    return this.request('/banks/account/delete', { method: 'DELETE' });
  }

  // --- Dashboard ---
  async getAdminDashboard(): Promise<any> { return this.request('/dashboard/admin', { method: 'GET' }); }
  async getCompanyDashboard(): Promise<any> { return this.request('/dashboard/company', { method: 'GET' }); }
  async getBranchDashboard(branchId: string): Promise<any> { return this.request(`/dashboard/branch/${branchId}`, { method: 'GET' }); }
  async getConductorDashboard(conductorId: string): Promise<any> { return this.request(`/dashboard/conductor/${conductorId}`, { method: 'GET' }); }
  async getPassengerDashboard(): Promise<any> { return this.request('/dashboard/passenger', { method: 'GET' }); }
}

export const apiService = new ApiService();
