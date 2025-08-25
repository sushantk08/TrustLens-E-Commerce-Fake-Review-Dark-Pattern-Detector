import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function LiveProgressBar({ taskId, onComplete, onError }) {
  const [progress, setProgress] = useState(15);
  const [stepMessage, setStepMessage] = useState('Analysis running in background...');
  const [isFailed, setIsFailed] = useState(false);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    let isCompleted = false;

    // Resolve dynamic protocol: wss:// for https (production), ws:// for http (local)
    const apiBase = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const wsProtocol = apiBase.startsWith('https') ? 'wss://' : 'ws://';
    const host = apiBase.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProtocol}${host}/ws/progress/${taskId}/`;

    // 1. Try WebSocket Connection
    let socket = null;
    try {
      socket = new WebSocket(wsUrl);

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.status === 'connected') return;

          if (data.progress !== undefined) setProgress(data.progress);
          if (data.message) setStepMessage(data.message);

          if (data.step === 'FAILED') {
            setIsFailed(true);
            if (onError) onError(data.message);
          }

          if (data.step === 'COMPLETED') {
            isCompleted = true;
            setIsDone(true);
            setProgress(100);
            if (onComplete && data.data?.product_id) {
              onComplete(data.data.product_id);
            }
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };

      socket.onerror = () => {
        console.log('WebSocket closed, using polling fallback...');
      };
    } catch (e) {
      console.log('Using polling fallback...');
    }

    // 2. Polling Fallback
    const pollInterval = setInterval(async () => {
      if (isCompleted) {
        clearInterval(pollInterval);
        return;
      }

      try {
        const res = await fetch(`${apiBase}/api/products/lookup/?task_id=${taskId}`);
        if (res.ok) {
          const prod = await res.json();
          if (prod && prod.analysis_report) {
            isCompleted = true;
            clearInterval(pollInterval);
            setIsDone(true);
            setProgress(100);
            setStepMessage('Analysis complete.');
            if (onComplete) onComplete(prod.id);
          }
        }
      } catch (err) {
        // Continue polling
      }
    }, 3000);

    return () => {
      if (socket) socket.close();
      clearInterval(pollInterval);
    };
  }, [taskId]);

  return (
    <div className="w-full max-w-3xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-gray-100 space-y-4">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 font-medium text-gray-700">
          {isFailed ? (
            <AlertTriangle className="text-red-500" size={18} />
          ) : isDone ? (
            <CheckCircle2 className="text-green-500" size={18} />
          ) : (
            <Loader2 className="text-blue-500 animate-spin" size={18} />
          )}
          <span>{stepMessage}</span>
        </div>
        <span className="font-semibold text-gray-600">{progress}%</span>
      </div>

      <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full transition-all duration-500 ease-out ${
            isFailed ? 'bg-red-500' : isDone ? 'bg-green-500' : 'bg-blue-600'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}