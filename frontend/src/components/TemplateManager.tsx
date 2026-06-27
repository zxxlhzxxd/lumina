import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Button, Modal, Space, Tooltip } from "antd";
import {
  CopyOutlined,
  DeleteOutlined,
  ExportOutlined,
  ImportOutlined,
} from "@ant-design/icons";
import {
  api,
  pickTemplateExportPath,
  pickTemplateImportPath,
} from "../api";
import type { TemplateSummary } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  onChanged?: () => void;
}

export function TemplateManager({ open, onClose, onChanged }: Props) {
  const { message, modal } = AntApp.useApp();
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);

  const load = useCallback(async () => {
    try {
      setTemplates(await api.listTemplates());
    } catch (e: any) {
      message.error(e.message ?? "加载模板失败");
    }
  }, [message]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const handleDuplicate = async (id: string) => {
    try {
      await api.duplicateTemplate(id);
      await load();
      onChanged?.();
      message.success("已复制模板");
    } catch (e: any) {
      message.error(e.message ?? "复制失败");
    }
  };

  const handleDelete = (t: TemplateSummary) => {
    modal.confirm({
      title: "删除流程模板",
      content: `确定删除「${t.name}」？`,
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await api.deleteTemplate(t.id);
          await load();
          onChanged?.();
        } catch (e: any) {
          message.error(e.message ?? "删除失败");
        }
      },
    });
  };

  const handleExport = async (t: TemplateSummary) => {
    const path = await pickTemplateExportPath(`${t.name}.lumina`);
    if (!path) return;
    try {
      const res = await api.exportTemplate(t.id, path);
      message.success(`已导出: ${res.path}`);
    } catch (e: any) {
      message.error(e.message ?? "导出失败");
    }
  };

  const handleImport = async () => {
    const path = await pickTemplateImportPath();
    if (!path) return;
    try {
      await api.importTemplate(path);
      await load();
      onChanged?.();
      message.success("已导入模板");
    } catch (e: any) {
      message.error(e.message ?? "导入失败");
    }
  };

  return (
    <Modal
      title="流程模板管理"
      open={open}
      onCancel={onClose}
      width={600}
      footer={[
        <Button key="import" icon={<ImportOutlined />} onClick={handleImport}>
          导入模板
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: "100%" }} size={8}>
        {templates.map((t) => (
          <div
            key={t.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 12px",
              border: "1px solid #303030",
              borderRadius: 6,
            }}
          >
            <span style={{ flex: 1 }}>
              {t.name}
              <span style={{ color: "#7d8794", fontSize: 12, marginLeft: 8 }}>
                {t.section_count} 段
              </span>
            </span>
            <Tooltip title="导出（含媒体）">
              <Button
                type="text"
                size="small"
                icon={<ExportOutlined />}
                onClick={() => handleExport(t)}
              />
            </Tooltip>
            <Tooltip title="复制">
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleDuplicate(t.id)}
              />
            </Tooltip>
            {!t.builtin && (
              <Tooltip title="删除">
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(t)}
                />
              </Tooltip>
            )}
          </div>
        ))}
        <div style={{ color: "#7d8794", fontSize: 12 }}>
          导入/导出的模板容器（.lumina）包含全部引用的媒体文件。
        </div>
      </Space>
    </Modal>
  );
}
