import { useMemo, useState } from "react";
import {
  App as AntApp,
  Alert,
  Button,
  Empty,
  Input,
  Modal,
  Space,
  Tabs,
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
import { api, pickMediaFiles } from "../api";
import type {
  MediaAsset,
  MediaBatchImportResult,
  MediaKind,
  Project,
  Section,
} from "../types";
import { SECTION_TYPE_LABEL } from "../types";
import { MediaThumb } from "./MediaPicker";

interface Props {
  open: boolean;
  project: Project | null;
  onClose: () => void;
  onChange: (project: Project) => void;
}

const KINDS: MediaKind[] = ["image", "audio", "video"];
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

function sourceFileName(path: string) {
  return path.split(/[\\/]/).pop() || path;
}

function assetLabel(asset: MediaAsset) {
  return asset.name?.trim() || fileName(asset.ref);
}

function sectionLabel(section: Section) {
  return section.title || SECTION_TYPE_LABEL[section.type];
}

function usagesFor(project: Project, ref: string) {
  const usages: string[] = [];
  for (const section of project.sections) {
    if (section.style?.background_image === ref) {
      usages.push(`${sectionLabel(section)} / 背景图片`);
    }
    if (section.style?.background_video === ref) {
      usages.push(`${sectionLabel(section)} / 背景视频`);
    }
    if (section.type === "media") {
      if (section.audio_ref === ref) usages.push(`${sectionLabel(section)} / 音频`);
      if (section.video_ref === ref) usages.push(`${sectionLabel(section)} / 视频`);
    }
  }
  return usages;
}

export function MediaLibraryModal({ open, project, onClose, onChange }: Props) {
  const { message } = AntApp.useApp();
  const [activeKind, setActiveKind] = useState<MediaKind>("image");
  const [query, setQuery] = useState("");
  const [busyKind, setBusyKind] = useState<MediaKind | null>(null);
  const [batchResult, setBatchResult] = useState<MediaBatchImportResult | null>(
    null
  );

  const assets = project?.media_assets ?? [];
  const visibleAssets = useMemo(() => {
    const q = query.trim().toLowerCase();
    return assets
      .filter((asset) => asset.kind === activeKind)
      .filter((asset) => {
        if (!q) return true;
        return `${asset.name} ${asset.ref}`.toLowerCase().includes(q);
      });
  }, [activeKind, assets, query]);

  const replaceAssets = (nextAssets: MediaAsset[]) => {
    if (!project) return;
    onChange({ ...project, media_assets: nextAssets });
  };

  const mergeAssets = (imported: MediaAsset[]) => {
    const nextAssets = [...assets];
    for (const asset of imported) {
      const index = nextAssets.findIndex(
        (item) => item.id === asset.id || item.ref === asset.ref
      );
      if (index >= 0) {
        nextAssets[index] = asset;
      } else {
        nextAssets.push(asset);
      }
    }
    replaceAssets(nextAssets);
  };

  const handleImport = async (kind: MediaKind) => {
    if (!project) return;
    const paths = await pickMediaFiles(kind);
    if (!paths.length) return;
    setBatchResult(null);
    setBusyKind(kind);
    try {
      const result = await api.importMediaBatch(project.id, paths, kind);
      mergeAssets(result.assets);
      setBatchResult(result);
      setActiveKind(kind);
    } catch (e: any) {
      message.error(e.message ?? "添加媒体失败");
    } finally {
      setBusyKind(null);
    }
  };

  const handleClose = () => {
    setBatchResult(null);
    onClose();
  };

  const renameAsset = (asset: MediaAsset, name: string) => {
    replaceAssets(
      assets.map((item) => (item.id === asset.id ? { ...item, name } : item))
    );
  };

  const deleteAsset = async (asset: MediaAsset) => {
    if (!project) return;
    const usages = usagesFor(project, asset.ref);
    if (usages.length) {
      message.warning(`资源正在使用：${usages.join("、")}`);
      return;
    }
    try {
      await api.deleteMedia(project.id, asset.ref);
      replaceAssets(assets.filter((item) => item.id !== asset.id));
      message.success("已删除资源");
    } catch (e: any) {
      message.error(e.message ?? "删除媒体失败");
    }
  };

  return (
    <Modal
      title="媒体资源库"
      open={open}
      onCancel={handleClose}
      width={840}
      footer={[
        <Button key="close" onClick={handleClose}>
          关闭
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: "100%" }} size={12}>
        <Tabs
          activeKey={activeKind}
          onChange={(key) => {
            setActiveKind(key as MediaKind);
            setQuery("");
          }}
          items={KINDS.map((kind) => ({
            key: kind,
            label: (
              <Space size={6}>
                {KIND_ICON[kind]}
                <span>{KIND_LABEL[kind]}</span>
                <Tag>{assets.filter((asset) => asset.kind === kind).length}</Tag>
              </Space>
            ),
          }))}
        />
        <div className="media-library-toolbar">
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder={`搜索${KIND_LABEL[activeKind]}资源`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            loading={busyKind === activeKind}
            disabled={busyKind !== null}
            onClick={() => handleImport(activeKind)}
          >
            添加{KIND_LABEL[activeKind]}
          </Button>
        </div>
        {batchResult && (
          <Alert
            showIcon
            type={
              batchResult.failed.length === 0
                ? "success"
                : batchResult.assets.length > 0
                  ? "warning"
                  : "error"
            }
            message={`批量导入完成：成功 ${batchResult.assets.length} 个，失败 ${batchResult.failed.length} 个`}
            description={
              batchResult.failed.length > 0 ? (
                <ul className="media-import-failures">
                  {batchResult.failed.map((failure, index) => (
                    <li key={`${failure.source_path}-${index}`}>
                      <strong>{sourceFileName(failure.source_path)}</strong>
                      <span>{failure.message}</span>
                    </li>
                  ))}
                </ul>
              ) : undefined
            }
          />
        )}
        {visibleAssets.length ? (
          <div className="media-library-list">
            {visibleAssets.map((asset) => {
              const usages = project ? usagesFor(project, asset.ref) : [];
              return (
                <div key={asset.id} className="media-library-row">
                  <MediaThumb asset={asset} projectId={project?.id ?? null} />
                  <div className="media-library-row__body">
                    <Input
                      value={asset.name}
                      placeholder={fileName(asset.ref)}
                      onChange={(e) => renameAsset(asset, e.target.value)}
                    />
                    <div className="media-library-row__meta">
                      <span>{fileName(asset.ref)}</span>
                      {asset.kind === "video" && <Tag color="default">暂不预览</Tag>}
                      {usages.length > 0 && <Tag color="gold">使用中</Tag>}
                    </div>
                  </div>
                  <Tooltip
                    title={
                      usages.length
                        ? `正在使用：${usages.join("、")}`
                        : "删除资源"
                    }
                  >
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => deleteAsset(asset)}
                    />
                  </Tooltip>
                </div>
              );
            })}
          </div>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={`暂无${KIND_LABEL[activeKind]}资源`}
          />
        )}
      </Space>
    </Modal>
  );
}
