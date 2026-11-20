import { useState, useEffect } from 'react';
import { analyzeRelease, getScenarios, submitApproval, toggleAction } from '../services/api';
import type {
  UnifiedRiskReport,
  ScenarioPreset,
  Severity,
  ActionStatus,
  ApprovalStatus,
  ReleaseType
} from '../types';
import {
  Shield, ShieldAlert, ShieldCheck, Activity, GitCommit,
  TrendingUp, TrendingDown, Minus, CheckCircle2,
  AlertTriangle, Zap, Cpu, Award, FileSpreadsheet, Lock
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export const RiskDashboard = () => {
  const [repo, setRepo] = useState('facebook/react');
  const [release, setRelease] = useState('v19.0.0');
  const [releaseType, setReleaseType] = useState<ReleaseType>('MINOR');
  const [environment, setEnvironment] = useState('production');
  const [scenario, setScenario] = useState('standard_healthy');
  
  const [scenarios, setScenarios] = useState<ScenarioPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState<UnifiedRiskReport | null>(null);

  // Approval Form State
  const [approverName, setApproverName] = useState('');
  const [approverRole, setApproverRole] = useState('Release Manager');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [submittingApproval, setSubmittingApproval] = useState(false);

  useEffect(() => {
    getScenarios()
      .then(setScenarios)
      .catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!repo || !release) return;
    setLoading(true);
    setError('');
    
    try {
      const data = await analyzeRelease({
        repository: repo,
        release,
        release_type: releaseType,
        target_environment: environment,
        scenario
      });
      setReport(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred during multi-agent analysis.');
    } finally {
      setLoading(false);
    }
  };

  const handleActionToggle = async (actionId: string, currentStatus: ActionStatus) => {
    if (!report) return;
    const newStatus: ActionStatus = currentStatus === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await toggleAction({
        repository: report.repository,
        release: report.release,
        action_id: actionId,
        status: newStatus
      });
      // Update local state
      setReport({
        ...report,
        required_actions: report.required_actions.map(act =>
          act.id === actionId ? { ...act, status: newStatus } : act
        )
      });
    } catch (err) {
      console.error('Failed to toggle action status', err);
    }
  };

  const handleSubmitApproval = async (status: ApprovalStatus) => {
    if (!report) return;
    if (!approverName.trim()) {
      alert('Please enter an Approver Name for the audit record.');
      return;
    }
    setSubmittingApproval(true);
    try {
      const updatedApproval = await submitApproval({
        repository: report.repository,
        release: report.release,
        status,
        approver_name: approverName,
        approver_role: approverRole,
        notes: approvalNotes
      });
      setReport({
        ...report,
        approval: updatedApproval
      });
      setApprovalNotes('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record approval decision.');
    } finally {
      setSubmittingApproval(false);
    }
  };

  const renderRiskShield = (level: Severity) => {
    switch (level) {
      case 'CRITICAL':
      case 'HIGH':
        return <ShieldAlert className="w-14 h-14 text-red-500" />;
      case 'MEDIUM':
        return <Shield className="w-14 h-14 text-amber-500" />;
      case 'LOW':
        return <ShieldCheck className="w-14 h-14 text-emerald-500" />;
      default:
        return <Shield className="w-14 h-14 text-slate-500" />;
    }
  };

  const renderTrendIcon = (trend: string) => {
    switch (trend) {
      case 'INCREASING':
        return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'DECREASING':
        return <TrendingDown className="w-4 h-4 text-emerald-500" />;
      default:
        return <Minus className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6 bg-slate-50 min-h-screen">
      
      {/* HEADER & INPUT CONFIGURATION */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 pb-6 border-b border-slate-100">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-3">
              <Shield className="w-8 h-8 text-indigo-600" />
              ReleaseShield <span className="text-xs px-2.5 py-1 font-semibold bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">MVP Risk Advisor</span>
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Multi-Agentic Release Risk Advisor with Hybrid XGBoost Engine & Mandatory Human Gatekeeper Sign-Off
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-3 py-1 bg-slate-100 text-slate-700 rounded-lg border border-slate-200">
              Deployment: <strong className="text-slate-900">Manual / Human-Gated</strong>
            </span>
          </div>
        </div>

        {/* INPUTS ROW */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Repository</label>
            <input
              type="text"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none font-medium"
              placeholder="e.g. facebook/react"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Target Release Tag</label>
            <input
              type="text"
              value={release}
              onChange={(e) => setRelease(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none font-medium"
              placeholder="e.g. v19.0.0"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Release Type</label>
            <select
              value={releaseType}
              onChange={(e) => setReleaseType(e.target.value as ReleaseType)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none font-medium"
            >
              <option value="MAJOR">MAJOR (Breaking Changes)</option>
              <option value="MINOR">MINOR (Feature Release)</option>
              <option value="PATCH">PATCH (Bug Fixes)</option>
              <option value="HOTFIX">HOTFIX (Urgent Emergency)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Target Environment</label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white outline-none font-medium"
            >
              <option value="production">Production (High SLA)</option>
              <option value="staging">Staging / Pre-Prod</option>
            </select>
          </div>
        </div>

        {/* SCENARIO PRESETS BAR */}
        <div className="pt-2">
          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            Evaluation Scenario Preset (Academic MVP Synthetic Telemetry):
          </label>
          <div className="flex flex-wrap gap-2">
            {scenarios.map((sc) => (
              <button
                key={sc.id}
                type="button"
                onClick={() => setScenario(sc.id)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                  scenario === sc.id
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                {sc.name}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="px-8 py-3 bg-indigo-600 text-white font-bold text-sm rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-md shadow-indigo-100 flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Evaluating 4 Agents & XGBoost...
              </>
            ) : (
              'Run Multi-Agent Risk Assessment'
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
            <div>
              <p className="font-semibold">Assessment Error</p>
              <p className="mt-0.5">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* DASHBOARD BODY */}
      {report && (
        <div className="space-y-6">

          {/* 1. MANDATORY HUMAN APPROVAL GATE BANNER */}
          <div className={`rounded-2xl p-6 border shadow-sm ${
            report.approval.status === 'APPROVED'
              ? 'bg-emerald-50 border-emerald-200'
              : report.approval.status === 'REJECTED'
              ? 'bg-red-50 border-red-200'
              : 'bg-amber-50 border-amber-200'
          }`}>
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-xl ${
                  report.approval.status === 'APPROVED'
                    ? 'bg-emerald-100 text-emerald-800'
                    : report.approval.status === 'REJECTED'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-amber-100 text-amber-800'
                }`}>
                  <Lock className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded bg-white border">
                      Mandatory Human Gate
                    </span>
                    <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                      report.approval.status === 'APPROVED'
                        ? 'bg-emerald-200 text-emerald-900'
                        : report.approval.status === 'REJECTED'
                        ? 'bg-red-200 text-red-900'
                        : 'bg-amber-200 text-amber-900'
                    }`}>
                      {report.approval.status.replace('_', ' ')}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">
                    {report.approval.status === 'APPROVED'
                      ? `Deployment Permitted: Signed off by ${report.approval.approver_name} (${report.approval.approver_role})`
                      : report.approval.status === 'REJECTED'
                      ? `Release Blocked: Rejected by ${report.approval.approver_name}`
                      : 'Release Blocked: Awaiting Human Gatekeeper Review'}
                  </h3>
                  <p className="text-xs text-slate-600 mt-1">
                    ReleaseShield provides explainable advisory intelligence only. Automated deployment is strictly out-of-scope; manual sign-off is required.
                  </p>
                  {report.approval.notes && (
                    <p className="text-xs italic text-slate-700 mt-1 bg-white/70 p-2 rounded border border-black/5">
                      " {report.approval.notes} "
                    </p>
                  )}
                </div>
              </div>

              {/* Approval Action Form */}
              <div className="w-full lg:w-auto bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <p className="text-xs font-bold text-slate-700 uppercase tracking-wider">Gatekeeper Sign-Off</p>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Approver Full Name"
                    value={approverName}
                    onChange={(e) => setApproverName(e.target.value)}
                    className="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 outline-none"
                  />
                  <select
                    value={approverRole}
                    onChange={(e) => setApproverRole(e.target.value)}
                    className="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 outline-none"
                  >
                    <option value="Release Manager">Release Manager</option>
                    <option value="QA Lead">QA Lead</option>
                    <option value="VP of Engineering">VP Engineering</option>
                    <option value="DevOps / SRE Lead">DevOps / SRE Lead</option>
                    <option value="Tech Lead">Tech Lead</option>
                  </select>
                </div>
                <input
                  type="text"
                  placeholder="Review Notes / Justification (optional)"
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                  className="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg focus:ring-1 focus:ring-indigo-500 outline-none"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSubmitApproval('APPROVED')}
                    disabled={submittingApproval}
                    className="flex-1 px-3 py-1.5 bg-emerald-600 text-white font-bold text-xs rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                  >
                    Approve Release
                  </button>
                  <button
                    onClick={() => handleSubmitApproval('REJECTED')}
                    disabled={submittingApproval}
                    className="flex-1 px-3 py-1.5 bg-red-600 text-white font-bold text-xs rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                  >
                    Reject Release
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 2. OVERALL RISK & HYBRID ENGINE CARD */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Blended Score & Shield */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col items-center justify-center text-center">
              {renderRiskShield(report.risk_level)}
              <span className={`mt-3 text-xs font-extrabold uppercase px-3 py-1 rounded-full ${
                report.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                report.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                report.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                'bg-emerald-100 text-emerald-800'
              }`}>
                {report.risk_level} RISK
              </span>
              <p className="text-4xl font-black text-slate-900 mt-2">{report.risk_score.toFixed(2)}</p>
              <p className="text-xs text-slate-500 font-medium mt-1">Blended Risk Index (0.00 - 1.00)</p>
            </div>

            {/* Context & Metadata */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between space-y-4">
              <div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Release Context</p>
                <p className="text-base font-bold text-slate-900 mt-1">{report.repository} @ {report.release}</p>
                <div className="flex gap-2 mt-2">
                  <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-700 rounded font-semibold">{report.release_type}</span>
                  <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-700 rounded font-semibold">{report.target_environment}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-100">
                <div>
                  <p className="text-xs font-medium text-slate-500">Historical Trend</p>
                  <div className="flex items-center gap-1.5 font-bold text-slate-800 text-sm mt-0.5">
                    {renderTrendIcon(report.trend)}
                    {report.trend}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-500">Data Confidence</p>
                  <p className="text-sm font-bold text-slate-800 mt-0.5">{(report.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            </div>

            {/* Hybrid Engine Component Breakdown */}
            <div className="bg-indigo-900 text-white p-6 rounded-2xl shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold tracking-wider uppercase text-indigo-300 flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5" /> Hybrid Risk Engine
                  </span>
                  <span className="text-xs bg-indigo-800 text-indigo-200 px-2 py-0.5 rounded font-mono">v3.4</span>
                </div>
                <div className="mt-4 space-y-3">
                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-indigo-200">XGBoost ML Probability</span>
                      <span>{(report.hybrid_engine.xgboost_risk_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-indigo-950 rounded-full h-2">
                      <div className="bg-cyan-400 h-2 rounded-full" style={{ width: `${report.hybrid_engine.xgboost_risk_score * 100}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span className="text-indigo-200">Deterministic Rules Score</span>
                      <span>{(report.hybrid_engine.deterministic_rule_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-indigo-950 rounded-full h-2">
                      <div className="bg-amber-400 h-2 rounded-full" style={{ width: `${report.hybrid_engine.deterministic_rule_score * 100}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

              {report.hybrid_engine.hard_gate_triggered && (
                <div className="mt-4 p-2.5 bg-red-950/80 border border-red-500/50 rounded-xl text-xs text-red-200 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <span>{report.hybrid_engine.hard_gate_reason}</span>
                </div>
              )}
            </div>

          </div>

          {/* 3. KEY RISK DRIVERS (XGBoost Feature Attribution) */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-600" />
                Key Risk Drivers (XGBoost Feature Importance Attribution)
              </h3>
              <span className="text-xs text-slate-400 font-medium">Ranked by risk contribution</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {report.risk_drivers.map((driver, idx) => (
                <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700">{driver.display_name}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      driver.impact_level === 'HIGH' ? 'bg-red-100 text-red-700' :
                      driver.impact_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                      'bg-slate-200 text-slate-700'
                    }`}>
                      {driver.contribution_pct}% Impact
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        driver.impact_level === 'HIGH' ? 'bg-red-500' :
                        driver.impact_level === 'MEDIUM' ? 'bg-amber-500' : 'bg-slate-400'
                      }`}
                      style={{ width: `${Math.min(driver.contribution_pct, 100)}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-slate-600">{driver.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 4. THE FOUR DOMAIN AGENTS */}
          <div>
            <h2 className="text-lg font-black text-slate-900 tracking-tight mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-600" />
              The Four Domain Agents
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              
              {/* CODE AGENT */}
              <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <span className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                      <GitCommit className="w-4 h-4 text-blue-600" /> Code Agent
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      report.code_agent.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' :
                      report.code_agent.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {report.code_agent.risk_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Code Churn:</span>
                      <strong className="text-slate-900">{report.code_agent.metrics.code_churn?.toLocaleString()} lines</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Files Changed:</span>
                      <strong className="text-slate-900">{report.code_agent.metrics.files_changed}</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Avg PR Merge:</span>
                      <strong className="text-slate-900">{report.code_agent.metrics.avg_pr_merge_time_hours} hrs</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Core/Config Touches:</span>
                      <strong className="text-slate-900">{report.code_agent.metrics.high_risk_files_touched}</strong>
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-xs text-slate-500 pt-3 border-t border-slate-100">{report.code_agent.summary}</p>
              </div>

              {/* TEST AGENT */}
              <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <span className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Test Agent
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      report.test_agent.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                      report.test_agent.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                      report.test_agent.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {report.test_agent.risk_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Pass Rate:</span>
                      <strong className={report.test_agent.metrics.pass_rate_pct < 100 ? 'text-red-600 font-bold' : 'text-emerald-700 font-bold'}>
                        {report.test_agent.metrics.pass_rate_pct}%
                      </strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Coverage:</span>
                      <strong className="text-slate-900">{report.test_agent.metrics.coverage_pct}%</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Coverage Delta:</span>
                      <strong className={report.test_agent.metrics.coverage_delta_pct < 0 ? 'text-red-600' : 'text-emerald-600'}>
                        {report.test_agent.metrics.coverage_delta_pct > 0 ? '+' : ''}{report.test_agent.metrics.coverage_delta_pct}%
                      </strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Flaky Tests:</span>
                      <strong className="text-slate-900">{report.test_agent.metrics.flaky_tests_count}</strong>
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-xs text-slate-500 pt-3 border-t border-slate-100">{report.test_agent.summary}</p>
              </div>

              {/* DEFECT AGENT */}
              <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <span className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600" /> Defect Agent
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      report.defect_agent.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                      report.defect_agent.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                      report.defect_agent.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {report.defect_agent.risk_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Open Blockers (P0):</span>
                      <strong className={report.defect_agent.metrics.open_blockers > 0 ? 'text-red-600 font-black' : 'text-emerald-700'}>
                        {report.defect_agent.metrics.open_blockers}
                      </strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Open Critical (P1):</span>
                      <strong className="text-slate-900">{report.defect_agent.metrics.open_critical}</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Defect Density:</span>
                      <strong className="text-slate-900">{report.defect_agent.metrics.defect_density_per_kloc}/KLOC</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Bug Escape Rate:</span>
                      <strong className="text-slate-900">{report.defect_agent.metrics.bug_escape_rate_pct}%</strong>
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-xs text-slate-500 pt-3 border-t border-slate-100">{report.defect_agent.summary}</p>
              </div>

              {/* OPERATIONS AGENT */}
              <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <span className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                      <Activity className="w-4 h-4 text-purple-600" /> Operations Agent
                    </span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      report.operations_agent.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                      report.operations_agent.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                      report.operations_agent.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {report.operations_agent.risk_score.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Pipeline Pass Rate:</span>
                      <strong className="text-slate-900">{report.operations_agent.metrics.pipeline_success_rate_pct}%</strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Staging Status:</span>
                      <strong className={report.operations_agent.metrics.staging_deploy_status !== 'HEALTHY' ? 'text-red-600 font-bold' : 'text-emerald-700'}>
                        {report.operations_agent.metrics.staging_deploy_status}
                      </strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Staging Rollbacks (7d):</span>
                      <strong className={report.operations_agent.metrics.staging_rollbacks_7d > 0 ? 'text-red-600 font-bold' : 'text-slate-900'}>
                        {report.operations_agent.metrics.staging_rollbacks_7d}
                      </strong>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Infra Drift:</span>
                      <strong className={report.operations_agent.metrics.infra_config_drift ? 'text-red-600 font-bold' : 'text-emerald-700'}>
                        {report.operations_agent.metrics.infra_config_drift ? 'DETECTED' : 'NONE'}
                      </strong>
                    </div>
                  </div>
                </div>
                <p className="mt-4 text-xs text-slate-500 pt-3 border-t border-slate-100">{report.operations_agent.summary}</p>
              </div>

            </div>
          </div>

          {/* 5. PRACTICAL REQUIRED ACTIONS & READINESS CHECKLIST */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                  Release Readiness & Required Actions Checklist
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Concrete operational actions required prior to release sign-off</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg">
                {report.required_actions.filter(a => a.status === 'COMPLETED').length} of {report.required_actions.length} Completed
              </span>
            </div>

            <div className="space-y-3">
              {report.required_actions.map((act) => (
                <div
                  key={act.id}
                  className={`p-4 rounded-xl border flex flex-col md:flex-row justify-between items-start md:items-center gap-3 transition-all ${
                    act.status === 'COMPLETED'
                      ? 'bg-emerald-50/50 border-emerald-200 text-slate-700'
                      : act.priority === 'BLOCKER'
                      ? 'bg-red-50/60 border-red-200'
                      : 'bg-slate-50 border-slate-200'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-2xs font-black uppercase px-2 py-0.5 rounded ${
                        act.priority === 'BLOCKER' ? 'bg-red-200 text-red-900' :
                        act.priority === 'HIGH' ? 'bg-orange-200 text-orange-900' :
                        'bg-slate-200 text-slate-800'
                      }`}>
                        {act.priority}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">{act.category}</span>
                      <span className="text-xs font-medium text-slate-400">• Owner: <strong>{act.owner_role}</strong></span>
                    </div>
                    <p className="text-sm font-bold text-slate-900">{act.title}</p>
                    <p className="text-xs text-slate-600">{act.description}</p>
                  </div>

                  <button
                    onClick={() => handleActionToggle(act.id, act.status)}
                    className={`px-4 py-2 text-xs font-bold rounded-lg border transition-all ${
                      act.status === 'COMPLETED'
                        ? 'bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700'
                        : 'bg-white text-slate-700 border-slate-300 hover:border-slate-400 hover:bg-slate-100'
                    }`}
                  >
                    {act.status === 'COMPLETED' ? '✓ Completed' : 'Mark Complete'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* 6. PRACTICAL RECOMMENDATIONS & EXPLAINABLE REPORT */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Recommendations */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-indigo-600" />
                Actionable Recommendations
              </h3>
              <ul className="space-y-3 text-xs text-slate-700">
                {report.recommendations.map((rec, idx) => (
                  <li key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center flex-shrink-0 text-xs">
                      {idx + 1}
                    </span>
                    <span className="mt-0.5 leading-relaxed font-medium">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* AI Explainable Report */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                Explainable Risk Assessment Report
              </h3>
              <div className="prose prose-sm max-w-none text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-200 max-h-[380px] overflow-y-auto text-xs leading-relaxed">
                <ReactMarkdown>{report.explanation}</ReactMarkdown>
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
};
