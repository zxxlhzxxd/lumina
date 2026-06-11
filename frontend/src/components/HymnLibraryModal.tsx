import { useCallback, useEffect, useState } from "react";
import {
  App as AntApp,
  Button,
  Input,
  Modal,
  Space,
  Tag,
  Tooltip,
} from "antd";
import {
  CopyOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { api } from "../api";
import type { Hymn, HymnSummary } from "../types";

const { TextArea } = Input;

const blocksToText = (blocks: string[]) => blocks.join("\n\n");
const textToBlocks = (text: string) =>
  text.split(/\n\s*\n/).map((s) => s.trimEnd()).filter((s) => s.trim());

interface Props {
  open: boolean;
  onClose: () => void;
  onInsert: (hymn: Hymn) => void;
}

const emptyDraft = (): Hymn => ({
  id: "",
  title: "",
  author: "",
  number: "",
  source: "",
  builtin: false,
  sections: [],
});

export function HymnLibraryModal({ open, onClose, onInsert }: Props) {
  const { message, modal } = AntApp.useApp();
  const [query, setQuery] = useState("");
  const [list, setList] = useState<HymnSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Hymn>(emptyDraft());
  const [lyricsText, setLyricsText] = useState("");

  const load = useCallback(
    async (q = "") => {
      try {
        setList(await api.listHymns(q));
      } catch (e: any) {
        message.error(e.message ?? "加载赞美诗库失败");
      }
    },
    [message]
  );

  useEffect(() => {
    if (open) {
      load("");
      setSelectedId(null);
      setDraft(emptyDraft());
      setLyricsText("");
      setQuery("");
    }
  }, [open, load]);

  const selectHymn = async (id: string) => {
    try {
      const h = await api.getHymn(id);
      setSelectedId(id);
      setDraft(h);
      setLyricsText(blocksToText(h.sections.map((s) => s.text)));
    } catch (e: any) {
      message.error(e.message ?? "加载失败");
    }
  };

  const startNew = () => {
    setSelectedId(null);
    setDraft(emptyDraft());
    setLyricsText("");
  };

  const buildPayload = (): Hymn => ({
    ...draft,
    sections: textToBlocks(lyricsText).map((text, i) => ({
      order: i,
      label: draft.sections[i]?.label ?? "",
      text,
    })),
  });

  const handleSave = async () => {
    if (!draft.title.trim()) {
      message.warning("请填写诗歌名");
      return;
    }
    try {
      const payload = buildPayload();
      const saved =
        selectedId && !draft.builtin
          ? await api.updateHymn(selectedId, payload)
          : await api.createHymn(payload);
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
      const copy = await api.duplicateHymn(id);
      await load(query);
      selectHymn(copy.id);
      message.success("已复制为可编辑副本");
    } catch (e: any) {
      message.error(e.message ?? "复制失败");
    }
  };

  const handleDelete = (h: HymnSummary) => {
    modal.confirm({
      title: "删除赞美诗",
      content: `确定删除「${h.title}」？`,
      okText: "删除",
      okType: "danger",
      cancelText: "取消",
      onOk: async () => {
        try {
          await api.deleteHymn(h.id);
          if (selectedId === h.id) startNew();
          await load(query);
        } catch (e: any) {
          message.error(e.message ?? "删除失败");
        }
      },
    });
  };

  const handleInsert = async () => {
    try {
      const hymn = selectedId ? await api.getHymn(selectedId) : buildPayload();
      onInsert(hymn);
    } catch (e: any) {
      message.error(e.message ?? "插入失败");
    }
  };

  return (
    <Modal
      title="赞美诗库"
      open={open}
      onCancel={onClose}
      width={860}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button key="save" onClick={handleSave} disabled={draft.builtin}>
          {selectedId && !draft.builtin ? "保存修改" : "保存为新诗歌"}
        </Button>,
        <Button key="insert" type="primary" onClick={handleInsert}>
          插入到段落
        </Button>,
      ]}
    >
      <div style={{ display: "flex", gap: 16, minHeight: 420 }}>
        <div style={{ width: 300, display: "flex", flexDirection: "column" }}>
          <Space.Compact style={{ width: "100%", marginBottom: 8 }}>
            <Input
              placeholder="搜索诗名 / 作者 / 歌词"
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
            新建诗歌
          </Button>
          <div style={{ overflowY: "auto", flex: 1, border: "1px solid #303030", borderRadius: 6 }}>
            {list.map((h) => (
              <div
                key={h.id}
                onClick={() => selectHymn(h.id)}
                style={{
                  padding: "8px 10px",
                  cursor: "pointer",
                  borderBottom: "1px solid #262626",
                  background: selectedId === h.id ? "#2a2a22" : undefined,
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {h.title || "（未命名）"}
                  {h.author && (
                    <span style={{ color: "#7d8794", fontSize: 12 }}> · {h.author}</span>
                  )}
                </span>
                {h.builtin && <Tag color="blue">内置</Tag>}
                <Tooltip title="复制">
                  <Button
                    size="small"
                    type="text"
                    icon={<CopyOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDuplicate(h.id);
                    }}
                  />
                </Tooltip>
                {!h.builtin && (
                  <Tooltip title="删除">
                    <Button
                      size="small"
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(h);
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
              内置诗歌为只读，复制后可编辑
            </Tag>
          )}
          <Space direction="vertical" style={{ width: "100%" }} size={10}>
            <Input
              placeholder="诗歌名"
              value={draft.title}
              disabled={draft.builtin}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
            <Space>
              <Input
                placeholder="作者"
                value={draft.author}
                disabled={draft.builtin}
                onChange={(e) => setDraft({ ...draft, author: e.target.value })}
              />
              <Input
                placeholder="编号"
                value={draft.number}
                disabled={draft.builtin}
                onChange={(e) => setDraft({ ...draft, number: e.target.value })}
              />
            </Space>
            <TextArea
              rows={13}
              placeholder="歌词（空行分隔不同段落/节）"
              value={lyricsText}
              disabled={draft.builtin}
              onChange={(e) => setLyricsText(e.target.value)}
            />
          </Space>
        </div>
      </div>
    </Modal>
  );
}
