export type ApiUser = {
  id: string;
  username: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  phone_number?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type FinancialData = {
  id: string;
  user_id: string;
  job_id?: string | null;
  date?: string | null;
  category: string;
  amount: string | number;
  type: 'INCOME' | 'EXPENSE';
  description?: string | null;
  created_at?: string;
};

export type Job = {
  id: string;
  user_id?: string;
  name: string;
  description?: string | null;
  status?: string;
  type: string;
  priority?: number;
  progress?: number;
  created_at?: string;
};

export type JobResult = {
  id: string;
  job_id: string;
  result_type: string;
  result_data: any;
  created_at: string;
};

export type JobEvent = {
  id: string;
  job_id: string;
  type: string;
  message: string | null;
  created_at: string;
};

export class ApiError extends Error {
  status: number;
  requestId?: string;
  details?: unknown;
  rawBody?: string;

  constructor(message: string, init: { status: number; requestId?: string; details?: unknown; rawBody?: string }) {
    super(message);
    this.name = 'ApiError';
    this.status = init.status;
    this.requestId = init.requestId;
    this.details = init.details;
    this.rawBody = init.rawBody;
  }
}

function getApiBase(): string {
  // Vite proxy can rewrite /api to backend.
  return "";
}

function getFilenameFromContentDisposition(header: string | null): string | undefined {
  if (!header) {
    return undefined;
  }

  const utf8Match = header.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const asciiMatch = header.match(/filename="?([^";]+)"?/i);
  return asciiMatch?.[1];
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token");

  const headers = new Headers(init.headers);
  const hasBody = init.body != null;
  const isFormBody = init.body instanceof FormData || init.body instanceof URLSearchParams;
  if (!headers.has("Content-Type") && hasBody && !isFormBody) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers,
  });

  const contentType = res.headers.get('content-type') ?? '';
  const text = await res.text().catch(() => '');

  if (!res.ok) {
    let parsed: any = null;
    if (text && contentType.includes('application/json')) {
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = null;
      }
    }

    const requestId = res.headers.get('x-request-id') ?? parsed?.request_id;
    const details = parsed?.details;
    const message = buildErrorMessage({
      status: res.status,
      text,
      contentType,
      parsed,
    });

    throw new ApiError(message, {
      status: res.status,
      requestId: typeof requestId === 'string' ? requestId : undefined,
      details,
      rawBody: text,
    });
  }

  if (!text) {
    return undefined as T;
  }

  if (!contentType.includes('application/json')) {
    throw new ApiError(
      `The server returned an unexpected ${contentType || 'text'} response instead of JSON. This usually means the backend route is unavailable or a proxy returned an HTML error page.`,
      { status: res.status, rawBody: text },
    );
  }

  return JSON.parse(text) as T;
}

async function apiDownload(path: string, init: RequestInit = {}): Promise<{ blob: Blob; filename?: string; contentType: string }> {
  const token = localStorage.getItem('token');

  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const res = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers,
  });

  const contentType = res.headers.get('content-type') ?? '';

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    let parsed: any = null;

    if (text && contentType.includes('application/json')) {
      try {
        parsed = JSON.parse(text);
      } catch {
        parsed = null;
      }
    }

    const requestId = res.headers.get('x-request-id') ?? parsed?.request_id;
    const details = parsed?.details;
    const message = buildErrorMessage({
      status: res.status,
      text,
      contentType,
      parsed,
    });

    throw new ApiError(message, {
      status: res.status,
      requestId: typeof requestId === 'string' ? requestId : undefined,
      details,
      rawBody: text,
    });
  }

  return {
    blob: await res.blob(),
    filename: getFilenameFromContentDisposition(res.headers.get('content-disposition')),
    contentType,
  };
}

