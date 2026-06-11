/**
 * Client-side style cascade (mirrors backend/app/services/styling.py).
 * Theme.default_style -> Theme.type_styles[type] -> Section.style
 */
import type { Section, SectionStyle, TextStyle, Theme } from "./types";

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
  return result;
}

export function resolveStyle(theme: Theme | null | undefined, section: Section): SectionStyle {
  let effective: SectionStyle = {};
  if (theme) {
    effective = mergeStyle(effective, theme.default_style ?? undefined);
    const typeStyle = theme.type_styles?.[section.type];
    effective = mergeStyle(effective, typeStyle);
  }
  effective = mergeStyle(effective, section.style ?? undefined);
  return effective;
}

/** Serialize resolved style for SlideModel.style (API-compatible dict). */
export function resolvedStyleDict(
  theme: Theme | null | undefined,
  section: Section
): SectionStyle {
  return resolveStyle(theme, section);
}
