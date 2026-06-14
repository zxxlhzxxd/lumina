/**
 * Preview layout constants aligned with backend/app/pptx/builder.py.
 * Positions are in inches on a 13.333" × 7.5" wide slide.
 */
import type { CSSProperties } from "react";
import type { SectionStyle, SlideModel, TextStyle } from "./types";

export const SLIDE_W_IN = 13.333;
export const SLIDE_H_IN = 7.5;
/** Full slide width in CSS pixels at 96dpi (matches PPTX 13.333" wide layout). */
export const SLIDE_WIDTH_PX = SLIDE_W_IN * 96;
/** Typical preview card width used when layout is not yet measured. */
export const TYPICAL_PREVIEW_WIDTH_PX = 320;
export const DEFAULT_MARGIN_IN = 0.8;
export const DEFAULT_FONT = "Microsoft YaHei";

export const DEFAULT_TEXT_COLOR = "#F5F5F5";
export const DEFAULT_ACCENT_COLOR = "#E0B34A";
export const DEFAULT_MUTED_COLOR = "#9FB3C8";

export interface TextBoxLayout {
  leftPct: number;
  topPct: number;
  widthPct: number;
  heightPct: number;
  role: "title" | "body" | "label";
  /** Builder default font size in pt when style has no override. */
  defaultPt: number;
  defaultBold?: boolean;
  defaultColor?: string;
  defaultAlign?: "left" | "center" | "right";
  /** Vertical alignment within the box. */
  vAlign?: "top" | "middle" | "bottom";
}

function marginIn(style: SectionStyle | null | undefined): number {
  const m = style?.margin;
  if (typeof m === "number" && m > 0) return m;
  return DEFAULT_MARGIN_IN;
}

function contentWidthPct(style: SectionStyle | null | undefined): number {
  const mx = marginIn(style);
  return ((SLIDE_W_IN - 2 * mx) / SLIDE_W_IN) * 100;
}

function leftPct(style: SectionStyle | null | undefined): number {
  return (marginIn(style) / SLIDE_W_IN) * 100;
}

function inToTopPct(inches: number): number {
  return (inches / SLIDE_H_IN) * 100;
}

function inToHeightPct(inches: number): number {
  return (inches / SLIDE_H_IN) * 100;
}

function inToWidthPct(inches: number): number {
  return (inches / SLIDE_W_IN) * 100;
}

/** scale = preview container width / full slide pixel width */
export function computePreviewScale(measuredWidthPx: number): number {
  if (measuredWidthPx <= 0) return TYPICAL_PREVIEW_WIDTH_PX / SLIDE_WIDTH_PX;
  return measuredWidthPx / SLIDE_WIDTH_PX;
}

/** Convert PowerPoint pt to CSS px at the given preview scale. */
export function ptToPx(pt: number, scale: number): number {
  return pt * (96 / 72) * scale;
}

export /**
 * Map a configured font name to a cross-platform CSS font stack.
 *
 * The font picker exposes Windows-oriented Chinese fonts (e.g. "Microsoft YaHei",
 * "SimSun") that don't exist on macOS, while Latin fonts (Arial / Times New Roman)
 * carry no Chinese glyphs. Without fallbacks every choice silently collapses to the
 * same system Chinese font, so font changes appear to do nothing in the preview.
 * Each stack therefore includes equivalents available on macOS so switching fonts is
 * actually visible.
 */
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
  defaults: {
    pt: number;
    bold?: boolean;
    color?: string;
    align?: "left" | "center" | "right";
    font?: string;
  },
  scale: number
): CSSProperties {
  const ts = (slideStyle?.[role] ?? {}) as TextStyle;
  const pt = ts.font_size ?? defaults.pt;
  const css: CSSProperties = {
    fontSize: ptToPx(pt, scale),
    fontWeight: ts.bold != null ? (ts.bold ? 700 : 400) : defaults.bold ? 700 : 400,
    color: ts.color ?? defaults.color ?? DEFAULT_TEXT_COLOR,
    textAlign: ts.align ?? defaults.align ?? "center",
    fontFamily: cssFontFamily(ts.font_family ?? defaults.font ?? DEFAULT_FONT),
  };
  if (ts.line_spacing) css.lineHeight = ts.line_spacing;
  return css;
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
  return {
    left: `${box.leftPct}%`,
    top: `${box.topPct}%`,
    width: `${box.widthPct}%`,
    height: `${box.heightPct}%`,
    ...vAlignStyle(box.vAlign),
    ...roleStyle(slideStyle, box.role, {
      pt: box.defaultPt,
      bold: box.defaultBold,
      color: box.defaultColor,
      align: box.defaultAlign,
    }, scale),
  };
}

