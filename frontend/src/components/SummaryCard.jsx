import React from 'react';
import { FileCheck, ShieldAlert, Cpu, Layers } from 'lucide-react';

export default function SummaryCard({ summary, summaryHi, totalClauses, flaggedCount, parseMethod, fileName, language = 'en' }) {
  const isHindi = language === 'hi';
  const displaySummary = isHindi && summaryHi ? summaryHi : summary;
  const titleText = isHindi ? "दस्तावेज़ का सारांश (Summary)" : "Document Summary";
  const clausesText = isHindi ? `${totalClauses} क्लॉज` : `${totalClauses} Clauses`;
  const risksText = isHindi ? `${flaggedCount} जोखिम चिह्नित` : `${flaggedCount} Flagged Risks`;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-100 pb-4 mb-4 gap-4">
        <div>
          <span className="text-xs font-bold tracking-wider text-blue-600 uppercase">{titleText}</span>
          <h2 className="text-xl font-bold text-slate-900 mt-0.5">{fileName || 'Uploaded Agreement'}</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5" />
            <span>{clausesText}</span>
          </div>

          <div className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
            flaggedCount > 0 ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'
          }`}>
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>{risksText}</span>
          </div>

          <div className="bg-slate-100 text-slate-600 px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" />
            <span className="capitalize">{parseMethod}</span>
          </div>
        </div>
      </div>

      <div className="text-slate-700 text-sm leading-relaxed whitespace-pre-line bg-slate-50 p-4 rounded-lg border border-slate-100">
        {displaySummary}
      </div>
    </div>
  );
}
