import { createContext, useContext, useEffect, useMemo, useRef, useState, ReactNode } from 'react';
import { api, tokenStorage, type FinancialData, type Job as ApiJob, type JobResult as ApiJobResult } from '../lib/api';
import { connectJobEventsWS } from '../lib/ws';

export interface Transaction {
  id: string;
  date: string;
  category: string;
  amount: number;
  type: 'Income' | 'Expense';
  description: string;
}

export interface AnalysisItem {
  id: string;
  name: string;
  type: string;
  priority: 'High' | 'Medium' | 'Low';
  status: 'PENDING' | 'STARTED' | 'PROCESSING' | 'COMPLETED' | 'ERROR';
  progress: number;
  createdAt: string;
}

export interface AnalysisEvent {
  id: string;
  analysisId: string;
  type: string;
  message: string;
  timestamp: string;
}

export interface AnalysisResult {
  analysisId: string;
  totalExpenses: number;
  totalIncome: number;
  byCategory: Record<string, number>;
  anomalies: Array<{
    id: string;
    date: string | null;
    category: string;
    amount: number;
    description: string | null;
    reason: string;
    summary?: string;
    debug?: any;
    method?: string;
    score?: number;
    threshold?: number;
  }>;
  createdAt: string;
}

interface AppContextType {
  user: { email: string; username: string } | null;
  isAuthenticated: boolean;
  authLoading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  signup: (data: { username: string; email: string; password: string }) => Promise<void>;
  logout: () => void;

  transactions: Transaction[];
  addTransaction: (transaction: Omit<Transaction, 'id'>) => Promise<void>;

  analyses: AnalysisItem[];
  createAnalysis: () => Promise<string>;

  analysisEvents: AnalysisEvent[];
  results: AnalysisResult[];
  getResultByAnalysisId: (analysisId: string) => AnalysisResult | undefined;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const USER_STORAGE_KEY = 'finflow_user';

function readStoredUser(): { email: string; username: string } | null {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { email?: unknown; username?: unknown };
    if (typeof parsed?.email === 'string' && typeof parsed?.username === 'string') {
      return { email: parsed.email, username: parsed.username };
    }
    return null;
  } catch {
    // Corrupted/stale localStorage value should not crash app boot.
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}

function priorityToInt(p: AnalysisItem['priority']): number {
  if (p === 'High') return 2;
  if (p === 'Medium') return 1;
  return 0;
}

function intToPriority(n: number): AnalysisItem['priority'] {
  if (n >= 2) return 'High';
  if (n === 1) return 'Medium';
  return 'Low';
}

function analysisToUI(job: ApiJob): AnalysisItem {
  const status = String(job.status ?? 'PENDING').toUpperCase() as AnalysisItem['status'];
  const progressByStatus: Record<AnalysisItem['status'], number> = {
    PENDING: 5,
    STARTED: 30,
    PROCESSING: 70,
    COMPLETED: 100,
    ERROR: 100,
  };

  return {
    id: job.id,
    name: job.name,
    type: job.type,
    priority: intToPriority(job.priority ?? 0),
    status,
    progress: progressByStatus[status] ?? 5,
    createdAt: job.created_at ?? new Date().toISOString(),
  };
}

function financialToTransaction(r: FinancialData): Transaction {
  return {
    id: r.id,
    date: (r.date ?? r.created_at ?? new Date().toISOString()).slice(0, 10),
    category: r.category,
    amount: Number(r.amount),
    type: r.type === 'INCOME' ? 'Income' : 'Expense',
    description: r.description ?? '',
  };
}

function resultToUI(res: ApiJobResult): AnalysisResult {
  const byCategoryRaw = res.result_data?.by_category ?? {};
  const byCategory: Record<string, number> = Object.fromEntries(
    Object.entries(byCategoryRaw).map(([k, v]) => [k, Number(v)])
  );

  const anomaliesRaw = (res.result_data?.anomalies ?? []) as any[];
  const anomalies = anomaliesRaw
    .filter(Boolean)
    .map((a) => ({
      id: String(a.id ?? ''),
      date: a.date ? String(a.date) : null,
      category: String(a.category ?? 'unknown'),
      amount: Number(a.amount ?? 0),
      description: a.description != null ? String(a.description) : null,
      reason: String(a.reason ?? ''),
      summary: a.summary != null ? String(a.summary) : undefined,
      debug: a.debug ?? undefined,
      method: a.method != null ? String(a.method) : undefined,
      score: a.score != null ? Number(a.score) : undefined,
      threshold: a.threshold != null ? Number(a.threshold) : undefined,
    }));

  return {
    analysisId: res.job_id,
    totalExpenses: Number(res.result_data?.total_expense ?? 0),
    totalIncome: Number(res.result_data?.total_income ?? 0),
    byCategory,
    anomalies,
    createdAt: res.created_at,
  };
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ email: string; username: string } | null>(() => readStoredUser());
  const [authLoading, setAuthLoading] = useState(true);

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [analysisEvents, setAnalysisEvents] = useState<AnalysisEvent[]>([]);
  const [results, setResults] = useState<AnalysisResult[]>([]);

