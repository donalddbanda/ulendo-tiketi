import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, PlusCircle, Mail, Users, RefreshCcw } from 'lucide-react';
import { apiService } from '../services/api';

export default function AdminDashboard() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [newCompany, setNewCompany] = useState({
    name: '',
    email: '',
    phone_number: '',
    password: '',
    description: '',
    bank_name: '',
    bank_account_number: '',
    bank_account_name: ''
  });
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch all companies
  const fetchCompanies = async () => {
    try {
      const res = await apiService.getCompanies(); // Make sure apiService.getCompanies exists
      setCompanies(res.bus_companies || []);
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Failed to fetch companies' });
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  // Add / Register new company
  const handleAddCompany = async () => {
    const { name, email, phone_number, password, description, bank_name, bank_account_number, bank_account_name } = newCompany;
    if (!name || !email || !phone_number || !password) {
      setMessage({ type: 'error', text: 'Please fill all required fields' });
      return;
    }

    try {
      setLoading(true);
      await apiService.registerCompany({
        name,
        email,
        phone_number,
        password,
        description,
        bank_name,
        bank_account_number,
        bank_account_name
      });
      setMessage({ type: 'success', text: 'Company registered successfully' });
      setNewCompany({
        name: '',
        email: '',
        phone_number: '',
        password: '',
        description: '',
        bank_name: '',
        bank_account_number: '',
        bank_account_name: ''
      });
      fetchCompanies();
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: err?.message || 'Failed to register company' });
    } finally {
      setLoading(false);
    }
  };

  // Approve or Reject company
  const handleReviewCompany = async (id: number, action: 'approve' | 'reject') => {
    try {
      await apiService.reviewCompany(id, action);
      setMessage({ type: 'success', text: `Company ${action}d successfully` });
      fetchCompanies();
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: `Failed to ${action} company` });
    }
  };

  // Send password reset link
  const handleSendPasswordReset = async (email: string) => {
    try {
      await apiService.sendPasswordReset(email);
      setMessage({ type: 'success', text: `Password reset link sent to ${email}` });
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Failed to send password reset link' });
    }
  };

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-[#0A2239] mb-6">Admin Dashboard</h1>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            {message.text}
          </div>
        )}

        {/* Add Company */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <div className="flex items-center gap-2 mb-4">
            <PlusCircle className="w-6 h-6 text-[#0057A4]" />
            <h2 className="text-lg font-semibold text-[#0A2239]">Add New Company</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {['name','email','phone_number','password','description','bank_name','bank_account_number','bank_account_name'].map((field) => (
              <input
                key={field}
                type={field === 'email' ? 'email' : field === 'password' ? 'password' : 'text'}
                placeholder={field.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                value={(newCompany as any)[field]}
                onChange={(e) => setNewCompany({ ...newCompany, [field]: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0057A4]"
              />
            ))}
          </div>

          <button
            onClick={handleAddCompany}
            disabled={loading}
            className="mt-4 w-full bg-[#0057A4] text-white px-4 py-2 rounded-lg hover:bg-[#003D7A] transition-all disabled:opacity-50"
          >
            {loading ? 'Adding...' : 'Add Company'}
          </button>
        </div>

        {/* Company List */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-6 h-6 text-[#0057A4]" />
            <h2 className="text-lg font-semibold text-[#0A2239]">Registered Companies</h2>
            <button onClick={fetchCompanies} className="ml-auto bg-gray-200 px-2 py-1 rounded hover:bg-gray-300 flex items-center gap-1">
              <RefreshCcw className="w-4 h-4" /> Refresh
            </button>
          </div>

          {companies.length === 0 ? (
            <p className="text-gray-600">No companies registered yet.</p>
          ) : (
            <table className="w-full text-left border border-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2">Name</th>
                  <th className="px-4 py-2">Email</th>
                  <th className="px-4 py-2">Phone</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((c) => (
                  <tr key={c.id} className="border-t border-gray-200">
                    <td className="px-4 py-2">{c.name}</td>
                    <td className="px-4 py-2">{c.email}</td>
                    <td className="px-4 py-2">{c.phone_number}</td>
                    <td className="px-4 py-2">{c.is_active ? 'Active' : 'Pending'}</td>
                    <td className="px-4 py-2 flex gap-2">
                      {!c.is_active && (
                        <>
                          <button
                            onClick={() => handleReviewCompany(c.id, 'approve')}
                            className="bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReviewCompany(c.id, 'reject')}
                            className="bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleSendPasswordReset(c.email)}
                        className="bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 flex items-center gap-1"
                      >
                        <Mail className="w-4 h-4" /> Reset Password
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
