import React, { useState } from 'react';
import { AlertOctagon, ChevronDown, ChevronUp, FileText, Info, HelpCircle } from 'lucide-react';

export default function FlaggedClauseCard({ clause, rank }) {
  const [showOriginal, setShowOriginal] = useState(false);
  const [showGrounding, setShowGrounding] = useState(false);

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'High':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'Medium':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
            #{rank}
          </span>
          <h3 className="font-bold text-slate-900 text-base">{clause.title}</h3>
          <span className="text-xs text-slate-500 font-mono">({clause.clause_id})</span>
        </div>

        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getSeverityBadge(clause.severity)}`}>
          {clause.severity} Risk Priority
        </span>
      </div>

      {/* Plain English Explanation */}
      <div className="bg-blue-50/70 border border-blue-100 rounded-lg p-3.5 mb-3">
        <div className="flex items-center gap-1.5 font-semibold text-xs text-blue-900 mb-1">
          <Info className="w-4 h-4 text-blue-600" />
          <span>What this clause means:</span>
        </div>
        <p className="text-sm text-slate-800 leading-relaxed font-medium">
          {clause.explanation}
        </p>
      </div>

      {/* Why it's risky */}
      <div className="bg-amber-50/70 border border-amber-100 rounded-lg p-3.5 mb-3">
        <div className="flex items-center gap-1.5 font-semibold text-xs text-amber-900 mb-1">
          <AlertOctagon className="w-4 h-4 text-amber-600" />
          <span>Why it's risky or one-sided:</span>
        </div>
        <p className="text-sm text-slate-800 leading-relaxed">
          {clause.risk_reason}
        </p>
      </div>

      {/* Collapsible Original Text & Vector Grounding */}
      <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
        <button
          onClick={() => setShowOriginal(!showOriginal)}
          className="text-slate-600 hover:text-slate-900 font-medium flex items-center gap-1"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>{showOriginal ? 'Hide Original Clause Text' : 'View Original Clause Text'}</span>
          {showOriginal ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {clause.grounding_examples && clause.grounding_examples.length > 0 && (
          <button
            onClick={() => setShowGrounding(!showGrounding)}
            className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>{showGrounding ? 'Hide Vector Reference Matches' : 'View Vector Grounding Examples'}</span>
          </button>
        )}
      </div>

      {/* Original Clause Text Box */}
      {showOriginal && (
        <div className="mt-3 bg-slate-900 text-slate-100 p-3.5 rounded-lg text-xs font-mono leading-relaxed overflow-x-auto">
          {clause.original_text}
        </div>
      )}

      {/* Grounding Reference Examples Box */}
      {showGrounding && (
        <div className="mt-3 bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs space-y-2">
          <p className="font-semibold text-slate-700">ChromaDB Nearest Reference Examples:</p>
          {clause.grounding_examples.map((eg, idx) => (
            <div key={idx} className="bg-white p-2 rounded border border-slate-200">
              <span className={`font-semibold uppercase text-[10px] px-1.5 py-0.5 rounded ${
                eg.category === 'one_sided' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}>
                {eg.category}
              </span>
              <p className="text-slate-600 italic mt-1 font-serif">"{eg.text}"</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
