import { Button, Form, InputNumber, Segmented, Select, Space, Switch } from "antd";
import type { Section, SectionStyle, TextStyle } from "../types";
import { MediaPicker } from "./MediaPicker";

interface Props {
  section: Section;
  projectId: string | null;
  effectiveStyle: SectionStyle;
  onChange: (patch: Partial<Section>) => void;
  onSetTypeDefault: (style: SectionStyle) => void;
}

type TextRole = "body" | "title" | "label";

const FONT_OPTIONS = [
  { label: "继承主题", value: "" },
  { label: "微软雅黑", value: "Microsoft YaHei" },
  { label: "宋体", value: "SimSun" },
  { label: "黑体", value: "SimHei" },
  { label: "楷体", value: "KaiTi" },
  { label: "仿宋", value: "FangSong" },
  { label: "Arial", value: "Arial" },
  { label: "Times New Roman", value: "Times New Roman" },
];

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

function inheritFontSizeHint(
  role: TextRole,
  sectionStyle: SectionStyle,
  effectiveStyle: SectionStyle
): string {
  const override = sectionStyle[role]?.font_size;
  if (override != null) return "";
  const inherited = effectiveStyle[role]?.font_size;
  if (inherited == null) return "";
  return `继承主题：${inherited}pt`;
}

export function StylePanel({
  section,
  projectId,
  effectiveStyle,
  onChange,
  onSetTypeDefault,
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
    const hint = inheritFontSizeHint(role, style, effectiveStyle);
    return (
      <div className="style-workspace__text-role">
        <div className="style-workspace__role-label">{label}</div>
        <Space wrap size={10}>
          <Select
            placeholder="字体"
            style={{ width: 140 }}
            value={ts.font_family ?? ""}
            options={FONT_OPTIONS}
            onChange={(v) => patchText(role, { font_family: v || null })}
          />
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
        {hint && (
          <div style={{ color: "#6b6b6b", fontSize: 12, marginTop: 4 }}>{hint}</div>
        )}
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
        <Button onClick={() => onSetTypeDefault(style)}>
          设为本类型默认（写入当前主题）
        </Button>
      </Form>
    </div>
  );
}
