import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Building, 
  Route, 
  CreditCard, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  XCircle,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Search,
  Filter,
  Download
} from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, change, icon, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-[#0A2239] mt-1">{value}</p>
          <p className={`text-sm mt-1 ${change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
            {change}
          </p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

interface User {
  id: string;
  name: string;
  email: string;
  role: 'passenger' | 'company' | 'admin';
  status: 'active' | 'suspended';
  joinDate: string;
}

interface Company {
  id: string;
  name: string;
  contact: string;
  buses: number;
  status: 'verified' | 'pending' | 'rejected';
  joinDate: string;
}

interface CashoutRequest {
  id: string;
  company: string;
  amount: string;
  date: string;
  status: 'pending' | 'approved' | 'rejected';
}

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'companies' | 'cashouts'>('overview');
  const [users, setUsers] = useState<User[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [cashoutRequests, setCashoutRequests] = useState<CashoutRequest[]>([]);

  useEffect(() => {
    // Mock data - replace with actual API calls
    loadMockData();
  }, []);

  const loadMockData = () => {
    // Mock users
    const mockUsers: User[] = [
      {
        id: '1',
        name: 'John Banda',
        email: 'john@example.com',
        role: 'passenger',
        status: 'active',
        joinDate: '2024-10-15'
      },
      {
        id: '2',
        name: 'Sarah Mwale',
        email: 'sarah@example.com',
        role: 'company',
        status: 'active',
        joinDate: '2024-10-12'
      },
      {
        id: '3',
        name: 'Mike Juma',
        email: 'mike@example.com',
        role: 'passenger',
        status: 'suspended',
        joinDate: '2024-10-10'
      }
    ];

    // Mock companies
    const mockCompanies: Company[] = [
      {
        id: '1',
        name: 'Malawi Bus Company',
        contact: '+265 991 234 567',
        buses: 12,
        status: 'verified',
        joinDate: '2024-09-01'
      },
      {
        id: '2',
        name: 'ABC Transport',
        contact: '+265 992 345 678',
        buses: 8,
        status: 'pending',
        joinDate: '2024-10-15'
      },
      {
        id: '3',
        name: 'Express Travel',
        contact: '+265 993 456 789',
        buses: 6,
        status: 'verified',
        joinDate: '2024-09-20'
      }
    ];

    // Mock cashout requests
    const mockCashouts: CashoutRequest[] = [
      {
        id: '1',
        company: 'Malawi Bus Company',
        amount: 'MWK 245,000',
        date: '2024-11-10',
        status: 'pending'
      },
      {
        id: '2',
        company: 'Express Travel',
        amount: 'MWK 180,500',
        date: '2024-11-09',
        status: 'approved'
      },
      {
        id: '3',
        company: 'ABC Transport',
        amount: 'MWK 95,000',
        date: '2024-11-08',
        status: 'rejected'
      }
    ];

    setUsers(mockUsers);
    setCompanies(mockCompanies);
    setCashoutRequests(mockCashouts);
  };

  const handleApproveCashout = (id: string) => {
    setCashoutRequests(prev => 
      prev.map(req => 
        req.id === id ? { ...req, status: 'approved' } : req
      )
    );
  };

  const handleRejectCashout = (id: string) => {
    setCashoutRequests(prev => 
      prev.map(req => 
        req.id === id ? { ...req, status: 'rejected' } : req
      )
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'verified':
      case 'approved':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'suspended':
      case 'rejected':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'company':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#0A2239] mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Manage the Ulendo Tiketi platform</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Users"
            value="1,847"
            change="+12%"
            icon={<Users className="w-6 h-6 text-[#0057A4]" />}
            color="bg-blue-50"
          />
          <StatCard
            title="Bus Companies"
            value="24"
            change="+8%"
            icon={<Building className="w-6 h-6 text-[#00B4A2]" />}
            color="bg-teal-50"
          />
          <StatCard
            title="Active Routes"
            value="56"
            change="+15%"
            icon={<Route className="w-6 h-6 text-[#FF7A00]" />}
            color="bg-orange-50"
          />
          <StatCard
            title="Platform Revenue"
            value="MWK 4.2M"
            change="+22%"
            icon={<CreditCard className="w-6 h-6 text-green-500" />}
            color="bg-green-50"
          />
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-xl shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {[
                { id: 'overview', name: 'Overview', icon: TrendingUp },
                { id: 'users', name: 'Users', icon: Users },
                { id: 'companies', name: 'Companies', icon: Building },
                { id: 'cashouts', name: 'Cashouts', icon: CreditCard },
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-2 py-4 px-6 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-[#0057A4] text-[#0057A4]'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-[#0A2239] mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                      {[
                        { action: 'New booking from John Banda', time: '2 min ago', type: 'booking' },
                        { action: 'Malawi Bus Company registered', time: '1 hour ago', type: 'registration' },
                        { action: 'Cashout request from ABC Transport', time: '3 hours ago', type: 'cashout' },
                        { action: 'User Sarah Mwale updated profile', time: '5 hours ago', type: 'update' },
                      ].map((activity, index) => (
                        <div key={index} className="flex items-center gap-3 p-3 bg-white rounded-lg shadow-sm">
                          <div className={`w-2 h-2 rounded-full ${
                            activity.type === 'booking' ? 'bg-green-500' :
                            activity.type === 'registration' ? 'bg-blue-500' :
                            activity.type === 'cashout' ? 'bg-orange-500' : 'bg-purple-500'
                          }`}></div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-[#0A2239]">{activity.action}</p>
                            <p className="text-xs text-gray-500">{activity.time}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-[#0A2239] mb-4">Quick Actions</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-all text-center">
                        <Users className="w-6 h-6 text-[#0057A4] mx-auto mb-2" />
                        <span className="text-sm font-medium text-[#0A2239]">Manage Users</span>
                      </button>
                      <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-all text-center">
                        <Building className="w-6 h-6 text-[#00B4A2] mx-auto mb-2" />
                        <span className="text-sm font-medium text-[#0A2239]">Verify Companies</span>
                      </button>
                      <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-all text-center">
                        <CreditCard className="w-6 h-6 text-[#FF7A00] mx-auto mb-2" />
                        <span className="text-sm font-medium text-[#0A2239]">Process Cashouts</span>
                      </button>
                      <button className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-all text-center">
                        <Route className="w-6 h-6 text-purple-500 mx-auto mb-2" />
                        <span className="text-sm font-medium text-[#0A2239]">View Routes</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Users Tab */}
            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-[#0A2239]">User Management</h3>
                  <div className="flex gap-3">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search users..."
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent"
                      />
                    </div>
                    <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2">
                      <Filter className="w-4 h-4" />
                      Filter
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">User</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Role</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Join Date</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4">
                            <div>
                              <p className="font-medium text-[#0A2239]">{user.name}</p>
                              <p className="text-sm text-gray-600">{user.email}</p>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRoleColor(user.role)}`}>
                              {user.role}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(user.status)}`}>
                              {user.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {new Date(user.joinDate).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex gap-2">
                              <button className="p-1 hover:bg-gray-100 rounded">
                                <Eye className="w-4 h-4 text-gray-600" />
                              </button>
                              <button className="p-1 hover:bg-gray-100 rounded">
                                <Edit className="w-4 h-4 text-blue-600" />
                              </button>
                              <button className="p-1 hover:bg-gray-100 rounded">
                                <Trash2 className="w-4 h-4 text-red-600" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Companies Tab */}
            {activeTab === 'companies' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-[#0A2239]">Bus Company Management</h3>
                  <div className="flex gap-3">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search companies..."
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0057A4] focus:border-transparent"
                      />
                    </div>
                    <button className="px-4 py-2 bg-[#0057A4] text-white rounded-lg hover:bg-[#0057A4]/90 flex items-center gap-2">
                      <Download className="w-4 h-4" />
                      Export
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Company</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Contact</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Buses</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Join Date</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {companies.map((company) => (
                        <tr key={company.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4">
                            <p className="font-medium text-[#0A2239]">{company.name}</p>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {company.contact}
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                              {company.buses} buses
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(company.status)}`}>
                              {company.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {new Date(company.joinDate).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex gap-2">
                              <button className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm hover:bg-green-200">
                                Verify
                              </button>
                              <button className="p-1 hover:bg-gray-100 rounded">
                                <MoreVertical className="w-4 h-4 text-gray-600" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Cashouts Tab */}
            {activeTab === 'cashouts' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-[#0A2239]">Cashout Requests</h3>
                  <div className="text-sm text-gray-600">
                    {cashoutRequests.filter(req => req.status === 'pending').length} pending requests
                  </div>
                </div>

                <div className="space-y-4">
                  {cashoutRequests.map((request) => (
                    <div key={request.id} className="bg-white border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`p-3 rounded-lg ${
                            request.status === 'pending' ? 'bg-yellow-50' :
                            request.status === 'approved' ? 'bg-green-50' : 'bg-red-50'
                          }`}>
                            {request.status === 'pending' && <AlertCircle className="w-6 h-6 text-yellow-600" />}
                            {request.status === 'approved' && <CheckCircle className="w-6 h-6 text-green-600" />}
                            {request.status === 'rejected' && <XCircle className="w-6 h-6 text-red-600" />}
                          </div>
                          <div>
                            <p className="font-medium text-[#0A2239]">{request.company}</p>
                            <p className="text-sm text-gray-600">Requested on {new Date(request.date).toLocaleDateString()}</p>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <p className="text-lg font-bold text-[#0A2239]">{request.amount}</p>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(request.status)}`}>
                            {request.status}
                          </span>
                        </div>

                        {request.status === 'pending' && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleApproveCashout(request.id)}
                              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2"
                            >
                              <CheckCircle className="w-4 h-4" />
                              Approve
                            </button>
                            <button
                              onClick={() => handleRejectCashout(request.id)}
                              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center gap-2"
                            >
                              <XCircle className="w-4 h-4" />
                              Reject
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}