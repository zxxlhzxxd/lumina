import { useEffect, useRef, useState, type CSSProperties } from "react";
import { mediaUrl } from "../api";
import {
  boxStyle,
  computePreviewScale,
  slideTextBoxes,
  textRunStyle,
} from "../previewLayout";
import type { SlideModel, SlideSize } from "../types";

export function SlidePreview({
  slide,
  slideSize,
  projectId,
  onClick,
}: {
  slide: SlideModel;
  slideSize: SlideSize;
  projectId?: string | null;
  onClick?: () => void;
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
    const update = () => setScale(computePreviewScale(el.clientWidth, slideSize));
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [slideSize]);

  const cardStyle: CSSProperties = {
    aspectRatio: slideSize === "4:3" ? "4 / 3" : "16 / 9",
  };
  if (style?.background_color) cardStyle.background = style.background_color;
  if (bgUrl) {
    cardStyle.backgroundImage = `url("${bgUrl}")`;
    cardStyle.backgroundSize = "cover";
    cardStyle.backgroundPosition = "center";
  }

  const boxes = slideTextBoxes(slide, slideSize);
  const interactiveProps = onClick
    ? {
        role: "button",
        tabIndex: 0,
        onClick,
        onKeyDown: (e: React.KeyboardEvent<HTMLDivElement>) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onClick();
          }
        },
      }
    : {};

  return (
    <div
      ref={containerRef}
      className={`slide-card${onClick ? " clickable" : ""}`}
      style={cardStyle}
      {...interactiveProps}
    >
      <div className="slide-card__layer">
        {boxes.map((box, i) => (
          <div
            key={i}
            className="slide-card__text"
            style={boxStyle(box, style, scale)}
          >
            <div className="slide-card__text-line">
              <span
                className="slide-card__text-run"
                style={textRunStyle(style, box.role, box.blockId)}
              >
                {box.text}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
