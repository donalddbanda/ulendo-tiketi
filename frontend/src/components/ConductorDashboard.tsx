import React, { useState, useRef } from 'react';
import { Smartphone, Camera, Zap, CheckCircle2, AlertCircle, MapPin, Clock } from 'lucide-react';
import { apiService } from '../services/api';

export default function ConductorDashboard() {
  const [busId, setBusId] = useState('');
  const [qrInput, setQrInput] = useState('');
  const [useCamera, setUseCamera] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const cameraRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleScanQR = async () => {
    if (!busId) return setMessage({ type: 'error', text: 'Please select a bus first' });
    if (!qrInput) return setMessage({ type: 'error', text: 'Please enter or scan QR code' });

    try {
      setIsScanning(true);
      const result = await apiService.scanQRCode(qrInput, busId);

      if (result.success) {
        setScanResult(result);
        setMessage({ type: 'success', text: 'Ticket validated!' });
        setQrInput('');
      } else {
        setScanResult(result);
        setMessage({ type: 'error', text: result.message });
      }
    } catch (err) {
      setScanResult(null);
      setMessage({ type: 'error', text: 'Failed to validate QR code' });
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setMessage({ type: 'error', text: 'QR code image decoding requires additional library (jsQR)' });
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (cameraRef.current) {
        cameraRef.current.srcObject = stream;
        setUseCamera(true);
      }
    } catch {
      setMessage({ type: 'error', text: 'Camera access denied' });
    }
  };

  const stopCamera = () => {
    if (cameraRef.current?.srcObject) {
      (cameraRef.current.srcObject as MediaStream).getTracks().forEach(track => track.stop());
      setUseCamera(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#0A2239] mb-2">Conductor QR Scanner</h1>
          <p className="text-gray-600">Scan passenger tickets for boarding</p>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            {message.text}
          </div>
        )}

        {/* Bus Selection */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-lg font-semibold text-[#0A2239] mb-4">Bus Information</h2>
          <input
            type="text"
            placeholder="Enter Bus ID (e.g., 1)"
            value={busId}
            onChange={(e) => setBusId(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0057A4]"
          />
          <p className="text-sm text-gray-600 mt-2">This should match the bus you are currently operating</p>
        </div>

        {/* QR Scanner Modes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Manual Input */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Smartphone className="w-6 h-6 text-[#0057A4]" />
              <h3 className="font-semibold text-[#0A2239]">Manual Input</h3>
            </div>
            <input
              type="text"
              placeholder="Paste QR code reference"
              value={qrInput}
              onChange={(e) => setQrInput(e.target.value)}
              onKeyPress={(e) => { if (e.key === 'Enter') handleScanQR(); }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0057A4] mb-3"
            />
            <button
              onClick={handleScanQR}
              disabled={isScanning}
              className="w-full bg-[#0057A4] text-white px-4 py-2 rounded-lg hover:bg-[#003D7A] transition-all disabled:opacity-50"
            >
              {isScanning ? 'Scanning...' : 'Validate QR'}
            </button>
          </div>

          {/* Camera/File Upload */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Camera className="w-6 h-6 text-[#00B4A2]" />
              <h3 className="font-semibold text-[#0A2239]">Image Upload</h3>
            </div>
            {!useCamera ? (
              <>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full bg-[#00B4A2] text-white px-4 py-2 rounded-lg hover:bg-[#009080] transition-all mb-2"
                >
                  Upload QR Image
                </button>
                <button
                  onClick={startCamera}
                  className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-all"
                >
                  Start Camera
                </button>
                <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
              </>
            ) : (
              <button
                onClick={stopCamera}
                className="w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-all"
              >
                Stop Camera
              </button>
            )}
            <p className="text-xs text-gray-600 mt-3">Camera scanning requires additional QR decoding library</p>
          </div>
        </div>

        {useCamera && (
          <div className="bg-white rounded-xl p-4 shadow-sm mb-6">
            <video ref={cameraRef} autoPlay playsInline className="w-full rounded-lg" />
          </div>
        )}

        {/* Scan Result */}
        {scanResult && (
          <div className={`rounded-xl p-6 shadow-sm ${scanResult.success ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'}`}>
            <div className="flex items-start gap-3 mb-4">
              {scanResult.success ? (
                <CheckCircle2 className="w-8 h-8 text-green-600 flex-shrink-0 mt-1" />
              ) : (
                <AlertCircle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
              )}
              <div className="flex-1">
                <h3 className={`font-semibold text-lg mb-1 ${scanResult.success ? 'text-green-700' : 'text-red-700'}`}>
                  {scanResult.success ? 'Ticket Validated' : 'Validation Failed'}
                </h3>
                <p className={scanResult.success ? 'text-green-600' : 'text-red-600'}>
                  {scanResult.message}
                </p>
              </div>
            </div>

            {scanResult.success && (
              <div className="bg-white rounded-lg p-4 space-y-3">
                <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                  <span className="text-gray-600">Passenger Name:</span>
                  <span className="font-semibold text-[#0A2239]">{scanResult.passenger_name}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                  <span className="text-gray-600">Seat Number:</span>
                  <span className="font-semibold text-[#0A2239]">Seat {scanResult.seat_number}</span>
                </div>
                <div className="flex items-center gap-2 pb-3 border-b border-gray-200">
                  <MapPin className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-600">{scanResult.route}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-600">{new Date(scanResult.departure_time).toLocaleString()}</span>
                </div>
              </div>
            )}

            <button
              onClick={() => { setScanResult(null); setQrInput(''); }}
              className="w-full mt-4 bg-[#0057A4] text-white px-4 py-2 rounded-lg hover:bg-[#003D7A] transition-all"
            >
              Scan Next Ticket
            </button>
          </div>
        )}

        {/* Instructions */}
        {!scanResult && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <Zap className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-blue-900 mb-2">How to Use</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>1. Enter the Bus ID you are currently operating</li>
                  <li>2. Ask passenger for their QR code reference</li>
                  <li>3. Paste the QR reference or upload/scan QR image</li>
                  <li>4. System validates ticket and confirms boarding</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
