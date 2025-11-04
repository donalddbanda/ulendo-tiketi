import React from 'react';
import { Bus, Calendar, DollarSign, Users, Plus, BarChart3 } from 'lucide-react';

export function CompanyDashboard() {
  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#0A2239] mb-2">Company Dashboard</h1>
          <p className="text-gray-600">Manage your buses and schedules</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <Bus className="w-8 h-8 text-[#0057A4]" />
              <div>
                <p className="text-2xl font-bold text-[#0A2239]">12</p>
                <p className="text-gray-600">Active Buses</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <Calendar className="w-8 h-8 text-[#00B4A2]" />
              <div>
                <p className="text-2xl font-bold text-[#0A2239]">47</p>
                <p className="text-gray-600">Schedules</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <Users className="w-8 h-8 text-[#FF7A00]" />
              <div>
                <p className="text-2xl font-bold text-[#0A2239]">1,247</p>
                <p className="text-gray-600">Bookings</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <DollarSign className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-2xl font-bold text-[#0A2239]">MWK 8.7M</p>
                <p className="text-gray-600">Revenue</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-[#0A2239] mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-[#0057A4] hover:shadow-md transition-all text-center group">
              <Plus className="w-8 h-8 text-[#0057A4] mx-auto mb-2 group-hover:scale-110 transition-transform" />
              <span className="font-semibold text-[#0A2239]">Add New Bus</span>
            </button>
            
            <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-[#0057A4] hover:shadow-md transition-all text-center group">
              <Calendar className="w-8 h-8 text-[#00B4A2] mx-auto mb-2 group-hover:scale-110 transition-transform" />
              <span className="font-semibold text-[#0A2239]">Create Schedule</span>
            </button>
            
            <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-[#0057A4] hover:shadow-md transition-all text-center group">
              <DollarSign className="w-8 h-8 text-[#FF7A00] mx-auto mb-2 group-hover:scale-110 transition-transform" />
              <span className="font-semibold text-[#0A2239]">Request Cashout</span>
            </button>
            
            <button className="p-4 border-2 border-gray-200 rounded-lg hover:border-[#0057A4] hover:shadow-md transition-all text-center group">
              <BarChart3 className="w-8 h-8 text-green-500 mx-auto mb-2 group-hover:scale-110 transition-transform" />
              <span className="font-semibold text-[#0A2239]">View Analytics</span>
            </button>
          </div>
        </div>

        {/* Recent Bookings Section */}
        <div className="mt-8 bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-[#0A2239] mb-4">Recent Bookings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <p className="font-semibold text-[#0A2239]">UTK-AB12CD34</p>
                <p className="text-gray-600 text-sm">Lilongwe → Blantyre</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-[#0A2239]">MWK 15,000</p>
                <p className="text-green-600 text-sm">Confirmed</p>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div>
                <p className="font-semibold text-[#0A2239]">UTK-EF56GH78</p>
                <p className="text-gray-600 text-sm">Blantyre → Mzuzu</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-[#0A2239]">MWK 18,000</p>
                <p className="text-green-600 text-sm">Confirmed</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}