  const wsRef = useRef<{ close(): void } | null>(null);
  const activeAnalysisIdRef = useRef<string | null>(null);
  const isAuthenticated = !!tokenStorage.getToken();

  const persistUser = (u: { email: string; username: string } | null) => {
    setUser(u);
    if (!u) localStorage.removeItem(USER_STORAGE_KEY);
    else localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(u));
  };

  const logout = () => {
    wsRef.current?.close();
    wsRef.current = null;
    activeAnalysisIdRef.current = null;
    tokenStorage.setToken(null);
    persistUser(null);
    setTransactions([]);
    setAnalyses([]);
    setAnalysisEvents([]);
    setResults([]);
  };

  const login = async (usernameOrEmail: string, password: string) => {
    const username = usernameOrEmail.includes('@') ? usernameOrEmail.split('@')[0] : usernameOrEmail;
    const token = await api.login(username, password);
    tokenStorage.setToken(token.access_token);
    // We don't have /users/me, so keep a lightweight local user object for UI.
    persistUser({ email: usernameOrEmail.includes('@') ? usernameOrEmail : `${username}@local`, username });
    await refreshAll();
  };

  const signup = async (data: { username: string; email: string; password: string }) => {
    await api.signup(data);
    await login(data.username, data.password);
  };

  const refreshAll = async () => {
    const [fd, jb, jr, je] = await Promise.all([
      api.listFinancialData(),
      api.listJobs(),
      api.listJobResults(),
      api.listJobEvents(),
    ]);
    setTransactions(fd.map(financialToTransaction));
    setAnalyses(jb.map(analysisToUI));
    setResults(jr.map(resultToUI));

    // Map events to UI log
    setAnalysisEvents(
      je
        .slice()
        .reverse()
        .map((e) => ({
          id: e.id,
          analysisId: e.job_id,
          type: e.type,
          message: e.message ?? e.type,
          timestamp: e.created_at,
        }))
    );
  };

  // Initial load on refresh
  useEffect(() => {
    (async () => {
      try {
        if (isAuthenticated) {
          await refreshAll();
        }
      } finally {
        setAuthLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // REST fallback polling for jobs/events/results
  useEffect(() => {
    if (!isAuthenticated) return;
    const id = window.setInterval(() => {
      refreshAll().catch(() => void 0);
    }, 5000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const addTransaction = async (transaction: Omit<Transaction, 'id'>) => {
    const payload = {
      date: transaction.date,
      category: transaction.category,
      amount: transaction.amount,
      type: transaction.type === 'Income' ? ('INCOME' as const) : ('EXPENSE' as const),
      description: transaction.description,
    };
    try {
      await api.createFinancialData(payload);
      await refreshAll();
    } catch (e) {
      // keep UI responsive; surface error in console for now
      console.error('Failed to add transaction', e);
      throw e;
    }
  };

  const createAnalysis = async (): Promise<string> => {
    const nowLabel = new Date().toLocaleTimeString();
    const created = await api.createJob({
      name: `Financial Analysis ${nowLabel}`,
      type: 'expense_analysis',
      priority: priorityToInt('High'),
      description: 'Expense analysis',
    });

    // Set active analysis for WS subscription
    activeAnalysisIdRef.current = created.id;
    wsRef.current?.close();
    wsRef.current = null;

    const token = tokenStorage.getToken();
    if (token) {
      wsRef.current = connectJobEventsWS({
        token,
        jobId: created.id,
        onEvents: (events) => {
          setAnalysisEvents((prev: AnalysisEvent[]) => {
            const mapped: AnalysisEvent[] = events.map((e) => ({
              id: e.id,
              analysisId: e.job_id,
              type: e.type,
              message: e.message ?? e.type,
              timestamp: e.created_at,
            }));
            // newest first
            return [...mapped.reverse(), ...prev].slice(0, 200);
          });
          // Refresh analysis status/results on events
          refreshAll().catch(() => void 0);
        },
      });
    }

    await refreshAll();
    return created.id;
  };

  const getResultByAnalysisId = (analysisId: string) => results.find((r: AnalysisResult) => r.analysisId === analysisId);

  const value = useMemo<AppContextType>(() => ({
    user,
    isAuthenticated,
    authLoading,
    login,
    signup,
    logout,
    transactions,
    addTransaction,
    analyses,
    createAnalysis,
    analysisEvents,
    results,
    getResultByAnalysisId,
  }), [user, isAuthenticated, authLoading, transactions, analyses, analysisEvents, results]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
