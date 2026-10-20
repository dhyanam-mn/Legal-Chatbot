import React, { useState } from 'react';
import { UserCheck, Users, DollarSign, FileText, ArrowRight } from 'lucide-react';

export default function IntakeForm({ onSubmitIntake, language = 'en' }) {
  const [formData, setFormData] = useState({
    employment_type: 'salaried',
    has_dependents: false,
    dependents_count: 0,
    income_bracket: 'medium',
    document_type: 'employment_contract'
  });

  const isHindi = language === 'hi';
  const isTamil = language === 'ta';
  const langFontClass = isTamil ? 'lang-ta' : isHindi ? 'lang-hi' : '';

  const t = {
    title: isTamil ? "வாடிக்கையாளர் விவர சூழல்" : isHindi ? "ग्राहक प्रोफ़ाइल संदर्भ" : "Client Intake Context",
    subtitle: isTamil
      ? "உங்கள் சூழ்நிலைக்கு ஏற்ப இடர்களை வரிசைப்படுத்த உங்கள் சுயவிவரத் தகவலை வழங்கவும்."
      : isHindi
      ? "अपनी प्रोफ़ाइल जानकारी प्रदान करें ताकि हम आपकी स्थिति के अनुसार क्लॉज के जोखिमों को प्राथमिकता दे सकें।"
      : "Provide your profile information so we can rank and prioritize clause risks specific to your situation.",
    employmentType: isTamil ? "வேலைவாய்ப்பு வகை" : isHindi ? "रोज़गार का प्रकार" : "Employment Type",
    empOptions: [
      { id: 'salaried', label: isTamil ? "மாதச் சம்பளப் பணியாளர்" : isHindi ? "वेतनभोगी कर्मचारी" : "Salaried Employee" },
      { id: 'self_employed', label: isTamil ? "சுயதொழில் / ஃப்ரீலான்சர்" : isHindi ? "स्व-नियोजित / फ्रीलांसर" : "Self-Employed / Freelancer" },
      { id: 'business_owner', label: isTamil ? "வணிக உரிமையாளர்" : isHindi ? "व्यवसाय स्वामी" : "Business Owner" },
      { id: 'unemployed', label: isTamil ? "வேலை தேடுபவர் / வேலையில்லாதவர்" : isHindi ? "नौकरी तलाशने वाले / बेरोजगार" : "Job Seeking / Unemployed" },
      { id: 'retired', label: isTamil ? "ஓய்வு பெற்றவர்" : isHindi ? "सेवानिवृत्त" : "Retired" },
    ],
    dependents: isTamil ? "சார்ந்திருப்போர் விவரம்" : isHindi ? "आश्रितों की प्रोफ़ाइल" : "Dependents Profile",
    hasDependentsCheck: isTamil ? "என்னைச் சார்ந்திருப்பவர்கள் உள்ளனர்" : isHindi ? "मेरे वित्तीय आश्रित हैं" : "I have financial dependents",
    count: isTamil ? "எண்ணிக்கை:" : isHindi ? "संख्या:" : "Count:",
    incomeBracket: isTamil ? "தோராயமான வருமான வரம்பு" : isHindi ? "अनुमानित आय वर्ग" : "Approximate Income Bracket",
    incomeOptions: [
      { id: 'low', label: isTamil ? "குறைந்த / தொடக்க நிலை" : isHindi ? "निम्न / प्रवेश स्तर" : "Lower / Entry" },
      { id: 'medium', label: isTamil ? "நடுத்தர நிலை" : isHindi ? "मध्यम" : "Middle" },
      { id: 'high', label: isTamil ? "உயர் நிலை" : isHindi ? "उच्च / समृद्ध" : "Upper / High" },
    ],
    docType: isTamil ? "பகுப்பாய்வு செய்ய வேண்டிய ஆவண வகை" : isHindi ? "विश्लेषण के लिए दस्तावेज़ प्रकार" : "Document Type to Analyze",
    docOptions: [
      { id: 'employment_contract', label: isTamil ? "வேலைவாய்ப்பு ஒப்பந்தம்" : isHindi ? "रोजगार अनुबंध" : "Employment Contract" },
      { id: 'rental_agreement', label: isTamil ? "வாடகை / குத்தகை ஒப்பந்தம்" : isHindi ? "किराया / पट्टा समझौता" : "Rental / Lease Agreement" },
      { id: 'service_agreement', label: isTamil ? "சேவை / ஃப்ரீலான்ஸ் ஒப்பந்தம்" : isHindi ? "सेवा / फ्रीलांस अनुबंध" : "Freelance / Service Contract" },
      { id: 'loan_agreement', label: isTamil ? "கடன் / நிதி ஒப்பந்தம்" : isHindi ? "ऋण / वित्तीय समझौता" : "Loan / Financial Agreement" },
      { id: 'other', label: isTamil ? "பிற சட்ட ஆவணம்" : isHindi ? "अन्य कानूनी दस्तावेज़" : "Other Legal Document" },
    ],
    submitBtn: isTamil ? "ஆவணப் பதிவேற்றத்திற்குத் தொடரவும்" : isHindi ? "दस्तावेज़ अपलोड पर आगे बढ़ें" : "Continue to Document Upload",
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmitIntake(formData);
  };

  return (
    <div className={`max-w-xl mx-auto bg-white rounded-xl shadow-md border border-slate-200 p-6 md:p-8 ${langFontClass}`}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-slate-900">{t.title}</h2>
        <p className="text-sm text-slate-500 mt-1">
          {t.subtitle}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Employment Type */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <UserCheck className="w-4 h-4 text-blue-600" />
            {t.employmentType}
          </label>
          <select
            value={formData.employment_type}
            onChange={(e) => handleChange('employment_type', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50 text-slate-800"
          >
            {t.empOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Dependents */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <Users className="w-4 h-4 text-blue-600" />
            {t.dependents}
          </label>
          <div className="flex items-center gap-4 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-700 font-medium">
              <input
                type="checkbox"
                checked={formData.has_dependents}
                onChange={(e) => {
                  const has = e.target.checked;
                  handleChange('has_dependents', has);
                  if (!has) handleChange('dependents_count', 0);
                  else if (formData.dependents_count === 0) handleChange('dependents_count', 1);
                }}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              {t.hasDependentsCheck}
            </label>

            {formData.has_dependents && (
              <div className="flex items-center gap-2 ml-auto">
                <span className="text-xs text-slate-500">{t.count}</span>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.dependents_count}
                  onChange={(e) => handleChange('dependents_count', parseInt(e.target.value) || 0)}
                  className="w-16 px-2 py-1 border border-slate-300 rounded text-center text-sm font-medium bg-white"
                />
              </div>
            )}
          </div>
        </div>

        {/* Income Bracket */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <DollarSign className="w-4 h-4 text-blue-600" />
            {t.incomeBracket}
          </label>
          <div className="grid grid-cols-3 gap-3">
            {t.incomeOptions.map(b => (
              <button
                type="button"
                key={b.id}
                onClick={() => handleChange('income_bracket', b.id)}
                className={`py-2.5 px-3 text-sm font-medium rounded-lg border transition-all ${
                  formData.income_bracket === b.id
                    ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-sm'
                    : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        {/* Document Type */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <FileText className="w-4 h-4 text-blue-600" />
            {t.docType}
          </label>
          <select
            value={formData.document_type}
            onChange={(e) => handleChange('document_type', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50 text-slate-800"
          >
            {t.docOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{opt.label}</option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-md"
        >
          <span>{t.submitBtn}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
