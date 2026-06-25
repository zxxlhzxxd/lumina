/**
 * Preview text block layout. Geometry mirrors backend/app/pptx/layout.py.
 */
import type { CSSProperties } from "react";
import type {
  BlockAnchor,
  BlockLayout,
  SectionStyle,
  SlideModel,
  SlideSize,
  TextStyle,
} from "./types";

export const SLIDE_H_IN = 7.5;
export const WIDE_SLIDE_W_IN = 13.333;
export const STANDARD_SLIDE_W_IN = 10;
export const TYPICAL_PREVIEW_WIDTH_PX = 320;
export const DEFAULT_MARGIN_IN = 0.8;
export const DEFAULT_FONT = "Microsoft YaHei";
export const DEFAULT_TEXT_COLOR = "#F5F5F5";
export const DEFAULT_ACCENT_COLOR = "#E0B34A";
export const DEFAULT_MUTED_COLOR = "#9FB3C8";

interface Rect {
  left: number;
  top: number;
  width: number;
  height: number;
}

interface BlockSpec {
  blockId: string;
  role: "title" | "body" | "label";
  text: string;
  rect: Rect;
  defaultAnchor: BlockAnchor;
  defaultPt: number;
  defaultBold?: boolean;
  defaultColor?: string;
  defaultAlign?: "left" | "center" | "right";
  vAlign?: "top" | "middle" | "bottom";
}

export interface TextBoxLayout {
  blockId: string;
  leftPct: number;
  topPct: number;
  widthPct: number;
  heightPct: number;
  role: "title" | "body" | "label";
  defaultPt: number;
  defaultBold?: boolean;
  defaultColor?: string;
  defaultAlign?: "left" | "center" | "right";
  vAlign?: "top" | "middle" | "bottom";
}

export function slideDimensions(slideSize: SlideSize): {
  width: number;
  height: number;
} {
  return {
    width: slideSize === "4:3" ? STANDARD_SLIDE_W_IN : WIDE_SLIDE_W_IN,
    height: SLIDE_H_IN,
  };
}

function legacyMargin(style: SectionStyle | null | undefined): number {
  const value = style?.margin;
  return typeof value === "number" && value > 0 ? value : DEFAULT_MARGIN_IN;
}

function blockOverride(
  style: SectionStyle | null | undefined,
  blockId: string
): BlockLayout | null {
  return style?.blocks?.[blockId]?.layout ?? null;
}

function fitMargins(start: number, end: number, total: number): [number, number] {
  const safeStart = Math.max(0, start);
  const safeEnd = Math.max(0, end);
  const maximum = Math.max(0, total - 0.01);
  const combined = safeStart + safeEnd;
  if (combined <= maximum || combined === 0) return [safeStart, safeEnd];
  const scale = maximum / combined;
  return [safeStart * scale, safeEnd * scale];
}

export function resolveBlockRect(
  base: Rect,
  blockId: string,
  defaultAnchor: BlockAnchor,
  style: SectionStyle | null | undefined,
  slideWidth: number,
  slideHeight: number
): Rect {
  const override = blockOverride(style, blockId);
  if (!override) return base;

  const fallback = legacyMargin(style);
  let top = override.margin?.top ?? fallback;
  let right = override.margin?.right ?? fallback;
  let bottom = override.margin?.bottom ?? fallback;
  let left = override.margin?.left ?? fallback;
  [left, right] = fitMargins(left, right, slideWidth);
  [top, bottom] = fitMargins(top, bottom, slideHeight);
  const availableWidth = Math.max(0.01, slideWidth - left - right);
  const availableHeight = Math.max(0.01, slideHeight - top - bottom);
  const width = Math.min(base.width, availableWidth);
  const height = Math.min(base.height, availableHeight);
  const anchor = override.anchor ?? defaultAnchor;
  const [vertical, horizontal] = anchor.split("_");

  let resolvedLeft = left + (availableWidth - width) / 2;
  if (horizontal === "left") resolvedLeft = left;
  if (horizontal === "right") resolvedLeft = slideWidth - right - width;

  let resolvedTop = top + (availableHeight - height) / 2;
  if (vertical === "top") resolvedTop = top;
  if (vertical === "bottom") resolvedTop = slideHeight - bottom - height;

  return { left: resolvedLeft, top: resolvedTop, width, height };
}

