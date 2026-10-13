import React from 'react';
import { ShieldAlert, Cpu, Layers } from 'lucide-react';

export default function SummaryCard({
  summary,
  summaryHi,
  summaryTa,
  totalClauses,
  flaggedCount,
  parseMethod,
  fileName,
  language = 'en'
}) {
  const isHindi = language === 'hi';
  const isTamil = language === 'ta';

  const displaySummary =
    isTamil && summaryTa
      ? summaryTa
      : isHindi && summaryHi
      ? summaryHi
      : summary;

  const titleText = isTamil
    ? "ஆவணச் சுருக்கம் (Summary)"
    : isHindi
    ? "दस्तावेज़ का सारांश (Summary)"
    : "Document Summary";

  const clausesText = isTamil
    ? `${totalClauses} பிரிவுகள்`
    : isHindi
    ? `${totalClauses} खंड`
    : `${totalClauses} Clauses`;

  const risksText = isTamil
    ? `${flaggedCount} இடர்கள் கண்டறியப்பட்டன`
    : isHindi
    ? `${flaggedCount} जोखिम चिह्नित`
    : `${flaggedCount} Flagged Risks`;

  const langClass = isTamil ? 'lang-ta leading-[1.85]' : isHindi ? 'lang-hi leading-[1.75]' : 'leading-relaxed';

  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-6 mb-6 overflow-hidden ${isTamil ? 'lang-ta' : isHindi ? 'lang-hi' : ''}`}>
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-100 pb-4 mb-4 gap-3">
        <div className="min-w-0">
          <span className="text-xs font-bold tracking-wider text-blue-600 uppercase block break-words">{titleText}</span>
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 mt-0.5 truncate">{fileName || 'Uploaded Agreement'}</h2>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="bg-blue-50 text-blue-700 px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 shrink-0" />
            <span className="break-words">{clausesText}</span>
          </div>

          <div className={`px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
            flaggedCount > 0 ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'
          }`}>
            <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
            <span className="break-words">{risksText}</span>
          </div>

          <div className="bg-slate-100 text-slate-600 px-2.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 shrink-0" />
            <span className="capitalize">{parseMethod}</span>
          </div>
        </div>
      </div>

      <div className={`text-slate-700 text-sm whitespace-pre-line break-words bg-slate-50 p-4 rounded-lg border border-slate-100 ${langClass}`}>
        {displaySummary}
      </div>
    </div>
  );
}
