import React from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Bus, MapPin, Calendar, Clock, User } from 'lucide-react';

interface TicketProps {
  booking: {
    booking_reference: string;
    passenger_name: string;
    passenger_phone: string;
    schedule: {
      departure_time: string;
      arrival_time: string;
      bus: {
        bus_number: string;
        company: {
          name: string;
        };
      };
      route: {
        origin: string;
        destination: string;
      };
    };
    seat_number: number;
  };
}

export function Ticket({ booking }: TicketProps) {
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const ticketData = JSON.stringify({
    reference: booking.booking_reference,
    passenger: booking.passenger_name,
    route: `${booking.schedule.route.origin} → ${booking.schedule.route.destination}`,
    seat: booking.seat_number,
    date: booking.schedule.departure_time,
  });

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden max-w-md mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#0057A4] to-[#00B4A2] p-6 text-white text-center">
        <h2 className="text-2xl font-bold">Ulendo Tiketi</h2>
        <p className="text-sm opacity-90">Digital Travel Ticket</p>
      </div>

      {/* Body */}
      <div className="p-6">
        {/* Route */}
        <div className="flex items-center justify-between mb-6">
          <div className="text-center">
            <div className="text-lg font-bold text-[#0A2239]">{booking.schedule.route.origin}</div>
            <div className="text-sm text-gray-600">Origin</div>
          </div>
          <div className="text-[#FF7A00] font-bold text-xl">→</div>
          <div className="text-center">
            <div className="text-lg font-bold text-[#0A2239]">{booking.schedule.route.destination}</div>
            <div className="text-sm text-gray-600">Destination</div>
          </div>
        </div>

        {/* Details */}
        <div className="space-y-3 mb-6">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Passenger</span>
            <span className="font-semibold text-[#0A2239] flex items-center gap-2">
              <User className="w-4 h-4" />
              {booking.passenger_name}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Date</span>
            <span className="font-semibold text-[#0A2239] flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              {formatDate(booking.schedule.departure_time)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Departure</span>
            <span className="font-semibold text-[#0A2239] flex items-center gap-2">
              <Clock className="w-4 h-4" />
              {formatTime(booking.schedule.departure_time)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Bus Company</span>
            <span className="font-semibold text-[#0A2239] flex items-center gap-2">
              <Bus className="w-4 h-4" />
              {booking.schedule.bus.company.name}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">Seat Number</span>
            <span className="font-bold text-[#0057A4] text-lg">{booking.seat_number}</span>
          </div>
        </div>

        {/* QR Code */}
        <div className="border-t pt-4 text-center">
          <div className="bg-gray-50 p-4 rounded-lg inline-block">
            <QRCodeSVG value={ticketData} size={150} />
          </div>
          <div className="mt-3 font-mono font-bold text-[#0057A4] text-lg">
            {booking.booking_reference}
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Show this QR code to the bus conductor when boarding
          </p>
        </div>
      </div>
    </div>
  );
}