import React from 'react';
import { Logo } from './Logo';

export function Footer() {
  return (
    <footer className="bg-[#0A2239] text-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <Logo />
            <p className="mt-4 text-gray-300">
              Your trusted partner for intercity bus travel in Malawi. Book with ease, travel in peace.
            </p>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li><a href="/" className="text-gray-300 hover:text-white transition-colors">Home</a></li>
              <li><a href="/search" className="text-gray-300 hover:text-white transition-colors">Book Tickets</a></li>
              <li><a href="/dashboard" className="text-gray-300 hover:text-white transition-colors">My Trips</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Support</h3>
            <ul className="space-y-2">
              <li><a href="/help" className="text-gray-300 hover:text-white transition-colors">Help Center</a></li>
              <li><a href="/contact" className="text-gray-300 hover:text-white transition-colors">Contact Us</a></li>
              <li><a href="/faq" className="text-gray-300 hover:text-white transition-colors">FAQ</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Contact Info</h3>
            <ul className="space-y-2 text-gray-300">
              <li>📞 +265 880 725061</li>
              <li>✉️ support@ulendotiketi.mw</li>
              <li>📍 Blantyre, Malawi</li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-600 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2025 Ulendo Tiketi. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}