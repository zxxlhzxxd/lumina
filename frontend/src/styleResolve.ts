/**
 * Client-side style cascade (mirrors backend/app/services/styling.py).
 * Built-in default -> per-type default -> Section.style
 */
import type {
  BlockLayout,
  EdgeInsets,
  Section,
  SectionStyle,
  TextBlockStyle,
  TextStyle,
} from "./types";

const CJK_FONT = "Microsoft YaHei";

const DEFAULT_STYLE: SectionStyle = {
  background_color: "#F7F3E9",
  body: {
    font_family: CJK_FONT,
    font_size: 32,
    color: "#2B2B2B",
    align: "center",
  },
  title: {
    font_family: CJK_FONT,
    font_size: 54,
    color: "#7A5C1E",
    bold: true,
    align: "center",
  },
  label: {
    font_family: CJK_FONT,
    font_size: 44,
    color: "#B8860B",
    bold: true,
  },
  margin: 0.8,
};

const TYPE_STYLES: Record<string, SectionStyle> = {
  hymn: {
    body: {
      font_family: CJK_FONT,
      font_size: 40,
      color: "#2B2B2B",
      bold: true,
      align: "center",
    },
  },
};

function mergeText(
  base: TextStyle | null | undefined,
  over: TextStyle | null | undefined
): TextStyle | null {
  if (!base) return over ? { ...over } : null;
  if (!over) return { ...base };
  const merged: TextStyle = { ...base };
  for (const key of Object.keys(over) as (keyof TextStyle)[]) {
    const value = over[key];
    if (value != null) {
      (merged as Record<string, unknown>)[key] = value;
    }
  }
  return merged;
}

function mergeInsets(
  base: EdgeInsets | null | undefined,
  over: EdgeInsets | null | undefined
): EdgeInsets | null {
  if (!base) return over ? { ...over } : null;
  if (!over) return { ...base };
  const result = { ...base };
  for (const side of ["top", "right", "bottom", "left"] as const) {
    if (over[side] != null) result[side] = over[side];
  }
  return result;
}

function mergeBlock(
  base: BlockLayout | null | undefined,
  over: BlockLayout | null | undefined
): BlockLayout | null {
  if (!base) return over ? { ...over, margin: over.margin ? { ...over.margin } : null } : null;
  if (!over) return { ...base, margin: base.margin ? { ...base.margin } : null };
  return {
    anchor: over.anchor ?? base.anchor,
    margin: mergeInsets(base.margin, over.margin),
  };
}

function mergeTextBlock(
  base: TextBlockStyle | null | undefined,
  over: TextBlockStyle | null | undefined
): TextBlockStyle | null {
  if (!base) {
    if (!over) return null;
    return {
      text: mergeText(null, over.text),
      layout: mergeBlock(null, over.layout),
    };
  }
  if (!over) {
    return {
      text: mergeText(null, base.text),
      layout: mergeBlock(null, base.layout),
    };
  }
  return {
    text: mergeText(base.text, over.text),
    layout: mergeBlock(base.layout, over.layout),
  };
}

function mergeStyle(
  base: SectionStyle | null | undefined,
  over: SectionStyle | null | undefined
): SectionStyle {
  const result: SectionStyle = base ? { ...base } : {};
  if (!over) return result;

  if (over.background_color != null) result.background_color = over.background_color;
  if (over.background_image != null) result.background_image = over.background_image;
  if (over.background_video != null) result.background_video = over.background_video;
  if (over.margin != null) result.margin = over.margin;
  result.body = mergeText(result.body, over.body);
  result.title = mergeText(result.title, over.title);
  result.label = mergeText(result.label, over.label);
  const blocks = { ...(result.blocks ?? {}) };
  for (const [key, value] of Object.entries(over.blocks ?? {})) {
    blocks[key] = mergeTextBlock(blocks[key], value) as TextBlockStyle;
  }
  result.blocks = blocks;
  return result;
}

export function resolveStyle(section: Section): SectionStyle {
  let effective: SectionStyle = {};
  effective = mergeStyle(effective, DEFAULT_STYLE);
  const typeStyle = TYPE_STYLES[section.type];
  effective = mergeStyle(effective, typeStyle);
  effective = mergeStyle(effective, section.style ?? undefined);
  return effective;
}

/** Serialize resolved style for SlideModel.style (API-compatible dict). */
export function resolvedStyleDict(section: Section): SectionStyle {
  return resolveStyle(section);
}
