import { useState } from 'react';
import { Search, Bus, Shield, Clock, CreditCard, MapPin, Calendar } from 'lucide-react';

interface HomePageProps {
  onSearch: (origin: string, destination: string, date: string) => void;
}

export function HomePage({ onSearch }: HomePageProps) {
  const [searchData, setSearchData] = useState({
    origin: '',
    destination: '',
    date: '',
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchData.origin && searchData.destination && searchData.date) {
      onSearch(searchData.origin, searchData.destination, searchData.date);
    }
  };

  const popularRoutes = [
    { from: 'Blantyre', to: 'Lilongwe', duration: '4h 30m' },
    { from: 'Lilongwe', to: 'Mzuzu', duration: '5h 15m' },
    { from: 'Zomba', to: 'Lilongwe', duration: '5h' },
    { from: 'Blantyre', to: 'Mzuzu', duration: '8h' },
  ];

  const cities = ['Blantyre', 'Lilongwe', 'Mzuzu', 'Zomba', 'Mangochi', 'Karonga', 'Kasungu', 'Salima'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F2F4F7] via-white to-[#F2F4F7]">
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-[#0057A4]/10 via-[#00B4A2]/5 to-transparent"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 relative">
          <div className="text-center mb-12">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-[#0A2239] mb-4 leading-tight">
              Book with Ease,<br />
              <span className="text-[#0057A4]">Travel in Peace</span>
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto">
              Discover and book intercity bus tickets across Malawi with secure payments and instant confirmation
            </p>
          </div>

          <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl p-6 sm:p-8">
            <form onSubmit={handleSearch} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[#0A2239] mb-2">
                    From
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0057A4]" />
                    <select
                      required
                      value={searchData.origin}
                      onChange={(e) => setSearchData({ ...searchData, origin: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all appearance-none bg-white"
                    >
                      <option value="">Select origin</option>
                      {cities.map((city) => (
                        <option key={city} value={city}>{city}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0A2239] mb-2">
                    To
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#00B4A2]" />
                    <select
                      required
                      value={searchData.destination}
                      onChange={(e) => setSearchData({ ...searchData, destination: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all appearance-none bg-white"
                    >
                      <option value="">Select destination</option>
                      {cities.map((city) => (
                        <option key={city} value={city}>{city}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#0A2239] mb-2">
                    Travel Date
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#FF7A00]" />
                    <input
                      type="date"
                      required
                      value={searchData.date}
                      onChange={(e) => setSearchData({ ...searchData, date: e.target.value })}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent transition-all"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-4 bg-[#FF7A00] text-white rounded-lg font-semibold text-lg hover:bg-[#FF7A00]/90 transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
              >
                <Search className="w-5 h-5" />
                Search Buses
              </button>
            </form>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-all">
            <div className="w-14 h-14 bg-[#0057A4]/10 rounded-lg flex items-center justify-center mb-4">
              <Clock className="w-7 h-7 text-[#0057A4]" />
            </div>
            <h3 className="text-xl font-bold text-[#0A2239] mb-2">Quick Booking</h3>
            <p className="text-gray-600 leading-relaxed">
              Book your bus tickets in minutes from anywhere. No more queuing at bus stations.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-all">
            <div className="w-14 h-14 bg-[#00B4A2]/10 rounded-lg flex items-center justify-center mb-4">
              <CreditCard className="w-7 h-7 text-[#00B4A2]" />
            </div>
            <h3 className="text-xl font-bold text-[#0A2239] mb-2">Secure Payments</h3>
            <p className="text-gray-600 leading-relaxed">
              Pay safely with PayChangu. All transactions are encrypted and secure.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-all">
            <div className="w-14 h-14 bg-[#FF7A00]/10 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-7 h-7 text-[#FF7A00]" />
            </div>
            <h3 className="text-xl font-bold text-[#0A2239] mb-2">Instant Confirmation</h3>
            <p className="text-gray-600 leading-relaxed">
              Get your ticket with QR code instantly via email. Easy check-in at the bus.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-[#0A2239] mb-6">Popular Routes</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {popularRoutes.map((route, index) => (
              <button
                key={index}
                onClick={() => setSearchData({
                  origin: route.from,
                  destination: route.to,
                  date: new Date().toISOString().split('T')[0],
                })}
                className="p-4 border-2 border-gray-200 rounded-lg hover:border-[#0057A4] hover:shadow-md transition-all text-left group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Bus className="w-5 h-5 text-[#0057A4] group-hover:text-[#00B4A2] transition-colors" />
                  <span className="font-semibold text-[#0A2239]">{route.from}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <span>→</span>
                  <span>{route.to}</span>
                </div>
                <div className="mt-2 text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {route.duration}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
