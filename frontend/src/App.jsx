import React, { useState } from 'react';
import IntakeForm from './components/IntakeForm';
import FileUpload from './components/FileUpload';
import SummaryCard from './components/SummaryCard';
import FlaggedClauseCard from './components/FlaggedClauseCard';
import ChatThread from './components/ChatThread';
import Disclaimer from './components/Disclaimer';
import { Scale, RefreshCw, FileText, CheckCircle2, Globe } from 'lucide-react';

export default function App() {
  const [step, setStep] = useState(1); // 1: Intake, 2: Upload, 3: Results
  const [intakeContext, setIntakeContext] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [fileName, setFileName] = useState('');
  const [language, setLanguage] = useState('en'); // 'en' | 'hi'

  const isHindi = language === 'hi';

  const handleIntakeSubmit = (context) => {
    setIntakeContext(context);
    setStep(2);
  };

  const handleUploadSuccess = (data, uploadedFileName) => {
    setAnalysisResult(data);
    setFileName(uploadedFileName);
    setStep(3);
  };

  const handleReset = () => {
    setStep(1);
    setIntakeContext(null);
    setAnalysisResult(null);
    setFileName('');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Navbar */}
      <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-base leading-tight">LexGuard AI</h1>
              <p className="text-[11px] text-slate-400">Phase 1 Legal Document Chatbot</p>
            </div>
          </div>

          {/* Right Controls: Language Toggle + Reset Button */}
          <div className="flex items-center gap-3">
            {/* Language Switcher Toggle */}
            <div className="flex items-center bg-slate-800 rounded-lg p-1 border border-slate-700 gap-1">
              <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-0.5" />
              <button
                onClick={() => setLanguage('en')}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                  language === 'en' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage('hi')}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                  language === 'hi' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                हिंदी
              </button>
            </div>

            {step > 1 && (
              <button
                onClick={handleReset}
                className="text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>{isHindi ? "नया दस्तावेज़ शुरू करें" : "Start New Document"}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        {/* Step Indicator */}
        <div className="max-w-md mx-auto mb-8 flex items-center justify-between text-xs font-semibold text-slate-500">
          <div className={`flex items-center gap-1.5 ${step >= 1 ? 'text-blue-600' : ''}`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
              step >= 1 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>1</span>
            <span>{isHindi ? "प्रोफ़ाइल संदर्भ" : "Intake Profile"}</span>
          </div>
          <div className="h-0.5 w-10 bg-slate-200"></div>
          <div className={`flex items-center gap-1.5 ${step >= 2 ? 'text-blue-600' : ''}`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
              step >= 2 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>2</span>
            <span>{isHindi ? "पीडीएफ अपलोड" : "Upload PDF"}</span>
          </div>
          <div className="h-0.5 w-10 bg-slate-200"></div>
          <div className={`flex items-center gap-1.5 ${step >= 3 ? 'text-blue-600' : ''}`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center font-bold ${
              step >= 3 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>3</span>
            <span>{isHindi ? "जोखिम रिपोर्ट व चैट" : "Risk Report & Chat"}</span>
          </div>
        </div>

        {/* Step 1: Intake Form */}
        {step === 1 && (
          <IntakeForm onSubmitIntake={handleIntakeSubmit} />
        )}

        {/* Step 2: File Upload */}
        {step === 2 && intakeContext && (
          <FileUpload
            intakeContext={intakeContext}
            onEditIntake={() => setStep(1)}
            onUploadSuccess={handleUploadSuccess}
          />
        )}

        {/* Step 3: Analysis Results Dashboard */}
        {step === 3 && analysisResult && (
          <div className="space-y-6">
            {/* Disclaimer Banner */}
            <Disclaimer language={language} />

            {/* Document Summary */}
            <SummaryCard
              summary={analysisResult.document_summary}
              summaryHi={analysisResult.document_summary_hi}
              totalClauses={analysisResult.total_clauses}
              flaggedCount={analysisResult.flagged_clauses.length}
              parseMethod={analysisResult.parsed_method}
              fileName={fileName}
              language={language}
            />

            {/* Content Layout: Flagged Clauses + Interactive Chat */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Flagged Clauses Column */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <span>{isHindi ? "व्यक्तिगत संदर्भ अनुसार प्राथमिकता प्राप्त जोखिम" : "Contextually Ranked Flagged Risks"}</span>
                    <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-semibold">
                      {analysisResult.flagged_clauses.length}
                    </span>
                  </h2>
                  <span className="text-xs text-slate-500">{isHindi ? "व्यक्तिगत संदर्भ द्वारा व्यवस्थित" : "Sorted by personal context priority"}</span>
                </div>

                {analysisResult.flagged_clauses.length === 0 ? (
                  <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-600">
                    <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-2" />
                    <h3 className="font-bold text-slate-800">{isHindi ? "कोई उच्च जोखिम वाला क्लॉज नहीं मिला" : "No High-Risk Clauses Flagged"}</h3>
                    <p className="text-sm text-slate-500 mt-1">
                      {isHindi
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
              <div className="lg:col-span-5">
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
        <p className="max-w-4xl mx-auto px-4">
          LexGuard Legal Chatbot • Phase 1 MVP • Embeddings: bge-small-en • Vector Store: ChromaDB • LLM: Gemini • Translation: IndicTrans2 Guidelines & Legal Glossary
        </p>
      </footer>
    </div>
  );
}
