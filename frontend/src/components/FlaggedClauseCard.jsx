import React, { useState } from 'react';
import {
  AlertOctagon,
  ChevronDown,
  ChevronUp,
  FileText,
  Info,
  HelpCircle,
  Scale,
  BookOpen,
  ExternalLink,
  ShieldAlert
} from 'lucide-react';

const DEFAULT_DISCLAIMER_EN =
  "This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this.";
const DEFAULT_DISCLAIMER_HI =
  "यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।";
const DEFAULT_DISCLAIMER_TA =
  "இது இந்தப் பிரிவின் பொருளை விளக்குகிறது. இது சட்ட ஆலோசனை அல்ல. இதன் அடிப்படையில் செயல்படுவதற்கு முன் ஒரு வழக்கறிஞரைக் கலந்தாலோசிக்கவும்.";

export default function FlaggedClauseCard({ clause, rank, language = 'en' }) {
  const [showLegalBasis, setShowLegalBasis] = useState(false);
  const [showTypicalPhrasing, setShowTypicalPhrasing] = useState(false);
  const [showOriginal, setShowOriginal] = useState(false);
  const [showGrounding, setShowGrounding] = useState(false);

  const isHindi = language === 'hi';
  const isTamil = language === 'ta';

  const explanationText =
    isTamil && clause.explanation_ta
      ? clause.explanation_ta
      : isHindi && clause.explanation_hi
      ? clause.explanation_hi
      : clause.explanation;

  const riskText =
    isTamil && clause.risk_reason_ta
      ? clause.risk_reason_ta
      : isHindi && clause.risk_reason_hi
      ? clause.risk_reason_hi
      : clause.risk_reason;

  const explanationLabel = isTamil
    ? "இந்தப் பிரிவின் பொருள் என்ன:"
    : isHindi
    ? "इस खंड का क्या अर्थ है:"
    : "What this clause means:";

  const riskLabel = isTamil
    ? "இது ஏன் இடர் நிறைந்தது அல்லது ஒருதலைப்பட்சமானது:"
    : isHindi
    ? "यह जोखिम भरा या एकतरफा क्यों है:"
    : "Why it's risky or one-sided:";

  const severitySuffix = isTamil
    ? "இடர் முன்னுரிமை"
    : isHindi
    ? "जोखिम प्राथमिकता"
    : "Risk Priority";

  const typicalPhrasingDisclaimer = isTamil
    ? clause.typical_phrasing_disclaimer_ta || DEFAULT_DISCLAIMER_TA
    : isHindi
    ? clause.typical_phrasing_disclaimer_hi || DEFAULT_DISCLAIMER_HI
    : clause.typical_phrasing_disclaimer || DEFAULT_DISCLAIMER_EN;

  const citations = Array.isArray(clause.statutory_citations) ? clause.statutory_citations : [];
  const standardAlternatives = Array.isArray(clause.standard_alternatives)
    ? clause.standard_alternatives
    : [];

  const noStatuteMsg =
    isTamil && clause.legal_basis_message_ta
      ? clause.legal_basis_message_ta
      : isHindi && clause.legal_basis_message_hi
      ? clause.legal_basis_message_hi
      : clause.legal_basis_message || "No statutory provision retrieved";

  const langClass = isTamil
    ? 'lang-ta leading-[1.85]'
    : isHindi
    ? 'lang-hi leading-[1.75]'
    : 'leading-relaxed';

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
    <div
      className={`bg-white rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 hover:shadow-md transition-shadow overflow-hidden ${
        isTamil ? 'lang-ta' : isHindi ? 'lang-hi' : ''
      }`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-start sm:items-center justify-between gap-2.5 mb-3">
        <div className="flex flex-wrap items-center gap-2 min-w-0">
          <span className="w-6 h-6 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center shrink-0">
            #{rank}
          </span>
          <h3 className="font-bold text-slate-900 text-sm sm:text-base break-words">
            {clause.title}
          </h3>
          <span className="text-xs text-slate-500 font-mono">({clause.clause_id})</span>
        </div>

        <span
          className={`px-2.5 py-1 rounded-full text-xs font-semibold border shrink-0 max-w-full break-words ${getSeverityBadge(
            clause.severity
          )}`}
        >
          {clause.severity} {severitySuffix}
        </span>
      </div>

      {/* Explanation Box */}
      <div className="bg-blue-50/70 border border-blue-100 rounded-lg p-3.5 mb-3">
        <div className="flex items-start gap-1.5 font-semibold text-xs text-blue-900 mb-1.5">
          <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <span className="break-words">{explanationLabel}</span>
        </div>
        <p className={`text-sm text-slate-800 font-medium break-words ${langClass}`}>
          {explanationText}
        </p>
      </div>

      {/* Risk Reason Box */}
      <div className="bg-amber-50/70 border border-amber-100 rounded-lg p-3.5 mb-3">
        <div className="flex items-start gap-1.5 font-semibold text-xs text-amber-900 mb-1.5">
          <AlertOctagon className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span className="break-words">{riskLabel}</span>
        </div>
        <p className={`text-sm text-slate-800 break-words ${langClass}`}>{riskText}</p>
      </div>

      {/* Collapsible Controls: Legal basis | Typical phrasing | Original Clause Text | Vector Grounding */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3 border-t border-slate-100 pt-3 text-xs">
        <button
          type="button"
          onClick={() => setShowLegalBasis(!showLegalBasis)}
          className={`px-2.5 py-1.5 rounded-lg border font-semibold flex items-center gap-1.5 transition-colors text-left ${
            showLegalBasis
              ? 'bg-indigo-50 border-indigo-200 text-indigo-900'
              : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
          }`}
        >
          <Scale className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
          <span className="break-words">
            {isTamil
              ? 'சட்ட அடிப்படை (Legal basis)'
              : isHindi
              ? 'कानूनी आधार (Legal basis)'
              : 'Legal basis'}
          </span>
          <span className="px-1.5 py-0.2 rounded-full bg-indigo-100 text-indigo-800 text-[10px] font-mono">
            {citations.length}
          </span>
          {showLegalBasis ? (
            <ChevronUp className="w-3.5 h-3.5 shrink-0" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 shrink-0" />
          )}
        </button>

        <button
          type="button"
          onClick={() => setShowTypicalPhrasing(!showTypicalPhrasing)}
          className={`px-2.5 py-1.5 rounded-lg border font-semibold flex items-center gap-1.5 transition-colors text-left ${
            showTypicalPhrasing
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
          }`}
        >
          <BookOpen className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span className="break-words">
            {isTamil
              ? 'வழக்கமான வாசகம் (Typical phrasing)'
              : isHindi
              ? 'सामान्य शब्दावली (Typical phrasing)'
              : 'Typical phrasing'}
          </span>
          {showTypicalPhrasing ? (
            <ChevronUp className="w-3.5 h-3.5 shrink-0" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 shrink-0" />
          )}
        </button>

        <button
          type="button"
          onClick={() => setShowOriginal(!showOriginal)}
          className="text-slate-600 hover:text-slate-900 font-medium flex items-center gap-1.5 py-1 px-1.5 text-left"
        >
          <FileText className="w-3.5 h-3.5 shrink-0" />
          <span className="break-words">
            {showOriginal
              ? isTamil
                ? 'மூலப் பிரிவு உரையை மறை'
                : isHindi
                ? 'मूल खंड टेक्स्ट छिपाएं'
                : 'Hide Original Clause Text'
              : isTamil
              ? 'மூலப் பிரிவு உரையைக் காண்க'
              : isHindi
              ? 'मूल खंड टेक्स्ट देखें'
              : 'View Original Clause Text'}
          </span>
          {showOriginal ? (
            <ChevronUp className="w-3.5 h-3.5 shrink-0" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 shrink-0" />
          )}
        </button>

        {clause.grounding_examples && clause.grounding_examples.length > 0 && (
          <button
            type="button"
            onClick={() => setShowGrounding(!showGrounding)}
            className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1.5 py-1 px-1.5 text-left ml-auto"
          >
            <HelpCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="break-words">
              {showGrounding
                ? isTamil
                  ? 'மேற்கோள் எடுத்துக்காட்டுகளை மறை'
                  : isHindi
                  ? 'वेक्टर संदर्भ उदाहरण छिपाएं'
                  : 'Hide Vector Reference Matches'
                : isTamil
                ? 'மேற்கோள் எடுத்துக்காட்டுகளைக் காண்க'
                : isHindi
                ? 'वेक्टर संदर्भ उदाहरण देखें'
                : 'View Vector Grounding Examples'}
            </span>
          </button>
        )}
      </div>

      {/* Collapsible Panel 1: Legal basis (Statutory Citations) */}
      {showLegalBasis && (
        <div className="mt-3 bg-indigo-50/50 border border-indigo-100 rounded-lg p-3.5 space-y-2.5">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-950 flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
              <span>Legal basis</span>
            </h4>
            <span className="text-[11px] text-indigo-700 font-mono">
              {citations.length > 0
                ? `${citations.length} verified provision(s)`
                : '0 provisions'}
            </span>
          </div>

          {citations.length === 0 ? (
            <p className="text-xs text-slate-600 italic bg-white border border-slate-200 rounded p-2.5">
              {noStatuteMsg}
            </p>
          ) : (
            <div className="space-y-2">
              {citations.map((cit, idx) => {
                const reasonText =
                  isTamil && cit.reason_ta
                    ? cit.reason_ta
                    : isHindi && cit.reason_hi
                    ? cit.reason_hi
                    : cit.reason;
                return (
                  <div
                    key={cit.provision_id || idx}
                    className="bg-white border border-indigo-100 rounded-lg p-3 shadow-2xs space-y-1.5"
                  >
                    {/* Statute ID, Section number, and Act name always kept untranslated in English */}
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="px-2 py-0.5 rounded bg-indigo-900 text-white font-mono text-[11px] font-semibold">
                          {cit.provision_id}
                        </span>
                        <span className="text-xs font-bold text-slate-900">
                          {cit.act} — {cit.section}
                        </span>
                        {cit.title && (
                          <span className="text-xs text-slate-600">({cit.title})</span>
                        )}
                      </div>
                      {cit.source_url && (
                        <a
                          href={cit.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1 font-medium"
                        >
                          <span>Official Text</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    <p className={`text-xs sm:text-sm text-slate-800 break-words ${langClass}`}>
                      {reasonText}
                    </p>
                    {cit.statutory_text && (
                      <div className="mt-2 pt-2 border-t border-slate-100 bg-slate-50/80 rounded p-2.5">
                        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 font-mono">
                          Statutory Provision Text (Verbatim):
                        </div>
                        <p className="text-xs font-mono text-slate-700 whitespace-pre-wrap leading-relaxed select-text">
                          {cit.statutory_text}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Collapsible Panel 2: Typical phrasing ("How this is typically written" + prepended mandatory disclaimer) */}
      {showTypicalPhrasing && (
        <div className="mt-3 bg-emerald-50/50 border border-emerald-200 rounded-lg p-3.5 space-y-3">
          {/* Prepended Mandatory Disclaimer */}
          <div className="bg-amber-50 border border-amber-200 rounded-md p-2.5 flex items-start gap-2 text-xs text-amber-950">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className={`font-medium break-words ${langClass}`}>
              {typicalPhrasingDisclaimer}
            </p>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-950 mb-2 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
              <span>{clause.typical_phrasing_header || 'How this is typically written'}</span>
            </h4>

            {standardAlternatives.length === 0 ? (
              <p className="text-xs text-slate-600 italic bg-white border border-slate-200 rounded p-2.5">
                No standard reference phrasing available for this clause category.
              </p>
            ) : (
              <div className="space-y-2">
                {standardAlternatives.map((altText, idx) => (
                  <div
                    key={idx}
                    className="bg-white border border-emerald-100 rounded-lg p-3 text-xs sm:text-sm text-slate-700 font-serif italic leading-relaxed break-words"
                  >
                    "{altText}"
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Original Clause Text Box */}
      {showOriginal && (
        <div className="mt-3 bg-slate-900 text-slate-100 p-3.5 rounded-lg text-xs font-mono leading-relaxed overflow-x-auto break-words">
          {clause.original_text}
        </div>
      )}

      {/* Grounding Reference Examples Box */}
      {showGrounding && (
        <div className="mt-3 bg-slate-50 border border-slate-200 p-3 rounded-lg text-xs space-y-2">
          <p className="font-semibold text-slate-700">ChromaDB Nearest Reference Examples:</p>
          {clause.grounding_examples.map((eg, idx) => (
            <div key={idx} className="bg-white p-2 rounded border border-slate-200 break-words">
              <span
                className={`font-semibold uppercase text-[10px] px-1.5 py-0.5 rounded ${
                  eg.category === 'one_sided'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {eg.category}
              </span>
              <p className="text-slate-600 italic mt-1 font-serif break-words">"{eg.text}"</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
