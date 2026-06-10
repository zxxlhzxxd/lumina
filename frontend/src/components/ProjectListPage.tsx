import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Button, Empty, Modal, Space, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import { CopyOutlined, DeleteOutlined, FileAddOutlined } from "@ant-design/icons";
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

  const columns: ColumnsType<ProjectSummary> = [
    {
      title: "工程名称",
      dataIndex: "name",
      key: "name",
      render: (name: string) => name || "（未命名）",
    },
    {
      title: "段落数",
      dataIndex: "section_count",
      key: "section_count",
      width: 90,
      align: "center",
    },
    {
      title: "最近更新",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 180,
      render: (v?: string) => formatUpdatedAt(v),
    },
    {
      title: "操作",
      key: "actions",
      width: 200,
      render: (_, row) => (
        <Space size="small" onClick={(e) => e.stopPropagation()}>
          <Button type="link" size="small" onClick={() => onOpen(row.id)}>
            打开
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CopyOutlined />}
            onClick={(e) => handleDuplicate(row.id, e)}
          >
            复制
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={(e) => handleDelete(row.id, row.name, e)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="center-state project-list-page">
        <Spin size="large" />
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="center-state project-list-page">
        <Empty description="还没有工程" />
        <Button type="primary" icon={<FileAddOutlined />} onClick={onNew}>
          从模板新建礼拜
        </Button>
      </div>
    );
  }

  return (
    <div className="project-list-page">
      <div className="project-list-header">
        <h2 className="project-list-title">礼拜工程</h2>
        <Button type="primary" icon={<FileAddOutlined />} onClick={onNew}>
          新建
        </Button>
      </div>
      <Table
        className="project-list-table"
        columns={columns}
        dataSource={projects}
        rowKey="id"
        pagination={false}
        onRow={(row) => ({
          onClick: () => onOpen(row.id),
          className: "project-list-row",
        })}
      />
    </div>
  );
}
