import React, { useState, useRef, useEffect } from 'react';
import { Smartphone, Camera, Zap, CheckCircle2, AlertCircle, MapPin, Clock } from 'lucide-react';
import { apiService } from '../services/api';

export default function ConductorDashboard() {
  const [busId, setBusId] = useState('');
  const [qrInput, setQrInput] = useState('');
  const [useCamera, setUseCamera] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

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
      setMessage({ type: 'error', text: 'Failed to validate QR code' });
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setMessage({ type: 'error', text: 'QR code image decoding requires jsQR library' });
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });

      if (cameraRef.current) {
        cameraRef.current.srcObject = stream;
      }
      setUseCamera(true);
    } catch {
      setMessage({ type: 'error', text: 'Camera access denied' });
    }
  };

  const stopCamera = () => {
    if (cameraRef.current?.srcObject) {
      (cameraRef.current.srcObject as MediaStream)
        .getTracks()
        .forEach((track) => track.stop());
    }
    setUseCamera(false);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  return (
    <div className="min-h-screen bg-[#F2F4F7] py-8">
      <div className="max-w-2xl mx-auto px-4">

        <h1 className="text-3xl font-bold text-[#0A2239] mb-2">Conductor QR Scanner</h1>
        <p className="text-gray-600 mb-6">Scan passenger tickets for boarding</p>

        {message && (
          <div
            className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
              message.type === 'success'
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            {message.text}
          </div>
        )}

        {/* BUS ID INPUT */}
        <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
          <h2 className="text-lg font-semibold mb-3">Bus Information</h2>

          <input
            type="text"
            placeholder="Enter Bus ID (e.g. 1)"
            value={busId}
            onChange={(e) => setBusId(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg"
          />

          <p className="text-sm text-gray-600 mt-2">
            This must match the bus you are operating
          </p>
        </div>

        {/* SCANNER OPTIONS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">

          {/* MANUAL ENTRY */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Smartphone className="w-6 h-6 text-blue-600" />
              <h3 className="font-semibold">Manual Input</h3>
            </div>

            <input
              type="text"
              placeholder="Paste QR Code Reference"
              value={qrInput}
              onChange={(e) => setQrInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleScanQR()}
              className="w-full px-4 py-2 border rounded-lg mb-3"
            />

            <button
              onClick={handleScanQR}
              disabled={isScanning}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white py-2 rounded-lg"
            >
              {isScanning ? 'Scanning...' : 'Validate QR'}
            </button>
          </div>

          {/* IMAGE / CAMERA */}
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Camera className="w-6 h-6 text-teal-600" />
              <h3 className="font-semibold">Image Upload</h3>
            </div>

            {!useCamera ? (
              <>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white py-2 rounded-lg mb-2"
                >
                  Upload QR Image
                </button>

                <button
                  onClick={startCamera}
                  className="w-full bg-gray-700 hover:bg-gray-800 text-white py-2 rounded-lg"
                >
                  Start Camera
                </button>

                <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />
              </>
            ) : (
              <button
                onClick={stopCamera}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg"
              >
                Stop Camera
              </button>
            )}

            <p className="text-xs text-gray-500 mt-3">
              Camera scanning requires a QR decoding library
            </p>
          </div>
        </div>

        {/* CAMERA PREVIEW */}
        {useCamera && (
          <div className="bg-white rounded-xl p-4 shadow-sm mb-6">
            <video ref={cameraRef} autoPlay playsInline className="w-full rounded-lg" />
          </div>
        )}

        {/* RESULT */}
        {scanResult && (
          <div
            className={`rounded-xl p-6 ${
              scanResult.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="flex items-start gap-3 mb-4">
              {scanResult.success ? (
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              ) : (
                <AlertCircle className="w-8 h-8 text-red-600" />
              )}

              <div>
                <h3 className="font-semibold text-lg">
                  {scanResult.success ? 'Ticket Validated' : 'Validation Failed'}
                </h3>
                <p className="text-sm">
                  {scanResult.message}
                </p>
              </div>
            </div>

            {scanResult.success && (
              <div className="bg-white p-4 rounded-lg space-y-3">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">Passenger Name:</span>
                  <span className="font-semibold">{scanResult.passenger_name}</span>
                </div>

                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-600">Seat Number:</span>
                  <span className="font-semibold">Seat {scanResult.seat_number}</span>
                </div>

                <div className="flex items-center gap-2 border-b pb-2">
                  <MapPin className="w-4 h-4 text-gray-600" />
                  <span className="text-sm">{scanResult.route}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-600" />
                  <span className="text-sm">
                    {new Date(scanResult.departure_time).toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            <button
              onClick={() => setScanResult(null)}
              className="w-full mt-4 bg-blue-700 hover:bg-blue-800 text-white py-2 rounded-lg"
            >
              Scan Next Ticket
            </button>
          </div>
        )}

        {/* Instructions */}
        {!scanResult && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <Zap className="w-6 h-6 text-blue-600" />
              <div>
                <h3 className="font-semibold">How to Use</h3>
                <ul className="text-sm mt-2 space-y-1">
                  <li>1. Enter the bus ID</li>
                  <li>2. Paste QR reference or upload/scan QR image</li>
                  <li>3. System validates ticket & confirms boarding</li>
                </ul>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
