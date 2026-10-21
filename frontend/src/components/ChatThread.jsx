import React, { useState } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import {
  MANDATORY_DISCLAIMER_TEXT,
  MANDATORY_DISCLAIMER_HI_TEXT,
  MANDATORY_DISCLAIMER_TA_TEXT
} from './Disclaimer';

export default function ChatThread({ documentText, intakeContext, language = 'en' }) {
  const isHindi = language === 'hi';
  const isTamil = language === 'ta';

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I have analyzed your document. Feel free to ask me any specific questions about clauses, obligations, or risks.',
      content_hi: 'नमस्ते! मैंने आपके दस्तावेज़ का विश्लेषण किया है। क्लॉज, दायित्वों या जोखिमों के बारे में मुझसे कोई भी प्रश्न पूछें।',
      content_ta: 'வணக்கம்! உங்கள் ஆவணத்தை நான் பகுப்பாய்வு செய்துள்ளேன். பிரிவுகள், கடமைகள் அல்லது இடர்கள் குறித்து எந்தக் கேள்வியையும் என்னிடம் கேட்கலாம்.'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          document_text: documentText || '',
          intake_context: intakeContext,
          chat_history: messages.map(m => ({ role: m.role, content: m.content })),
          language: language || 'en'
        })
      });

      if (!res.ok) throw new Error('Chat API failed');
      const data = await res.json();

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply,
          content_hi: data.reply_hi || data.reply,
          content_ta: data.reply_ta || data.reply
        }
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error while processing your request.',
          content_hi: 'क्षमा करें, आपके अनुरोध को प्रोसेस करते समय एक त्रुटि हुई।',
          content_ta: 'மன்னிக்கவும், உங்கள் கோரிக்கையைச் செயல்படுத்தும்போது பிழை ஏற்பட்டது.'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const currentDisclaimer = isTamil
    ? MANDATORY_DISCLAIMER_TA_TEXT
    : isHindi
    ? MANDATORY_DISCLAIMER_HI_TEXT
    : MANDATORY_DISCLAIMER_TEXT;

  const langClass = isTamil ? 'lang-ta leading-[1.85]' : isHindi ? 'lang-hi leading-[1.75]' : 'leading-relaxed';

  return (
    <div className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[550px] ${isTamil ? 'lang-ta' : isHindi ? 'lang-hi' : ''}`}>
      {/* Thread Header */}
      <div className="bg-slate-900 text-white p-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div className="min-w-0">
          <h3 className="font-bold text-sm break-words">
            {isTamil
              ? "ஆவணக் கேள்வி-பதில்"
              : isHindi
              ? "इंटरएक्टिव दस्तावेज़ प्रश्नोत्तर"
              : "Interactive Document Q&A"}
          </h3>
          <p className="text-xs text-slate-300 break-words">
            {isTamil
              ? "குறிப்பிட்ட விதிமுறைகள் அல்லது இடர்கள் பற்றி கேள்விகள் கேட்கவும்"
              : isHindi
              ? "विशिष्ट शर्तों या जोखिमों के बारे में प्रश्न पूछें"
              : "Ask questions about specific terms or risks"}
          </p>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50">
        {messages.map((msg, index) => {
          const displayContent =
            msg.role === 'assistant'
              ? isTamil && msg.content_ta
                ? msg.content_ta
                : isHindi && msg.content_hi
                ? msg.content_hi
                : msg.content
              : msg.content;

          return (
            <div
              key={index}
              className={`flex items-start gap-2.5 sm:gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold ${
                msg.role === 'user' ? 'bg-slate-800' : 'bg-blue-600'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`max-w-[85%] sm:max-w-[80%] min-w-0 rounded-xl p-3.5 sm:p-4 shadow-sm text-sm break-words ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none space-y-3'
              }`}>
                <div className={`whitespace-pre-line break-words ${langClass}`}>{displayContent}</div>

                {msg.role === 'assistant' && (
                  <div className={`pt-2 border-t border-slate-100 text-[11px] text-amber-800 font-medium break-words ${langClass}`}>
                    {currentDisclaimer}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center gap-2 text-slate-500 text-xs italic p-2">
            <Loader2 className="w-4 h-4 animate-spin text-blue-600 shrink-0" />
            <span className="break-words">
              {isTamil
                ? "ஆவணச் சூழலுடன் கேள்வி பகுப்பாய்வு செய்யப்படுகிறது..."
                : isHindi
                ? "दस्तावेज़ संदर्भ के विरुद्ध प्रश्न का विश्लेषण किया जा रहा है..."
                : "Analyzing question against document context..."}
            </span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-200 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isTamil
              ? "இந்த ஆவணத்தைப் பற்றிக் கேட்கவும்..."
              : isHindi
              ? "दस्तावेज़ के बारे में प्रश्न पूछें..."
              : "Ask a question about this document (e.g. Can I terminate early?)..."
          }
          className="flex-1 min-w-0 px-3 sm:px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-3.5 sm:px-4 py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
