import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Button, Modal, Spin, Tooltip } from "antd";
import {
  CopyOutlined,
  DeleteOutlined,
  FileAddOutlined,
  FolderOpenOutlined,
} from "@ant-design/icons";
import { api } from "../api";
import type { ProjectSummary } from "../types";

function formatUpdatedAt(iso?: string): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

interface Props {
  onOpen: (id: string) => void;
  onNew: () => void;
  refreshKey?: number;
}

export function ProjectListPage({ onOpen, onNew, refreshKey = 0 }: Props) {
  const { message } = AntApp.useApp();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await api.listProjects();
      setProjects(list);
    } catch (e: any) {
      message.error(e.message ?? "加载工程列表失败");
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const handleDuplicate = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.duplicateProject(id);
      message.success("已复制工程");
      load();
    } catch (err: any) {
      message.error(err.message ?? "复制失败");
    }
  };

  const handleDelete = (id: string, name: string, e: React.MouseEvent) => {
    e.stopPropagation();
    Modal.confirm({
      title: "删除工程",
      content: `确定删除「${name}」吗？此操作不可撤销。`,
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await api.deleteProject(id);
          message.success("已删除");
          load();
        } catch (err: any) {
          message.error(err.message ?? "删除失败");
        }
      },
    });
  };

  if (loading) {
    return (
      <div className="center-state project-list-page">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="project-list-page">
      <div className="project-list-header">
        <h2 className="project-list-title">礼拜工程</h2>
      </div>

      <div className="project-grid">
        <button type="button" className="project-card project-card--new" onClick={onNew}>
          <FileAddOutlined className="project-card__new-icon" />
          <span className="project-card__new-label">新建</span>
        </button>

        {projects.map((p) => (
          <div
            key={p.id}
            className="project-card"
            role="button"
            tabIndex={0}
            onClick={() => onOpen(p.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onOpen(p.id);
              }
            }}
          >
            <div className="project-card__thumb">
              <FolderOpenOutlined />
            </div>
            <div className="project-card__body">
              <div className="project-card__name" title={p.name || "（未命名）"}>
                {p.name || "（未命名）"}
              </div>
              <div className="project-card__meta">
                <span className="project-card__badge">{p.section_count} 段</span>
                {p.date && <span className="project-card__date">{p.date}</span>}
              </div>
              <div className="project-card__updated">
                更新于 {formatUpdatedAt(p.updated_at)}
              </div>
            </div>
            <div className="project-card__actions" onClick={(e) => e.stopPropagation()}>
              <Tooltip title="打开">
                <Button
                  type="text"
                  size="small"
                  icon={<FolderOpenOutlined />}
                  onClick={() => onOpen(p.id)}
                />
              </Tooltip>
              <Tooltip title="复制">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={(e) => handleDuplicate(p.id, e)}
                />
              </Tooltip>
              <Tooltip title="删除">
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={(e) => handleDelete(p.id, p.name, e)}
                />
              </Tooltip>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
