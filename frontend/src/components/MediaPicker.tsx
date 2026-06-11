import { useEffect, useState } from "react";
import { App as AntApp, Button, Space } from "antd";
import { DeleteOutlined, UploadOutlined } from "@ant-design/icons";
import { api, mediaUrl, pickMediaFile } from "../api";

interface Props {
  kind: "image" | "audio" | "video";
  projectId: string | null;
  value: string | null;
  onChange: (ref: string | null) => void;
}

const KIND_LABEL = { image: "图片", audio: "音频", video: "视频" } as const;

export function MediaPicker({ kind, projectId, value, onChange }: Props) {
  const { message } = AntApp.useApp();
  const [busy, setBusy] = useState(false);
  const [thumb, setThumb] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    if (kind === "image" && value && projectId) {
      mediaUrl(projectId, value)
        .then((u) => alive && setThumb(u))
        .catch(() => alive && setThumb(null));
    } else {
      setThumb(null);
    }
    return () => {
      alive = false;
    };
  }, [kind, value, projectId]);

  const handlePick = async () => {
    if (!projectId) {
      message.warning("请先保存工程后再添加媒体");
      return;
    }
    const path = await pickMediaFile(kind);
    if (!path) return;
    setBusy(true);
    try {
      const { ref } = await api.importMedia(projectId, path);
      onChange(ref);
      message.success(`已添加${KIND_LABEL[kind]}`);
    } catch (e: any) {
      message.error(e.message ?? "添加媒体失败");
    } finally {
      setBusy(false);
    }
  };

  const fileName = value ? value.replace(/^media\//, "") : "";

  return (
    <Space direction="vertical" style={{ width: "100%" }} size={6}>
      <Space>
        <Button icon={<UploadOutlined />} loading={busy} onClick={handlePick}>
          选择{KIND_LABEL[kind]}
        </Button>
        {value && (
          <Button
            icon={<DeleteOutlined />}
            danger
            type="text"
            onClick={() => onChange(null)}
          >
            清除
          </Button>
        )}
      </Space>
      {value && (
        <span style={{ color: "#9fb3c8", fontSize: 12, wordBreak: "break-all" }}>
          {fileName}
        </span>
      )}
      {thumb && (
        <img
          src={thumb}
          alt="预览"
          style={{
            maxWidth: "100%",
            maxHeight: 120,
            borderRadius: 4,
            border: "1px solid #303030",
          }}
        />
      )}
    </Space>
  );
}
