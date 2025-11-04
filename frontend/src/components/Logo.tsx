// src/components/Logo.tsx - Original Clean Style
import React from 'react';
import { Bus, Ticket } from 'lucide-react';

export function Logo() {
  return (
    <div className="flex items-center gap-2 cursor-pointer">
      {/* Simple Bus & Ticket Icons */}
      <div className="flex items-center gap-1">
        <Bus className="w-6 h-6 text-[#0057A4]" />
        <Ticket className="w-5 h-5 text-[#00B4A2]" />
      </div>
      
      {/* Original Text Style */}
      <div>
        <h1 className="text-xl font-bold text-[#0A2239]">Ulendo Tiketi</h1>
        <p className="text-xs text-[#0057A4] -mt-1">Book with Ease, Travel in Peace</p>
      </div>
    </div>
  );
}