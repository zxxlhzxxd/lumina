import { useState } from "react";
import { Button, InputNumber, Tooltip } from "antd";
import {
  ArrowDownOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  ArrowUpOutlined,
  ClearOutlined,
  LockOutlined,
  UnlockOutlined,
} from "@ant-design/icons";
import type { BlockAnchor, BlockLayout } from "../types";

type MarginSide = "top" | "right" | "bottom" | "left";

const ANCHORS: Array<{
  value: BlockAnchor;
  label: string;
  placement: "top" | "bottom" | "left" | "right";
  offset?: [number, number];
}> = [
  { value: "top_left", label: "左上", placement: "top" },
  { value: "top_center", label: "顶部居中", placement: "top" },
  { value: "top_right", label: "右上", placement: "top" },
  { value: "middle_left", label: "左侧居中", placement: "left" },
  {
    value: "middle_center",
    label: "页面居中",
    placement: "top",
    offset: [0, -38],
  },
  { value: "middle_right", label: "右侧居中", placement: "right" },
  { value: "bottom_left", label: "左下", placement: "bottom" },
  { value: "bottom_center", label: "底部居中", placement: "bottom" },
  { value: "bottom_right", label: "右下", placement: "bottom" },
];

const MARGIN_META: Record<
  MarginSide,
  { label: string; icon: React.ReactNode }
> = {
  top: { label: "上边距", icon: <ArrowUpOutlined /> },
  right: { label: "右边距", icon: <ArrowRightOutlined /> },
  bottom: { label: "下边距", icon: <ArrowDownOutlined /> },
  left: { label: "左边距", icon: <ArrowLeftOutlined /> },
};

interface Props {
  value: BlockLayout | null | undefined;
  fallbackMargin: number;
  onChange: (layout: BlockLayout | null) => void;
}

export function BlockLayoutEditor({
  value,
  fallbackMargin,
  onChange,
}: Props) {
  const [linked, setLinked] = useState(true);

  const patch = (next: Partial<BlockLayout>) => {
    onChange({ ...value, ...next });
  };

  const setMargin = (side: MarginSide, next: number | null) => {
    const margin = { ...(value?.margin ?? {}) };
    if (linked) {
      margin.top = next;
      margin.right = next;
      margin.bottom = next;
      margin.left = next;
    } else {
      margin[side] = next;
    }
    patch({ margin });
  };

  return (
    <div className="block-layout-editor">
      <div className="block-layout-editor__header">
        <span>页面位置与边距</span>
        <Tooltip title="恢复默认布局" placement="left">
          <Button
            type="text"
            icon={<ClearOutlined />}
            aria-label="恢复默认块布局"
            disabled={!value}
            onClick={() => onChange(null)}
          />
        </Tooltip>
      </div>

      <div className="block-layout-editor__content">
        <div className="block-layout-editor__anchor-grid">
          {ANCHORS.map((anchor) => (
            <Tooltip
              title={anchor.label}
              placement={anchor.placement}
              align={anchor.offset ? { offset: anchor.offset } : undefined}
              autoAdjustOverflow={false}
              overlayClassName="block-layout-editor__tooltip"
              mouseEnterDelay={0.25}
              key={anchor.value}
            >
              <Button
                type={value?.anchor === anchor.value ? "primary" : "text"}
                className="block-layout-editor__anchor"
                aria-label={anchor.label}
                aria-pressed={value?.anchor === anchor.value}
                onClick={() => patch({ anchor: anchor.value })}
              >
                <span className="block-layout-editor__anchor-dot" />
              </Button>
            </Tooltip>
          ))}
        </div>

        <div className="block-layout-editor__margins">
          <div className="block-layout-editor__margin-grid">
            {(["top", "right", "bottom", "left"] as MarginSide[]).map((side) => {
              const meta = MARGIN_META[side];
              return (
                <Tooltip title={`${meta.label}（英寸）`} placement="top" key={side}>
                  <div className="block-layout-editor__margin">
                    <span aria-hidden>{meta.icon}</span>
                    <InputNumber
                      aria-label={`${meta.label}（英寸）`}
                      min={0}
                      max={7.5}
                      step={0.1}
                      precision={1}
                      value={value?.margin?.[side] ?? fallbackMargin}
                      onChange={(next) => setMargin(side, next)}
                    />
                  </div>
                </Tooltip>
              );
            })}
          </div>
          <Tooltip title={linked ? "四边距已联动" : "四边距独立调整"}>
            <Button
              type={linked ? "primary" : "text"}
              icon={linked ? <LockOutlined /> : <UnlockOutlined />}
              aria-label={linked ? "取消四边距联动" : "联动四边距"}
              aria-pressed={linked}
              onClick={() => setLinked((current) => !current)}
            />
          </Tooltip>
        </div>
      </div>
    </div>
  );
}
