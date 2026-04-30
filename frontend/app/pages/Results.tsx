import { useParams, Link } from 'react-router';
import { useApp } from '../context/AppContext';
import { api, formatApiError } from '../lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { LineChartAnalysis, TrendPoint } from '../components/LineChartAnalysis';
import { ArrowLeft, TrendingDown, DollarSign, Calendar, Download, AlertTriangle, Sparkles, Brain, BadgeAlert, Target, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';
import { useState } from 'react';
import { useNavigate } from 'react-router';

const COLORS = ['#6366f1', '#ec4899', '#8b5cf6', '#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#14b8a6'];

export function Results() {
  const { analysisId } = useParams();
  const { getResultByAnalysisId, analyses, transactions, deleteAnalysis } = useApp();
  const navigate = useNavigate();

  const result = getResultByAnalysisId(analysisId!);
  const analysis = analyses.find((item) => item.id === analysisId);

  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [chartGranularity, setChartGranularity] = useState<'day' | 'month' | 'year'>('month');
  const handleDeleteAnalysis = async () => {
    if (!analysisId || isDeleting) return;
    const accepted = window.confirm('Delete this analysis and its report? This action cannot be undone.');
    if (!accepted) return;
    try {
      setIsDeleting(true);
      await deleteAnalysis(analysisId);
      navigate('/app/analyses');
    } catch (e: any) {
      alert(formatApiError(e) || 'Failed to delete analysis.');
    } finally {
      setIsDeleting(false);
    }
  };


  const tipsByCategory: Record<string, string> = {
    groceries: 'Set a weekly cap and buy staples in bulk to reduce small frequent purchases.',
    transport: 'Compare monthly passes versus ride-hailing costs and keep trips in one route when possible.',
    entertainment: 'Group non-essential spending into a fixed budget so it does not leak across the month.',
    healthcare: 'Treat recurring prescriptions separately so one-time costs do not distort your monthly average.',
    utilities: 'Look for recurring spikes and compare them month over month before the next billing cycle.',
    dining: 'Move one or two meals per week to home cooking to see a measurable reduction.',
    shopping: 'Use a 24-hour delay rule for non-essential purchases to avoid impulse spending.',
    rent: 'Fixed costs should be tracked separately from discretionary spend when planning savings.',
    insurance: 'Review annual plans once per year and compare the effective monthly cost.',
    travel: 'Create a dedicated travel reserve so you do not pull from emergency savings.',
    salary: 'If income is stable, automate transfers right after payday to lock in savings early.',
    freelance: 'Irregular income works better with a baseline budget and a surplus buffer.',
    investment: 'Avoid treating investment gains as spendable cash; keep them in a separate bucket.',
  };

  const anomalyPatterns = result?.anomalies?.length
    ? [
      'The anomaly detector found spending outliers. Review the largest entries first, then check whether they were one-time exceptions or recurring risks.',
      'If the same category appears repeatedly in anomalies, it is a structural issue rather than a one-off event.',
    ]
    : [
      'No anomalies were detected. That is a good sign, but keep monitoring categories with volatile spending.',
    ];

  const handleExport = async () => {
    if (!result || !analysisId) return;
    try {
      setIsExporting(true);
      const { blob, filename, contentType } = await api.downloadAnalysisReport(analysisId);
      if (!contentType.includes('application/pdf')) {
        throw new Error('The analysis report was not generated as a PDF.');
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `analysis-report-${analysisId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      console.error('Failed to export report', e);
      alert(formatApiError(e) || 'The export could not be generated. Please try again or contact support if the issue persists.');
    } finally {
      setIsExporting(false);
    }
  };

  if (!result) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <h2 className="text-2xl mb-2">Analysis Not Found</h2>
          <p className="text-slate-400 mb-2">We could not load the analysis results for this identifier.</p>
          <p className="text-slate-500 mb-6">This usually means the analysis has not finished yet, the record was removed, or the browser cached an outdated link.</p>
          <Link
            to="/app/analyses"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Analyses
          </Link>
        </div>
      </div>
    );
  }

  const groupedFromTransactions = Object.values(
    transactions.reduce<Record<string, { key: string; label: string; income: number; expense: number }>>((acc, tx) => {
      const txDate = new Date(tx.date);
      if (Number.isNaN(txDate.getTime())) return acc;
      const key = chartGranularity === 'day'
        ? `${txDate.getFullYear()}-${String(txDate.getMonth() + 1).padStart(2, '0')}-${String(txDate.getDate()).padStart(2, '0')}`
        : chartGranularity === 'year'
          ? `${txDate.getFullYear()}`
          : `${txDate.getFullYear()}-${String(txDate.getMonth() + 1).padStart(2, '0')}`;
      if (!acc[key]) {
        const label = chartGranularity === 'day'
          ? txDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
          : chartGranularity === 'year'
            ? txDate.toLocaleDateString('en-US', { year: 'numeric' })
            : txDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        acc[key] = {
          key,
          label,
          income: 0,
          expense: 0,
        };
      }
      if (tx.type === 'Income') acc[key].income += Number(tx.amount ?? 0);
      else acc[key].expense += Number(tx.amount ?? 0);
      return acc;
    }, {})
  )
    .sort((a, b) => a.key.localeCompare(b.key))
    .map((item) => ({ ...item, net: item.income - item.expense }));
  const chartDataPoints: TrendPoint[] = groupedFromTransactions;

  const chartData = Object.entries(result.byCategory).map(([name, value]) => ({
    name,
    value,
  }));
  const sortedChartData = [...chartData].sort((a, b) => b.value - a.value);

  const netBalance = result.totalIncome - result.totalExpenses;
  const savingsRate = result.totalIncome > 0 ? (netBalance / result.totalIncome) * 100 : null;
  const largestCategoryPct = result.totalExpenses > 0 && sortedChartData[0]?.value != null
    ? (sortedChartData[0].value / result.totalExpenses) * 100
    : null;
  const recommendationsFromAnalysis = (result as any)?.recommendations;
  const recommendationLines = Array.isArray(recommendationsFromAnalysis) && recommendationsFromAnalysis.length > 0
    ? recommendationsFromAnalysis.slice(0, 3)
    : [
      'Review fixed vs variable costs separately to spot persistent leakages.',
      'Prioritize categories where both total amount and anomaly frequency are high.',
      'Set a monthly savings transfer based on your current net balance trend.',
    ];
  const dominantCategory = sortedChartData[0]?.name ?? null;
  const analysisFindings = [
    netBalance >= 0
      ? `Current period closes with a surplus of $${netBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}.`
      : `Current period closes with a deficit of $${Math.abs(netBalance).toLocaleString('en-US', { minimumFractionDigits: 2 })}.`,
    savingsRate === null
      ? 'Savings rate is unavailable because income data is missing for this period.'
      : `Estimated savings rate is ${savingsRate.toFixed(1)}%, which indicates ${savingsRate >= 20 ? 'healthy' : savingsRate >= 10 ? 'moderate' : 'low'} saving capacity.`,
    dominantCategory && largestCategoryPct !== null
      ? `${dominantCategory} is the dominant expense category at ${largestCategoryPct.toFixed(1)}% of total expenses.`
      : 'No dominant category detected yet.',
    result.anomalies.length > 0
      ? `${result.anomalies.length} anomalies were flagged; focus first on the largest amounts to reduce risk quickly.`
      : 'No anomalies were flagged in this run, indicating stable spending behavior for the analyzed data.',
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/app/analyses"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Analyses
          </Link>
          <h1 className="text-3xl mb-2">Analysis Results</h1>
          <p className="text-slate-400">{analysis?.name || 'Financial Analysis'}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDeleteAnalysis}
            disabled={isDeleting}
            className="flex items-center gap-2 px-5 py-2.5 bg-red-900/40 hover:bg-red-800/60 text-red-200 rounded-lg transition-all border border-red-700/50 disabled:opacity-50"
          >
            <Trash2 className="w-5 h-5" />
            {isDeleting ? 'Deleting...' : 'Delete Analysis'}
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-all border border-slate-700 disabled:opacity-50"
          >
            <Download className="w-5 h-5" />
            {isExporting ? 'Exporting...' : 'Export Report'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-red-600/20 rounded-lg flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-red-400" />
            </div>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">Core Metric</span>
          </div>
          <div className="text-3xl text-red-400 mb-1">
            ${result.totalExpenses.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-slate-400">Total Expenses</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-emerald-600/20 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-emerald-400" />
            </div>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">Core Metric</span>
          </div>
          <div className="text-3xl text-emerald-400 mb-1">
            ${result.totalIncome.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-slate-400">Total Income</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${netBalance >= 0 ? 'bg-indigo-600/20' : 'bg-red-600/20'
              }`}>
              <DollarSign className={`w-6 h-6 ${netBalance >= 0 ? 'text-indigo-400' : 'text-red-400'}`} />
            </div>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">Core Metric</span>
          </div>
          <div className={`text-3xl mb-1 ${netBalance >= 0 ? 'text-indigo-400' : 'text-red-400'}`}>
            ${Math.abs(netBalance).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="text-sm text-slate-400">{netBalance >= 0 ? 'Surplus' : 'Deficit'}</div>
        </motion.div>
      </div>

      {/* Line Chart: Income/Expense/Net by Month */}
      {chartDataPoints.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8"
        >
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl mb-1">Income vs Expenses Trend</h2>
              <p className="text-sm text-slate-400">Compare income, expense, and net by selected interval.</p>
            </div>
            <div className="flex rounded-lg border border-slate-700 bg-slate-950/50 p-1">
              {(['day', 'month', 'year'] as const).map((option) => (
                <button
                  key={option}
                  onClick={() => setChartGranularity(option)}
                  className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                    chartGranularity === option ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {option === 'day' ? 'Daily' : option === 'month' ? 'Monthly' : 'Yearly'}
                </button>
              ))}
            </div>
          </div>
          <LineChartAnalysis data={chartDataPoints} />
        </motion.div>
      )}

      {/* Chart and Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6"
        >
          <h2 className="text-xl mb-6">Expense Distribution</h2>
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '0.5rem',
                  color: '#fff'
                }}
                formatter={(value: number) => `$${value.toFixed(2)}`}
              />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Category Breakdown */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6"
        >
          <h2 className="text-xl mb-6">Category Breakdown</h2>
          <div className="space-y-4">
            {sortedChartData.map((category, index) => {
              const percentage = (category.value / result.totalExpenses) * 100;
              return (
                <motion.div
                  key={category.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.05 * index }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-sm text-slate-300">{category.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white">
                        ${category.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-xs text-slate-500">
                        {percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 * index }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Analysis Info */}
          <div className="mt-8 pt-6 border-t border-slate-800">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Calendar className="w-4 h-4" />
              Analysis completed on {new Date(result.createdAt).toLocaleString()}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Insights Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border border-indigo-800/30 rounded-xl p-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="w-5 h-5 text-indigo-300" />
          <h2 className="text-xl">AI Insight Summary</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <div className="flex items-center gap-2 mb-2 text-slate-200">
              <Target className="w-4 h-4 text-indigo-300" />
              Concentration
            </div>
            <p className="text-sm text-slate-400">
              {chartData[0]?.name || 'N/A'} accounts for {largestCategoryPct === null ? 'N/A' : largestCategoryPct.toFixed(1) + '%'} of total expenses.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <div className="flex items-center gap-2 mb-2 text-slate-200">
              <Brain className="w-4 h-4 text-emerald-300" />
              Saving Pressure
            </div>
            <p className="text-sm text-slate-400">
              You saved {savingsRate === null ? 'N/A' : savingsRate.toFixed(1) + '%'} of income during this period.
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <div className="flex items-center gap-2 mb-2 text-slate-200">
              <BadgeAlert className="w-4 h-4 text-amber-300" />
              Risk Signal
            </div>
            <p className="text-sm text-slate-400">
              {result.anomalies.length === 0 ? 'No anomaly signals detected.' : `${result.anomalies.length} anomaly signals were detected and ranked by amount.`}
            </p>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.62 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        <div className="rounded-2xl border border-indigo-700/30 bg-gradient-to-b from-indigo-950/35 via-slate-900 to-slate-900 p-6 shadow-[0_18px_50px_-24px_rgba(79,70,229,0.55)]">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-indigo-500/40 bg-indigo-500/15">
              <Brain className="h-4 w-4 text-indigo-200" />
            </div>
            <h2 className="text-xl text-slate-100">Spending Overview</h2>
          </div>
          <div className="space-y-4 text-sm leading-7 text-slate-300">
            {analysisFindings.map((line) => (
              <p key={line}>{line}</p>
            ))}
            <div className="rounded-xl border border-slate-700/70 bg-slate-950/70 p-4">
              <div className="mb-3 text-sm font-medium text-slate-100">Analysis-backed recommendations</div>
              <ul className="space-y-2 text-slate-300">
                {recommendationLines.map((tip) => (
                  <li key={tip} className="flex items-start gap-2">
                    <span className="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-indigo-300" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="w-5 h-5 text-emerald-300" />
            <h2 className="text-xl">Category Guidance</h2>
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            {Object.entries(result.byCategory).slice(0, 6).map(([category]) => {
              const tip = tipsByCategory[category.toLowerCase()] || 'Track this category separately and compare it against the previous period to spot drift early.';
              return (
                <div key={category} className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                  <div className="mb-1 text-slate-200">{category}</div>
                  <div className="text-slate-400">{tip}</div>
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.64 }}
        className="bg-slate-900 border border-slate-800 rounded-xl p-6"
      >
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="w-5 h-5 text-amber-300" />
          <h2 className="text-xl">Interpretation</h2>
        </div>
        <div className="space-y-3 text-sm text-slate-300">
          {anomalyPatterns.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      </motion.div>

      {/* Anomalies */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.65 }}
        className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden"
      >
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-xl">Anomalies</h2>
            <p className="text-sm text-slate-400 mt-1">
              Detected unusual expense transactions ({result.anomalies?.length ?? 0})
            </p>
          </div>
          <div className="w-10 h-10 bg-amber-600/20 rounded-lg flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
        </div>

        {(!result.anomalies || result.anomalies.length === 0) ? (
          <div className="p-10 text-center text-slate-500">
            <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-6 h-6 text-slate-500" />
            </div>
            No anomalies detected for this analysis.
            <div className="text-xs text-slate-600 mt-2">
              Tip: add more expense transactions per category to enable robust detection.
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-right text-xs text-slate-400 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase tracking-wider">Method</th>
                  <th className="px-6 py-3 text-right text-xs text-slate-400 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3 text-left text-xs text-slate-400 uppercase tracking-wider">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {result.anomalies
                  .slice()
                  .sort((a, b) => (b.amount ?? 0) - (a.amount ?? 0))
                  .map((a) => (
                    <tr key={a.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                        {a.date ? new Date(a.date).toLocaleString() : '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{a.category}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-amber-400">
                        ${Number(a.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-400">
                        {a.method ?? '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-xs text-slate-400">
                        {a.score != null ? a.score.toFixed(2) : '—'}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-300">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                          <div className="break-words">
                            <div className="text-slate-200">{(a as any).summary || a.reason || 'Anomaly detected'}</div>
                            {a.description ? (
                              <div className="text-slate-500 mt-1">{a.description}</div>
                            ) : null}
                            {(a as any).debug ? (
                              <details className="mt-2">
                                <summary className="cursor-pointer text-slate-500 hover:text-slate-400">
                                  Details
                                </summary>
                                <pre className="mt-2 text-[11px] text-slate-500 whitespace-pre-wrap">
                                  {JSON.stringify((a as any).debug, null, 2)}
                                </pre>
                              </details>
                            ) : null}
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  );
}
