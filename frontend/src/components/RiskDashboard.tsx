import React, { useState } from 'react';
import { analyzeRelease } from '../services/api';
import type { RiskReport } from '../types';
import { Shield, ShieldAlert, ShieldCheck, Activity, GitCommit, FileCode, Users, GitPullRequest, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export const RiskDashboard = () => {
  const [repo, setRepo] = useState('facebook/react');
  const [release, setRelease] = useState('v19.0.0');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState<RiskReport | null>(null);

  const handleAnalyze = async () => {
    if (!repo || !release) return;
    setLoading(true);
    setError('');
    
    try {
      const data = await analyzeRelease({ repository: repo, release });
      setReport(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during analysis.');
    } finally {
      setLoading(false);
    }
  };

  const renderRiskShield = (level: string) => {
    switch(level) {
      case 'CRITICAL':
      case 'HIGH': return <ShieldAlert className="w-12 h-12 text-red-500" />;
      case 'MEDIUM': return <Shield className="w-12 h-12 text-yellow-500" />;
      case 'LOW': return <ShieldCheck className="w-12 h-12 text-green-500" />;
      default: return <Shield className="w-12 h-12 text-gray-500" />;
    }
  };
  
  const renderTrendIcon = (trend: string) => {
    switch(trend) {
      case 'INCREASING': return <TrendingUp className="w-5 h-5 text-red-500" />;
      case 'DECREASING': return <TrendingDown className="w-5 h-5 text-green-500" />;
      default: return <Minus className="w-5 h-5 text-gray-500" />;
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      
      {/* HEADER & INPUTS */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2 mb-6">
          <Shield className="text-indigo-600" />
          ReleaseShield Risk Analysis
        </h1>
        
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-600 mb-1">Repository (owner/name)</label>
            <input 
              type="text" 
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              placeholder="e.g., facebook/react"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-600 mb-1">Target Release / Tag</label>
            <input 
              type="text" 
              value={release}
              onChange={(e) => setRelease(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              placeholder="e.g., v19.0.0"
            />
          </div>
          <button 
            onClick={handleAnalyze}
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze Release'}
          </button>
        </div>
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
            {error}
          </div>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center p-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      )}

      {/* REPORT DASHBOARD */}
      {!loading && report && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* TOP CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Risk Score */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col items-center justify-center">
              {renderRiskShield(report.risk_level)}
              <h2 className="text-xl font-bold mt-2 text-slate-800">{report.risk_level} RISK</h2>
              <p className="text-3xl font-black text-slate-900 mt-1">{report.risk_score.toFixed(2)}</p>
            </div>
            
            {/* Meta Info */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col justify-center space-y-4">
              <div>
                <p className="text-sm text-slate-500">Repository</p>
                <p className="font-semibold text-slate-800">{report.repository}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Release</p>
                <p className="font-semibold text-slate-800">{report.release}</p>
              </div>
            </div>
            
            {/* Trend & Confidence */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col justify-center space-y-4">
              <div>
                <p className="text-sm text-slate-500 mb-1">Risk Trend</p>
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  {renderTrendIcon(report.trend)}
                  {report.trend}
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-500">Data Confidence</p>
                <div className="w-full bg-slate-200 rounded-full h-2.5 mt-2">
                  <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${report.confidence * 100}%` }}></div>
                </div>
                <p className="text-xs text-right mt-1 font-medium text-slate-600">{(report.confidence * 100).toFixed(0)}%</p>
              </div>
            </div>
            
          </div>

          {/* METRICS */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" /> Git Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              <MetricItem icon={<GitCommit />} label="Commits" value={report.metrics.commit_count} />
              <MetricItem icon={<FileCode />} label="Files Changed" value={report.metrics.files_changed} />
              <MetricItem icon={<span className="text-green-500 font-bold">+</span>} label="Lines Added" value={report.metrics.lines_added} />
              <MetricItem icon={<span className="text-red-500 font-bold">-</span>} label="Lines Deleted" value={report.metrics.lines_deleted} />
              <MetricItem icon={<Activity />} label="Code Churn" value={report.metrics.code_churn} highlight />
              <MetricItem icon={<Users />} label="Contributors" value={report.metrics.unique_contributors} />
              <MetricItem icon={<GitPullRequest />} label="Pull Requests" value={report.metrics.pr_count} />
            </div>
          </div>

          {/* FINDINGS & RECOMMENDATIONS */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4">Risk Findings</h3>
              {report.findings.length === 0 ? (
                <p className="text-slate-500 italic">No significant anomalies detected.</p>
              ) : (
                <div className="space-y-3">
                  {report.findings.map((f, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-3">
                       <span className={`text-xs font-bold px-2 py-1 rounded ${
                         f.severity === 'HIGH' ? 'bg-red-100 text-red-700' :
                         f.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-700' :
                         'bg-slate-200 text-slate-700'
                       }`}>
                         {f.severity}
                       </span>
                       <div>
                         <p className="text-sm font-semibold text-slate-800">{f.category}</p>
                         <p className="text-sm text-slate-600 mt-1">{f.message}</p>
                       </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4">Recommendations</h3>
              <ul className="list-disc list-inside space-y-2 text-sm text-slate-700">
                {report.recommendations.map((r, idx) => (
                  <li key={idx} className="pl-2">{r}</li>
                ))}
              </ul>
            </div>
            
          </div>

          {/* LLM EXPLANATION */}
          <div className="bg-indigo-50 p-6 rounded-xl shadow-sm border border-indigo-100">
            <h3 className="text-lg font-bold text-indigo-900 mb-4 flex items-center gap-2">
              🤖 AI Explanation
            </h3>
            <div className="prose prose-indigo prose-sm max-w-none text-slate-700">
              <ReactMarkdown>{report.explanation || "No explanation provided."}</ReactMarkdown>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

const MetricItem = ({ icon, label, value, highlight = false }: any) => (
  <div className={`p-4 rounded-lg flex flex-col items-center justify-center text-center ${highlight ? 'bg-indigo-50 border border-indigo-100' : 'bg-slate-50 border border-slate-100'}`}>
    <div className="text-slate-400 mb-2">{icon}</div>
    <p className={`text-xl font-bold ${highlight ? 'text-indigo-700' : 'text-slate-800'}`}>
      {typeof value === 'number' ? value.toLocaleString() : value}
    </p>
    <p className="text-xs text-slate-500 font-medium uppercase mt-1">{label}</p>
  </div>
);
