import type { SlideModel } from "../types";

// Approximate (HTML/CSS) preview of a generated slide. Mirrors the PPTX layout
// closely enough to be useful; high-fidelity rendering is a later phase.
export function SlidePreview({ slide }: { slide: SlideModel }) {
  const isTitle =
    slide.kind === "cover" ||
    slide.kind === "scripture_title" ||
    slide.kind === "hymn_title";
  const big = slide.kind === "responsive_verse" || slide.section_type === "hymn";

  return (
    <div className={`slide-card${big ? " big" : ""}`}>
      {slide.label && <div className="label">{slide.label}</div>}
      {isTitle ? (
        <>
          <div className="title">{slide.title || "（未填写标题）"}</div>
          {slide.subtitle && <div className="subtitle">{slide.subtitle}</div>}
          {slide.body && <div className="subtitle">{slide.body}</div>}
        </>
      ) : (
        <>
          {slide.title && <div className="title" style={{ marginBottom: 6 }}>{slide.title}</div>}
          {slide.body && <div className="body">{slide.body}</div>}
          {slide.reference && <div className="reference">{slide.reference}</div>}
        </>
      )}
    </div>
  );
}
