import React, { useState } from 'react';
import { Search, Link as LinkIcon, AlertCircle } from 'lucide-react';

export default function UrlInput({ onSubmit, isLoading }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    const trimmed = url.trim().toLowerCase();
    if (!trimmed) {
      setError('Please enter a valid product URL.');
      return;
    }

    const isSupported = trimmed.includes('amazon') || trimmed.includes('flipkart') || trimmed.includes('google.') || trimmed.includes('goo.gl');
    if (!isSupported) {
      setError('Supported platforms: Amazon, Flipkart, and Google Maps.');
      return;
    }

    onSubmit(url.trim());
  };

  return (
    <div className="w-full max-w-3xl mx-auto p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <h2 className="text-xl font-semibold text-gray-800 mb-2">Inspect a Product</h2>
      <p className="text-sm text-gray-500 mb-4">
        Paste an Amazon or Flipkart link to detect review velocity spikes, bot rings, and deceptive pricing.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
            <LinkIcon size={18} />
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste Amazon, Flipkart, or Google Maps link (e.g. restaurant, hospital, showroom)..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-medium rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
        >
          <Search size={16} />
          <span>{isLoading ? 'Processing...' : 'Analyze'}</span>
        </button>
      </form>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-sm text-red-600">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}