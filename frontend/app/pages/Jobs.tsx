import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router';
import { Activity, Clock, CheckCircle2, AlertCircle, ChevronRight, Play, Zap, Trash2 } from 'lucide-react';
import { motion } from 'motion/react';
import { useEffect, useMemo, useRef, useState } from 'react';

const statusConfig = {
  PENDING: {
    color: 'text-slate-400',
    bg: 'bg-slate-900/30 border-slate-700/30',
    icon: Clock,
    label: 'Pending',
    stepColor: 'border-slate-500/70 bg-slate-500/15 text-slate-200'
  },
  STARTED: {
    color: 'text-blue-400',
    bg: 'bg-blue-900/30 border-blue-700/30',
    icon: Activity,
    label: 'Processing',
    stepColor: 'border-blue-500/70 bg-blue-500/15 text-blue-200'
  },
  PROCESSING: {
    color: 'text-cyan-400',
    bg: 'bg-cyan-900/30 border-cyan-700/30',
    icon: Activity,
    label: 'Processing',
    stepColor: 'border-cyan-500/70 bg-cyan-500/15 text-cyan-200'
  },
  COMPLETED: {
    color: 'text-emerald-400',
    bg: 'bg-emerald-900/30 border-emerald-700/30',
    icon: CheckCircle2,
    label: 'Completed',
    stepColor: 'border-emerald-500/70 bg-emerald-500/15 text-emerald-200'
  },
  ERROR: {
    color: 'text-red-400',
    bg: 'bg-red-900/30 border-red-700/30',
    icon: AlertCircle,
    label: 'Error',
    stepColor: 'border-red-500/70 bg-red-500/15 text-red-200'
  }
};

const priorityColors = {
  High: 'text-red-400 bg-red-900/30 border-red-700/30',
  Medium: 'text-yellow-400 bg-yellow-900/30 border-yellow-700/30',
  Low: 'text-slate-400 bg-slate-900/30 border-slate-700/30'
};

type AnalysisStatus = 'PENDING' | 'STARTED' | 'PROCESSING' | 'COMPLETED' | 'ERROR';

const statusFlow: AnalysisStatus[] = ['PENDING', 'STARTED', 'PROCESSING', 'COMPLETED'];
const progressByStatus: Record<AnalysisStatus, number> = {
  PENDING: 5,
  STARTED: 30,
  PROCESSING: 70,
  COMPLETED: 100,
  ERROR: 100,
};
const stageDurationMs: Record<AnalysisStatus, number> = {
  PENDING: 500,
  STARTED: 1200,
  PROCESSING: 1800,
  COMPLETED: 900,
  ERROR: 800,
};

interface DisplayAnalysisState {
  status: AnalysisStatus;
  progress: number;
}

