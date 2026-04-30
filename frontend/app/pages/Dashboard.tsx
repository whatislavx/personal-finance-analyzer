import { useMemo, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router';
import { Play, TrendingUp, TrendingDown, Plus, Calendar, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';
import { AddTransactionModal } from '../components/AddTransactionModal';

type PeriodKey = 'day' | 'month' | 'year';
const periodOptions: PeriodKey[] = ['day', 'month', 'year'];

export function Dashboard() {
  const { transactions, createAnalysis, deleteTransaction } = useApp();
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deletingTransactionId, setDeletingTransactionId] = useState<string | null>(null);
  const navigate = useNavigate();


  const [period, setPeriod] = useState<PeriodKey>('month');

  // Helper functions for period filtering
  function parseTransactionDate(value: string): Date | null {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  const { totalIncome, totalExpenses } = useMemo(() => {
    const now = new Date();
    const periodStart = period === 'day'
      ? new Date(now.getFullYear(), now.getMonth(), now.getDate())
      : period === 'year'
        ? new Date(now.getFullYear(), 0, 1)
        : new Date(now.getFullYear(), now.getMonth(), 1);

    const filtered = transactions.filter((t) => {
      const date = parseTransactionDate(t.date);
      return date && date >= periodStart && date <= now;
    });
    const income = filtered
      .filter((t) => t.type === 'Income')
      .reduce((sum, t) => sum + t.amount, 0);
    const expenses = filtered
      .filter((t) => t.type === 'Expense')
      .reduce((sum, t) => sum + t.amount, 0);
    return { totalIncome: income, totalExpenses: expenses };
  }, [transactions, period]);

  const handleDeleteTransaction = async (transactionId: string) => {
    if (deletingTransactionId) return;
    const confirmed = window.confirm('Delete this transaction? This action cannot be undone.');
    if (!confirmed) return;
    try {
      setDeletingTransactionId(transactionId);
      await deleteTransaction(transactionId);
    } finally {
      setDeletingTransactionId(null);
    }
  };

  const formatMoney = (value: number) => `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const handleRunAnalysis = async () => {
    setLoadingAnalysis(true);
    try {
      await createAnalysis();
      navigate('/app/analyses');
    } finally {
      setLoadingAnalysis(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="mb-1 text-3xl">Financial Dashboard</h1>
          <p className="text-slate-400">Manage transactions and track your financial activity.</p>
        </div>
        <div className="flex flex-wrap gap-2 sm:gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-white transition-all hover:bg-slate-700 sm:px-5"
          >
            <Plus className="h-5 w-5" />
            Add Transaction
          </button>
          <motion.button
            onClick={handleRunAnalysis}
            disabled={loadingAnalysis}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-white transition-all shadow-lg shadow-indigo-600/20 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60 sm:px-5"
          >
            <Play className="w-5 h-5" />
            {loadingAnalysis ? 'Starting…' : 'Run Full Analysis'}
          </motion.button>
        </div>
      </div>

      {/* Period Selector */}
      <div className="flex flex-wrap gap-2 mb-2">
        {periodOptions.map((option) => (
          <button
            key={option}
            onClick={() => setPeriod(option)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-all ${period === option
              ? 'bg-indigo-600 text-white'
              : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
          >
            {option === 'day' ? 'Daily' : option === 'month' ? 'Monthly' : 'Yearly'}
          </button>
        ))}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-xl border border-slate-800 bg-slate-900 p-5"
        >
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-600/20">
              <TrendingUp className="w-6 h-6 text-emerald-400" />
            </div>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
              {period === 'day' ? 'Today' : period === 'month' ? 'This month' : 'This year'}
            </span>
          </div>
          <div className="mb-1 text-2xl text-emerald-400">
            {formatMoney(totalIncome)}
          </div>
          <div className="text-sm text-slate-400">Total Income</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-xl border border-slate-800 bg-slate-900 p-5"
        >
          <div className="mb-3 flex items-center justify-between">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-red-600/20">
              <TrendingDown className="w-6 h-6 text-red-400" />
            </div>
            <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
              {period === 'day' ? 'Today' : period === 'month' ? 'This month' : 'This year'}
            </span>
          </div>
          <div className="mb-1 text-2xl text-red-400">
            {formatMoney(totalExpenses)}
          </div>
          <div className="text-sm text-slate-400">Total Expenses</div>
        </motion.div>
      </div>

      {/* Transactions Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900"
      >
        <div className="flex items-center justify-between border-b border-slate-800 p-6">
          <div>
            <h2 className="text-xl">Recent Transactions</h2>
            <p className="text-sm text-slate-400 mt-1">Full transaction history with date, category, and type.</p>
          </div>
          <div className="hidden sm:flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/50 px-3 py-2 text-sm text-slate-400">
            <Calendar className="h-4 w-4" />
            {transactions.length} records
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs uppercase tracking-wider text-slate-400">Date</th>
                <th className="px-6 py-3 text-left text-xs uppercase tracking-wider text-slate-400">Category</th>
                <th className="px-6 py-3 text-left text-xs uppercase tracking-wider text-slate-400">Description</th>
                <th className="px-6 py-3 text-left text-xs uppercase tracking-wider text-slate-400">Type</th>
                <th className="px-6 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Amount</th>
                <th className="px-6 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {transactions.map((transaction, index) => (
                <motion.tr
                  key={transaction.id}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.03 * index }}
                  className="transition-colors hover:bg-slate-800/30"
                >
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-slate-300">
                      <Calendar className="h-4 w-4 text-slate-500" />
                      {new Date(transaction.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-white">{transaction.category}</td>
                  <td className="px-6 py-4 text-sm text-slate-400">{transaction.description}</td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs ${transaction.type === 'Income'
                      ? 'border-emerald-700/30 bg-emerald-900/30 text-emerald-400'
                      : 'border-red-700/30 bg-red-900/30 text-red-400'
                      }`}>
                      {transaction.type}
                    </span>
                  </td>
                  <td className={`whitespace-nowrap px-6 py-4 text-right text-sm ${transaction.type === 'Income' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {transaction.type === 'Income' ? '+' : '-'}
                    ${transaction.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <button
                      onClick={() => handleDeleteTransaction(transaction.id)}
                      disabled={deletingTransactionId === transaction.id}
                      className="inline-flex items-center gap-1 rounded-md border border-red-700/40 bg-red-900/20 px-2.5 py-1 text-xs text-red-300 transition hover:bg-red-900/35 disabled:opacity-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {deletingTransactionId === transaction.id ? 'Deleting' : 'Delete'}
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      <AddTransactionModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}
