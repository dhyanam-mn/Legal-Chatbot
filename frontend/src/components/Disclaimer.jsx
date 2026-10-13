import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const MANDATORY_DISCLAIMER_TEXT = "This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this.";
export const MANDATORY_DISCLAIMER_HI_TEXT = "यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।";

export default function Disclaimer({ compact = false, language = 'en' }) {
  const disclaimerContent = language === 'hi' ? MANDATORY_DISCLAIMER_HI_TEXT : MANDATORY_DISCLAIMER_TEXT;
  const disclaimerTitle = language === 'hi' ? "महत्वपूर्ण कानूनी चेतावनी (Disclaimer)" : "Important Disclaimer";

  if (compact) {
    return (
      <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-md p-2 text-xs flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>{disclaimerContent}</span>
      </div>
    );
  }

  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 text-amber-900 p-4 rounded-r-lg shadow-sm flex items-start gap-3 my-4">
      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <div>
        <h4 className="font-semibold text-xs tracking-wider uppercase text-amber-800">{disclaimerTitle}</h4>
        <p className="text-sm mt-0.5 font-medium">{disclaimerContent}</p>
      </div>
    </div>
  );
}