/** scale = preview container width / full slide pixel width */
export function computePreviewScale(
  measuredWidthPx: number,
  slideSize: SlideSize
): number {
  const widthPx = slideDimensions(slideSize).width * 96;
  if (measuredWidthPx <= 0) return TYPICAL_PREVIEW_WIDTH_PX / widthPx;
  return measuredWidthPx / widthPx;
}

export function ptToPx(pt: number, scale: number): number {
  return pt * (96 / 72) * scale;
}

const FONT_STACKS: Record<string, string> = {
  "Microsoft YaHei": '"Microsoft YaHei", "PingFang SC", "Heiti SC", sans-serif',
  SimHei: '"SimHei", "Heiti SC", "STHeiti", sans-serif',
  SimSun: '"SimSun", "Songti SC", "STSong", serif',
  KaiTi: '"KaiTi", "Kaiti SC", "STKaiti", serif',
  FangSong: '"FangSong", "STFangsong", "Songti SC", serif',
  Arial: 'Arial, "Helvetica Neue", "PingFang SC", sans-serif',
  "Times New Roman": '"Times New Roman", Georgia, "Songti SC", serif',
};

function cssFontFamily(name: string): string {
  const stack = FONT_STACKS[name];
  if (stack) return stack;
  const quoted = name.includes(" ") ? `"${name}"` : name;
  return `${quoted}, sans-serif`;
}

function roleStyle(
  slideStyle: SectionStyle | null | undefined,
  role: "title" | "body" | "label",
  blockId: string,
  defaults: {
    pt: number;
    bold?: boolean;
    color?: string;
    align?: "left" | "center" | "right";
  },
  scale: number
): CSSProperties {
  const roleText = (slideStyle?.[role] ?? {}) as TextStyle;
  const blockText = slideStyle?.blocks?.[blockId]?.text ?? {};
  const ts = { ...roleText, ...blockText } as TextStyle;
  const pt = ts.font_size ?? defaults.pt;
  const css: CSSProperties = {
    fontSize: ptToPx(pt, scale),
    fontWeight: ts.bold != null ? (ts.bold ? 700 : 400) : defaults.bold ? 700 : 400,
    fontStyle: ts.italic ? "italic" : "normal",
    textDecoration: ts.underline ? "underline" : "none",
    color: ts.color ?? defaults.color ?? DEFAULT_TEXT_COLOR,
    textAlign: ts.align ?? defaults.align ?? "center",
    fontFamily: cssFontFamily(ts.font_family ?? DEFAULT_FONT),
  };
  if (ts.line_spacing) css.lineHeight = ts.line_spacing;
  return css;
}

export function textRunStyle(
  slideStyle: SectionStyle | null | undefined,
  role: "title" | "body" | "label",
  blockId: string
): CSSProperties {
  const ts = {
    ...((slideStyle?.[role] ?? {}) as TextStyle),
    ...(slideStyle?.blocks?.[blockId]?.text ?? {}),
  };
  return ts.highlight_color ? { backgroundColor: ts.highlight_color } : {};
}

function vAlignStyle(v: TextBoxLayout["vAlign"]): CSSProperties {
  if (v === "top") {
    return { display: "flex", flexDirection: "column", justifyContent: "flex-start" };
  }
  if (v === "bottom") {
    return { display: "flex", flexDirection: "column", justifyContent: "flex-end" };
  }
  return { display: "flex", flexDirection: "column", justifyContent: "center" };
}

export function boxStyle(
  box: TextBoxLayout,
  slideStyle: SectionStyle | null | undefined,
  scale: number
): CSSProperties {
  const verticalAlign =
    slideStyle?.blocks?.[box.blockId]?.text?.vertical_align ?? box.vAlign;
  return {
    left: `${box.leftPct}%`,
    top: `${box.topPct}%`,
    width: `${box.widthPct}%`,
    height: `${box.heightPct}%`,
    ...vAlignStyle(verticalAlign),
    ...roleStyle(
      slideStyle,
      box.role,
      box.blockId,
      {
        pt: box.defaultPt,
        bold: box.defaultBold,
        color: box.defaultColor,
        align: box.defaultAlign,
      },
      scale
    ),
  };
}

