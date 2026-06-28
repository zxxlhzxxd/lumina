import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  App as AntApp,
  Button,
  Dropdown,
  Input,
  Modal,
  Result,
  Select,
  Space,
  Spin,
  Tag,
  Tooltip,
} from "antd";
import type { MenuProps } from "antd";
import {
  ArrowLeftOutlined,
  AppstoreOutlined,
  CheckCircleOutlined,
  CopyOutlined,
  DeleteOutlined,
  DownOutlined,
  EditOutlined,
  ExportOutlined,
  MenuOutlined,
  PictureOutlined,
  PlusOutlined,
  SaveOutlined,
  StopOutlined,
} from "@ant-design/icons";
import { api, pickSavePath } from "./api";
import type {
  Project,
  MediaAsset,
  Section,
  SectionType,
  SlideModel,
  TemplateSummary,
} from "./types";
import { SECTION_TYPE_LABEL } from "./types";
import { makeSection } from "./sectionFactory";
import { resolveStyle } from "./styleResolve";
import { ProjectListPage } from "./components/ProjectListPage";
import { SectionEditor } from "./components/SectionEditor";
import { SlidePreview } from "./components/SlidePreview";
import { TemplateManager } from "./components/TemplateManager";
import { MediaLibraryModal } from "./components/MediaLibraryModal";

type BackendState = "loading" | "ready" | "error";
type Screen = "list" | "editor";
type LayoutTarget = { sectionId: string; blockId: string };

