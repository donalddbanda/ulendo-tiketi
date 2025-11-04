import { useState, useEffect } from 'react';
import { Bus, Clock, MapPin, Armchair, ArrowLeft } from 'lucide-react';
import { apiService, Schedule } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface SearchResultsProps {
  origin: string;
  destination: string;
  date: string;
  onBack: () => void;
  onBook: (scheduleId: string) => void;
  onShowAuth: () => void;
}

export function SearchResults({ origin, destination, date, onBack, onBook, onShowAuth }: SearchResultsProps) {
  const { user } = useAuth();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSchedules();
  }, [origin, destination, date]);

  const loadSchedules = async () => {
    setLoading(true);
    try {
      const data = await apiService.searchSchedules({ origin, destination, date });
      setSchedules(data);
    } catch (error) {
      console.error('Failed to load schedules:', error);
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

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins > 0 ? `${mins}m` : ''}`;
  };

  const handleBookClick = (scheduleId: string) => {
    if (!user) {
      onShowAuth();
      return;
    }
    onBook(scheduleId);
  };

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ... rest of the component remains the same, just update the data mapping */}
        {schedules.map((schedule) => (
          <div key={schedule.id} className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all p-6">
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-[#0A2239]">{schedule.bus.company.name}</h3>
                    <p className="text-gray-600">Bus: {schedule.bus.bus_number} - {schedule.bus.bus_type}</p>
                  </div>
                </div>

                <div className="flex items-center gap-8 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">Departure</p>
                    <p className="text-2xl font-bold text-[#0057A4]">{formatTime(schedule.departure_time)}</p>
                  </div>
                  <div className="flex-1 flex items-center gap-2">
                    <div className="flex-1 h-0.5 bg-gray-300"></div>
                    <Clock className="w-5 h-5 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {formatDuration(schedule.route.estimated_duration_minutes)}
                    </span>
                    <div className="flex-1 h-0.5 bg-gray-300"></div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Arrival</p>
                    <p className="text-2xl font-bold text-[#00B4A2]">{formatTime(schedule.arrival_time)}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Armchair className="w-4 h-4" />
                    {schedule.available_seats} seats available
                  </div>
                  {schedule.bus.amenities.length > 0 && (
                    <div className="flex gap-2">
                      {schedule.bus.amenities.slice(0, 3).map((amenity, idx) => (
                        <span key={idx} className="px-2 py-1 bg-[#F2F4F7] rounded text-xs">
                          {amenity}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="lg:border-l lg:pl-6 flex flex-col justify-between items-end">
                <div className="text-right mb-4">
                  <p className="text-sm text-gray-600">Price per seat</p>
                  <p className="text-3xl font-bold text-[#0A2239]">
                    MWK {schedule.price.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">+ MWK 3,000 service fee</p>
                </div>
                <button
                  onClick={() => handleBookClick(schedule.id)}
                  className="w-full lg:w-auto px-8 py-3 bg-[#FF7A00] text-white rounded-lg font-semibold hover:bg-[#FF7A00]/90 transition-all shadow-sm hover:shadow-md"
                >
                  Book Now
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}