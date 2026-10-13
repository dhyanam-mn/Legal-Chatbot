import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const MANDATORY_DISCLAIMER_TEXT = "This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this.";
export const MANDATORY_DISCLAIMER_HI_TEXT = "यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।";
export const MANDATORY_DISCLAIMER_TA_TEXT = "இது இந்தப் பிரிவின் பொருளை விளக்குகிறது. இது சட்ட ஆலோசனை அல்ல. இதன் அடிப்படையில் செயல்படுவதற்கு முன் ஒரு வழக்கறிஞரைக் கலந்தாலோசிக்கவும்.";

export default function Disclaimer({ compact = false, language = 'en' }) {
  const disclaimerContent =
    language === 'ta'
      ? MANDATORY_DISCLAIMER_TA_TEXT
      : language === 'hi'
      ? MANDATORY_DISCLAIMER_HI_TEXT
      : MANDATORY_DISCLAIMER_TEXT;

  const disclaimerTitle =
    language === 'ta'
      ? "முக்கிய சட்ட பொறுப்புத்துறப்பு (Disclaimer)"
      : language === 'hi'
      ? "महत्वपूर्ण कानूनी चेतावनी (Disclaimer)"
      : "Important Disclaimer";

  const langClass = language === 'ta' ? 'lang-ta leading-[1.85]' : language === 'hi' ? 'lang-hi leading-[1.75]' : '';

  if (compact) {
    return (
      <div className={`bg-amber-50 border border-amber-200 text-amber-900 rounded-md p-2.5 text-xs flex items-start sm:items-center gap-2 break-words ${langClass}`}>
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5 sm:mt-0" />
        <span className="min-w-0 break-words">{disclaimerContent}</span>
      </div>
    );
  }

  return (
    <div className={`bg-amber-50 border-l-4 border-amber-500 text-amber-900 p-4 rounded-r-lg shadow-sm flex items-start gap-3 my-4 ${langClass}`}>
      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <div className="min-w-0 flex-1 break-words">
        <h4 className="font-semibold text-xs tracking-wider uppercase text-amber-800">{disclaimerTitle}</h4>
        <p className="text-sm mt-1 font-medium break-words">{disclaimerContent}</p>
      </div>
    </div>
  );
}
