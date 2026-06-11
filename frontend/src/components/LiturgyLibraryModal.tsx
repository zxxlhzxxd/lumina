import { useCallback, useEffect, useState } from "react";
import { App as AntApp, Button, Input, Modal, Space, Tag, Tooltip } from "antd";
import {
  CopyOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { api } from "../api";
import type { LiturgyText, LiturgyTextSummary } from "../types";

const { TextArea } = Input;

const blocksToText = (blocks: string[]) => blocks.join("\n\n");
const textToBlocks = (text: string) =>
  text.split(/\n\s*\n/).map((s) => s.trimEnd()).filter((s) => s.trim());

interface Props {
  open: boolean;
  onClose: () => void;
  onInsert: (text: LiturgyText) => void;
}

const emptyDraft = (): LiturgyText => ({
  id: "",
  title: "",
  builtin: false,
  paragraphs: [],
});

export function LiturgyLibraryModal({ open, onClose, onInsert }: Props) {
  const { message, modal } = AntApp.useApp();
  const [query, setQuery] = useState("");
  const [list, setList] = useState<LiturgyTextSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<LiturgyText>(emptyDraft());
  const [bodyText, setBodyText] = useState("");

  const load = useCallback(
    async (q = "") => {
      try {
        setList(await api.listLiturgy(q));
      } catch (e: any) {
        message.error(e.message ?? "加载礼文库失败");
      }
    },
    [message]
  );

  useEffect(() => {
    if (open) {
      load("");
      setSelectedId(null);
      setDraft(emptyDraft());
      setBodyText("");
      setQuery("");
    }
  }, [open, load]);

  const selectText = async (id: string) => {
    try {
      const t = await api.getLiturgy(id);
      setSelectedId(id);
      setDraft(t);
      setBodyText(blocksToText(t.paragraphs));
    } catch (e: any) {
      message.error(e.message ?? "加载失败");
    }
  };

  const startNew = () => {
    setSelectedId(null);
    setDraft(emptyDraft());
    setBodyText("");
  };

  const buildPayload = (): LiturgyText => ({
    ...draft,
    paragraphs: textToBlocks(bodyText),
  });

  const handleSave = async () => {
    if (!draft.title.trim()) {
      message.warning("请填写礼文标题");
      return;
    }
    try {
      const payload = buildPayload();
      const saved =
        selectedId && !draft.builtin
          ? await api.updateLiturgy(selectedId, payload)
          : await api.createLiturgy(payload);
      message.success("已保存");
      await load(query);
      setSelectedId(saved.id);
      setDraft(saved);
    } catch (e: any) {
      message.error(e.message ?? "保存失败");
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      const copy = await api.duplicateLiturgy(id);
      await load(query);
      selectText(copy.id);
      message.success("已复制为可编辑副本");
    } catch (e: any) {
      message.error(e.message ?? "复制失败");
    }
  };

  const handleDelete = (t: LiturgyTextSummary) => {
    modal.confirm({
      title: "删除礼文",
      content: `确定删除「${t.title}」？`,
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await api.deleteLiturgy(t.id);
          if (selectedId === t.id) startNew();
          await load(query);
        } catch (e: any) {
          message.error(e.message ?? "删除失败");
        }
      },
    });
  };

  const handleInsert = async () => {
    try {
      const text = selectedId ? await api.getLiturgy(selectedId) : buildPayload();
      onInsert(text);
    } catch (e: any) {
      message.error(e.message ?? "插入失败");
    }
  };

  return (
    <Modal
      title="礼文库"
      open={open}
      onCancel={onClose}
      width={820}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button key="save" onClick={handleSave} disabled={draft.builtin}>
          {selectedId && !draft.builtin ? "保存修改" : "保存为新礼文"}
        </Button>,
        <Button key="insert" type="primary" onClick={handleInsert}>
          插入到段落
        </Button>,
      ]}
    >
      <div style={{ display: "flex", gap: 16, minHeight: 400 }}>
        <div style={{ width: 280, display: "flex", flexDirection: "column" }}>
          <Space.Compact style={{ width: "100%", marginBottom: 8 }}>
            <Input
              placeholder="搜索礼文"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onPressEnter={() => load(query)}
              prefix={<SearchOutlined />}
            />
            <Button onClick={() => load(query)}>搜索</Button>
          </Space.Compact>
          <Button
            icon={<PlusOutlined />}
            onClick={startNew}
            style={{ marginBottom: 8 }}
            block
          >
            新建礼文
          </Button>
          <div style={{ overflowY: "auto", flex: 1, border: "1px solid #303030", borderRadius: 6 }}>
            {list.map((t) => (
              <div
                key={t.id}
                onClick={() => selectText(t.id)}
                style={{
                  padding: "8px 10px",
                  cursor: "pointer",
                  borderBottom: "1px solid #262626",
                  background: selectedId === t.id ? "#2a2a22" : undefined,
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.title || "（未命名）"}
                </span>
                {t.builtin && <Tag color="blue">内置</Tag>}
                <Tooltip title="复制">
                  <Button
                    size="small"
                    type="text"
                    icon={<CopyOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDuplicate(t.id);
                    }}
                  />
                </Tooltip>
                {!t.builtin && (
                  <Tooltip title="删除">
                    <Button
                      size="small"
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(t);
                      }}
                    />
                  </Tooltip>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ flex: 1 }}>
          {draft.builtin && (
            <Tag color="blue" style={{ marginBottom: 8 }}>
              内置礼文为只读，复制后可编辑
            </Tag>
          )}
          <Space direction="vertical" style={{ width: "100%" }} size={10}>
            <Input
              placeholder="礼文标题"
              value={draft.title}
              disabled={draft.builtin}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
            <TextArea
              rows={14}
              placeholder="礼文内容（空行分隔段落）"
              value={bodyText}
              disabled={draft.builtin}
              onChange={(e) => setBodyText(e.target.value)}
            />
          </Space>
        </div>
      </div>
    </Modal>
  );
}
