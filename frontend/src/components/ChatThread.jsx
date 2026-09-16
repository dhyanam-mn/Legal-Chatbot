import React, { useState } from 'react';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import Disclaimer, { MANDATORY_DISCLAIMER_TEXT } from './Disclaimer';

export default function ChatThread({ documentText, intakeContext }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I have analyzed your document. Feel free to ask me any specific questions about clauses, obligations, or risks.'
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
          chat_history: messages.map(m => ({ role: m.role, content: m.content }))
        })
      });

      if (!res.ok) throw new Error('Chat API failed');
      const data = await res.json();

      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.reply }
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error while processing your request.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-[550px]">
      {/* Thread Header */}
      <div className="bg-slate-900 text-white p-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-bold text-sm">Interactive Document Q&A</h3>
          <p className="text-xs text-slate-300">Ask questions about specific terms or risks</p>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs font-bold ${
              msg.role === 'user' ? 'bg-slate-800' : 'bg-blue-600'
            }`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className={`max-w-[80%] rounded-xl p-4 shadow-sm text-sm ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-tr-none'
                : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none space-y-3'
            }`}>
              <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>

              {msg.role === 'assistant' && (
                <div className="pt-2 border-t border-slate-100 text-[11px] text-amber-800 font-medium">
                  {MANDATORY_DISCLAIMER_TEXT}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-slate-500 text-xs italic p-2">
            <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
            <span>Analyzing question against document context...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-200 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this document (e.g. Can I terminate early?)..."
          className="flex-1 px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-4 py-2.5 rounded-lg font-medium transition-colors flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
