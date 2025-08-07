import React from 'react';
import { Shield, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function TrustScoreBadge({ trustScore, fakeReviewPct, rawRating }) {
  const getScoreColor = (score) => {
    if (score >= 75) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 50) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getScoreIcon = (score) => {
    if (score >= 75) return <ShieldCheck className="text-green-600" size={36} />;
    if (score >= 50) return <Shield className="text-amber-600" size={36} />;
    return <ShieldAlert className="text-red-600" size={36} />;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* True Trust Score */}
      <div className={`p-6 rounded-xl border flex items-center gap-4 ${getScoreColor(trustScore)}`}>
        <div>{getScoreIcon(trustScore)}</div>
        <div>
          <div className="text-xs uppercase font-semibold tracking-wider">True Trust Score</div>
          <div className="text-3xl font-extrabold">{trustScore}<span className="text-lg font-normal text-gray-500">/100</span></div>
        </div>
      </div>

      {/* Manipulated Reviews Percentage */}
      <div className="p-6 rounded-xl border border-gray-200 bg-white flex flex-col justify-center">
        <span className="text-xs uppercase font-semibold text-gray-400">Suspicious Reviews</span>
        <span className="text-3xl font-extrabold text-gray-800">
          {fakeReviewPct}%
        </span>
        <span className="text-xs text-gray-500 mt-1">Identified as spun, duplicate, or unverified</span>
      </div>

      {/* Raw Rating vs Adjusted */}
      <div className="p-6 rounded-xl border border-gray-200 bg-white flex flex-col justify-center">
        <span className="text-xs uppercase font-semibold text-gray-400">Platform Star Rating</span>
        <span className="text-3xl font-extrabold text-gray-800">
          {rawRating ? `${rawRating} ★` : 'N/A'}
        </span>
        <span className="text-xs text-gray-500 mt-1">Reported by seller listing</span>
      </div>
    </div>
  );
}