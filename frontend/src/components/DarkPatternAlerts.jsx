import React from 'react';
import { AlertCircle, AlertTriangle } from 'lucide-react';

export default function DarkPatternAlerts({ patterns, summaryReasons }) {
  const hasPatterns = patterns && patterns.length > 0;
  const hasReasons = summaryReasons && summaryReasons.length > 0;

  if (!hasPatterns && !hasReasons) {
    return null;
  }

  return (
    <div className="p-6 bg-white border border-gray-200 rounded-xl space-y-4">
      <h3 className="text-base font-bold text-gray-800 flex items-center gap-2">
        <AlertTriangle size={18} className="text-amber-500" />
        <span>Flagged Deceptions & Anomaly Alerts</span>
      </h3>

      {/* Dark Patterns */}
      {hasPatterns && (
        <div className="space-y-2">
          {patterns.map((p, idx) => (
            <div key={idx} className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-900 flex items-start gap-2.5">
              <AlertCircle size={17} className="text-amber-600 mt-0.5 shrink-0" />
              <div>
                <strong className="font-semibold block text-xs uppercase text-amber-700 tracking-wider">
                  {p.type.replace(/_/g, ' ')}
                </strong>
                <span>{p.description}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Reasons */}
      {hasReasons && (
        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1 pl-1">
          {summaryReasons.map((reason, idx) => (
            <li key={idx}>{reason}</li>
          ))}
        </ul>
      )}
    </div>
  );
}