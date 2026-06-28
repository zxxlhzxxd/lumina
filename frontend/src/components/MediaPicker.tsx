import { useEffect, useMemo, useState } from "react";
import {
  App as AntApp,
  Button,
  Dropdown,
  Empty,
  Input,
  Modal,
  Space,
  Tag,
  Tooltip,
} from "antd";
import {
  DeleteOutlined,
  PictureOutlined,
  PlusOutlined,
  SearchOutlined,
  SoundOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import { api, mediaUrl, pickMediaFile } from "../api";
import type { MediaAsset, MediaKind } from "../types";

interface Props {
  kind: MediaKind;
  projectId: string | null;
  assets: MediaAsset[];
  value: string | null;
  onChange: (ref: string | null) => void;
  onAssetChange: (asset: MediaAsset) => void;
}

const KIND_LABEL: Record<MediaKind, string> = {
  image: "图片",
  audio: "音频",
  video: "视频",
};

const KIND_ICON: Record<MediaKind, JSX.Element> = {
  image: <PictureOutlined />,
  audio: <SoundOutlined />,
  video: <VideoCameraOutlined />,
};

function fileName(ref: string) {
  return ref.replace(/^media\//, "");
}

function assetLabel(asset: MediaAsset) {
  return asset.name?.trim() || fileName(asset.ref);
}

export function MediaThumb({
  asset,
  projectId,
  compact = false,
}: {
  asset: MediaAsset;
  projectId: string | null;
  compact?: boolean;
}) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    if (asset.kind === "image" && projectId) {
      mediaUrl(projectId, asset.ref)
        .then((u) => alive && setUrl(u))
        .catch(() => alive && setUrl(null));
    } else {
      setUrl(null);
    }
    return () => {
      alive = false;
    };
  }, [asset.kind, asset.ref, projectId]);

  if (asset.kind === "image" && url) {
    return (
      <img
        className={compact ? "media-thumb media-thumb--compact" : "media-thumb"}
        src={url}
        alt={assetLabel(asset)}
      />
    );
  }
  return (
    <div className={compact ? "media-thumb media-thumb--compact" : "media-thumb"}>
      {KIND_ICON[asset.kind]}
    </div>
  );
}

export function MediaPicker({
  kind,
  projectId,
  assets,
  value,
  onChange,
  onAssetChange,
}: Props) {
  const { message } = AntApp.useApp();
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [renameTarget, setRenameTarget] = useState<MediaAsset | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const typedAssets = useMemo(
    () => assets.filter((asset) => asset.kind === kind),
    [assets, kind]
  );
  const visibleAssets = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return typedAssets;
    return typedAssets.filter((asset) => {
      const haystack = `${asset.name} ${asset.ref}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [query, typedAssets]);
  const selectedAsset = assets.find((asset) => asset.ref === value) ?? null;
  const selectedName = selectedAsset
    ? assetLabel(selectedAsset)
    : value
      ? fileName(value)
      : "";

  const handleImport = async () => {
    if (!projectId) {
      message.warning("请先保存工程后再添加媒体");
      return;
    }
    const path = await pickMediaFile(kind);
    if (!path) return;
    setBusy(true);
    try {
      const { asset } = await api.importMedia(projectId, path, kind);
      onAssetChange(asset);
      onChange(asset.ref);
      setOpen(false);
      setQuery("");
      message.success(`已添加${KIND_LABEL[kind]}`);
    } catch (e: any) {
      message.error(e.message ?? "添加媒体失败");
    } finally {
      setBusy(false);
    }
  };

  const selectAsset = (asset: MediaAsset) => {
    onChange(asset.ref);
    setOpen(false);
    setQuery("");
  };

  const openRename = (asset: MediaAsset) => {
    setRenameTarget(asset);
    setRenameValue(assetLabel(asset));
  };

  const confirmRename = () => {
    if (!renameTarget) return;
    onAssetChange({ ...renameTarget, name: renameValue.trim() });
    setRenameTarget(null);
    setRenameValue("");
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size={6}>
      <Space wrap>
        <Button icon={KIND_ICON[kind]} onClick={() => setOpen(true)}>
          选择{KIND_LABEL[kind]}
        </Button>
        {value && (
          <Tooltip title="清除当前选择">
            <Button
              icon={<DeleteOutlined />}
              danger
              type="text"
              onClick={() => onChange(null)}
            />
          </Tooltip>
        )}
      </Space>
      {value && (
        <div className="media-picker-current">
          {selectedAsset && (
            <MediaThumb asset={selectedAsset} projectId={projectId} compact />
          )}
          <span>{selectedName}</span>
        </div>
      )}
      <Modal
        title={`选择${KIND_LABEL[kind]}`}
        open={open}
        onCancel={() => setOpen(false)}
        width={720}
        footer={[
          <Button key="import" icon={<PlusOutlined />} loading={busy} onClick={handleImport}>
            添加{KIND_LABEL[kind]}
          </Button>,
          <Button key="close" onClick={() => setOpen(false)}>
            关闭
          </Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: "100%" }} size={12}>
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder={`搜索${KIND_LABEL[kind]}资源`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {visibleAssets.length ? (
            <div className="media-select-grid">
              {visibleAssets.map((asset) => (
                <Dropdown
                  key={asset.id}
                  trigger={["contextMenu"]}
                  menu={{
                    items: [{ key: "rename", label: "重命名" }],
                    onClick: ({ domEvent }) => {
                      domEvent.stopPropagation();
                      openRename(asset);
                    },
                  }}
                >
                  <button
                    type="button"
                    className={`media-select-item${
                      asset.ref === value ? " media-select-item--active" : ""
                    }`}
                    onClick={() => selectAsset(asset)}
                  >
                    <MediaThumb asset={asset} projectId={projectId} />
                    <div className="media-select-item__body">
                      <div className="media-select-item__name">{assetLabel(asset)}</div>
                      <div className="media-select-item__ref">{fileName(asset.ref)}</div>
                      {asset.kind === "video" && <Tag color="default">暂不预览</Tag>}
                    </div>
                  </button>
                </Dropdown>
              ))}
            </div>
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={`暂无${KIND_LABEL[kind]}资源`}
            />
          )}
        </Space>
      </Modal>
      <Modal
        title="重命名资源"
        open={renameTarget !== null}
        onCancel={() => {
          setRenameTarget(null);
          setRenameValue("");
        }}
        onOk={confirmRename}
        okText="保存"
        cancelText="取消"
      >
        <Input
          autoFocus
          value={renameValue}
          placeholder={renameTarget ? fileName(renameTarget.ref) : "资源名称"}
          onChange={(e) => setRenameValue(e.target.value)}
          onPressEnter={confirmRename}
        />
      </Modal>
    </Space>
  );
}
