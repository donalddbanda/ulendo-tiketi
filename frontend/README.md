# Ulendo Tiketi

**Book with Ease, Travel in Peace**

A modern bus booking platform for Malawi that connects passengers with licensed bus companies through an intuitive online system.

## Features

### For Passengers
- Search and compare bus routes across Malawi
- Book tickets online anytime, anywhere
- Secure payments via PayChangu
- Instant booking confirmation with QR code
- View and manage bookings
- Cancel bookings up to 24 hours before departure

### For Bus Companies
- Manage buses and schedules
- View bookings in real-time
- Process cancellations
- Request cashouts
- Track revenue and analytics

### For Administrators
- Manage all users, companies, and routes
- Oversee payments and bookings
- Approve/reject cashout requests
- System analytics and reporting

## Tech Stack

- **Frontend**: React + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Icons**: Lucide React

## Color Palette

- **Royal Blue** `#0057A4` - Trust, technology, reliability
- **Bright Teal** `#00B4A2` - Movement, travel, innovation
- **Sunrise Orange** `#FF7A00` - Action, energy, friendliness
- **Cool Gray** `#F2F4F7` - Background
- **Midnight Navy** `#0A2239` - Text and icons

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ulendo-tiketi
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Add your Supabase credentials:
     ```
     VITE_SUPABASE_URL=your-project-url
     VITE_SUPABASE_ANON_KEY=your-anon-key
     ```

4. **Database setup**
   - The database schema has been applied via migrations
   - Tables include: profiles, bus_companies, buses, routes, schedules, bookings, payments, cashout_requests
   - All tables have Row Level Security (RLS) enabled

5. **Run development server**
   ```bash
   npm run dev
   ```

6. **Build for production**
   ```bash
   npm run build
   ```

## Project Structure

```
src/
├── components/          # React components
│   ├── Navbar.tsx      # Navigation bar
│   ├── AuthModal.tsx   # Login/Register modal
│   ├── HomePage.tsx    # Landing page with search
│   ├── SearchResults.tsx    # Bus search results
│   ├── BookingFlow.tsx      # Seat selection and payment
│   └── UserDashboard.tsx    # User bookings dashboard
├── contexts/
│   └── AuthContext.tsx      # Authentication context
├── lib/
│   ├── supabase.ts         # Supabase client
│   └── database.types.ts   # TypeScript types
├── App.tsx                  # Main app component
└── main.tsx                # Entry point
```

## User Roles

- **Passenger**: Can search and book bus tickets
- **Company**: Can manage buses, schedules, and view bookings
- **Admin**: Full system access and oversight

## Payment Information

- Service fee: MWK 3,000 per booking
- Payment processor: PayChangu
- Revenue flow: Customer → Ulendo Tiketi → Bus Company (minus platform fee)

## Cancellation Policy

- Bookings can be cancelled up to 24 hours before departure
- Cancellations made less than 24 hours before departure are not allowed

## Support

For questions or issues, contact the development team:
- Backend Developer: Donald Banda
- Frontend Developer: Gomezgani Chirwa

---

**Ulendo Tiketi** - Transforming bus travel in Malawi