function buildErrorMessage({
  status,
  text,
  contentType,
  parsed,
}: {
  status: number;
  text: string;
  contentType: string;
  parsed: any;
}): string {
  const backendMessage = typeof parsed?.message === 'string' ? parsed.message : '';

  if (status === 401) {
    return backendMessage || 'Authentication failed. Your session is missing, expired, or invalid. Sign in again.';
  }

  if (status === 403) {
    return backendMessage || 'Access denied. You do not have permission to perform this action.';
  }

  if (status === 404) {
    return backendMessage || 'The requested resource was not found.';
  }

  if (status === 409) {
    return backendMessage || 'The request conflicts with an existing record.';
  }

  if (status === 422) {
    return backendMessage || 'Validation failed. One or more fields contain invalid values.';
  }

  if (backendMessage) {
    return backendMessage;
  }

  const preview = text
    ? text.replace(/\s+/g, ' ').slice(0, 300)
    : '';

  if (contentType.includes('text/html') || /<html|<!doctype/i.test(text)) {
    return `The server returned HTML instead of JSON (${status}). This usually means the backend route crashed, the server is unavailable, or a reverse proxy served an error page. Response preview: ${preview || 'n/a'}`;
  }

  return `The request failed with status ${status}. ${preview ? `Server response: ${preview}` : 'No additional error details were returned.'}`;
}

export function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    const parts = [error.message];

    if (error.requestId) {
      parts.push(`Request ID: ${error.requestId}`);
    }

    if (Array.isArray(error.details) && error.details.length > 0) {
      const detailLines = error.details.map((item: any) => {
        const field = Array.isArray(item?.loc) ? item.loc.filter((value: unknown) => value !== 'body').join('.') : 'request';
        const message = item?.msg ? String(item.msg) : 'Invalid value';
        return `- ${field}: ${message}`;
      });
      parts.push('Details:', ...detailLines);
    } else if (error.details && typeof error.details === 'object') {
      parts.push(`Details: ${JSON.stringify(error.details, null, 2)}`);
    }

    if (error.rawBody && typeof error.rawBody === 'string' && error.rawBody.length > 0) {
      parts.push(`Raw response: ${error.rawBody.slice(0, 300)}`);
    }

    return parts.join('\n');
  }

  if (error instanceof Error) {
    return error.message || 'An unexpected error occurred.';
  }

  return 'An unexpected error occurred.';
}

export const tokenStorage = {
  getToken(): string | null {
    return localStorage.getItem('token');
  },
  setToken(t: string | null) {
    if (t) localStorage.setItem('token', t);
    else localStorage.removeItem('token');
  }
};

export const api = {
  // auth
  async login(username: string, password: string) {
    return apiFetch<{ access_token: string; token_type: string }>("/api/token", {
      method: 'POST',
      body: new URLSearchParams({
        username,
        password,
      }),
    });
  },
  async signup({ username, email, password }: { username: string; email: string; password: string }) {
    return apiFetch<ApiUser>("/api/users/", {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  },

  // profile
  getMyProfile: () => apiFetch<ApiUser>("/api/users/profile"),
  updateMyProfile: (payload: Partial<ApiUser> & { password?: string }) =>
    apiFetch<ApiUser>("/api/users/profile", { method: 'PUT', body: JSON.stringify(payload) }),

  // financial
  listFinancialData: () => apiFetch<FinancialData[]>('/api/financial-data'),
  createFinancialData: (payload: Partial<FinancialData>) => apiFetch<FinancialData>('/api/financial-data', { method: 'POST', body: JSON.stringify(payload) }),
  deleteFinancialData: (recordId: string) => apiFetch<void>(`/api/financial-data/${recordId}`, { method: 'DELETE' }),

  // jobs
  listJobs: () => apiFetch<Job[]>("/api/jobs"),
  createJob: (payload: Partial<Job>) => apiFetch<Job>("/api/jobs", { method: 'POST', body: JSON.stringify(payload) }),
  deleteJob: (jobId: string) => apiFetch<void>(`/api/jobs/${jobId}`, { method: 'DELETE' }),

  // job results/events
  listJobResults: () => apiFetch<JobResult[]>('/api/job-results'),
  listJobEvents: () => apiFetch<JobEvent[]>('/api/job-events'),

  // reports
  downloadAnalysisReport: (analysisId: string) => apiDownload(`/api/job-results/jobs/${analysisId}/report`),
};

// backward-compatible named exports
export const { getMyProfile, updateMyProfile } = api;
