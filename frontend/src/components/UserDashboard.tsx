import { useState, useEffect } from 'react';
import { Ticket, Calendar, MapPin, Bus, QrCode, X, AlertCircle } from 'lucide-react';
import { apiService, Booking } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export function UserDashboard() {
  const { user } = useAuth();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [cancelError, setCancelError] = useState('');

  useEffect(() => {
    loadBookings();
  }, [user]);

  const loadBookings = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const userBookings = await apiService.getUserBookings();
      setBookings(userBookings);
    } catch (error) {
      console.error('Failed to load bookings:', error);
      setBookings([]);
    } finally {
      setLoading(false);
    }
  };

  const canCancelBooking = (departureTime: string) => {
    const departure = new Date(departureTime);
    const now = new Date();
    const hoursUntilDeparture = (departure.getTime() - now.getTime()) / (1000 * 60 * 60);
    return hoursUntilDeparture >= 24;
  };

  const handleCancelBooking = async (bookingId: string) => {
    setCancelError('');
    const booking = bookings.find((b) => b.id === bookingId);
    if (!booking) return;

    if (!canCancelBooking(booking.schedule.departure_time)) {
      setCancelError('Bookings can only be cancelled up to 24 hours before departure');
      return;
    }

    try {
      await apiService.cancelBooking(bookingId);
      setSelectedBooking(null);
      loadBookings(); // Reload bookings to reflect cancellation
    } catch (error) {
      setCancelError('Failed to cancel booking');
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'cancelled':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'completed':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const activeBookings = bookings.filter(
    (b) => b.status === 'confirmed' && new Date(b.schedule.departure_time) > new Date()
  );
  const pastBookings = bookings.filter(
    (b) => b.status === 'completed' || new Date(b.schedule.departure_time) <= new Date()
  );

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#0A2239] mb-2">My Bookings</h1>
          <p className="text-gray-600">Welcome back, {user?.full_name}</p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#0057A4]"></div>
          </div>
        ) : bookings.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <Ticket className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-[#0A2239] mb-2">No bookings yet</h3>
            <p className="text-gray-600 mb-6">Start your journey by booking your first bus ticket</p>
            <a
              href="/"
              className="inline-block px-6 py-3 bg-[#FF7A00] text-white rounded-lg font-semibold hover:bg-[#FF7A00]/90 transition-all"
            >
              Search Buses
            </a>
          </div>
        ) : (
          <div className="space-y-8">
            {activeBookings.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-[#0A2239] mb-4">Upcoming Trips</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {activeBookings.map((booking) => (
                    <div key={booking.id} className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Booking Ref</p>
                          <p className="font-mono font-bold text-[#0057A4]">{booking.booking_reference}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(booking.status)}`}>
                          {booking.status}
                        </span>
                      </div>

                      <div className="space-y-3 mb-4">
                        <div className="flex items-center gap-2">
                          <Bus className="w-5 h-5 text-[#0057A4]" />
                          <span className="font-semibold text-[#0A2239]">{booking.schedule.bus.company.name}</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <MapPin className="w-5 h-5 text-gray-400" />
                          <span className="text-gray-700">
                            {booking.schedule.route.origin} → {booking.schedule.route.destination}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <Calendar className="w-5 h-5 text-gray-400" />
                          <span className="text-gray-700">
                            {formatDate(booking.schedule.departure_time)} at {formatTime(booking.schedule.departure_time)}
                          </span>
                        </div>

                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-gray-600">Seat: <span className="font-semibold text-[#0A2239]">{booking.seat_number}</span></span>
                          <span className="text-gray-600">Bus: <span className="font-semibold text-[#0A2239]">{booking.schedule.bus.bus_number}</span></span>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => setSelectedBooking(booking)}
                          className="flex-1 py-2 bg-[#0057A4] text-white rounded-lg font-medium hover:bg-[#0057A4]/90 transition-all flex items-center justify-center gap-2"
                        >
                          <QrCode className="w-4 h-4" />
                          View Ticket
                        </button>
                        {canCancelBooking(booking.schedule.departure_time) && (
                          <button
                            onClick={() => handleCancelBooking(booking.id)}
                            className="px-4 py-2 border-2 border-red-500 text-red-500 rounded-lg font-medium hover:bg-red-50 transition-all"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {pastBookings.length > 0 && (
              <div>
                <h2 className="text-xl font-bold text-[#0A2239] mb-4">Past Trips</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {pastBookings.map((booking) => (
                    <div key={booking.id} className="bg-white rounded-xl shadow-sm p-6 opacity-75">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Booking Ref</p>
                          <p className="font-mono font-bold text-gray-700">{booking.booking_reference}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(booking.status)}`}>
                          {booking.status}
                        </span>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <Bus className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-700">{booking.schedule.bus.company.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-600">
                            {booking.schedule.route.origin} → {booking.schedule.route.destination}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-600">{formatDate(booking.schedule.departure_time)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {selectedBooking && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 relative">
            <button
              onClick={() => setSelectedBooking(null)}
              className="absolute top-4 right-4 p-2 hover:bg-[#F2F4F7] rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-2xl font-bold text-[#0A2239] mb-6">Your Ticket</h2>

            <div className="space-y-4 mb-6">
              <div className="bg-[#F2F4F7] p-4 rounded-lg text-center">
                <QrCode className="w-32 h-32 text-[#0057A4] mx-auto mb-2" />
                <p className="font-mono font-bold text-[#0057A4] text-lg">{selectedBooking.booking_reference}</p>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Company</span>
                  <span className="font-semibold text-[#0A2239]">{selectedBooking.schedule.bus?.company?.name || selectedBooking.schedule.bus.company.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Route</span>
                  <span className="font-semibold text-[#0A2239]">
                    {selectedBooking.schedule.route?.origin || selectedBooking.schedule.route.origin} → {selectedBooking.schedule.route?.destination || selectedBooking.schedule.route.destination}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Date</span>
                  <span className="font-semibold text-[#0A2239]">{formatDate(selectedBooking.schedule.departure_time)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Departure</span>
                  <span className="font-semibold text-[#0A2239]">{formatTime(selectedBooking.schedule.departure_time)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Seat Number</span>
                  <span className="font-semibold text-[#0057A4] text-lg">{selectedBooking.seat_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Bus Number</span>
                  <span className="font-semibold text-[#0A2239]">{selectedBooking.schedule.bus?.bus_number || selectedBooking.schedule.bus.bus_number}</span>
                </div>
              </div>
            </div>

            <div className="space-y-2 mb-4">
              <button
                onClick={async () => {
                  try {
                    const blob = await apiService.getQRCode(selectedBooking.id);
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `ticket-${selectedBooking.booking_reference}.png`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                  } catch (err) {
                    console.error('Failed to download QR code:', err);
                  }
                }}
                className="w-full py-2 bg-[#0057A4] text-white rounded-lg font-medium hover:bg-[#0057A4]/90 transition-all"
              >
                Download QR Code
              </button>
            </div>

            <p className="text-xs text-gray-500 text-center">
              Show this QR code to the bus conductor when boarding
            </p>
          </div>
        </div>
      )}

      {cancelError && (
        <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3 max-w-md shadow-lg">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-600 font-medium">Cannot Cancel</p>
            <p className="text-red-600 text-sm">{cancelError}</p>
          </div>
          <button onClick={() => setCancelError('')} className="ml-auto">
            <X className="w-5 h-5 text-red-600" />
          </button>
        </div>
      )}
    </div>
  );
}