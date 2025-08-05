import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function LiveProgressBar({ taskId, onComplete, onError }) {
  const [progress, setProgress] = useState(5);
  const [stepMessage, setStepMessage] = useState('Connecting to real-time service...');
  const [isFailed, setIsFailed] = useState(false);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    // Connect to Django Channels WebSocket
    const wsUrl = `ws://localhost:8000/ws/progress/${taskId}/`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setStepMessage('Connected. Awaiting scraping pipeline...');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Discard subscription handshake
        if (data.status === 'connected') return;

        if (data.progress !== undefined) {
          setProgress(data.progress);
        }

        if (data.message) {
          setStepMessage(data.message);
        }

        if (data.step === 'FAILED') {
          setIsFailed(true);
          if (onError) onError(data.message);
        }

        if (data.step === 'COMPLETED') {
          setIsDone(true);
          if (onComplete && data.data?.product_id) {
            onComplete(data.data.product_id);
          }
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      setStepMessage('WebSocket connection interrupted.');
    };

    socket.onclose = () => {
      console.log('WebSocket closed.');
    };

    return () => {
      socket.close();
    };
  }, [taskId]);

  return (
    <div className="w-full max-w-3xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-gray-100 space-y-4">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 font-medium text-gray-700">
          {isFailed ? (
            <AlertTriangle className="text-red-500 animate-pulse" size={18} />
          ) : isDone ? (
            <CheckCircle2 className="text-green-500" size={18} />
          ) : (
            <Loader2 className="text-blue-500 animate-spin" size={18} />
          )}
          <span>{stepMessage}</span>
        </div>
        <span className="font-semibold text-gray-600">{progress}%</span>
      </div>

      {/* Progress Bar Track */}
      <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full transition-all duration-500 ease-out ${
            isFailed
              ? 'bg-red-500'
              : isDone
              ? 'bg-green-500'
              : 'bg-blue-600'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}