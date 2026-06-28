import {
  Button,
  ColorPicker,
  Divider,
  InputNumber,
  Popover,
  Select,
  Space,
  Tooltip,
} from "antd";
import {
  AlignCenterOutlined,
  AlignLeftOutlined,
  AlignRightOutlined,
  BgColorsOutlined,
  BoldOutlined,
  ClearOutlined,
  FontColorsOutlined,
  ItalicOutlined,
  LayoutOutlined,
  UnderlineOutlined,
  VerticalAlignBottomOutlined,
  VerticalAlignMiddleOutlined,
  VerticalAlignTopOutlined,
} from "@ant-design/icons";
import type { BlockLayout, TextStyle } from "../types";
import {
  BlockLayoutEditor,
  type BlockAnchorMode,
} from "./BlockLayoutEditor";

interface Props {
  value: TextStyle;
  effectiveValue: TextStyle;
  layoutValue: BlockLayout | null | undefined;
  fallbackMargin: number;
  blockAnchorMode?: BlockAnchorMode;
  onChange: (patch: Partial<TextStyle>) => void;
  onLayoutChange: (layout: BlockLayout | null) => void;
  onLayoutOpenChange?: (open: boolean) => void;
}

const FONT_OPTIONS = [
  { label: "微软雅黑", value: "Microsoft YaHei" },
  { label: "宋体", value: "SimSun" },
  { label: "黑体", value: "SimHei" },
  { label: "楷体", value: "KaiTi" },
  { label: "仿宋", value: "FangSong" },
  { label: "Arial", value: "Arial" },
  { label: "Times New Roman", value: "Times New Roman" },
];

const RESET_STYLE: Partial<TextStyle> = {
  font_family: null,
  font_size: null,
  color: null,
  bold: null,
  italic: null,
  underline: null,
  highlight_color: null,
  align: null,
  vertical_align: null,
};

const EDITABLE_STYLE_KEYS: Array<keyof TextStyle> = [
  "font_family",
  "font_size",
  "color",
  "bold",
  "italic",
  "underline",
  "highlight_color",
  "align",
  "vertical_align",
];

type BooleanStyleKey = "bold" | "italic" | "underline";
type Align = NonNullable<TextStyle["align"]>;
type VerticalAlign = NonNullable<TextStyle["vertical_align"]>;

function FormatButton({
  title,
  active,
  icon,
  onClick,
}: {
  title: string;
  active: boolean;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <Tooltip title={title}>
      <Button
        type={active ? "primary" : "text"}
        className="font-editor__icon-button"
        icon={icon}
        aria-label={title}
        aria-pressed={active}
        onClick={onClick}
      />
    </Tooltip>
  );
}

function ColorButton({
  title,
  icon,
  value,
  fallback,
  onChange,
}: {
  title: string;
  icon: React.ReactNode;
  value?: string | null;
  fallback: string;
  onChange: (color: string | null) => void;
}) {
  const displayColor = value || fallback;
  return (
    <ColorPicker
      value={displayColor}
      disabledAlpha
      allowClear
      onChange={(color) =>
        onChange(color.cleared ? null : color.toHexString().toUpperCase())
      }
      onClear={() => onChange(null)}
    >
      <Tooltip title={title}>
        <Button
          type="text"
          className="font-editor__color-button"
          aria-label={title}
        >
          {icon}
          <span
            className="font-editor__color-line"
            style={{ backgroundColor: displayColor }}
          />
        </Button>
      </Tooltip>
    </ColorPicker>
  );
}

