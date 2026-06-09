import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  App as AntApp,
  Button,
  Empty,
  Input,
  Modal,
  Result,
  Select,
  Space,
  Spin,
  Tag,
  Tooltip,
} from "antd";
import {
  CopyOutlined,
  DeleteOutlined,
  DownOutlined,
  ExportOutlined,
  FileAddOutlined,
  SaveOutlined,
  UpOutlined,
} from "@ant-design/icons";
import { api, pickSavePath } from "./api";
import type { Project, Section, SlideModel, TemplateSummary } from "./types";
import { SECTION_TYPE_LABEL } from "./types";
import { SectionEditor } from "./components/SectionEditor";
import { SlidePreview } from "./components/SlidePreview";

type BackendState = "loading" | "ready" | "error";

function Main() {
  const { message } = AntApp.useApp();
  const [backend, setBackend] = useState<BackendState>("loading");
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [slides, setSlides] = useState<SlideModel[]>([]);
  const [newOpen, setNewOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const previewTimer = useRef<number | null>(null);

  // ---- backend bootstrap ----
  useEffect(() => {
    (async () => {
      try {
        await api.waitForBackend();
        const tpls = await api.listTemplates();
        setTemplates(tpls);
        setBackend("ready");
      } catch {
        setBackend("error");
      }
    })();
  }, []);

  // ---- debounced whole-project preview ----
  useEffect(() => {
    if (!project) {
      setSlides([]);
      return;
    }
    if (previewTimer.current) window.clearTimeout(previewTimer.current);
    previewTimer.current = window.setTimeout(async () => {
      try {
        const res = await api.previewProject(project);
        setSlides(res.slides);
      } catch (e: any) {
        // Invalid reference etc. — keep last good preview, surface lightly.
      }
    }, 350);
    return () => {
      if (previewTimer.current) window.clearTimeout(previewTimer.current);
    };
  }, [project]);

  const selectedSection = useMemo(
    () => project?.sections.find((s) => s.id === selectedId) ?? null,
    [project, selectedId]
  );

  const selectedSlides = useMemo(
    () => slides.filter((s) => s.section_id === selectedId),
    [slides, selectedId]
  );

  // ---- project ops ----
  const handleCreate = async (templateId: string, name: string) => {
    try {
      const p = await api.createProject(templateId || null, name);
      setProject(p);
      setSelectedId(p.sections[0]?.id ?? null);
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

  const moveSection = (id: string, dir: -1 | 1) => {
    setProject((prev) => {
      if (!prev) return prev;
      const idx = prev.sections.findIndex((s) => s.id === id);
      const next = idx + dir;
      if (idx < 0 || next < 0 || next >= prev.sections.length) return prev;
      const sections = [...prev.sections];
      [sections[idx], sections[next]] = [sections[next], sections[idx]];
      return { ...prev, sections };
    });
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

  const duplicateProject = () => {
    if (!project) return;
    const copy: Project = JSON.parse(JSON.stringify(project));
    copy.id = crypto.randomUUID();
    copy.name = `${project.name} 副本`;
    copy.sections = copy.sections.map((s) => ({ ...s, id: crypto.randomUUID() }));
    setProject(copy);
    setSelectedId(copy.sections[0]?.id ?? null);
    message.success("已复制为新工程");
  };

  const handleExport = async () => {
    if (!project) return;
    setExporting(true);
    try {
      const { issues: preIssues } = await api.validateProject(project);
      const errors = preIssues.filter((i) => i.level === "error");
      if (errors.length) {
        Modal.confirm({
          title: "导出前检查到问题",
          content: (
            <div>
              {preIssues.map((i, idx) => (
                <div key={idx} style={{ color: i.level === "error" ? "#ff7875" : "#d4b106" }}>
                  {i.level === "error" ? "✕ " : "! "}
                  {i.message}
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

  const handleSave = async () => {
    if (!project) return;
    try {
      await api.saveProject(project);
      await api.saveToDisk(project.id);
      message.success("已保存");
    } catch (e: any) {
      message.error(e.message ?? "保存失败");
    }
  };

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
        <strong style={{ color: "#e0b34a", fontSize: 16 }}>Lumina</strong>
        {project && (
          <Input
            style={{ width: 240 }}
            value={project.name}
            onChange={(e) => setProject({ ...project, name: e.target.value })}
          />
        )}
        <div className="spacer" />
        <Space>
          <Button icon={<FileAddOutlined />} onClick={() => setNewOpen(true)}>
            新建
          </Button>
          <Button icon={<CopyOutlined />} disabled={!project} onClick={duplicateProject}>
            复制工程
          </Button>
          <Button icon={<SaveOutlined />} disabled={!project} onClick={handleSave}>
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
      </div>

      <div className="app-body">
        {!project ? (
          <div className="center-state" style={{ flex: 1 }}>
            <Empty description="还没有工程" />
            <Button type="primary" icon={<FileAddOutlined />} onClick={() => setNewOpen(true)}>
              从模板新建礼拜
            </Button>
          </div>
        ) : (
          <>
            <div className="panel panel-outline">
              <div className="panel-header">段落大纲（{project.sections.length}）</div>
              <div className="outline-list">
                {project.sections.map((s, idx) => (
                  <div
                    key={s.id}
                    className={`outline-item${s.id === selectedId ? " active" : ""}${
                      s.enabled ? "" : " disabled"
                    }`}
                    onClick={() => setSelectedId(s.id)}
                  >
                    <Tag style={{ margin: 0 }}>{SECTION_TYPE_LABEL[s.type]}</Tag>
                    <span className="title">{s.title || "（未命名）"}</span>
                    <Space size={2} onClick={(e) => e.stopPropagation()}>
                      <Tooltip title="上移">
                        <Button
                          size="small"
                          type="text"
                          icon={<UpOutlined />}
                          disabled={idx === 0}
                          onClick={() => moveSection(s.id, -1)}
                        />
                      </Tooltip>
                      <Tooltip title="下移">
                        <Button
                          size="small"
                          type="text"
                          icon={<DownOutlined />}
                          disabled={idx === project.sections.length - 1}
                          onClick={() => moveSection(s.id, 1)}
                        />
                      </Tooltip>
                      <Tooltip title="复制段落">
                        <Button
                          size="small"
                          type="text"
                          icon={<CopyOutlined />}
                          onClick={() => duplicateSection(s.id)}
                        />
                      </Tooltip>
                      <Tooltip title={s.enabled ? "停用（不导出）" : "启用"}>
                        <Button
                          size="small"
                          type="text"
                          onClick={() => toggleSection(s.id)}
                        >
                          {s.enabled ? "○" : "—"}
                        </Button>
                      </Tooltip>
                      <Tooltip title="删除段落">
                        <Button
                          size="small"
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => deleteSection(s.id)}
                        />
                      </Tooltip>
                    </Space>
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
                    onChange={(patch) => updateSection(selectedSection.id, patch)}
                  />
                  {selectedSlides.length > 0 && (
                    <>
                      <div className="panel-header" style={{ paddingLeft: 0, marginTop: 16 }}>
                        本段落将生成 {selectedSlides.length} 页
                      </div>
                      <div className="inline-preview-grid">
                        {selectedSlides.map((sl, i) => (
                          <SlidePreview key={i} slide={sl} />
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
                整体预览（{slides.length} 页）
              </div>
              {slides.map((sl, i) => (
                <SlidePreview key={i} slide={sl} />
              ))}
            </div>
          </>
        )}
      </div>

      <NewProjectModal
        open={newOpen}
        templates={templates}
        onCancel={() => setNewOpen(false)}
        onCreate={handleCreate}
      />
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
