import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, Loader2, Edit3 } from 'lucide-react';

export default function FileUpload({ intakeContext, onEditIntake, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (!selected.name.toLowerCase().endswith('.pdf') && selected.type !== 'application/pdf') {
        setError('Please select a valid PDF file.');
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
        setError('Please upload a PDF document.');
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
      setError('Please select a PDF file first.');
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
    <div className="max-w-xl mx-auto space-y-6">
      {/* Client Profile Header Badge */}
      <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 flex items-center justify-between text-sm text-slate-700">
        <div>
          <span className="font-semibold text-slate-900">Active Profile:</span>{' '}
          <span className="capitalize">{intakeContext.employment_type.replace('_', ' ')}</span> •{' '}
          <span>{intakeContext.has_dependents ? `${intakeContext.dependents_count} Dependents` : 'No Dependents'}</span> •{' '}
          <span className="capitalize">{intakeContext.document_type.replace('_', ' ')}</span>
        </div>
        <button
          onClick={onEditIntake}
          className="text-blue-600 hover:text-blue-800 text-xs font-semibold flex items-center gap-1 hover:underline"
        >
          <Edit3 className="w-3.5 h-3.5" />
          Edit Profile
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
              {file ? file.name : 'Click to upload or drag & drop your PDF'}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports PDF contract templates, leases, agreements (Max 25MB)
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
            <span>Analyzing Clauses & Assessing Risks...</span>
          </>
        ) : (
          <span>Analyze Legal Document</span>
        )}
      </button>
    </div>
  );
}