export function FontEditor({
  value,
  effectiveValue,
  layoutValue,
  fallbackMargin,
  blockAnchorMode,
  onChange,
  onLayoutChange,
  onLayoutOpenChange,
}: Props) {
  const toggle = (key: BooleanStyleKey) => {
    onChange({ [key]: effectiveValue[key] !== true } as Partial<TextStyle>);
  };

  const setAlign = (align: Align) => {
    onChange({ align });
  };

  const hasOverride = EDITABLE_STYLE_KEYS.some((key) => value[key] != null);
  const effectiveAlign = effectiveValue.align ?? "center";
  const effectiveVerticalAlign = effectiveValue.vertical_align;

  return (
    <div className="font-editor">
      <div className="font-editor__toolbar">
        <Select
          aria-label="字体"
          className="font-editor__font-family"
          value={value.font_family ?? effectiveValue.font_family ?? undefined}
          options={FONT_OPTIONS}
          showSearch
          optionFilterProp="label"
          allowClear
          onChange={(font) => onChange({ font_family: font ?? null })}
        />
        <InputNumber
          aria-label="字号"
          className="font-editor__font-size"
          min={8}
          max={120}
          value={value.font_size ?? effectiveValue.font_size ?? undefined}
          onChange={(size) => onChange({ font_size: size ?? null })}
        />

        <Divider type="vertical" />

        <Space.Compact>
          <FormatButton
            title="加粗"
            active={effectiveValue.bold === true}
            icon={<BoldOutlined />}
            onClick={() => toggle("bold")}
          />
          <FormatButton
            title="斜体"
            active={effectiveValue.italic === true}
            icon={<ItalicOutlined />}
            onClick={() => toggle("italic")}
          />
          <FormatButton
            title="下划线"
            active={effectiveValue.underline === true}
            icon={<UnderlineOutlined />}
            onClick={() => toggle("underline")}
          />
        </Space.Compact>

        <Divider type="vertical" />

        <Space.Compact>
          <ColorButton
            title="文字高亮"
            icon={<BgColorsOutlined />}
            value={value.highlight_color ?? effectiveValue.highlight_color}
            fallback="#FFF200"
            onChange={(highlight_color) => onChange({ highlight_color })}
          />
          <ColorButton
            title="字体颜色"
            icon={<FontColorsOutlined />}
            value={value.color ?? effectiveValue.color}
            fallback="#000000"
            onChange={(color) => onChange({ color })}
          />
        </Space.Compact>

        <Divider type="vertical" />

        <Space.Compact>
          <FormatButton
            title="左对齐"
            active={effectiveAlign === "left"}
            icon={<AlignLeftOutlined />}
            onClick={() => setAlign("left")}
          />
          <FormatButton
            title="居中"
            active={effectiveAlign === "center"}
            icon={<AlignCenterOutlined />}
            onClick={() => setAlign("center")}
          />
          <FormatButton
            title="右对齐"
            active={effectiveAlign === "right"}
            icon={<AlignRightOutlined />}
            onClick={() => setAlign("right")}
          />
        </Space.Compact>

        <Divider type="vertical" />

        <Space.Compact>
          <FormatButton
            title="文字靠上"
            active={effectiveVerticalAlign === "top"}
            icon={<VerticalAlignTopOutlined />}
            onClick={() => onChange({ vertical_align: "top" as VerticalAlign })}
          />
          <FormatButton
            title="文字垂直居中"
            active={effectiveVerticalAlign === "middle"}
            icon={<VerticalAlignMiddleOutlined />}
            onClick={() => onChange({ vertical_align: "middle" as VerticalAlign })}
          />
          <FormatButton
            title="文字靠下"
            active={effectiveVerticalAlign === "bottom"}
            icon={<VerticalAlignBottomOutlined />}
            onClick={() => onChange({ vertical_align: "bottom" as VerticalAlign })}
          />
        </Space.Compact>

        <Divider type="vertical" />

        <Popover
          trigger="click"
          placement="bottomRight"
          arrow={false}
          overlayClassName="block-layout-popover"
          onOpenChange={onLayoutOpenChange}
          content={
            <BlockLayoutEditor
              value={layoutValue}
              fallbackMargin={fallbackMargin}
              anchorMode={blockAnchorMode}
              onChange={onLayoutChange}
            />
          }
        >
          <Tooltip title="设置文字块布局">
            <Button
              type={layoutValue ? "primary" : "text"}
              className="font-editor__icon-button"
              icon={<LayoutOutlined />}
              aria-label="设置文字块布局"
              aria-pressed={Boolean(layoutValue)}
            />
          </Tooltip>
        </Popover>

        <Divider type="vertical" />

        <Tooltip title="清除本级字体格式，恢复默认样式">
          <Button
            type="text"
            className="font-editor__icon-button"
            icon={<ClearOutlined />}
            aria-label="恢复默认字体样式"
            disabled={!hasOverride}
            onClick={() => onChange(RESET_STYLE)}
          />
        </Tooltip>
      </div>
    </div>
  );
}
