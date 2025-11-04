import React from 'react';
import { Armchair } from 'lucide-react';

interface SeatMapProps {
  selectedSeat: number | null;
  onSeatSelect: (seat: number) => void;
  bookedSeats: number[];
  capacity: number;
}

export function SeatMap({ selectedSeat, onSeatSelect, bookedSeats, capacity }: SeatMapProps) {
  const seats = Array.from({ length: capacity }, (_, i) => i + 1);

  return (
    <div className="bg-white rounded-xl p-6">
      <h3 className="text-lg font-semibold text-[#0A2239] mb-4">Select Your Seat</h3>
      
      {/* Bus Layout */}
      <div className="relative mb-8">
        <div className="text-center mb-4 bg-gray-100 py-2 rounded-lg">
          <span className="text-sm font-semibold text-gray-600">🚌 Driver</span>
        </div>
        
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
          {seats.map((seat) => {
            const isBooked = bookedSeats.includes(seat);
            const isSelected = selectedSeat === seat;

            return (
              <button
                key={seat}
                disabled={isBooked}
                onClick={() => onSeatSelect(seat)}
                className={`
                  aspect-square rounded-lg font-semibold text-sm transition-all
                  ${isBooked
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : isSelected
                    ? 'bg-[#0057A4] text-white shadow-md'
                    : 'bg-white border-2 border-gray-300 hover:border-[#0057A4] text-[#0A2239]'
                  }
                `}
              >
                {seat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-6 text-sm">
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
  );
}