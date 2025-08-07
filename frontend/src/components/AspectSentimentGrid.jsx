import React from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

export default function AspectSentimentGrid({ aspects }) {
  if (!aspects || Object.keys(aspects).length === 0) {
    return (
      <div className="p-6 bg-white border border-gray-200 rounded-xl text-sm text-gray-500 text-center">
        No specific product aspect clusters detected in scraped reviews.
      </div>
    );
  }

  return (
    <div className="p-6 bg-white border border-gray-200 rounded-xl space-y-4">
      <h3 className="text-base font-bold text-gray-800">Aspect-Based Sentiment Breakdown</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(aspects).map(([name, data]) => {
          const score = data.score;
          const isPositive = score >= 3.5;
          const isNegative = score < 2.5;

          return (
            <div key={name} className="p-4 rounded-lg border border-gray-100 bg-gray-50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-gray-800">{name}</span>
                <span
                  className={`text-sm font-bold px-2 py-0.5 rounded ${
                    isPositive
                      ? 'bg-green-100 text-green-700'
                      : isNegative
                      ? 'bg-red-100 text-red-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {score} / 5.0
                </span>
              </div>

              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <ThumbsUp size={13} className="text-green-600" /> {data.positive_mentions}
                </span>
                <span className="flex items-center gap-1">
                  <ThumbsDown size={13} className="text-red-600" /> {data.negative_mentions}
                </span>
                <span className="text-gray-400">({data.mentions} mentions)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}