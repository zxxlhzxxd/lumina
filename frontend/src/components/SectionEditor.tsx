import { useState } from "react";
import { Button, Input, Switch, Segmented, InputNumber, Form, Tag } from "antd";
import { BookOutlined } from "@ant-design/icons";
import type { Hymn, LiturgyText, Section, SectionStyle } from "../types";
import { SECTION_TYPE_LABEL } from "../types";
import { ReferencePicker } from "./ReferencePicker";
import { MediaPicker } from "./MediaPicker";
import { StylePanel } from "./StylePanel";
import { HymnLibraryModal } from "./HymnLibraryModal";
import { LiturgyLibraryModal } from "./LiturgyLibraryModal";

const { TextArea } = Input;

interface Props {
  section: Section;
  projectId: string | null;
  onChange: (patch: Partial<Section>) => void;
  onSetTypeDefault: (style: SectionStyle) => void;
}

// blank-line separated blocks <-> string[]
const blocksToText = (blocks: string[]) => blocks.join("\n\n");
const textToBlocks = (text: string) =>
  text.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);

// line separated items <-> string[]
const linesToText = (lines: string[]) => lines.join("\n");
const textToLines = (text: string) =>
  text.split("\n").map((s) => s.trim()).filter(Boolean);

export function SectionEditor({ section, projectId, onChange, onSetTypeDefault }: Props) {
  const patch = (p: Partial<Section>) => onChange(p);
  const [hymnLibOpen, setHymnLibOpen] = useState(false);
  const [liturgyLibOpen, setLiturgyLibOpen] = useState(false);

  const insertHymn = (hymn: Hymn) => {
    patch({
      hymn_id: hymn.id || null,
      song_title: hymn.title,
      author: hymn.author,
      hymn_number: hymn.number,
      lyrics: hymn.sections.map((s) => s.text),
    } as Partial<Section>);
    setHymnLibOpen(false);
  };

  const insertLiturgy = (text: LiturgyText) => {
    patch({
      liturgy_id: text.id || null,
      paragraphs: text.paragraphs,
    } as Partial<Section>);
    if (!section.title && text.title) {
      patch({ title: text.title } as Partial<Section>);
    }
    setLiturgyLibOpen(false);
  };

  return (
    <div>
      <div className="editor-section">
        <Tag color="gold">{SECTION_TYPE_LABEL[section.type]}</Tag>
        <Form layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item label="段落名称">
            <Input
              value={section.title}
              onChange={(e) => patch({ title: e.target.value } as Partial<Section>)}
              placeholder="段落名称"
            />
          </Form.Item>

          {section.type === "cover" && (
            <>
              <Form.Item label="主标题">
                <Input
                  value={section.main_title}
                  onChange={(e) => patch({ main_title: e.target.value } as Partial<Section>)}
                  placeholder="如：主日崇拜 / 证道题目"
                />
              </Form.Item>
              <Form.Item label="副标题">
                <Input
                  value={section.sub_title}
                  onChange={(e) => patch({ sub_title: e.target.value } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="附加信息（出处/牧者/日期）">
                <Input
                  value={section.extra}
                  onChange={(e) => patch({ extra: e.target.value } as Partial<Section>)}
                />
              </Form.Item>
            </>
          )}

          {section.type === "responsive_reading" && (
            <>
              <Form.Item
                label="经文引用"
                extra="选择书卷与起止章节，自动逐节生成（启先读）"
              >
                <ReferencePicker
                  value={section.reference}
                  onChange={(ref) => patch({ reference: ref } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="显示节引用">
                <Switch
                  checked={section.show_reference}
                  onChange={(v) => patch({ show_reference: v } as Partial<Section>)}
                />
              </Form.Item>
            </>
          )}

          {section.type === "scripture" && (
            <>
              <Form.Item label="经文引用" extra="选择书卷与起止章节（可跨章），按容量自动分页">
                <ReferencePicker
                  value={section.reference}
                  onChange={(ref) => patch({ reference: ref } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="生成经文标题页">
                <Switch
                  checked={section.include_title_slide}
                  onChange={(v) => patch({ include_title_slide: v } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="显示节号">
                <Switch
                  checked={section.show_verse_number}
                  onChange={(v) => patch({ show_verse_number: v } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="每页字数（约）">
                <InputNumber
                  min={40}
                  max={400}
                  value={section.chars_per_slide}
                  onChange={(v) => patch({ chars_per_slide: v ?? 140 } as Partial<Section>)}
                />
              </Form.Item>
            </>
          )}

          {section.type === "liturgy_text" && (
            <>
              <Form.Item>
                <Button icon={<BookOutlined />} onClick={() => setLiturgyLibOpen(true)}>
                  从礼文库选择
                </Button>
              </Form.Item>
              <Form.Item label="礼文内容" extra="空行分隔不同段落">
                <TextArea
                  rows={10}
                  value={blocksToText(section.paragraphs)}
                  onChange={(e) =>
                    patch({
                      paragraphs: textToBlocks(e.target.value),
                      liturgy_id: null,
                    } as Partial<Section>)
                  }
                  placeholder="输入礼文段落，空行分段"
                />
              </Form.Item>
              <Form.Item label="每页字数（约）">
                <InputNumber
                  min={40}
                  max={400}
                  value={section.chars_per_slide}
                  onChange={(v) => patch({ chars_per_slide: v ?? 160 } as Partial<Section>)}
                />
              </Form.Item>
            </>
          )}

          {section.type === "hymn" && (
            <>
              <Form.Item>
                <Button icon={<BookOutlined />} onClick={() => setHymnLibOpen(true)}>
                  从诗歌库选择
                </Button>
              </Form.Item>
              <Form.Item label="诗歌名">
                <Input
                  value={section.song_title}
                  onChange={(e) => patch({ song_title: e.target.value } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="作者 / 编号">
                <Input
                  value={section.author}
                  onChange={(e) => patch({ author: e.target.value } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="歌词" extra="空行分隔不同段落；每行一句">
                <TextArea
                  rows={10}
                  value={blocksToText(section.lyrics)}
                  onChange={(e) =>
                    patch({
                      lyrics: textToBlocks(e.target.value),
                      hymn_id: null,
                    } as Partial<Section>)
                  }
                />
              </Form.Item>
              <Form.Item label="每页歌词行数">
                <InputNumber
                  min={1}
                  max={6}
                  value={section.lines_per_slide}
                  onChange={(v) => patch({ lines_per_slide: v ?? 2 } as Partial<Section>)}
                />
              </Form.Item>
            </>
          )}

          {section.type === "announcement" && (
            <>
              <Form.Item label="标题">
                <Input
                  value={section.heading}
                  onChange={(e) => patch({ heading: e.target.value } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="公告事项" extra="每行一条">
                <TextArea
                  rows={8}
                  value={linesToText(section.items)}
                  onChange={(e) =>
                    patch({ items: textToLines(e.target.value) } as Partial<Section>)
                  }
                />
              </Form.Item>
            </>
          )}

          {section.type === "media" && (
            <>
              <Form.Item label="文字说明">
                <Input
                  value={section.caption}
                  onChange={(e) => patch({ caption: e.target.value } as Partial<Section>)}
                  placeholder="如：请起立默祷"
                />
              </Form.Item>
              <Form.Item label="绑定音频" extra="按单击顺序播放将在后续版本接入">
                <MediaPicker
                  kind="audio"
                  projectId={projectId}
                  value={section.audio_ref}
                  onChange={(ref) => patch({ audio_ref: ref } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="播放模式（音频）">
                <Segmented
                  value={section.play_mode}
                  onChange={(v) => patch({ play_mode: v as any } as Partial<Section>)}
                  options={[
                    { label: "播放一次", value: "once" },
                    { label: "循环", value: "loop" },
                  ]}
                />
              </Form.Item>
              <Form.Item label="背景视频" extra="导出仅随容器携带，播放将在后续版本接入">
                <MediaPicker
                  kind="video"
                  projectId={projectId}
                  value={section.video_ref}
                  onChange={(ref) => patch({ video_ref: ref } as Partial<Section>)}
                />
              </Form.Item>
            </>
          )}
        </Form>

        <StylePanel
          section={section}
          projectId={projectId}
          onChange={onChange}
          onSetTypeDefault={onSetTypeDefault}
        />
      </div>

      <HymnLibraryModal
        open={hymnLibOpen}
        onClose={() => setHymnLibOpen(false)}
        onInsert={insertHymn}
      />
      <LiturgyLibraryModal
        open={liturgyLibOpen}
        onClose={() => setLiturgyLibOpen(false)}
        onInsert={insertLiturgy}
      />
    </div>
  );
}
