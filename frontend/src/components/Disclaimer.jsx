import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const MANDATORY_DISCLAIMER_TEXT = "This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this.";

export default function Disclaimer({ compact = false }) {
  if (compact) {
    return (
      <div className="bg-amber-50 border border-amber-200 text-amber-900 rounded-md p-2 text-xs flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
        <span>{MANDATORY_DISCLAIMER_TEXT}</span>
      </div>
    );
  }

  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 text-amber-900 p-4 rounded-r-lg shadow-sm flex items-start gap-3 my-4">
      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <div>
        <h4 className="font-semibold text-xs tracking-wider uppercase text-amber-800">Important Disclaimer</h4>
        <p className="text-sm mt-0.5 font-medium">{MANDATORY_DISCLAIMER_TEXT}</p>
      </div>
    </div>
  );
}
