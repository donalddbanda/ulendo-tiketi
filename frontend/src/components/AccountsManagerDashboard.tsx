import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, RefreshCcw } from 'lucide-react';
import { apiService } from '../services/api';

export default function AccountsManagerDashboard() {
  const [companyBalance, setCompanyBalance] = useState(0);
  const [payouts, setPayouts] = useState<any[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch company balance and payout history
  const fetchBalance = async () => {
    try {
      const res = await apiService.getCompanyBalance(); // GET /accounts/balance
      setCompanyBalance(res.balance || 0);
      setPayouts(res.payouts || []);
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Failed to fetch balance and payouts' });
    }
  };

  useEffect(() => {
    fetchBalance();
  }, []);

  // Request payout
  const handlePayoutRequest = async () => {
    try {
      setLoading(true);
      await apiService.requestPayout(); // POST /accounts/payout
      setMessage({ type: 'success', text: 'Payout request sent successfully' });
      fetchBalance();
    } catch (err: any) {
      console.error(err);
      setMessage({ type: 'error', text: err?.message || 'Failed to request payout' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-[#0A2239] mb-6">Accounts Manager Dashboard</h1>

        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            {message.text}
          </div>
        )}

        {/* Company Balance */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-lg font-semibold text-[#0A2239] mb-4">Company Balance</h2>
          <p className="text-2xl font-bold text-[#0057A4]">${companyBalance.toFixed(2)}</p>
          <button
            onClick={handlePayoutRequest}
            disabled={loading || companyBalance <= 0}
            className="mt-4 bg-[#0057A4] text-white px-4 py-2 rounded-lg hover:bg-[#003D7A] transition-all disabled:opacity-50"
          >
            {loading ? 'Requesting...' : 'Request Payout'}
          </button>
        </div>

        {/* Payout History */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="text-lg font-semibold text-[#0A2239]">Payout History</h2>
            <button onClick={fetchBalance} className="ml-auto bg-gray-200 px-2 py-1 rounded hover:bg-gray-300 flex items-center gap-1">
              <RefreshCcw className="w-4 h-4" /> Refresh
            </button>
          </div>

          {payouts.length === 0 ? (
            <p className="text-gray-600">No payout requests yet.</p>
          ) : (
            <table className="w-full text-left border border-gray-200">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2">Amount</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {payouts.map((p, idx) => (
                  <tr key={idx} className="border-t border-gray-200">
                    <td className="px-4 py-2">${p.amount.toFixed(2)}</td>
                    <td className="px-4 py-2">{p.status}</td>
                    <td className="px-4 py-2">{new Date(p.date).toLocaleDateString()}</td>
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
