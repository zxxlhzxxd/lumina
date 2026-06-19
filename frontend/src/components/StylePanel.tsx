import { Button, Form, InputNumber, Space } from "antd";
import type { Section, SectionStyle, TextStyle } from "../types";
import { FontEditor } from "./FontEditor";
import { MediaPicker } from "./MediaPicker";

interface Props {
  section: Section;
  projectId: string | null;
  effectiveStyle: SectionStyle;
  onChange: (patch: Partial<Section>) => void;
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
        <span style={{ color: "#6b6b6b", fontSize: 12 }}>（使用默认）</span>
      )}
    </Space>
  );
}

export function StylePanel({
  section,
  projectId,
  effectiveStyle,
  onChange,
}: Props) {
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
    const effective = (effectiveStyle[role] ?? {}) as TextStyle;
    return (
      <div className="style-workspace__text-role">
        <div className="style-workspace__role-label">{label}</div>
        <FontEditor
          value={ts}
          effectiveValue={effective}
          onChange={(patch) => patchText(role, patch)}
        />
      </div>
    );
  };

  return (
    <div className="style-workspace">
      <div className="style-workspace__header">样式（背景 / 字体 / 排版）</div>
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
      </Form>
    </div>
  );
}
