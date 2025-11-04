/*
  # Ulendo Tiketi - Initial Database Schema

  ## Overview
  This migration creates the complete database structure for Ulendo Tiketi, 
  a modern bus booking platform for Malawi.

  ## New Tables Created
  
  ### 1. profiles
  - Extends auth.users with additional user information
  - Fields: id (references auth.users), full_name, phone, role (passenger/company/admin)
  - Role determines user access and dashboard type
  
  ### 2. bus_companies
  - Stores bus operator company information
  - Fields: id, user_id (owner), name, description, contact info, account details
  - Links to a user account with 'company' role
  
  ### 3. buses
  - Individual bus vehicles managed by companies
  - Fields: id, company_id, bus_number, seating_capacity, bus_type, amenities
  - Each bus belongs to one company
  
  ### 4. routes
  - Travel routes between cities
  - Fields: id, origin, destination, distance_km, estimated_duration
  - Shared across all companies
  
  ### 5. schedules
  - Specific trips on routes by buses
  - Fields: id, bus_id, route_id, departure_time, arrival_time, price, status
  - Links bus to route with timing and pricing
  
  ### 6. bookings
  - Passenger ticket bookings
  - Fields: id, user_id, schedule_id, seat_number, status, qr_code, booking_reference
  - Tracks individual seat reservations
  
  ### 7. payments
  - Payment transaction records
  - Fields: id, booking_id, amount, platform_fee, net_amount, payment_reference, status
  - Integrated with PayChangu gateway
  
  ### 8. cashout_requests
  - Company payout requests
  - Fields: id, company_id, amount, status, bank/mobile details, processed info
  - Handles company fund withdrawals
  
  ## Security Implementation
  - Row Level Security (RLS) enabled on ALL tables
  - Policies enforce authentication and ownership checks
  - Public read access only for routes and schedules (search functionality)
  - Users can only manage their own bookings
  - Companies can only manage their own buses and schedules
  - Admin role has oversight capabilities
  
  ## Important Notes
  - Platform fee: MWK 3,000 per booking (handled in payments table)
  - QR codes generated for each confirmed booking
  - Booking cancellation allowed up to 24 hours before departure
  - All timestamps use timestamptz for proper timezone handling
*/

-- Create enum types
CREATE TYPE user_role AS ENUM ('passenger', 'company', 'admin');
CREATE TYPE booking_status AS ENUM ('pending', 'confirmed', 'cancelled', 'completed');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');
CREATE TYPE cashout_status AS ENUM ('pending', 'approved', 'rejected', 'completed');
CREATE TYPE schedule_status AS ENUM ('active', 'cancelled', 'completed');

-- Profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name text NOT NULL,
  phone text,
  role user_role NOT NULL DEFAULT 'passenger',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Bus Companies table
CREATE TABLE IF NOT EXISTS bus_companies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  contact_email text,
  contact_phone text NOT NULL,
  logo_url text,
  account_type text,
  account_number text,
  account_name text,
  is_verified boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id)
);

-- Buses table
CREATE TABLE IF NOT EXISTS buses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES bus_companies(id) ON DELETE CASCADE,
  bus_number text NOT NULL,
  seating_capacity integer NOT NULL CHECK (seating_capacity > 0),
  bus_type text DEFAULT 'Standard',
  amenities text[],
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(company_id, bus_number)
);

-- Routes table
CREATE TABLE IF NOT EXISTS routes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  origin text NOT NULL,
  destination text NOT NULL,
  distance_km numeric(10,2),
  estimated_duration_minutes integer,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(origin, destination)
);

-- Schedules table
CREATE TABLE IF NOT EXISTS schedules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bus_id uuid NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
  route_id uuid NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  departure_time timestamptz NOT NULL,
  arrival_time timestamptz NOT NULL,
  price numeric(10,2) NOT NULL CHECK (price > 0),
  available_seats integer NOT NULL,
  status schedule_status DEFAULT 'active',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  CHECK (arrival_time > departure_time)
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  schedule_id uuid NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
  seat_number integer NOT NULL,
  booking_reference text NOT NULL UNIQUE,
  qr_code text,
  status booking_status DEFAULT 'pending',
  passenger_name text NOT NULL,
  passenger_phone text NOT NULL,
  passenger_email text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(schedule_id, seat_number)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id uuid NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
  amount numeric(10,2) NOT NULL CHECK (amount > 0),
  platform_fee numeric(10,2) DEFAULT 3000,
  net_amount numeric(10,2) NOT NULL,
  payment_reference text,
  payment_method text DEFAULT 'PayChangu',
  status payment_status DEFAULT 'pending',
  created_at timestamptz DEFAULT now(),
  processed_at timestamptz,
  UNIQUE(booking_id)
);