export function Jobs() {
  const { analyses, analysisEvents, createAnalysis, deleteAnalysis } = useApp();
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const [deletingAnalysisId, setDeletingAnalysisId] = useState<string | null>(null);
  const [displayState, setDisplayState] = useState<Record<string, DisplayAnalysisState>>({});

  const displayStateRef = useRef<Record<string, DisplayAnalysisState>>({});
  const timeoutRefs = useRef<Record<string, number[]>>({});
  const intervalRefs = useRef<Record<string, number | null>>({});
  const animatedTargetRef = useRef<Record<string, AnalysisStatus | null>>({});

  useEffect(() => {
    displayStateRef.current = displayState;
  }, [displayState]);

  const clearAnimation = (analysisId: string) => {
    const timeouts = timeoutRefs.current[analysisId] || [];
    for (const timeoutId of timeouts) {
      window.clearTimeout(timeoutId);
    }
    timeoutRefs.current[analysisId] = [];

    const intervalId = intervalRefs.current[analysisId];
    if (intervalId != null) {
      window.clearInterval(intervalId);
      intervalRefs.current[analysisId] = null;
    }
  };

  const animateProgress = (analysisId: string, target: number, durationMs: number) => {
    const existingIntervalId = intervalRefs.current[analysisId];
    if (existingIntervalId != null) {
      window.clearInterval(existingIntervalId);
    }

    const start = performance.now();
    const startProgress = displayStateRef.current[analysisId]?.progress ?? 0;
    const delta = target - startProgress;

    if (Math.abs(delta) < 0.5 || durationMs <= 0) {
      setDisplayState((prev) => ({
        ...prev,
        [analysisId]: {
          ...(prev[analysisId] ?? { status: 'PENDING', progress: 0 }),
          progress: target,
        },
      }));
      intervalRefs.current[analysisId] = null;
      return;
    }

    const intervalId = window.setInterval(() => {
      const elapsed = performance.now() - start;
      const t = Math.min(elapsed / durationMs, 1);
      const nextProgress = startProgress + delta * t;

      setDisplayState((prev) => ({
        ...prev,
        [analysisId]: {
          ...(prev[analysisId] ?? { status: 'PENDING', progress: 0 }),
          progress: Math.max(0, Math.min(100, nextProgress)),
        },
      }));

      if (t >= 1) {
        window.clearInterval(intervalId);
        intervalRefs.current[analysisId] = null;
      }
    }, 50);

    intervalRefs.current[analysisId] = intervalId;
  };

  const transitionStatus = (analysisId: string, from: AnalysisStatus, to: AnalysisStatus) => {
    clearAnimation(analysisId);
    animatedTargetRef.current[analysisId] = to;

    if (to === 'ERROR') {
      setDisplayState((prev) => ({
        ...prev,
        [analysisId]: {
          ...(prev[analysisId] ?? { status: 'PENDING', progress: 0 }),
          status: 'ERROR',
        },
      }));
      animateProgress(analysisId, progressByStatus.ERROR, stageDurationMs.ERROR);
      return;
    }

    const fromIndex = statusFlow.indexOf(from);
    const toIndex = statusFlow.indexOf(to);

    if (fromIndex < 0 || toIndex < 0 || toIndex <= fromIndex) {
      setDisplayState((prev) => ({
        ...prev,
        [analysisId]: {
          ...(prev[analysisId] ?? { status: 'PENDING', progress: 0 }),
          status: to,
        },
      }));
      animateProgress(analysisId, progressByStatus[to], 450);
      return;
    }

    let delay = 0;
    const nextStatuses = statusFlow.slice(fromIndex + 1, toIndex + 1);

    nextStatuses.forEach((nextStatus, idx) => {
      const isLast = idx === nextStatuses.length - 1;
      const duration = stageDurationMs[nextStatus];
      const timeoutId = window.setTimeout(() => {
        setDisplayState((prev) => ({
          ...prev,
          [analysisId]: {
            ...(prev[analysisId] ?? { status: 'PENDING', progress: 0 }),
            status: nextStatus,
          },
        }));
        animateProgress(analysisId, progressByStatus[nextStatus], duration);
        if (isLast) {
          animatedTargetRef.current[analysisId] = null;
        }
      }, delay);

      timeoutRefs.current[analysisId] = [...(timeoutRefs.current[analysisId] || []), timeoutId];
      delay += duration + 250;
    });
  };

  useEffect(() => {
    const currentIds = new Set(analyses.map((analysis) => analysis.id));

    Object.keys(displayStateRef.current).forEach((analysisId) => {
      if (!currentIds.has(analysisId)) {
        clearAnimation(analysisId);
        animatedTargetRef.current[analysisId] = null;
        setDisplayState((prev) => {
          if (!prev[analysisId]) return prev;
          const next = { ...prev };
          delete next[analysisId];
          return next;
        });
      }
    });

    for (const analysis of analyses) {
      const targetStatus = (String(analysis.status || 'PENDING').toUpperCase() as AnalysisStatus);
      const currentDisplay = displayStateRef.current[analysis.id];

      if (!currentDisplay) {
        const ageMs = Date.now() - new Date(analysis.createdAt).getTime();
        const shouldSimulateFreshFastCompletion = targetStatus === 'COMPLETED' && ageMs < 120000;

        if (shouldSimulateFreshFastCompletion) {
          setDisplayState((prev) => ({
            ...prev,
            [analysis.id]: { status: 'PENDING', progress: progressByStatus.PENDING },
          }));
          transitionStatus(analysis.id, 'PENDING', 'COMPLETED');
        } else {
          setDisplayState((prev) => ({
            ...prev,
            [analysis.id]: { status: targetStatus, progress: progressByStatus[targetStatus] },
          }));
        }
        continue;
      }

      if (currentDisplay.status !== targetStatus) {
        const alreadyAnimatingTo = animatedTargetRef.current[analysis.id];
        if (alreadyAnimatingTo !== targetStatus) {
          transitionStatus(analysis.id, currentDisplay.status, targetStatus);
        }
      } else {
        const targetProgress = progressByStatus[targetStatus];
        if (Math.abs(currentDisplay.progress - targetProgress) > 0.5) {
          animateProgress(analysis.id, targetProgress, 500);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analyses]);

  useEffect(() => {
    return () => {
      Object.keys(timeoutRefs.current).forEach(clearAnimation);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const eventsByAnalysisId = useMemo(() => {
    const grouped: Record<string, string[]> = {};
    for (const event of analysisEvents) {
      const type = String(event.type || '').toUpperCase();
      if (!grouped[event.analysisId]) grouped[event.analysisId] = [];
      grouped[event.analysisId].push(type);
    }
    return grouped;
  }, [analysisEvents]);

  const statusSteps = ['PENDING', 'STARTED', 'PROCESSING', 'COMPLETED'] as const;

  const getStepState = (analysisId: string, status: string) => {
    const current = String(status || 'PENDING').toUpperCase();
    const eventTypes = eventsByAnalysisId[analysisId] || [];
    const reached = new Set<string>(['PENDING']);

    for (const type of eventTypes) {
      if (type === 'STARTED') reached.add('STARTED');
      if (type === 'PROCESSING' || type === 'INFO' || type === 'RESULT') reached.add('PROCESSING');
      if (type === 'COMPLETED') reached.add('COMPLETED');
      if (type === 'FAILED' || type === 'ERROR') reached.add('ERROR');
    }

    if (statusSteps.includes(current as any)) {
      const currentIndex = statusSteps.indexOf(current as any);
      statusSteps.forEach((step, index) => {
        if (index <= currentIndex) reached.add(step);
      });
    }

    const hasError = current === 'ERROR' || reached.has('ERROR');
    return { reached, hasError };
  };

  const handleAnalysisClick = (analysisId: string, status: string) => {
    if (status === 'COMPLETED') {
      navigate(`/app/results/${analysisId}`);
    }
  };

  const handleCreateAnalysis = async () => {
    setCreating(true);
    try {
      await createAnalysis();
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteAnalysis = async (analysisId: string) => {
    if (deletingAnalysisId) return;
    const accepted = window.confirm('Delete this analysis and its report? This action cannot be undone.');
    if (!accepted) return;
    try {
      setDeletingAnalysisId(analysisId);
      await deleteAnalysis(analysisId);
    } finally {
      setDeletingAnalysisId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl mb-2">Analysis Center</h1>
          <p className="text-slate-400">Real-time tracking of running analyses and event updates</p>
        </div>
        <motion.button
          onClick={handleCreateAnalysis}
          disabled={creating}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white rounded-lg transition-all shadow-lg shadow-indigo-600/20"
        >
          <Play className="w-5 h-5" />
          {creating ? 'Starting…' : 'Start New Analysis'}
        </motion.button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Analysis List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl">Active Analyses</h2>
            <span className="text-sm text-slate-500">{analyses.length} total</span>
          </div>

          {analyses.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="mb-2 text-slate-300">No analyses yet</h3>
              <p className="text-slate-500 mb-6">Start your first analysis to see the live pipeline</p>
              <button
                onClick={handleCreateAnalysis}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all"
              >
                Create First Analysis
              </button>
            </div>
          ) : (
            analyses.map((analysis, index) => {
              const visible = displayState[analysis.id] ?? {
                status: analysis.status,
                progress: analysis.progress,
              };
              const statusInfo = (statusConfig as any)[visible.status] ?? statusConfig.PENDING;
              const StatusIcon = statusInfo.icon;
              const stepState = getStepState(analysis.id, visible.status);

              return (
                <motion.div
                  key={analysis.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * index }}
                  onClick={() => handleAnalysisClick(analysis.id, visible.status)}
                  className={`bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all ${visible.status === 'COMPLETED' ? 'cursor-pointer' : ''
                    }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg">{analysis.name}</h3>
                        {visible.status === 'COMPLETED' && (
                          <ChevronRight className="w-5 h-5 text-slate-500" />
                        )}
                      </div>
                      <p className="text-sm text-slate-400">{analysis.type}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs border ${priorityColors[analysis.priority]}`}>
                        {analysis.priority}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleDeleteAnalysis(analysis.id);
                        }}
                        disabled={deletingAnalysisId === analysis.id}
                        className="inline-flex items-center gap-1 rounded-md border border-red-700/40 bg-red-900/20 px-2.5 py-1 text-xs text-red-300 transition hover:bg-red-900/35 disabled:opacity-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        {deletingAnalysisId === analysis.id ? 'Deleting' : 'Delete'}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {/* Status Badge */}
                    <div className="flex items-center justify-between">
                      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border ${statusInfo.bg} ${statusInfo.color}`}>
                        <StatusIcon className={`w-4 h-4 ${visible.status === 'PROCESSING' ? 'animate-spin' : ''}`} />
                        {statusInfo.label}
                      </span>
                      <span className="text-sm text-slate-500">
                        {new Date(analysis.createdAt).toLocaleTimeString()}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Progress</span>
                        <span className="text-slate-300">{Math.round(visible.progress)}%</span>
                      </div>
                      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${visible.progress}%` }}
                          transition={{ duration: 0.5, ease: 'easeOut' }}
                          className={`h-full rounded-full ${visible.status === 'COMPLETED'
                            ? 'bg-emerald-500'
                            : visible.status === 'PROCESSING'
                              ? 'bg-blue-500'
                              : visible.status === 'ERROR'
                                ? 'bg-red-500'
                                : 'bg-slate-600'
                            }`}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-2 pt-1">
                      {statusSteps.map((step) => {
                        const isCurrent = stepState.reached.has(step) && !stepState.reached.has(statusSteps[statusSteps.indexOf(step) + 1]);
                        const stepConfig = (statusConfig as any)[step] ?? statusConfig.PENDING;
                        return (
                          <div
                            key={step}
                            className={`rounded-md border px-2 py-1 text-center text-[10px] uppercase tracking-[0.08em] transition-all ${isCurrent
                              ? stepConfig.stepColor
                              : 'border-slate-700/60 bg-slate-800/30 text-slate-500'
                              }`}
                          >
                            {step}
                          </div>
                        );
                      })}
                    </div>
                    {stepState.hasError && (
                      <div className="rounded-md border border-red-700/50 bg-red-900/20 px-2 py-1 text-xs text-red-300">
                        The analysis ended with an error. Check Live Activity Log for details.
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })
          )}
        </div>

        {/* Live Event Log */}
        <div className="lg:col-span-1">
          <h2 className="text-xl mb-4">Live Activity Log</h2>
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 h-[600px] overflow-y-auto text-xs" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {analysisEvents.length === 0 ? (
              <div className="text-slate-600 text-center py-8">
                No events yet...<br />
                <span className="text-[10px]">Events will appear here in real-time</span>
              </div>
            ) : (
              <div className="space-y-2">
                {analysisEvents.map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.02 * index }}
                    className="flex gap-2 text-slate-400 hover:text-slate-300 transition-colors p-2 hover:bg-slate-900/50 rounded"
                  >
                    <span className="text-slate-600 flex-shrink-0">
                      [{new Date(event.timestamp).toLocaleTimeString()}]
                    </span>
                    <span className="text-emerald-400 flex-shrink-0">&gt;</span>
                    <span className="break-all">{event.message}</span>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}