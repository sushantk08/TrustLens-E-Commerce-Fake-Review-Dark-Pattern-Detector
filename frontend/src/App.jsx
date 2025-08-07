import React, { useState } from 'react';
import { ShieldCheck, ExternalLink } from 'lucide-react';
import UrlInput from './components/UrlInput';
import LiveProgressBar from './components/LiveProgressBar';
import TrustScoreBadge from './components/TrustScoreBadge';
import AspectSentimentGrid from './components/AspectSentimentGrid';
import DarkPatternAlerts from './components/DarkPatternAlerts';
import { triggerAnalysis, fetchProductReport } from './api/client';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [product, setProduct] = useState(null);

  const handleUrlSubmit = async (url) => {
    setLoading(true);
    setProduct(null);
    setTaskId(null);

    try {
      const data = await triggerAnalysis(url);
      setTaskId(data.task_id);
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to trigger analysis.');
      setLoading(false);
    }
  };

  const handleTaskComplete = async (productId) => {
    setLoading(false);
    try {
      const report = await fetchProductReport(productId);
      setProduct(report);
    } catch (err) {
      console.error('Failed to load completed report:', err);
    }
  };

  const handleTaskError = (msg) => {
    setLoading(false);
    alert(msg || 'An error occurred during analysis.');
  };

  const report = product?.analysis_report;

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
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

        {taskId && !product && (
          <LiveProgressBar
            taskId={taskId}
            onComplete={handleTaskComplete}
            onError={handleTaskError}
          />
        )}

        {product && report && (
          <div className="space-y-6">
            {/* Product Header */}
            <div className="p-6 bg-white border border-gray-200 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs font-semibold uppercase text-blue-600 tracking-wider">
                  {product.platform}
                </span>
                <h2 className="text-xl font-bold text-gray-900">{product.title || 'Product Analysis'}</h2>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Price: ₹{product.current_price || 'N/A'}</span>
                  <span>•</span>
                  <span>{product.total_reviews_count || product.reviews?.length || 0} reviews analyzed</span>
                </div>
              </div>

              <a
                href={product.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-1.5 shrink-0"
              >
                <span>View Listing</span>
                <ExternalLink size={14} />
              </a>
            </div>

            {/* Badges */}
            <TrustScoreBadge
              trustScore={report.trust_score}
              fakeReviewPct={report.fake_review_percentage}
              rawRating={product.rating}
            />

            {/* Dark Patterns & Warnings */}
            <DarkPatternAlerts
              patterns={report.dark_patterns_detected}
              summaryReasons={report.summary_reasons}
            />

            {/* Aspects Sentiment */}
            <AspectSentimentGrid aspects={report.aspects_sentiment} />
          </div>
        )}
      </main>
    </div>
  );
}