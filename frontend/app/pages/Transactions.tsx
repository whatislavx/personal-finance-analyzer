import { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Plus, Calendar, TrendingUp, TrendingDown, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';
import { AddTransactionModal } from '../components/AddTransactionModal';

export function Transactions() {
    const { transactions, deleteTransaction } = useApp();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [deletingTransactionId, setDeletingTransactionId] = useState<string | null>(null);
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


    const totalIncome = transactions
        .filter((t) => t.type === 'Income')
        .reduce((sum, t) => sum + t.amount, 0);

    const totalExpenses = transactions
        .filter((t) => t.type === 'Expense')
        .reduce((sum, t) => sum + t.amount, 0);

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 className="text-3xl mb-2">Transactions</h1>
                    <p className="text-slate-400">A single place for all transaction records and editing.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-5 py-2.5 text-white transition-all hover:bg-slate-700"
                >
                    <Plus className="h-5 w-5" />
                    Add Transaction
                </button>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl border border-slate-800 bg-slate-900 p-6"
                >
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-emerald-600/20">
                            <TrendingUp className="h-5 w-5 text-emerald-400" />
                        </div>
                        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">All time</span>
                    </div>
                    <div className="text-2xl text-emerald-400">${totalIncome.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    <div className="mt-1 text-sm text-slate-400">Total Income</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl border border-slate-800 bg-slate-900 p-6"
                >
                    <div className="mb-4 flex items-center justify-between">
                        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-red-600/20">
                            <TrendingDown className="h-5 w-5 text-red-400" />
                        </div>
                        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">All time</span>
                    </div>
                    <div className="text-2xl text-red-400">${totalExpenses.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    <div className="mt-1 text-sm text-slate-400">Total Expenses</div>
                </motion.div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
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