/** Text boxes for a slide, mirroring PptxBuilder layout. */
export function slideTextBoxes(slide: SlideModel): Array<TextBoxLayout & { text: string }> {
  const style = slide.style ?? null;
  const cw = contentWidthPct(style);
  const left = leftPct(style);
  const kind = slide.kind;

  if (kind === "cover" || kind === "scripture_title" || kind === "hymn_title") {
    const boxes: Array<TextBoxLayout & { text: string }> = [
      {
        leftPct: left,
        topPct: inToTopPct(2.4),
        widthPct: cw,
        heightPct: inToHeightPct(2.0),
        role: "title",
        defaultPt: 54,
        defaultBold: true,
        defaultAlign: "center",
        vAlign: "middle",
        text: slide.title || "（未填写标题）",
      },
    ];
    if (slide.subtitle) {
      boxes.push({
        leftPct: left,
        topPct: inToTopPct(4.5),
        widthPct: cw,
        heightPct: inToHeightPct(1.2),
        role: "body",
        defaultPt: 28,
        defaultColor: DEFAULT_MUTED_COLOR,
        defaultAlign: "center",
        vAlign: "middle",
        text: slide.subtitle,
      });
    }
    if (slide.body) {
      boxes.push({
        leftPct: left,
        topPct: inToTopPct(5.7),
        widthPct: cw,
        heightPct: inToHeightPct(1.0),
        role: "body",
        defaultPt: 22,
        defaultColor: DEFAULT_MUTED_COLOR,
        defaultAlign: "center",
        vAlign: "middle",
        text: slide.body,
      });
    }
    return boxes;
  }

  if (kind === "responsive_verse") {
    const boxes: Array<TextBoxLayout & { text: string }> = [];
    if (slide.label) {
      boxes.push({
        leftPct: left,
        topPct: inToTopPct(0.5),
        widthPct: inToWidthPct(1.4),
        heightPct: inToHeightPct(1.4),
        role: "label",
        defaultPt: 44,
        defaultBold: true,
        defaultColor: DEFAULT_ACCENT_COLOR,
        defaultAlign: "left",
        vAlign: "top",
        text: slide.label,
      });
    }
    boxes.push({
      leftPct: left,
      topPct: inToTopPct(1.6),
      widthPct: cw,
      heightPct: inToHeightPct(4.6),
      role: "body",
      defaultPt: 40,
      defaultBold: true,
      defaultAlign: "center",
      vAlign: "middle",
      text: slide.body || "",
    });
    if (slide.reference) {
      boxes.push({
        leftPct: left,
        topPct: inToTopPct(6.5),
        widthPct: cw,
        heightPct: inToHeightPct(0.7),
        role: "body",
        defaultPt: 20,
        defaultColor: DEFAULT_MUTED_COLOR,
        defaultAlign: "center",
        vAlign: "bottom",
        text: slide.reference,
      });
    }
    return boxes;
  }

  // body / liturgy / hymn / announcement / etc.
  const bodyDefaultPt = slide.section_type === "hymn" ? 40 : 32;
  const bodyDefaultBold = slide.section_type === "hymn";
  const boxes: Array<TextBoxLayout & { text: string }> = [];
  let bodyTopIn = 0.8;

  if (slide.title) {
    boxes.push({
      leftPct: left,
      topPct: inToTopPct(0.6),
      widthPct: cw,
      heightPct: inToHeightPct(1.1),
      role: "title",
      defaultPt: 36,
      defaultBold: true,
      defaultColor: DEFAULT_ACCENT_COLOR,
      defaultAlign: "center",
      vAlign: "top",
      text: slide.title,
    });
    bodyTopIn = 1.9;
  }

  const bodyHeightIn = SLIDE_H_IN - bodyTopIn - 0.9;
  boxes.push({
    leftPct: left,
    topPct: inToTopPct(bodyTopIn),
    widthPct: cw,
    heightPct: inToHeightPct(bodyHeightIn),
    role: "body",
    defaultPt: bodyDefaultPt,
    defaultBold: bodyDefaultBold,
    defaultAlign: "center",
    vAlign: "middle",
    text: slide.body || "",
  });

  if (slide.reference) {
    boxes.push({
      leftPct: left,
      topPct: inToTopPct(SLIDE_H_IN - 0.8),
      widthPct: cw,
      heightPct: inToHeightPct(0.6),
      role: "body",
      defaultPt: 18,
      defaultColor: DEFAULT_MUTED_COLOR,
      defaultAlign: "center",
      vAlign: "bottom",
      text: slide.reference,
    });
  }

  return boxes;
}