function blockSpecs(
  slide: SlideModel,
  slideWidth: number,
  slideHeight: number
): BlockSpec[] {
  const style = slide.style;
  const margin = legacyMargin(style);
  const contentWidth = Math.max(0.01, slideWidth - 2 * margin);
  const blocks: BlockSpec[] = [];

  if (["cover", "scripture_title", "hymn_title"].includes(slide.kind)) {
    blocks.push({
      blockId: "title",
      role: "title",
      text: slide.title || "（未填写标题）",
      rect: { left: margin, top: 2.4, width: contentWidth, height: 2 },
      defaultAnchor: "middle_center",
      defaultPt: 54,
      defaultBold: true,
      defaultAlign: "center",
      vAlign: "middle",
    });
    if (slide.subtitle) {
      blocks.push({
        blockId: "subtitle",
        role: "body",
        text: slide.subtitle,
        rect: { left: margin, top: 4.5, width: contentWidth, height: 1.2 },
        defaultAnchor: "bottom_center",
        defaultPt: 28,
        defaultColor: DEFAULT_MUTED_COLOR,
        defaultAlign: "center",
        vAlign: "middle",
      });
    }
    if (slide.body) {
      blocks.push({
        blockId: "extra",
        role: "body",
        text: slide.body,
        rect: { left: margin, top: 5.7, width: contentWidth, height: 1 },
        defaultAnchor: "bottom_center",
        defaultPt: 22,
        defaultColor: DEFAULT_MUTED_COLOR,
        defaultAlign: "center",
        vAlign: "middle",
      });
    }
    return blocks;
  }

  if (slide.kind === "responsive_verse") {
    if (slide.label) {
      blocks.push({
        blockId: "label",
        role: "label",
        text: slide.label,
        rect: { left: margin, top: 0.5, width: 1.4, height: 1.4 },
        defaultAnchor: "top_left",
        defaultPt: 44,
        defaultBold: true,
        defaultColor: DEFAULT_ACCENT_COLOR,
        defaultAlign: "left",
        vAlign: "top",
      });
    }
    blocks.push({
      blockId: "body",
      role: "body",
      text: slide.body || "",
      rect: { left: margin, top: 1.6, width: contentWidth, height: 4.6 },
      defaultAnchor: "middle_center",
      defaultPt: 40,
      defaultBold: true,
      defaultAlign: "center",
      vAlign: "middle",
    });
    if (slide.reference) {
      blocks.push({
        blockId: "reference",
        role: "body",
        text: slide.reference,
        rect: { left: margin, top: 6.5, width: contentWidth, height: 0.7 },
        defaultAnchor: "bottom_center",
        defaultPt: 20,
        defaultColor: DEFAULT_MUTED_COLOR,
        defaultAlign: "center",
        vAlign: "bottom",
      });
    }
    return blocks;
  }

  let bodyTop = 0.8;
  if (slide.title) {
    blocks.push({
      blockId: "title",
      role: "title",
      text: slide.title,
      rect: { left: margin, top: 0.6, width: contentWidth, height: 1.1 },
      defaultAnchor: "top_center",
      defaultPt: 36,
      defaultBold: true,
      defaultColor: DEFAULT_ACCENT_COLOR,
      defaultAlign: "center",
      vAlign: "top",
    });
    bodyTop = 1.9;
  }
  blocks.push({
    blockId: "body",
    role: "body",
    text: slide.body || "",
    rect: {
      left: margin,
      top: bodyTop,
      width: contentWidth,
      height: Math.max(0.01, slideHeight - bodyTop - 0.9),
    },
    defaultAnchor: "middle_center",
    defaultPt: slide.section_type === "hymn" ? 40 : 32,
    defaultBold: slide.section_type === "hymn",
    defaultAlign: "center",
    vAlign: "middle",
  });
  if (slide.reference) {
    blocks.push({
      blockId: "reference",
      role: "body",
      text: slide.reference,
      rect: { left: margin, top: slideHeight - 0.8, width: contentWidth, height: 0.6 },
      defaultAnchor: "bottom_center",
      defaultPt: 18,
      defaultColor: DEFAULT_MUTED_COLOR,
      defaultAlign: "center",
      vAlign: "bottom",
    });
  }
  return blocks;
}

export function slideTextBoxes(
  slide: SlideModel,
  slideSize: SlideSize
): Array<TextBoxLayout & { text: string }> {
  const { width, height } = slideDimensions(slideSize);
  return blockSpecs(slide, width, height).map((block) => {
    const rect = resolveBlockRect(
      block.rect,
      block.blockId,
      block.defaultAnchor,
      slide.style,
      width,
      height
    );
    return {
      ...block,
      leftPct: (rect.left / width) * 100,
      topPct: (rect.top / height) * 100,
      widthPct: (rect.width / width) * 100,
      heightPct: (rect.height / height) * 100,
    };
  });
}
