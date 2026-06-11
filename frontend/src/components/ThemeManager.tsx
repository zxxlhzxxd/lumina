import { useCallback, useEffect, useState } from "react";
import {
  App as AntApp,
  Button,
  Modal,
  Space,
  Tag,
  Tooltip,
} from "antd";
import {
  CheckCircleOutlined,
  CopyOutlined,
  DeleteOutlined,
  StarFilled,
  StarOutlined,
} from "@ant-design/icons";
import { api } from "../api";
import type { ThemeSummary } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  onChanged?: () => void;
}

export function ThemeManager({ open, onClose, onChanged }: Props) {
  const { message, modal } = AntApp.useApp();
  const [themes, setThemes] = useState<ThemeSummary[]>([]);
  const [defaultId, setDefaultId] = useState<string>("");

  const load = useCallback(async () => {
    try {
      const res = await api.listThemes();
      setThemes(res.themes);
      setDefaultId(res.default_id);
    } catch (e: any) {
      message.error(e.message ?? "加载主题失败");
    }
  }, [message]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const handleDuplicate = async (id: string) => {
    try {
      await api.duplicateTheme(id);
      await load();
      onChanged?.();
      message.success("已复制主题");
    } catch (e: any) {
      message.error(e.message ?? "复制失败");
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await api.setDefaultTheme(id);
      await load();
      onChanged?.();
      message.success("已设为默认主题");
    } catch (e: any) {
      message.error(e.message ?? "设置失败");
    }
  };

  const handleDelete = (t: ThemeSummary) => {
    modal.confirm({
      title: "删除主题",
      content: `确定删除「${t.name}」？`,
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await api.deleteTheme(t.id);
          await load();
          onChanged?.();
        } catch (e: any) {
          message.error(e.message ?? "删除失败");
        }
      },
    });
  };

  return (
    <Modal title="视觉主题管理" open={open} onCancel={onClose} footer={null} width={560}>
      <Space direction="vertical" style={{ width: "100%" }} size={8}>
        {themes.map((t) => (
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
              {t.builtin && (
                <Tag color="blue" style={{ marginLeft: 8 }}>
                  内置
                </Tag>
              )}
              {t.id === defaultId && (
                <Tag color="gold" icon={<CheckCircleOutlined />} style={{ marginLeft: 4 }}>
                  默认
                </Tag>
              )}
            </span>
            <Tooltip title={t.id === defaultId ? "已是默认" : "设为默认"}>
              <Button
                type="text"
                size="small"
                icon={t.id === defaultId ? <StarFilled /> : <StarOutlined />}
                disabled={t.id === defaultId}
                onClick={() => handleSetDefault(t.id)}
              />
            </Tooltip>
            <Tooltip title="复制为可编辑副本">
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
          内置主题为只读，复制后可在「设为本类型默认」中写入自定义样式。
        </div>
      </Space>
    </Modal>
  );
}
