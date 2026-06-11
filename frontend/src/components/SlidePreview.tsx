import { useEffect, useState } from "react";
import { mediaUrl } from "../api";
import type { SlideModel, TextStyle } from "../types";

// Approximate (HTML/CSS) preview of a generated slide. Mirrors the PPTX layout
// and the resolved theme/section style closely enough to be useful;
// high-fidelity rendering is a later phase.

// Slides are ~13.3in wide; the preview card is ~170px. Scale point sizes down so
// the relative typography matches what the export will produce.
const FONT_SCALE = 0.34;

function textCss(ts?: TextStyle | null, fallbackPx?: number): React.CSSProperties {
  const css: React.CSSProperties = {};
  if (ts?.font_size) css.fontSize = Math.max(8, ts.font_size * FONT_SCALE);
  else if (fallbackPx) css.fontSize = fallbackPx;
  if (ts?.color) css.color = ts.color;
  if (ts?.bold != null) css.fontWeight = ts.bold ? 700 : 400;
  if (ts?.align) css.textAlign = ts.align;
  if (ts?.font_family) css.fontFamily = ts.font_family;
  return css;
}

export function SlidePreview({
  slide,
  projectId,
}: {
  slide: SlideModel;
  projectId?: string | null;
}) {
  const isTitle =
    slide.kind === "cover" ||
    slide.kind === "scripture_title" ||
    slide.kind === "hymn_title";
  const big = slide.kind === "responsive_verse" || slide.section_type === "hymn";
  const style = slide.style ?? null;

  const [bgUrl, setBgUrl] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    const ref = style?.background_image;
    if (ref && projectId) {
      mediaUrl(projectId, ref)
        .then((u) => alive && setBgUrl(u))
        .catch(() => alive && setBgUrl(null));
    } else {
      setBgUrl(null);
    }
    return () => {
      alive = false;
    };
  }, [style?.background_image, projectId]);

  const cardStyle: React.CSSProperties = {};
  if (style?.background_color) cardStyle.background = style.background_color;
  if (bgUrl) {
    cardStyle.backgroundImage = `url("${bgUrl}")`;
    cardStyle.backgroundSize = "cover";
    cardStyle.backgroundPosition = "center";
  }

  return (
    <div className={`slide-card${big ? " big" : ""}`} style={cardStyle}>
      {slide.label && (
        <div className="label" style={textCss(style?.label)}>
          {slide.label}
        </div>
      )}
      {isTitle ? (
        <>
          <div className="title" style={textCss(style?.title)}>
            {slide.title || "（未填写标题）"}
          </div>
          {slide.subtitle && (
            <div className="subtitle" style={textCss(style?.body)}>
              {slide.subtitle}
            </div>
          )}
          {slide.body && (
            <div className="subtitle" style={textCss(style?.body)}>
              {slide.body}
            </div>
          )}
        </>
      ) : (
        <>
          {slide.title && (
            <div className="title" style={{ marginBottom: 6, ...textCss(style?.title) }}>
              {slide.title}
            </div>
          )}
          {slide.body && (
            <div className="body" style={textCss(style?.body)}>
              {slide.body}
            </div>
          )}
          {slide.reference && (
            <div className="reference" style={textCss(style?.body)}>
              {slide.reference}
            </div>
          )}
        </>
      )}
    </div>
  );
}
