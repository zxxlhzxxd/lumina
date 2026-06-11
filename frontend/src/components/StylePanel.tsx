import { Button, Collapse, Form, InputNumber, Segmented, Space, Switch } from "antd";
import type { Section, SectionStyle, TextStyle } from "../types";
import { MediaPicker } from "./MediaPicker";

interface Props {
  section: Section;
  projectId: string | null;
  onChange: (patch: Partial<Section>) => void;
  onSetTypeDefault: (style: SectionStyle) => void;
}

type TextRole = "body" | "title" | "label";

function ColorField({
  value,
  onChange,
}: {
  value?: string | null;
  onChange: (v: string | null) => void;
}) {
  return (
    <Space>
      <input
        type="color"
        value={value ?? "#000000"}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: 40,
          height: 28,
          background: "transparent",
          border: "1px solid #303030",
          borderRadius: 4,
          cursor: "pointer",
        }}
      />
      {value ? (
        <>
          <span style={{ color: "#9fb3c8", fontSize: 12 }}>{value}</span>
          <Button size="small" type="text" onClick={() => onChange(null)}>
            清除
          </Button>
        </>
      ) : (
        <span style={{ color: "#6b6b6b", fontSize: 12 }}>（继承主题）</span>
      )}
    </Space>
  );
}

export function StylePanel({ section, projectId, onChange, onSetTypeDefault }: Props) {
  const style: SectionStyle = section.style ?? {};

  const patchStyle = (partial: Partial<SectionStyle>) => {
    onChange({ style: { ...style, ...partial } } as Partial<Section>);
  };

  const patchText = (role: TextRole, partial: Partial<TextStyle>) => {
    const current = (style[role] ?? {}) as TextStyle;
    patchStyle({ [role]: { ...current, ...partial } } as Partial<SectionStyle>);
  };

  const textEditor = (role: TextRole, label: string) => {
    const ts = (style[role] ?? {}) as TextStyle;
    return (
      <div style={{ marginBottom: 10 }}>
        <div style={{ color: "#9fb3c8", fontSize: 12, marginBottom: 6 }}>{label}</div>
        <Space wrap size={10}>
          <InputNumber
            placeholder="字号"
            min={8}
            max={120}
            value={ts.font_size ?? undefined}
            onChange={(v) => patchText(role, { font_size: v ?? null })}
            style={{ width: 90 }}
            addonAfter="pt"
          />
          <ColorField
            value={ts.color}
            onChange={(v) => patchText(role, { color: v })}
          />
          <Segmented
            size="small"
            value={ts.align ?? "center"}
            onChange={(v) => patchText(role, { align: v as TextStyle["align"] })}
            options={[
              { label: "左", value: "left" },
              { label: "中", value: "center" },
              { label: "右", value: "right" },
            ]}
          />
          <Space size={4}>
            <span style={{ fontSize: 12, color: "#9fb3c8" }}>加粗</span>
            <Switch
              size="small"
              checked={!!ts.bold}
              onChange={(v) => patchText(role, { bold: v })}
            />
          </Space>
        </Space>
      </div>
    );
  };

  return (
    <Collapse
      ghost
      style={{ marginTop: 8 }}
      items={[
        {
          key: "style",
          label: "样式（背景 / 字体 / 排版）",
          children: (
            <Form layout="vertical">
              <Form.Item label="背景颜色">
                <ColorField
                  value={style.background_color}
                  onChange={(v) => patchStyle({ background_color: v })}
                />
              </Form.Item>
              <Form.Item label="背景图片">
                <MediaPicker
                  kind="image"
                  projectId={projectId}
                  value={style.background_image ?? null}
                  onChange={(ref) => patchStyle({ background_image: ref })}
                />
              </Form.Item>
              {textEditor("title", "标题文字")}
              {textEditor("body", "正文文字")}
              {section.type === "responsive_reading" && textEditor("label", "启/应标识")}
              <Form.Item label="边距（英寸）">
                <InputNumber
                  min={0}
                  max={3}
                  step={0.1}
                  value={style.margin ?? undefined}
                  onChange={(v) => patchStyle({ margin: v ?? null })}
                  style={{ width: 120 }}
                />
              </Form.Item>
              <Button onClick={() => onSetTypeDefault(style)}>
                设为本类型默认（写入当前主题）
              </Button>
            </Form>
          ),
        },
      ]}
    />
  );
}