function Main() {
  const { message } = AntApp.useApp();
  const [backend, setBackend] = useState<BackendState>("loading");
  const [screen, setScreen] = useState<Screen>("list");
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [slides, setSlides] = useState<SlideModel[]>([]);
  const [newOpen, setNewOpen] = useState(false);
  const [templateMgrOpen, setTemplateMgrOpen] = useState(false);
  const [mediaLibraryOpen, setMediaLibraryOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);
  const [dirty, setDirty] = useState(false);
  const [savedSnapshot, setSavedSnapshot] = useState<string | null>(null);
  const [listRefreshKey, setListRefreshKey] = useState(0);
  const [unsavedOpen, setUnsavedOpen] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [activeLayoutTarget, setActiveLayoutTarget] =
    useState<LayoutTarget | null>(null);
  const pendingNav = useRef<(() => void) | null>(null);
  const previewTimer = useRef<number | null>(null);
  const outlineItemRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const markProjectClean = useCallback((p: Project) => {
    setSavedSnapshot(JSON.stringify({ ...p, media_assets: p.media_assets ?? [] }));
    setDirty(false);
  }, []);

  const refreshTemplates = useCallback(async () => {
    try {
      setTemplates(await api.listTemplates());
    } catch {
      // non-fatal
    }
  }, []);

  // ---- backend bootstrap ----
  useEffect(() => {
    (async () => {
      try {
        await api.waitForBackend();
        await refreshTemplates();
        setBackend("ready");
      } catch {
        setBackend("error");
      }
    })();
  }, [refreshTemplates]);

  // ---- dirty tracking ----
  useEffect(() => {
    if (!project || savedSnapshot === null) {
      setDirty(false);
      return;
    }
    setDirty(JSON.stringify(project) !== savedSnapshot);
  }, [project, savedSnapshot]);

  // ---- debounced whole-project preview ----
  useEffect(() => {
    if (!project || screen !== "editor") {
      setSlides([]);
      return;
    }
    if (previewTimer.current) window.clearTimeout(previewTimer.current);
    previewTimer.current = window.setTimeout(async () => {
      try {
        const res = await api.previewProject(project);
        setSlides(res.slides);
      } catch {
        // Invalid reference etc. — keep last good preview.
      }
    }, 350);
    return () => {
      if (previewTimer.current) window.clearTimeout(previewTimer.current);
    };
  }, [project, screen]);

  const selectedSection = useMemo(
    () => project?.sections.find((s) => s.id === selectedId) ?? null,
    [project, selectedId]
  );

  const selectedEffectiveStyle = useMemo(() => {
    if (!selectedSection) return {};
    return resolveStyle(selectedSection);
  }, [selectedSection]);

  const deletingSection = useMemo(
    () => project?.sections.find((s) => s.id === deletingId) ?? null,
    [project, deletingId]
  );

  /** Re-resolve styles client-side so style edits reflect instantly in preview. */
  const displaySlides = useMemo(() => {
    if (!project) return slides;
    const sectionById = new Map(project.sections.map((s) => [s.id, s]));
    return slides.map((sl) => {
      const section = sectionById.get(sl.section_id);
      if (!section) return sl;
      return { ...sl, style: resolveStyle(section) };
    });
  }, [slides, project]);

  const selectedDisplaySlides = useMemo(
    () => displaySlides.filter((s) => s.section_id === selectedId),
    [displaySlides, selectedId]
  );

  useEffect(() => {
    if (
      screen !== "editor" ||
      !selectedId ||
      activeLayoutTarget?.sectionId !== selectedId
    ) {
      setActiveLayoutTarget(null);
    }
  }, [activeLayoutTarget?.sectionId, screen, selectedId]);

  const handleBlockLayoutOpenChange = useCallback(
    (blockId: string, open: boolean) => {
      if (!selectedId) return;
      if (open) {
        setActiveLayoutTarget({ sectionId: selectedId, blockId });
        return;
      }
      setActiveLayoutTarget((current) =>
        current?.sectionId === selectedId && current.blockId === blockId
          ? null
          : current
      );
    },
    [selectedId]
  );

  const selectSectionFromPreview = useCallback(
    (sectionId: string) => {
      if (!project?.sections.some((s) => s.id === sectionId)) return;
      setSelectedId(sectionId);
      window.requestAnimationFrame(() => {
        outlineItemRefs.current[sectionId]?.scrollIntoView({
          block: "nearest",
        });
      });
    },
    [project]
  );

  const guardNavigation = useCallback(
    (action: () => void) => {
      if (screen === "editor" && dirty) {
        pendingNav.current = action;
        setUnsavedOpen(true);
      } else {
        action();
      }
    },
    [screen, dirty]
  );

  const navigateToList = useCallback(() => {
    guardNavigation(() => {
      setProject(null);
      setSelectedId(null);
      setSavedSnapshot(null);
      setDirty(false);
      setScreen("list");
      setListRefreshKey((k) => k + 1);
    });
  }, [guardNavigation]);

  const openProject = useCallback(
    async (id: string) => {
      try {
        const p = await api.getProject(id);
        setProject({ ...p, media_assets: p.media_assets ?? [] });
        setSelectedId(p.sections[0]?.id ?? null);
        markProjectClean({ ...p, media_assets: p.media_assets ?? [] });
        setScreen("editor");
      } catch (e: any) {
        message.error(e.message ?? "加载失败");
      }
    },
    [markProjectClean, message]
  );

  const requestNewProject = useCallback(() => {
    setNewOpen(true);
  }, []);

  // ---- project ops ----
  const handleCreate = async (templateId: string, name: string) => {
    try {
      const p = await api.createProject(templateId || null, name);
      setProject({ ...p, media_assets: p.media_assets ?? [] });
      setSelectedId(p.sections[0]?.id ?? null);
      markProjectClean({ ...p, media_assets: p.media_assets ?? [] });
      setScreen("editor");
      setNewOpen(false);
      message.success("已创建工程");
    } catch (e: any) {
      message.error(e.message ?? "创建失败");
    }
  };

  const updateSection = useCallback(
    (id: string, patch: Partial<Section>) => {
      setProject((prev) =>
        prev
          ? {
              ...prev,
              sections: prev.sections.map((s) =>
                s.id === id ? ({ ...s, ...patch } as Section) : s
              ),
            }
          : prev
      );
    },
    []
  );

  const upsertMediaAsset = useCallback((asset: MediaAsset) => {
    setProject((prev) => {
      if (!prev) return prev;
      const mediaAssets = prev.media_assets ?? [];
      const exists = mediaAssets.some(
        (item) => item.id === asset.id || item.ref === asset.ref
      );
      return {
        ...prev,
        media_assets: exists
          ? mediaAssets.map((item) => (item.ref === asset.ref ? asset : item))
          : [...mediaAssets, asset],
      };
    });
  }, []);

  const reorderSection = (from: number, to: number) => {
    setProject((prev) => {
      if (!prev) return prev;
      if (
        from === to ||
        from < 0 ||
        to < 0 ||
        from >= prev.sections.length ||
        to >= prev.sections.length
      ) {
        return prev;
      }
      const sections = [...prev.sections];
      const [moved] = sections.splice(from, 1);
      sections.splice(to, 0, moved);
      return { ...prev, sections };
    });
  };

  const addSection = (type: SectionType) => {
    if (!project) return;
    const s = makeSection(type);
    const idx = project.sections.findIndex((x) => x.id === selectedId);
    const sections = [...project.sections];
    sections.splice(idx >= 0 ? idx + 1 : sections.length, 0, s);
    setProject({ ...project, sections });
    setSelectedId(s.id);
  };

  const duplicateSection = (id: string) => {
    setProject((prev) => {
      if (!prev) return prev;
      const idx = prev.sections.findIndex((s) => s.id === id);
      if (idx < 0) return prev;
      const clone: Section = {
        ...JSON.parse(JSON.stringify(prev.sections[idx])),
        id: crypto.randomUUID(),
        title: prev.sections[idx].title
          ? `${prev.sections[idx].title} 副本`
          : "",
      };
      const sections = [...prev.sections];
      sections.splice(idx + 1, 0, clone);
      return { ...prev, sections };
    });
  };

  const deleteSection = (id: string) => {
    setProject((prev) => {
      if (!prev) return prev;
      const sections = prev.sections.filter((s) => s.id !== id);
      if (selectedId === id) setSelectedId(sections[0]?.id ?? null);
      return { ...prev, sections };
    });
  };

  const requestDeleteSection = (id: string) => {
    if (!project?.sections.some((s) => s.id === id)) return;
    setDeletingId(id);
  };

  const confirmDeleteSection = () => {
    if (!deletingId) return;
    deleteSection(deletingId);
    setDeletingId(null);
  };

  const toggleSection = (id: string) => {
    setProject((prev) =>
      prev
        ? {
            ...prev,
            sections: prev.sections.map((s) =>
              s.id === id ? ({ ...s, enabled: !s.enabled } as Section) : s
            ),
          }
        : prev
    );
  };

  const openRenameSection = (section: Section) => {
    setRenamingId(section.id);
    setRenameValue(section.title);
  };

  const confirmRenameSection = () => {
    if (!renamingId) return;
    updateSection(renamingId, { title: renameValue } as Partial<Section>);
    setRenamingId(null);
    setRenameValue("");
  };

  const duplicateProject = async () => {
    if (!project) return;
    try {
      const copy = await api.duplicateProject(project.id);
      setProject({ ...copy, media_assets: copy.media_assets ?? [] });
      setSelectedId(copy.sections[0]?.id ?? null);
      markProjectClean({ ...copy, media_assets: copy.media_assets ?? [] });
      message.success("已复制为新工程");
    } catch (e: any) {
      message.error(e.message ?? "复制失败");
    }
  };

  const saveAsTemplate = async () => {
    if (!project) return;
    try {
      await handleSave();
      await api.templateFromProject(project.id, `${project.name} 模板`);
      await refreshTemplates();
      message.success("已另存为流程模板");
    } catch (e: any) {
      message.error(e.message ?? "另存为模板失败");
    }
  };

  const handleExport = async () => {
    if (!project) return;
    setExporting(true);
    try {
      const { issues: preIssues } = await api.validateProject(project);
      const errors = preIssues.filter((i) => i.level === "error");
      if (errors.length) {
        Modal.error({
          title: "导出前检查到问题",
          content: (
            <div>
              {preIssues.map((i, idx) => (
                <div key={idx} style={{ color: i.level === "error" ? "#ff7875" : "#d4b106" }}>
                  {i.level === "error" ? "✕ " : "! "}
                  {i.message}
                </div>
              ))}
              <div style={{ marginTop: 8 }}>请修复错误后再导出。</div>
            </div>
          ),
          okText: "返回修改",
        });
      } else if (preIssues.length) {
        Modal.confirm({
          title: "导出前检查到提醒",
          content: (
            <div>
              {preIssues.map((i, idx) => (
                <div key={idx} style={{ color: "#d4b106" }}>
                  ! {i.message}
                </div>
              ))}
              <div style={{ marginTop: 8 }}>仍要继续导出吗？</div>
            </div>
          ),
          okText: "继续导出",
          cancelText: "返回修改",
          onOk: () => doExport(),
        });
      } else {
        await doExport();
      }
    } catch (e: any) {
      message.error(e.message ?? "导出失败");
    } finally {
      setExporting(false);
    }
  };

  const doExport = async () => {
    if (!project) return;
    const path = await pickSavePath(`${project.name || "礼拜"}.pptx`);
    const res = await api.exportProject(project, path);
    message.success(`已导出: ${res.path}`);
  };

  const handleSave = async (): Promise<boolean> => {
    if (!project) return true;
    try {
      const saved = await api.saveProject(project);
      await api.saveToDisk(project.id);
      const normalized = { ...saved, media_assets: saved.media_assets ?? [] };
      setProject(normalized);
      markProjectClean(normalized);
      message.success("已保存");
      return true;
    } catch (e: any) {
      message.error(e.message ?? "保存失败");
      return false;
    }
  };

  const handleUnsavedSave = async () => {
    const ok = await handleSave();
    if (ok) {
      setUnsavedOpen(false);
      const action = pendingNav.current;
      pendingNav.current = null;
      action?.();
    }
  };

  const handleUnsavedDiscard = () => {
    setUnsavedOpen(false);
    const action = pendingNav.current;
    pendingNav.current = null;
    action?.();
  };

  const handleUnsavedCancel = () => {
    setUnsavedOpen(false);
    pendingNav.current = null;
  };

  // ---- keyboard shortcuts ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      const key = e.key.toLowerCase();

      if (mod && key === "n" && screen === "list") {
        e.preventDefault();
        requestNewProject();
        return;
      }

      if (screen !== "editor" || !project) return;

      if (mod && key === "s") {
        e.preventDefault();
        handleSave();
      } else if (mod && key === "d") {
        e.preventDefault();
        if (selectedId) duplicateSection(selectedId);
        else duplicateProject();
      } else if (mod && key === "e") {
        e.preventDefault();
        handleExport();
      } else if ((e.key === "Delete" || e.key === "Backspace") && selectedId) {
        const el = document.activeElement as HTMLElement | null;
        const tag = el?.tagName;
        const editable =
          tag === "INPUT" || tag === "TEXTAREA" || !!el?.isContentEditable;
        if (!editable && deletingId === null && renamingId === null) {
          e.preventDefault();
          requestDeleteSection(selectedId);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [project, selectedId, screen, requestNewProject, deletingId, renamingId]);

  // ---- render ----
  if (backend === "loading") {
    return (
      <div className="center-state">
        <Spin size="large" />
        <div>正在启动后端服务…</div>
      </div>
    );
  }
  if (backend === "error") {
    return (
      <Result
        status="error"
        title="无法连接后端服务"
        subTitle="请确认后端已启动，或重启应用。"
      />
    );
  }

  return (
    <div className="app-layout">
      <div className="app-toolbar">
        {screen === "editor" ? (
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={navigateToList}
            className="back-to-list-btn"
          >
            返回列表
          </Button>
        ) : (
          <strong style={{ color: "#e0b34a", fontSize: 16 }}>Lumina</strong>
        )}
        {screen === "editor" && project && (
          <>
            <strong style={{ color: "#e0b34a", fontSize: 16 }}>Lumina</strong>
            <Input
              style={{ width: 240 }}
              value={project.name}
              onChange={(e) => setProject({ ...project, name: e.target.value })}
            />
            {dirty && <Tag color="gold">未保存</Tag>}
          </>
        )}
        <div className="spacer" />
        {screen === "editor" && (
          <Space>
            <Button icon={<AppstoreOutlined />} onClick={() => setTemplateMgrOpen(true)}>
              模板
            </Button>
            <Button icon={<PictureOutlined />} onClick={() => setMediaLibraryOpen(true)}>
              媒体资源库
            </Button>
            <Button icon={<CopyOutlined />} disabled={!project} onClick={duplicateProject}>
              复制工程
            </Button>
            <Button disabled={!project} onClick={saveAsTemplate}>
              另存为模板
            </Button>
            <Button icon={<SaveOutlined />} disabled={!project} onClick={() => handleSave()}>
              保存
            </Button>
            <Button
              type="primary"
              icon={<ExportOutlined />}
              disabled={!project}
              loading={exporting}
              onClick={handleExport}
            >
              导出 PPTX
            </Button>
          </Space>
        )}
      </div>

      <div className="app-body">
        {screen === "list" ? (
          <ProjectListPage
            onOpen={openProject}
            onNew={requestNewProject}
            refreshKey={listRefreshKey}
          />
        ) : project ? (
          <>
            <div className="panel panel-outline">
              <div className="panel-header outline-head">
                <span>段落大纲（{project.sections.length}）</span>
                <Dropdown
                  trigger={["click"]}
                  menu={{
                    items: (Object.keys(SECTION_TYPE_LABEL) as SectionType[]).map(
                      (t) => ({ key: t, label: SECTION_TYPE_LABEL[t] })
                    ),
                    onClick: ({ key }) => addSection(key as SectionType),
                  }}
                >
                  <Button size="small" type="primary" icon={<PlusOutlined />}>
                    新增段落 <DownOutlined />
                  </Button>
                </Dropdown>
              </div>
              <div className="outline-list">
                {project.sections.map((s, idx) => (
                  <div
                    key={s.id}
                    ref={(el) => {
                      outlineItemRefs.current[s.id] = el;
                    }}
                    className={`outline-item${s.id === selectedId ? " active" : ""}${
                      s.enabled ? "" : " disabled"
                    }${overIndex === idx && dragIndex !== null && dragIndex !== idx ? " drag-over" : ""}${
                      dragIndex === idx ? " dragging" : ""
                    }`}
                    draggable
                    onClick={() => setSelectedId(s.id)}
                    onDragStart={() => setDragIndex(idx)}
                    onDragOver={(e) => {
                      e.preventDefault();
                      if (overIndex !== idx) setOverIndex(idx);
                    }}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (dragIndex !== null) reorderSection(dragIndex, idx);
                      setDragIndex(null);
                      setOverIndex(null);
                    }}
                    onDragEnd={() => {
                      setDragIndex(null);
                      setOverIndex(null);
                    }}
                  >
                    <span className="drag-handle" aria-hidden>
                      ⠿
                    </span>
                    <Tag style={{ margin: 0 }}>{SECTION_TYPE_LABEL[s.type]}</Tag>
                    <span className="title">{s.title || "（未命名）"}</span>
                    <span
                      className="outline-action-wrap"
                      draggable={false}
                      onClick={(e) => e.stopPropagation()}
                      onMouseDown={(e) => e.stopPropagation()}
                    >
                      <Dropdown
                        trigger={["click"]}
                        menu={{
                          items: [
                            { key: "rename", icon: <EditOutlined />, label: "重命名段落" },
                            { key: "duplicate", icon: <CopyOutlined />, label: "复制段落" },
                            {
                              key: "toggle",
                              icon: s.enabled ? <StopOutlined /> : <CheckCircleOutlined />,
                              label: s.enabled ? "停用（不导出）" : "启用",
                            },
                            { type: "divider" },
                            {
                              key: "delete",
                              icon: <DeleteOutlined />,
                              label: "删除段落",
                              danger: true,
                            },
                          ] as MenuProps["items"],
                          onClick: ({ key, domEvent }) => {
                            domEvent.stopPropagation();
                            if (key === "rename") openRenameSection(s);
                            else if (key === "duplicate") duplicateSection(s.id);
                            else if (key === "toggle") toggleSection(s.id);
                            else if (key === "delete") requestDeleteSection(s.id);
                          },
                        }}
                      >
                        <Tooltip title="段落菜单" placement="right">
                          <Button
                            className="outline-action"
                            type="text"
                            size="small"
                            icon={<MenuOutlined />}
                            aria-label="段落菜单"
                            draggable={false}
                          />
                        </Tooltip>
                      </Dropdown>
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel panel-editor">
              {selectedSection ? (
                <>
                  <SectionEditor
                    key={selectedSection.id}
                    section={selectedSection}
                    projectId={project.id}
                    mediaAssets={project.media_assets ?? []}
                    effectiveStyle={selectedEffectiveStyle}
                    onChange={(patch) => updateSection(selectedSection.id, patch)}
                    onMediaAssetChange={upsertMediaAsset}
                    onBlockLayoutOpenChange={handleBlockLayoutOpenChange}
                  />
                  {selectedDisplaySlides.length > 0 && (
                    <>
                      <div className="panel-header" style={{ paddingLeft: 0, marginTop: 16 }}>
                        本段落将生成 {selectedDisplaySlides.length} 页
                      </div>
                      <div className="inline-preview-grid">
                        {selectedDisplaySlides.map((sl) => (
                          <SlidePreview
                            key={`${sl.section_id}-${sl.index}`}
                            slide={sl}
                            slideSize={project.slide_size}
                            projectId={project.id}
                            highlightedBlockId={
                              activeLayoutTarget?.sectionId === sl.section_id
                                ? activeLayoutTarget.blockId
                                : null
                            }
                          />
                        ))}
                      </div>
                    </>
                  )}
                </>
              ) : (
                <div className="center-state">请选择左侧段落进行编辑</div>
              )}
            </div>

            <div className="panel panel-preview">
              <div className="panel-header" style={{ paddingLeft: 4 }}>
                整体预览（{displaySlides.length} 页）
              </div>
              {displaySlides.map((sl) => (
                <SlidePreview
                  key={`${sl.section_id}-${sl.index}`}
                  slide={sl}
                  slideSize={project.slide_size}
                  projectId={project.id}
                  onClick={() => selectSectionFromPreview(sl.section_id)}
                />
              ))}
            </div>
          </>
        ) : null}
      </div>

      <NewProjectModal
        open={newOpen}
        templates={templates}
        onCancel={() => setNewOpen(false)}
        onCreate={handleCreate}
      />

      <TemplateManager
        open={templateMgrOpen}
        onClose={() => setTemplateMgrOpen(false)}
        onChanged={refreshTemplates}
      />

      <MediaLibraryModal
        open={mediaLibraryOpen}
        project={project}
        onClose={() => setMediaLibraryOpen(false)}
        onChange={setProject}
      />

      <Modal
        title="重命名段落"
        open={renamingId !== null}
        onCancel={() => {
          setRenamingId(null);
          setRenameValue("");
        }}
        onOk={confirmRenameSection}
        okText="保存"
        cancelText="取消"
      >
        <Input
          value={renameValue}
          autoFocus
          placeholder="段落名称"
          onChange={(e) => setRenameValue(e.target.value)}
          onPressEnter={confirmRenameSection}
        />
      </Modal>

      <Modal
        title="删除段落"
        open={deletingId !== null}
        onCancel={() => setDeletingId(null)}
        onOk={confirmDeleteSection}
        okText="删除"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        确定删除段落「{deletingSection?.title || "（未命名）"}」吗？
      </Modal>

      <Modal
        title="未保存的修改"
        open={unsavedOpen}
        onCancel={handleUnsavedCancel}
        footer={[
          <Button key="cancel" onClick={handleUnsavedCancel}>
            取消
          </Button>,
          <Button key="discard" onClick={handleUnsavedDiscard}>
            放弃修改
          </Button>,
          <Button key="save" type="primary" onClick={handleUnsavedSave}>
            保存并继续
          </Button>,
        ]}
      >
        当前工程有未保存的修改，离开前如何处理？
      </Modal>
    </div>
  );
}

function NewProjectModal({
  open,
  templates,
  onCancel,
  onCreate,
}: {
  open: boolean;
  templates: TemplateSummary[];
  onCancel: () => void;
  onCreate: (templateId: string, name: string) => void;
}) {
  const [name, setName] = useState("主日崇拜");
  const [templateId, setTemplateId] = useState<string>("");

  useEffect(() => {
    if (open && templates.length && !templateId) {
      setTemplateId(templates[0].id);
    }
  }, [open, templates, templateId]);

  return (
    <Modal
      title="新建礼拜工程"
      open={open}
      onCancel={onCancel}
      onOk={() => onCreate(templateId, name)}
      okText="创建"
      cancelText="取消"
    >
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <div>
          <div style={{ marginBottom: 6 }}>工程名称</div>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <div style={{ marginBottom: 6 }}>流程模板</div>
          <Select
            style={{ width: "100%" }}
            value={templateId}
            onChange={setTemplateId}
            options={templates.map((t) => ({
              label: `${t.name}（${t.section_count} 段）`,
              value: t.id,
            }))}
          />
        </div>
      </Space>
    </Modal>
  );
}

export default function App() {
  return (
    <AntApp>
      <Main />
    </AntApp>
  );
}
