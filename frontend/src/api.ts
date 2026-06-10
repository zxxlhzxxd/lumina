// API client. Resolves the backend base URL from the Electron bridge (the
// backend binds to a random local port), with a fallback for plain-browser dev.
// The UI depends only on these functions, never on backend internals.
import type {
  Book,
  ChapterInfo,
  Project,
  SlideModel,
  TemplateSummary,
  ValidationIssue,
} from "./types";

declare global {
  interface Window {
    lumina?: {
      getBackendInfo: () => Promise<{ port: number; baseUrl: string }>;
      savePptxDialog: (defaultName: string) => Promise<string | null>;
    };
  }
}

const FALLBACK_BASE_URL = "http://127.0.0.1:8799/api/v1";

let baseUrlPromise: Promise<string> | null = null;

function resolveBaseUrl(): Promise<string> {
  if (!baseUrlPromise) {
    baseUrlPromise = (async () => {
      if (window.lumina?.getBackendInfo) {
        try {
          const info = await window.lumina.getBackendInfo();
          return info.baseUrl;
        } catch {
          return FALLBACK_BASE_URL;
        }
      }
      return FALLBACK_BASE_URL;
    })();
  }
  return baseUrlPromise;
}

interface Envelope<T> {
  data: T | null;
  error: { code: string; message: string; details?: unknown } | null;
}

export class ApiError extends Error {
  code: string;
  details?: unknown;
  constructor(code: string, message: string, details?: unknown) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const base = await resolveBaseUrl();
  const res = await fetch(`${base}${path}`, {
    method,
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let json: Envelope<T>;
  try {
    json = (await res.json()) as Envelope<T>;
  } catch {
    throw new ApiError("INTERNAL_ERROR", `请求失败 (HTTP ${res.status})`);
  }
  if (json.error) {
    throw new ApiError(json.error.code, json.error.message, json.error.details);
  }
  return json.data as T;
}

export const api = {
  waitForBackend: async (timeoutMs = 30000): Promise<void> => {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        await request<{ status: string }>("GET", "/health");
        return;
      } catch {
        await new Promise((r) => setTimeout(r, 400));
      }
    }
    throw new ApiError("INTERNAL_ERROR", "无法连接后端服务");
  },

  getVersion: () => request<any>("GET", "/version"),

  listTemplates: () => request<TemplateSummary[]>("GET", "/service-templates"),

  createProject: (templateId: string | null, name?: string) =>
    request<Project>("POST", "/projects", {
      template_id: templateId,
      name,
    }),

  saveProject: (project: Project) =>
    request<Project>("PUT", `/projects/${project.id}`, project),

  saveToDisk: (projectId: string) =>
    request<{ path: string }>("POST", `/projects/${projectId}/save`),

  previewProject: (project: Project) =>
    request<{ slides: SlideModel[]; count: number }>(
      "POST",
      "/projects/preview",
      project
    ),

  validateProject: (project: Project) =>
    request<{ issues: ValidationIssue[] }>("POST", "/projects/validate", project),

  exportProject: (project: Project, path?: string | null) =>
    request<{ path: string; issues: ValidationIssue[] }>(
      "POST",
      "/projects/export",
      { project, path: path ?? null }
    ),

  parseRef: (ref: string) =>
    request<{ reference: { display: string; book_name: string } }>(
      "POST",
      "/bible/parse-ref",
      { ref }
    ),

  listBooks: () => request<Book[]>("GET", "/bible/books"),

  listChapters: (bookId: number) =>
    request<ChapterInfo[]>("GET", `/bible/books/${bookId}/chapters`),
};

export async function pickSavePath(defaultName: string): Promise<string | null> {
  if (window.lumina?.savePptxDialog) {
    return window.lumina.savePptxDialog(defaultName);
  }
  return null; // browser dev: backend chooses default path
}
