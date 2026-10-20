import React, { useState } from 'react';
import IntakeForm from './components/IntakeForm';
import FileUpload from './components/FileUpload';
import SummaryCard from './components/SummaryCard';
import FlaggedClauseCard from './components/FlaggedClauseCard';
import ChatThread from './components/ChatThread';
import Disclaimer from './components/Disclaimer';
import { Scale, RefreshCw, CheckCircle2, Globe, AlertTriangle } from 'lucide-react';

export default function App() {
  const [step, setStep] = useState(1); // 1: Intake, 2: Upload, 3: Results
  const [intakeContext, setIntakeContext] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [fileName, setFileName] = useState('');
  const [language, setLanguage] = useState('en'); // 'en' | 'hi' | 'ta'

  const isHindi = language === 'hi';
  const isTamil = language === 'ta';
  const langFontClass = isTamil ? 'lang-ta' : isHindi ? 'lang-hi' : '';

  const handleIntakeSubmit = (context) => {
    setIntakeContext(context);
    setStep(2);
  };

  const handleUploadSuccess = (data, uploadedFileName) => {
    setAnalysisResult(data);
    setFileName(uploadedFileName);
    // Set default output language = document language if Indic, else en
    if (data.detected_language && (data.detected_language === 'hi' || data.detected_language === 'ta')) {
      setLanguage(data.detected_language);
    } else {
      setLanguage('en');
    }
    setStep(3);
  };

  const handleReset = () => {
    setStep(1);
    setIntakeContext(null);
    setAnalysisResult(null);
    setFileName('');
  };

  return (
    <div className={`min-h-screen bg-slate-50 flex flex-col ${langFontClass}`}>
      {/* Navbar */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-3 sm:px-4 py-3 flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-2 bg-blue-600 rounded-lg shrink-0">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="font-bold text-base leading-tight truncate">LexGuard AI</h1>
              <p className="text-[11px] text-slate-400 truncate">Multilingual Legal Document Chatbot</p>
            </div>
          </div>

          {/* Right Controls: Language Toggle (English | हिंदी | தமிழ்) + Reset Button */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <div
              className="flex items-center bg-slate-800 rounded-lg p-1 border border-slate-700 gap-1"
              role="group"
              aria-label="Language Switcher"
            >
              <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-0.5 shrink-0" />
              <button
                onClick={() => setLanguage('en')}
                className={`px-2 sm:px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                  language === 'en' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('hi')}
                className={`px-2 sm:px-2.5 py-1 text-xs font-semibold rounded-md transition-colors lang-hi ${
                  language === 'hi' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                हिंदी
              </button>
              <button
                onClick={() => setLanguage('ta')}
                className={`px-2 sm:px-2.5 py-1 text-xs font-semibold rounded-md transition-colors lang-ta ${
                  language === 'ta' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                தமிழ்
              </button>
            </div>

            {step > 1 && (
              <button
                onClick={handleReset}
                className="text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 sm:px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors break-words"
              >
                <RefreshCw className="w-3.5 h-3.5 shrink-0" />
                <span>
                  {isTamil
                    ? "புதிய ஆவணம்"
                    : isHindi
                    ? "नया दस्तावेज़ शुरू करें"
                    : "Start New Document"}
                </span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-3 sm:px-4 py-6 sm:py-8">
        {/* Step Indicator */}
        <div className="max-w-lg mx-auto mb-8 flex flex-wrap items-center justify-between gap-2 text-xs font-semibold text-slate-500">
          <div className={`flex items-center gap-1.5 min-w-0 ${step >= 1 ? 'text-blue-600' : ''}`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold shrink-0 ${
              step >= 1 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>1</span>
            <span className="break-words">
              {isTamil ? "சுயவிவர விவரம்" : isHindi ? "प्रोफ़ाइल संदर्भ" : "Intake Profile"}
            </span>
          </div>
          <div className="hidden sm:block h-0.5 w-8 bg-slate-200"></div>
          <div className={`flex items-center gap-1.5 min-w-0 ${step >= 2 ? 'text-blue-600' : ''}`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold shrink-0 ${
              step >= 2 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>2</span>
            <span className="break-words">
              {isTamil ? "PDF பதிவேற்றம்" : isHindi ? "पीडीएफ अपलोड" : "Upload PDF"}
            </span>
          </div>
          <div className="hidden sm:block h-0.5 w-8 bg-slate-200"></div>
          <div className={`flex items-center gap-1.5 min-w-0 ${step >= 3 ? 'text-blue-600' : ''}`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold shrink-0 ${
              step >= 3 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>3</span>
            <span className="break-words">
              {isTamil ? "இடர் அறிக்கை & உரையாடல்" : isHindi ? "जोखिम रिपोर्ट व चैट" : "Risk Report & Chat"}
            </span>
          </div>
        </div>

        {/* Step 1: Intake Form */}
        {step === 1 && (
          <IntakeForm onSubmitIntake={handleIntakeSubmit} language={language} />
        )}

        {/* Step 2: File Upload */}
        {step === 2 && intakeContext && (
          <FileUpload
            intakeContext={intakeContext}
            onEditIntake={() => setStep(1)}
            onUploadSuccess={handleUploadSuccess}
            language={language}
          />
        )}

        {/* Step 3: Analysis Results Dashboard */}
        {step === 3 && analysisResult && (
          <div className="space-y-6">
            {/* Disclaimer Banner */}
            <Disclaimer language={language} />

            {/* Experimental Notice for Machine-Translated Indic Documents */}
            {analysisResult.experimental_notice && (
              <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-xs flex items-start gap-3 text-amber-950">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-amber-900 mb-0.5">
                    {language === 'ta' ? "பரிசோதனை நிலை அறிவிப்பு" : language === 'hi' ? "प्रायोगिक सूचना" : "Experimental Notice"}
                  </h4>
                  <p className="text-sm font-medium leading-relaxed break-words">
                    {analysisResult.experimental_notice}
                  </p>
                </div>
              </div>
            )}

            {/* Document Summary */}
            <SummaryCard
              summary={analysisResult.document_summary}
              summaryHi={analysisResult.document_summary_hi}
              summaryTa={analysisResult.document_summary_ta}
              totalClauses={analysisResult.total_clauses}
              flaggedCount={analysisResult.flagged_clauses.length}
              parseMethod={analysisResult.parsed_method}
              fileName={fileName}
              language={language}
            />

            {/* Content Layout: Flagged Clauses + Interactive Chat */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8">
              {/* Flagged Clauses Column */}
              <div className="lg:col-span-7 space-y-4 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
                  <h2 className="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2 min-w-0">
                    <span className="break-words">
                      {isTamil
                        ? "தனிநபர் சூழலின்படி வரிசைப்படுத்தப்பட்ட இடர்கள்"
                        : isHindi
                        ? "व्यक्तिगत संदर्भ अनुसार प्राथमिकता प्राप्त जोखिम"
                        : "Contextually Ranked Flagged Risks"}
                    </span>
                    <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-semibold shrink-0">
                      {analysisResult.flagged_clauses.length}
                    </span>
                  </h2>
                  <span className="text-xs text-slate-500 break-words">
                    {isTamil
                      ? "தனிநபர் முன்னுரிமைப்படி வரிசைப்படுத்தப்பட்டது"
                      : isHindi
                      ? "व्यक्तिगत संदर्भ द्वारा व्यवस्थित"
                      : "Sorted by personal context priority"}
                  </span>
                </div>

                {analysisResult.flagged_clauses.length === 0 ? (
                  <div className="bg-white border border-slate-200 rounded-xl p-6 sm:p-8 text-center text-slate-600">
                    <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-2" />
                    <h3 className="font-bold text-slate-800 break-words">
                      {isTamil
                        ? "அதிக இடர் கொண்ட பிரிவுகள் எதுவும் கண்டறியப்படவில்லை"
                        : isHindi
                        ? "कोई उच्च जोखिम वाला क्लॉज नहीं मिला"
                        : "No High-Risk Clauses Flagged"}
                    </h3>
                    <p className="text-sm text-slate-500 mt-1 break-words">
                      {isTamil
                        ? "மேற்கோள் தரவுத்தளத்துடன் ஒப்பிடும்போது ஒருதலைப்பட்சமான அல்லது அதிக இடர் கொண்ட பிரிவுகள் எதுவும் கண்டறியப்படவில்லை."
                        : isHindi
                        ? "वेक्टर संदर्भ डेटासेट के विरुद्ध कोई भी एकतरफा या उच्च जोखिम वाला क्लॉज नहीं मिला।"
                        : "No standard one-sided or high-risk clauses were matched against the vector reference dataset."}
                    </p>
                  </div>
                ) : (
                  analysisResult.flagged_clauses.map((clause, index) => (
                    <FlaggedClauseCard
                      key={clause.clause_id + index}
                      clause={clause}
                      rank={index + 1}
                      language={language}
                    />
                  ))
                )}
              </div>

              {/* Chat Thread Column */}
              <div className="lg:col-span-5 min-w-0">
                <div className="sticky top-20">
                  <ChatThread
                    documentText={analysisResult.all_clauses.map(c => c.text).join('\n\n')}
                    intakeContext={analysisResult.intake_context}
                    language={language}
                  />
                </div>
              </div>
            </div>

            {/* Bottom Footer Disclaimer */}
            <div className="pt-6 border-t border-slate-200">
              <Disclaimer compact language={language} />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 text-xs py-4 text-center border-t border-slate-800">
        <p className="max-w-4xl mx-auto px-4 break-words">
          LexGuard Legal Chatbot • Multilingual (EN / HI / TA) • Embeddings: bge-small-en • Vector Store: ChromaDB • LLM: Gemini • Translation: Local IndicTrans2 & Legal Glossary
        </p>
      </footer>
    </div>
  );
}
