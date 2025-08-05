import React, { useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import UrlInput from './components/UrlInput';
import LiveProgressBar from './components/LiveProgressBar';
import { triggerAnalysis, fetchProductReport } from './api/client';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [productData, setProductData] = useState(null);

  const handleUrlSubmit = async (url) => {
    setLoading(true);
    setProductData(null);
    setTaskId(null);

    try {
      const data = await triggerAnalysis(url);
      setTaskId(data.task_id);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to submit URL.');
      setLoading(false);
    }
  };

  const handleTaskComplete = async (productId) => {
    setLoading(false);
    try {
      const report = await fetchProductReport(productId);
      setProductData(report);
    } catch (err) {
      console.error('Failed to load completed report:', err);
    }
  };

  const handleTaskError = (message) => {
    setLoading(false);
    alert(message || 'An error occurred during analysis.');
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Navbar */}
      <header className="bg-white border-b border-gray-200 py-4 px-8">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="text-blue-600" size={28} />
            <span className="text-xl font-bold tracking-tight">TrustLens</span>
          </div>
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Review & Dark Pattern Detector
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-extrabold text-gray-900">
            Uncover the Real Trust Score
          </h1>
          <p className="text-gray-600 max-w-xl mx-auto">
            Analyze review velocities, catch spun bot clusters, and expose artificial pre-sale price hikes.
          </p>
        </div>

        <UrlInput onSubmit={handleUrlSubmit} isLoading={loading} />

        {taskId && (
          <LiveProgressBar
            taskId={taskId}
            onComplete={handleTaskComplete}
            onError={handleTaskError}
          />
        )}

        {productData && (
          <div className="max-w-3xl mx-auto p-6 bg-white border border-gray-200 rounded-xl shadow-sm text-center">
            <h3 className="text-lg font-bold text-gray-800 mb-1">{productData.title}</h3>
            <p className="text-sm text-gray-500">
              Scraped Trust Score: <strong>{productData.analysis_report?.trust_score ?? 'N/A'} / 100</strong>
            </p>
          </div>
        )}
      </main>
    </div>
  );
}