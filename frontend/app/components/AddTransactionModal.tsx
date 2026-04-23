import { useState } from 'react';
import { useApp } from '../context/AppContext';
import { X, ArrowDown, ArrowUp, CalendarDays } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Calendar } from './ui/calendar';

interface AddTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AddTransactionModal({ isOpen, onClose }: AddTransactionModalProps) {
  const { addTransaction } = useApp();
  const [calendarOpen, setCalendarOpen] = useState(false);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const toLocalDateString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const parseLocalDate = (value: string) => {
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, (month || 1) - 1, day || 1);
  };

  const prettyDate = (value: string) => {
    const parsed = parseLocalDate(value);
    return new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(parsed);
  };

  const [formData, setFormData] = useState({
    date: toLocalDateString(new Date()),
    category: '',
    amount: '',
    type: 'Expense' as 'Income' | 'Expense',
    description: '',
  });

  const expenseCategories = [
    'Groceries',
    'Transport',
    'Entertainment',
    'Healthcare',
    'Utilities',
    'Dining',
    'Shopping',
    'Rent',
    'Insurance',
    'Education',
    'Gifts',
    'Taxes',
    'Home Maintenance',
    'Personal Care',
    'Subscriptions',
    'Travel',
    'Charity',
    'Other',
  ];

  const incomeCategories = [
    'Salary',
    'Freelance',
    'Investment',
    'Business',
    'Rental Income',
    'Dividends',
    'Pension',
    'Royalties',
    'Side Hustle',
    'Other',
  ];

  const categories =
    formData.type === 'Income' ? incomeCategories : expenseCategories;

  const handleTypeChange = (type: 'Income' | 'Expense') => {
    setFormData({ ...formData, type, category: '' });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    addTransaction({
      date: formData.date,
      category: formData.category,
      amount: parseFloat(formData.amount),
      type: formData.type,
      description: formData.description,
    });
    setFormData({
      date: toLocalDateString(new Date()),
      category: '',
      amount: '',
      type: 'Expense',
      description: '',
    });
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md shadow-2xl"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl">Add Transaction</h2>
                <button
                  onClick={onClose}
                  className="w-8 h-8 flex items-center justify-center hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Date
                  </label>
                  <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
                    <PopoverTrigger asChild>
                      <button
                        type="button"
                        className="group flex h-11 w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-800/70 px-4 text-left text-slate-100 transition-all hover:border-slate-600 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                      >
                        <span className="text-sm">{prettyDate(formData.date)}</span>
                        <CalendarDays className="h-4 w-4 text-slate-400 transition-colors group-hover:text-indigo-300" />
                      </button>
                    </PopoverTrigger>
                    <PopoverContent
                      align="start"
                      side="bottom"
                      sideOffset={10}
                      className="w-auto rounded-lg border border-slate-700 bg-slate-900 p-0 shadow-2xl"
                    >
                      <Calendar
                        mode="single"
                        selected={parseLocalDate(formData.date)}
                        disabled={(date) => {
                          const check = new Date(date);
                          check.setHours(0, 0, 0, 0);
                          return check > today;
                        }}
                        onSelect={(value: Date | undefined) => {
                          if (!value) return;
                          const selected = new Date(value);
                          selected.setHours(0, 0, 0, 0);
                          if (selected > today) return;
                          setFormData((prev) => ({ ...prev, date: toLocalDateString(value) }));
                          setCalendarOpen(false);
                        }}
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Type
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => handleTypeChange('Expense')}
                      className={`flex-1 py-2 px-3 rounded-full transition-all text-sm font-medium flex items-center justify-center gap-2 ring-offset-2 focus:outline-none focus:ring-2 ${formData.type === 'Expense'
                        ? 'bg-gradient-to-r from-red-600 to-red-500 text-white shadow-sm'
                        : 'bg-transparent text-slate-300 border border-slate-700/40 hover:bg-slate-800/40'
                        }`}
                    >
                      <ArrowDown className="w-4 h-4" />
                      <span>Expense</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleTypeChange('Income')}
                      className={`flex-1 py-2 px-3 rounded-full transition-all text-sm font-medium flex items-center justify-center gap-2 ring-offset-2 focus:outline-none focus:ring-2 ${formData.type === 'Income'
                        ? 'bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-sm'
                        : 'bg-transparent text-slate-300 border border-slate-700/40 hover:bg-slate-800/40'
                        }`}
                    >
                      <ArrowUp className="w-4 h-4" />
                      <span>Income</span>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Category
                  </label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent side="bottom" align="start" sideOffset={8} collisionPadding={12}>
                      {categories.map((cat) => (
                        <SelectItem key={cat} value={cat}>
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Amount
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                      $
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.amount}
                      onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                      className="w-full pl-8 pr-4 py-2.5 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-slate-300 mb-2">
                    Description
                  </label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all"
                    placeholder="Enter description"
                    required
                  />
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-all border border-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all"
                  >
                    Add Transaction
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
