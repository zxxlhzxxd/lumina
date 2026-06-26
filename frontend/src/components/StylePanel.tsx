import { Button, Form, Space } from "antd";
import type {
  Section,
  SectionStyle,
  SectionType,
  TextBlockStyle,
  TextStyle,
} from "../types";
import { FontEditor } from "./FontEditor";
import { MediaPicker } from "./MediaPicker";
import { mergeTextStyle } from "../styleResolve";

interface Props {
  section: Section;
  projectId: string | null;
  effectiveStyle: SectionStyle;
  onChange: (patch: Partial<Section>) => void;
  onBlockLayoutOpenChange?: (blockId: string, open: boolean) => void;
}

type TextRole = "body" | "title" | "label";
type BlockId = "title" | "subtitle" | "body" | "label" | "reference" | "extra";

const BLOCKS_BY_SECTION: Record<
  SectionType,
  Array<{ id: BlockId; role: TextRole; label: string }>
> = {
  cover: [
    { id: "title", role: "title", label: "标题文字" },
    { id: "subtitle", role: "body", label: "副标题文字" },
    { id: "extra", role: "body", label: "附加信息文字" },
  ],
  responsive_reading: [
    { id: "label", role: "label", label: "启/应标识" },
    { id: "body", role: "body", label: "正文文字" },
    { id: "reference", role: "body", label: "经文出处" },
  ],
  scripture: [
    { id: "title", role: "title", label: "标题文字" },
    { id: "subtitle", role: "body", label: "副标题文字" },
    { id: "body", role: "body", label: "正文文字" },
    { id: "reference", role: "body", label: "经文出处" },
  ],
  hymn: [
    { id: "title", role: "title", label: "标题文字" },
    { id: "subtitle", role: "body", label: "副标题文字" },
    { id: "body", role: "body", label: "正文文字" },
  ],
  liturgy_text: [
    { id: "title", role: "title", label: "标题文字" },
    { id: "body", role: "body", label: "正文文字" },
  ],
  announcement: [
    { id: "title", role: "title", label: "标题文字" },
    { id: "body", role: "body", label: "正文文字" },
  ],
  media: [
    { id: "title", role: "title", label: "标题文字" },
    { id: "body", role: "body", label: "正文文字" },
  ],
};

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
  onBlockLayoutOpenChange,
}: Props) {
  const style: SectionStyle = section.style ?? {};

  const patchStyle = (partial: Partial<SectionStyle>) => {
    onChange({ style: { ...style, ...partial } } as Partial<Section>);
  };

  const patchBlock = (blockId: BlockId, partial: Partial<TextBlockStyle>) => {
    const blocks = style.blocks ?? {};
    const current = blocks[blockId] ?? {};
    patchStyle({
      blocks: {
        ...blocks,
        [blockId]: { ...current, ...partial },
      },
    });
  };

  const textEditor = (blockId: BlockId, role: TextRole, label: string) => {
    const block = style.blocks?.[blockId] ?? {};
    const effectiveBlock = effectiveStyle.blocks?.[blockId] ?? {};
    const ts = block.text ?? {};
    const effective =
      mergeTextStyle((effectiveStyle[role] ?? {}) as TextStyle, effectiveBlock.text) ??
      {};
    return (
      <div className="style-workspace__text-role">
        <div className="style-workspace__role-label">{label}</div>
        <FontEditor
          value={ts}
          effectiveValue={effective}
          layoutValue={block.layout}
          fallbackMargin={effectiveStyle.margin ?? 0.8}
          onChange={(patch) =>
            patchBlock(blockId, { text: { ...ts, ...patch } })
          }
          onLayoutChange={(layout) => patchBlock(blockId, { layout })}
          onLayoutOpenChange={(open) => onBlockLayoutOpenChange?.(blockId, open)}
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
        {BLOCKS_BY_SECTION[section.type].map((block) => (
          <div key={block.id}>
            {textEditor(block.id, block.role, block.label)}
          </div>
        ))}
      </Form>
    </div>
  );
}
