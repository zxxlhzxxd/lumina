// API client. Resolves the backend base URL from the Electron bridge (the
// backend binds to a random local port), with a fallback for plain-browser dev.
// The UI depends only on these functions, never on backend internals.
import type {
  Book,
  ChapterInfo,
  Hymn,
  HymnSummary,
  LiturgyText,
  LiturgyTextSummary,
  MediaAsset,
  MediaKind,
  Project,
  ProjectSummary,
  SlideModel,
  TemplateSummary,
  ValidationIssue,
} from "./types";

declare global {
  interface Window {
    lumina?: {
      getBackendInfo: () => Promise<{ port: number; baseUrl: string }>;
      savePptxDialog: (defaultName: string) => Promise<string | null>;
      pickMediaDialog: (
        kind: MediaKind
      ) => Promise<string | null>;
      exportTemplateDialog: (defaultName: string) => Promise<string | null>;
      importTemplateDialog: () => Promise<string | null>;
      exportHymnLibraryDialog: (defaultName: string) => Promise<string | null>;
      importHymnLibraryDialog: () => Promise<string | null>;
      exportLiturgyLibraryDialog: (defaultName: string) => Promise<string | null>;
      importLiturgyLibraryDialog: () => Promise<string | null>;
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

  listProjects: () => request<ProjectSummary[]>("GET", "/projects"),

  getProject: (id: string) => request<Project>("GET", `/projects/${id}`),

  createProject: (templateId: string | null, name?: string) =>
    request<Project>("POST", "/projects", {
      template_id: templateId,
      name,
    }),

  deleteProject: (id: string) =>
    request<{ deleted: string }>("DELETE", `/projects/${id}`),

  duplicateProject: (id: string) =>
    request<Project>("POST", `/projects/${id}/duplicate`),

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

  // ---- hymn library ----
  listHymns: (query = "") =>
    request<HymnSummary[]>("GET", `/hymns?query=${encodeURIComponent(query)}`),
  getHymn: (id: string) => request<Hymn>("GET", `/hymns/${id}`),
  createHymn: (hymn: Partial<Hymn>) => request<Hymn>("POST", "/hymns", hymn),
  updateHymn: (id: string, hymn: Hymn) => request<Hymn>("PUT", `/hymns/${id}`, hymn),
  deleteHymn: (id: string) =>
    request<{ deleted: string }>("DELETE", `/hymns/${id}`),
  duplicateHymn: (id: string) => request<Hymn>("POST", `/hymns/${id}/duplicate`),
  exportHymnLibrary: (path: string) =>
    request<{ path: string; count: number }>("POST", "/hymns/export", { path }),
  importHymnLibrary: (path: string) =>
    request<{ imported: number; items: Hymn[] }>("POST", "/hymns/import", { path }),

  // ---- liturgy library ----
  listLiturgy: (query = "") =>
    request<LiturgyTextSummary[]>(
      "GET",
      `/liturgy-texts?query=${encodeURIComponent(query)}`
    ),
  getLiturgy: (id: string) => request<LiturgyText>("GET", `/liturgy-texts/${id}`),
  createLiturgy: (text: Partial<LiturgyText>) =>
    request<LiturgyText>("POST", "/liturgy-texts", text),
  updateLiturgy: (id: string, text: LiturgyText) =>
    request<LiturgyText>("PUT", `/liturgy-texts/${id}`, text),
  deleteLiturgy: (id: string) =>
    request<{ deleted: string }>("DELETE", `/liturgy-texts/${id}`),
  duplicateLiturgy: (id: string) =>
    request<LiturgyText>("POST", `/liturgy-texts/${id}/duplicate`),
  exportLiturgyLibrary: (path: string) =>
    request<{ path: string; count: number }>("POST", "/liturgy-texts/export", {
      path,
    }),
  importLiturgyLibrary: (path: string) =>
    request<{ imported: number; items: LiturgyText[] }>(
      "POST",
      "/liturgy-texts/import",
      { path }
    ),

  // ---- service templates ----
  getTemplate: (id: string) => request<any>("GET", `/service-templates/${id}`),
  deleteTemplate: (id: string) =>
    request<{ deleted: string }>("DELETE", `/service-templates/${id}`),
  duplicateTemplate: (id: string) =>
    request<any>("POST", `/service-templates/${id}/duplicate`),
  templateFromProject: (projectId: string, name?: string, description = "") =>
    request<any>("POST", "/service-templates/from-project", {
      project_id: projectId,
      name,
      description,
    }),
  exportTemplate: (id: string, path: string) =>
    request<{ path: string }>("POST", `/service-templates/${id}/export`, { path }),
  importTemplate: (path: string) =>
    request<any>("POST", "/service-templates/import", { path }),

  // ---- media ----
  importMedia: (projectId: string, sourcePath: string, kind?: MediaKind) =>
    request<{ ref: string; asset: MediaAsset }>("POST", `/projects/${projectId}/media`, {
      source_path: sourcePath,
      kind: kind ?? null,
    }),
  deleteMedia: (projectId: string, ref: string) => {
    const file = ref.startsWith("media/") ? ref.slice("media/".length) : ref;
    return request<{ deleted: string }>(
      "DELETE",
      `/projects/${projectId}/media/${encodeURIComponent(file)}`
    );
  },
};

export async function mediaUrl(projectId: string, ref: string): Promise<string> {
  const base = await resolveBaseUrl();
  const file = ref.startsWith("media/") ? ref.slice("media/".length) : ref;
  return `${base}/projects/${projectId}/media/${encodeURIComponent(file)}`;
}

export async function pickSavePath(defaultName: string): Promise<string | null> {
  if (window.lumina?.savePptxDialog) {
    return window.lumina.savePptxDialog(defaultName);
  }
  return null; // browser dev: backend chooses default path
}

export async function pickMediaFile(
  kind: MediaKind
): Promise<string | null> {
  if (window.lumina?.pickMediaDialog) {
    return window.lumina.pickMediaDialog(kind);
  }
  return null;
}

export async function pickTemplateExportPath(
  defaultName: string
): Promise<string | null> {
  if (window.lumina?.exportTemplateDialog) {
    return window.lumina.exportTemplateDialog(defaultName);
  }
  return null;
}

export async function pickTemplateImportPath(): Promise<string | null> {
  if (window.lumina?.importTemplateDialog) {
    return window.lumina.importTemplateDialog();
  }
  return null;
}

export async function pickHymnLibraryExportPath(
  defaultName: string
): Promise<string | null> {
  if (window.lumina?.exportHymnLibraryDialog) {
    return window.lumina.exportHymnLibraryDialog(defaultName);
  }
  return null;
}

export async function pickHymnLibraryImportPath(): Promise<string | null> {
  if (window.lumina?.importHymnLibraryDialog) {
    return window.lumina.importHymnLibraryDialog();
  }
  return null;
}

export async function pickLiturgyLibraryExportPath(
  defaultName: string
): Promise<string | null> {
  if (window.lumina?.exportLiturgyLibraryDialog) {
    return window.lumina.exportLiturgyLibraryDialog(defaultName);
  }
  return null;
}

export async function pickLiturgyLibraryImportPath(): Promise<string | null> {
  if (window.lumina?.importLiturgyLibraryDialog) {
    return window.lumina.importLiturgyLibraryDialog();
  }
  return null;
}