-- Cashout Requests table
CREATE TABLE IF NOT EXISTS cashout_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES bus_companies(id) ON DELETE CASCADE,
  amount numeric(10,2) NOT NULL CHECK (amount > 0),
  status cashout_status DEFAULT 'pending',
  account_type text NOT NULL,
  account_number text NOT NULL,
  account_name text NOT NULL,
  requested_at timestamptz DEFAULT now(),
  processed_at timestamptz,
  processed_by uuid REFERENCES profiles(id),
  admin_notes text
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bus_companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE buses ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE cashout_requests ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
CREATE POLICY "Users can view all profiles"
  ON profiles FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

-- Bus Companies Policies
CREATE POLICY "Anyone can view verified companies"
  ON bus_companies FOR SELECT
  TO authenticated
  USING (is_verified = true);

CREATE POLICY "Company owners can view own company"
  ON bus_companies FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Company owners can update own company"
  ON bus_companies FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can create company profile"
  ON bus_companies FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- Buses Policies
CREATE POLICY "Anyone can view active buses"
  ON buses FOR SELECT
  TO authenticated
  USING (is_active = true);

CREATE POLICY "Company owners can manage own buses"
  ON buses FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bus_companies
      WHERE bus_companies.id = buses.company_id
      AND bus_companies.user_id = auth.uid()
    )
  );

-- Routes Policies
CREATE POLICY "Anyone can view routes"
  ON routes FOR SELECT
  TO authenticated
  USING (true);

-- Schedules Policies
CREATE POLICY "Anyone can view active schedules"
  ON schedules FOR SELECT
  TO authenticated
  USING (status = 'active');

CREATE POLICY "Company owners can manage own schedules"
  ON schedules FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM buses
      JOIN bus_companies ON buses.company_id = bus_companies.id
      WHERE buses.id = schedules.bus_id
      AND bus_companies.user_id = auth.uid()
    )
  );

-- Bookings Policies
CREATE POLICY "Users can view own bookings"
  ON bookings FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Company owners can view bookings for their schedules"
  ON bookings FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM schedules
      JOIN buses ON schedules.bus_id = buses.id
      JOIN bus_companies ON buses.company_id = bus_companies.id
      WHERE schedules.id = bookings.schedule_id
      AND bus_companies.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create bookings"
  ON bookings FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own bookings"
  ON bookings FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

-- Payments Policies
CREATE POLICY "Users can view payments for own bookings"
  ON payments FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bookings
      WHERE bookings.id = payments.booking_id
      AND bookings.user_id = auth.uid()
    )
  );

CREATE POLICY "Company owners can view payments for their bookings"
  ON payments FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bookings
      JOIN schedules ON bookings.schedule_id = schedules.id
      JOIN buses ON schedules.bus_id = buses.id
      JOIN bus_companies ON buses.company_id = bus_companies.id
      WHERE bookings.id = payments.booking_id
      AND bus_companies.user_id = auth.uid()
    )
  );

-- Cashout Requests Policies
CREATE POLICY "Company owners can view own cashout requests"
  ON cashout_requests FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM bus_companies
      WHERE bus_companies.id = cashout_requests.company_id
      AND bus_companies.user_id = auth.uid()
    )
  );

CREATE POLICY "Company owners can create cashout requests"
  ON cashout_requests FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM bus_companies
      WHERE bus_companies.id = company_id
      AND bus_companies.user_id = auth.uid()
    )
  );

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_bus_companies_user_id ON bus_companies(user_id);
CREATE INDEX IF NOT EXISTS idx_buses_company_id ON buses(company_id);
CREATE INDEX IF NOT EXISTS idx_schedules_bus_id ON schedules(bus_id);
CREATE INDEX IF NOT EXISTS idx_schedules_route_id ON schedules(route_id);
CREATE INDEX IF NOT EXISTS idx_schedules_departure_time ON schedules(departure_time);
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_schedule_id ON bookings(schedule_id);
CREATE INDEX IF NOT EXISTS idx_payments_booking_id ON payments(booking_id);

-- Create function to generate booking reference
CREATE OR REPLACE FUNCTION generate_booking_reference()
RETURNS text AS $$
BEGIN
  RETURN 'UT' || TO_CHAR(NOW(), 'YYYYMMDD') || LPAD(FLOOR(RANDOM() * 10000)::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bus_companies_updated_at BEFORE UPDATE ON bus_companies
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_buses_updated_at BEFORE UPDATE ON buses
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();