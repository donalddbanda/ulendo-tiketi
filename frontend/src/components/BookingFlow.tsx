import { useState, useEffect } from 'react';
import { ArrowLeft, User, Phone, Mail, CreditCard, AlertCircle, CheckCircle } from 'lucide-react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface BookingFlowProps {
  scheduleId: string;
  onBack: () => void;
  onComplete: () => void;
}

export function BookingFlow({ scheduleId, onBack, onComplete }: BookingFlowProps) {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const [scheduleDetails, setScheduleDetails] = useState<any>(null);
  const [selectedSeat, setSelectedSeat] = useState<number | null>(null);
  const [bookedSeats, setBookedSeats] = useState<number[]>([]);

  const [bookingData, setBookingData] = useState({
    passengerName: user?.full_name || '',
    passengerPhone: '',
    passengerEmail: user?.email || '',
  });

  useEffect(() => {
    // For now, we'll use mock data since the Python backend isn't ready
    loadMockScheduleDetails();
    loadMockBookedSeats();
  }, [scheduleId]);

  const loadMockScheduleDetails = () => {
    // Mock data - replace with actual API call when backend is ready
    const mockSchedule = {
      id: scheduleId,
      departure_time: '2024-11-15T08:00:00Z',
      arrival_time: '2024-11-15T14:00:00Z',
      price: 15000,
      available_seats: 24,
      buses: {
        bus_number: 'MBC-202',
        seating_capacity: 32,
        bus_type: 'Executive',
        bus_companies: {
          name: 'Malawi Bus Company',
          logo_url: null
        }
      },
      routes: {
        origin: 'Lilongwe',
        destination: 'Blantyre',
        distance_km: 350,
        estimated_duration_minutes: 360
      }
    };
    setScheduleDetails(mockSchedule);
  };

  const loadMockBookedSeats = () => {
    // Mock booked seats - replace with actual API call
    setBookedSeats([1, 5, 12, 18, 24]);
  };

  const handleBooking = async () => {
    if (!selectedSeat) {
      setError('Please select a seat');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Mock booking - replace with actual API call when backend is ready
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // TODO: Replace with actual API call
      // await apiService.createBooking({
      //   schedule_id: scheduleId,
      //   seat_number: selectedSeat,
      //   passenger_name: bookingData.passengerName,
      //   passenger_phone: bookingData.passengerPhone,
      //   passenger_email: bookingData.passengerEmail,
      // });

      setSuccess(true);
      setTimeout(() => {
        onComplete();
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Booking failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  if (!scheduleDetails) {
    return (
      <div className="min-h-screen bg-[#F2F4F7] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0057A4]"></div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#F2F4F7] flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-[#0A2239] mb-2">Booking Confirmed!</h2>
          <p className="text-gray-600 mb-6">
            Your ticket has been booked successfully. Check your dashboard for booking details.
          </p>
          <button
            onClick={onComplete}
            className="w-full py-3 bg-[#0057A4] text-white rounded-lg font-semibold hover:bg-[#0057A4]/90 transition-all"
          >
            View My Bookings
          </button>
        </div>
      </div>
    );
  }

  const capacity = scheduleDetails.buses.seating_capacity;
  const seats = Array.from({ length: capacity }, (_, i) => i + 1);

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-[#0057A4] hover:text-[#00B4A2] font-medium mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Results
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-2xl font-bold text-[#0A2239] mb-6">Complete Your Booking</h2>

              <div className="mb-6">
                <h3 className="text-lg font-semibold text-[#0A2239] mb-4">Step 1: Passenger Information</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-[#0A2239] mb-2">
                      Full Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="text"
                        required
                        value={bookingData.passengerName}
                        onChange={(e) => setBookingData({ ...bookingData, passengerName: e.target.value })}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                        placeholder="Enter your full name"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#0A2239] mb-2">
                      Phone Number
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="tel"
                        required
                        value={bookingData.passengerPhone}
                        onChange={(e) => setBookingData({ ...bookingData, passengerPhone: e.target.value })}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                        placeholder="+265 999 123 456"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-[#0A2239] mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="email"
                        required
                        value={bookingData.passengerEmail}
                        onChange={(e) => setBookingData({ ...bookingData, passengerEmail: e.target.value })}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                        placeholder="you@example.com"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-[#0A2239] mb-4">Step 2: Select Your Seat</h3>
                <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
                  {seats.map((seat) => {
                    const isBooked = bookedSeats.includes(seat);
                    const isSelected = selectedSeat === seat;

                    return (
                      <button
                        key={seat}
                        disabled={isBooked}
                        onClick={() => setSelectedSeat(seat)}
                        className={`aspect-square rounded-lg font-semibold text-sm transition-all ${
                          isBooked
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : isSelected
                            ? 'bg-[#0057A4] text-white shadow-md'
                            : 'bg-white border-2 border-gray-300 hover:border-[#0057A4] text-[#0A2239]'
                        }`}
                      >
                        {seat}
                      </button>
                    );
                  })}
                </div>

                <div className="flex gap-6 mt-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-white border-2 border-gray-300 rounded"></div>
                    <span>Available</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-[#0057A4] rounded"></div>
                    <span>Selected</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-gray-200 rounded"></div>
                    <span>Booked</span>
                  </div>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-red-600">{error}</p>
              </div>
            )}
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-6 sticky top-24">
              <h3 className="text-lg font-semibold text-[#0A2239] mb-4">Booking Summary</h3>

              <div className="space-y-3 mb-6 text-sm">
                <div>
                  <p className="text-gray-600">Company</p>
                  <p className="font-semibold text-[#0A2239]">{scheduleDetails.buses.bus_companies.name}</p>
                </div>
                <div>
                  <p className="text-gray-600">Route</p>
                  <p className="font-semibold text-[#0A2239]">
                    {scheduleDetails.routes.origin} → {scheduleDetails.routes.destination}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Departure</p>
                  <p className="font-semibold text-[#0A2239]">
                    {new Date(scheduleDetails.departure_time).toLocaleDateString()} at {formatTime(scheduleDetails.departure_time)}
                  </p>
                </div>
                {selectedSeat && (
                  <div>
                    <p className="text-gray-600">Seat Number</p>
                    <p className="font-semibold text-[#0A2239]">{selectedSeat}</p>
                  </div>
                )}
              </div>

              <div className="border-t pt-4 space-y-2 mb-6">
                <div className="flex justify-between">
                  <span className="text-gray-600">Ticket Price</span>
                  <span className="font-semibold">MWK {scheduleDetails.price.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Service Fee</span>
                  <span className="font-semibold">MWK 3,000</span>
                </div>
                <div className="flex justify-between text-lg font-bold pt-2 border-t">
                  <span>Total</span>
                  <span className="text-[#0057A4]">MWK {(scheduleDetails.price + 3000).toLocaleString()}</span>
                </div>
              </div>

              <button
                onClick={handleBooking}
                disabled={loading || !selectedSeat}
                className="w-full py-3 bg-[#FF7A00] text-white rounded-lg font-semibold hover:bg-[#FF7A00]/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md flex items-center justify-center gap-2"
              >
                <CreditCard className="w-5 h-5" />
                {loading ? 'Processing...' : 'Confirm & Pay'}
              </button>

              <p className="text-xs text-gray-500 text-center mt-3">
                Payment processed securely via PayChangu
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}