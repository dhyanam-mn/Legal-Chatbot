import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, Loader2, Edit3 } from 'lucide-react';

export default function FileUpload({ intakeContext, onEditIntake, onUploadSuccess, language = 'en' }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const isHindi = language === 'hi';
  const isTamil = language === 'ta';
  const langFontClass = isTamil ? 'lang-ta' : isHindi ? 'lang-hi' : '';

  const t = {
    activeProfile: isTamil ? "செயலில் உள்ள சுயவிவரம்:" : isHindi ? "सक्रिय प्रोफ़ाइल:" : "Active Profile:",
    editProfile: isTamil ? "சுயவிவரத்தைத் திருத்து" : isHindi ? "प्रोफ़ाइल संपादित करें" : "Edit Profile",
    dependents: (hasDep, count) => {
      if (isTamil) return hasDep ? `${count} சார்ந்திருப்போர்` : "சார்ந்திருப்போர் இல்லை";
      if (isHindi) return hasDep ? `${count} आश्रित` : "कोई आश्रित नहीं";
      return hasDep ? `${count} Dependents` : "No Dependents";
    },
    clickToUpload: isTamil
      ? "உங்கள் PDF-ஐப் பதிவேற்ற கிளிக் செய்யவும் அல்லது இங்கே இழுத்துப் போடவும்"
      : isHindi
      ? "पीडीएफ अपलोड करने के लिए क्लिक करें या यहाँ खींचें (ड्रैग करें)"
      : "Click to upload or drag & drop your PDF",
    fileSupport: isTamil
      ? "PDF ஒப்பந்தங்கள், குத்தகைகள், உடன்படிக்கைகள் ஆதரிக்கப்படுகின்றன (அதிகபட்சம் 25MB)"
      : isHindi
      ? "पीडीएफ अनुबंध, पट्टे, समझौते समर्थित हैं (अधिकतम 25MB)"
      : "Supports PDF contract templates, leases, agreements (Max 25MB)",
    invalidPdf: isTamil
      ? "தயவுசெய்து சரியான PDF (.pdf) கோப்பைத் தேர்ந்தெடுக்கவும்."
      : isHindi
      ? "कृपया एक वैध पीडीएफ (.pdf) फ़ाइल चुनें।"
      : "Please select a valid PDF file.",
    selectPdfFirst: isTamil
      ? "முதலில் ஒரு PDF கோப்பைத் தேர்ந்தெடுக்கவும்."
      : isHindi
      ? "कृपया पहले एक पीडीएफ फ़ाइल चुनें।"
      : "Please select a PDF file first.",
    analyzing: isTamil
      ? "பிரிவுகள் பகுப்பாய்வு செய்யப்பட்டு இடர்கள் மதிப்பிடப்படுகின்றன..."
      : isHindi
      ? "क्लॉज़ का विश्लेषण और जोखिम मूल्यांकन किया जा रहा है..."
      : "Analyzing Clauses & Assessing Risks...",
    analyzeBtn: isTamil
      ? "சட்ட ஆவணத்தை பகுப்பாய்வு செய்யவும்"
      : isHindi
      ? "कानूनी दस्तावेज़ का विश्लेषण करें"
      : "Analyze Legal Document",
  };

  const formatDocType = (dt) => {
    if (isTamil) {
      if (dt === 'employment_contract') return 'வேலைவாய்ப்பு ஒப்பந்தம்';
      if (dt === 'rental_agreement') return 'வாடகை / குத்தகை ஒப்பந்தம்';
      if (dt === 'service_agreement') return 'சேவை ஒப்பந்தம்';
      if (dt === 'loan_agreement') return 'கடன் ஒப்பந்தம்';
      return 'சட்ட ஆவணம்';
    }
    if (isHindi) {
      if (dt === 'employment_contract') return 'रोजगार अनुबंध';
      if (dt === 'rental_agreement') return 'किराया / पट्टा समझौता';
      if (dt === 'service_agreement') return 'सेवा अनुबंध';
      if (dt === 'loan_agreement') return 'ऋण समझौता';
      return 'कानूनी दस्तावेज़';
    }
    return (dt || '').replace('_', ' ');
  };

  const formatEmpType = (et) => {
    if (isTamil) {
      if (et === 'salaried') return 'மாதச் சம்பளப் பணியாளர்';
      if (et === 'self_employed') return 'சுயதொழில் / ஃப்ரீலான்சர்';
      if (et === 'business_owner') return 'வணிக உரிமையாளர்';
      if (et === 'unemployed') return 'வேலை தேடுபவர்';
      if (et === 'retired') return 'ஓய்வு பெற்றவர்';
    }
    if (isHindi) {
      if (et === 'salaried') return 'वेतनभोगी कर्मचारी';
      if (et === 'self_employed') return 'स्व-नियोजित / फ्रीलांसर';
      if (et === 'business_owner') return 'व्यवसाय स्वामी';
      if (et === 'unemployed') return 'बेरोजगार';
      if (et === 'retired') return 'सेवानिवृत्त';
    }
    return (et || '').replace('_', ' ');
  };

  const handleFileChange = (e) => {
    const selected = e.target.files && e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.pdf') && selected.type !== 'application/pdf') {
        setError(t.invalidPdf);
        return;
      }
      setFile(selected);
      setError('');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError(t.invalidPdf);
        return;
      }
      setFile(selected);
      setError('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleSubmit = async () => {
    if (!file) {
      setError(t.selectPdfFirst);
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('employment_type', intakeContext.employment_type);
    formData.append('has_dependents', intakeContext.has_dependents);
    formData.append('dependents_count', intakeContext.dependents_count);
    formData.append('income_bracket', intakeContext.income_bracket);
    formData.append('document_type', intakeContext.document_type);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to process and analyze document.');
      }

      const data = await res.json();
      onUploadSuccess(data, file.name);
    } catch (err) {
      console.error(err);
      setError(err.message || 'An unexpected error occurred during document upload.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`max-w-xl mx-auto space-y-6 ${langFontClass}`}>
      {/* Client Profile Header Badge */}
      <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 flex items-center justify-between text-sm text-slate-700">
        <div>
          <span className="font-semibold text-slate-900">{t.activeProfile}</span>{' '}
          <span className="capitalize">{formatEmpType(intakeContext.employment_type)}</span> •{' '}
          <span>{t.dependents(intakeContext.has_dependents, intakeContext.dependents_count)}</span> •{' '}
          <span className="capitalize">{formatDocType(intakeContext.document_type)}</span>
        </div>
        <button
          onClick={onEditIntake}
          className="text-blue-600 hover:text-blue-800 text-xs font-semibold flex items-center gap-1 hover:underline ml-2 shrink-0"
        >
          <Edit3 className="w-3.5 h-3.5" />
          {t.editProfile}
        </button>
      </div>

      {/* Upload Box */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all bg-white ${
          file ? 'border-blue-500 bg-blue-50/30' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
            <UploadCloud className="w-7 h-7" />
          </div>
          <div>
            <p className="text-base font-semibold text-slate-800">
              {file ? file.name : t.clickToUpload}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {t.fileSupport}
            </p>
          </div>

          {file && (
            <div className="flex items-center gap-2 text-xs text-blue-700 bg-blue-100/70 px-3 py-1.5 rounded-full font-medium">
              <File className="w-3.5 h-3.5" />
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className={`w-full font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-md ${
          !file || loading
            ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 text-white'
        }`}
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>{t.analyzing}</span>
          </>
        ) : (
          <span>{t.analyzeBtn}</span>
        )}
      </button>
    </div>
  );
}
