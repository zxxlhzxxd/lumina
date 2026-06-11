import { useEffect, useRef, useState, type CSSProperties } from "react";
import { mediaUrl } from "../api";
import {
  boxStyle,
  computePreviewScale,
  slideTextBoxes,
} from "../previewLayout";
import type { SlideModel } from "../types";

export function SlidePreview({
  slide,
  projectId,
}: {
  slide: SlideModel;
  projectId?: string | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
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

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setScale(computePreviewScale(el.clientWidth));
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const cardStyle: CSSProperties = {};
  if (style?.background_color) cardStyle.background = style.background_color;
  if (bgUrl) {
    cardStyle.backgroundImage = `url("${bgUrl}")`;
    cardStyle.backgroundSize = "cover";
    cardStyle.backgroundPosition = "center";
  }

  const boxes = slideTextBoxes(slide);

  return (
    <div ref={containerRef} className="slide-card" style={cardStyle}>
      <div className="slide-card__layer">
        {boxes.map((box, i) => (
          <div
            key={i}
            className="slide-card__text"
            style={boxStyle(box, style, scale)}
          >
            {box.text}
          </div>
        ))}
      </div>
    </div>
  );
}
