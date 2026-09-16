import React, { useState } from 'react';
import { UserCheck, Users, DollarSign, FileText, ArrowRight } from 'lucide-react';

export default function IntakeForm({ onSubmitIntake }) {
  const [formData, setFormData] = useState({
    employment_type: 'salaried',
    has_dependents: false,
    dependents_count: 0,
    income_bracket: 'medium',
    document_type: 'employment_contract'
  });

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
    <div className="max-w-xl mx-auto bg-white rounded-xl shadow-md border border-slate-200 p-6 md:p-8">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-slate-900">Client Intake Context</h2>
        <p className="text-sm text-slate-500 mt-1">
          Provide your profile information so we can rank and prioritize clause risks specific to your situation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Employment Type */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <UserCheck className="w-4 h-4 text-blue-600" />
            Employment Type
          </label>
          <select
            value={formData.employment_type}
            onChange={(e) => handleChange('employment_type', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50 text-slate-800"
          >
            <option value="salaried">Salaried Employee</option>
            <option value="self_employed">Self-Employed / Freelancer</option>
            <option value="business_owner">Business Owner</option>
            <option value="unemployed">Job Seeking / Unemployed</option>
            <option value="retired">Retired</option>
          </select>
        </div>

        {/* Dependents */}
        <div>
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-2">
            <Users className="w-4 h-4 text-blue-600" />
            Dependents Profile
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
              I have financial dependents
            </label>

            {formData.has_dependents && (
              <div className="flex items-center gap-2 ml-auto">
                <span className="text-xs text-slate-500">Count:</span>
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
            Approximate Income Bracket
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'low', label: 'Lower / Entry' },
              { id: 'medium', label: 'Middle' },
              { id: 'high', label: 'Upper / High' }
            ].map(b => (
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
            Document Type to Analyze
          </label>
          <select
            value={formData.document_type}
            onChange={(e) => handleChange('document_type', e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50 text-slate-800"
          >
            <option value="employment_contract">Employment Contract</option>
            <option value="rental_agreement">Rental / Lease Agreement</option>
            <option value="service_agreement">Freelance / Service Contract</option>
            <option value="loan_agreement">Loan / Financial Agreement</option>
            <option value="other">Other Legal Document</option>
          </select>
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-md"
        >
          <span>Continue to Document Upload</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
