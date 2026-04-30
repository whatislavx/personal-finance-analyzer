export function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-slate-800/80 bg-slate-950">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(79,70,229,0.15),transparent_35%),radial-gradient(circle_at_top_right,rgba(16,185,129,0.12),transparent_28%)]" />
      <div className="relative w-full px-4 py-12 sm:px-6 lg:px-8 xl:px-10 2xl:px-14">
        <div className="grid gap-10 md:grid-cols-[1.3fr_1fr_1fr]">
          <div>
            <div className="text-white text-2xl tracking-tight">FinFlow</div>
            <p className="mt-3 max-w-md text-sm leading-6 text-slate-400">
              A polished financial analysis workspace for monitoring transactions, spotting anomalies, and turning raw numbers into clear decisions.
            </p>
          </div>

          <div>
            <div className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Contact</div>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <a className="block transition-colors hover:text-white" href="mailto:support@finflow.local">
                support@finflow.local
              </a>
              <a className="block transition-colors hover:text-white" href="https://t.me/finflow" target="_blank" rel="noreferrer">
                Telegram
              </a>
              <a className="block transition-colors hover:text-white" href="https://github.com/" target="_blank" rel="noreferrer">
                GitHub
              </a>
            </div>
          </div>

          <div>
            <div className="text-sm font-medium uppercase tracking-[0.18em] text-slate-500">Product</div>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <p>Live analysis pipeline</p>
              <p>Profile management</p>
              <p>Smart spending insights</p>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-slate-800/80 pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <div>© {new Date().getFullYear()} FinFlow. All rights reserved.</div>
          <div>Built for clear financial analysis and reliable automation.</div>
        </div>
      </div>
    </footer>
  );
}

