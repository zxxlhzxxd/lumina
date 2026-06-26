import { useEffect, useState } from "react";
import { Button, Input, Switch, Segmented, InputNumber, Form, Tag, Space, Tooltip } from "antd";
import {
  BookOutlined,
  FormatPainterOutlined,
  RetweetOutlined,
  SwapOutlined,
} from "@ant-design/icons";
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
  effectiveStyle: SectionStyle;
  onChange: (patch: Partial<Section>) => void;
  onBlockLayoutOpenChange?: (blockId: string, open: boolean) => void;
}

// blank-line separated blocks <-> string[]
const blocksToText = (blocks: string[]) => blocks.join("\n\n");
const textToBlocks = (text: string) =>
  text.split(/\n\s*\n/).map((s) => s.trimEnd()).filter((s) => s.trim());

const textToLyrics = (text: string) => (text.length ? [text] : []);
const replacePunctuationWithSpaces = (text: string) => text.replace(/\p{P}/gu, " ");
const formatLyricsByLineCount = (text: string, linesPerSlide: number) => {
  const per = Math.max(1, linesPerSlide);
  const lines = text.split("\n").map((s) => s.trimEnd()).filter((s) => s.trim());
  const pages: string[] = [];
  for (let i = 0; i < lines.length; i += per) {
    pages.push(lines.slice(i, i + per).join("\n"));
  }
  return pages.join("\n\n");
};

// line separated items <-> string[]
const linesToText = (lines: string[]) => lines.join("\n");
const textToLines = (text: string) =>
  text.split("\n").map((s) => s.trim()).filter(Boolean);

export function SectionEditor({
  section,
  projectId,
  effectiveStyle,
  onChange,
  onBlockLayoutOpenChange,
}: Props) {
  const patch = (p: Partial<Section>) => onChange(p);
  const [hymnLibOpen, setHymnLibOpen] = useState(false);
  const [liturgyLibOpen, setLiturgyLibOpen] = useState(false);
  const [liturgyText, setLiturgyText] = useState("");
  const [lyricsText, setLyricsText] = useState("");
  const [lyricsFormatLineCount, setLyricsFormatLineCount] = useState<number | null>(null);

  useEffect(() => {
    if (section.type === "liturgy_text") {
      setLiturgyText(blocksToText(section.paragraphs));
    } else if (section.type === "hymn") {
      setLyricsText(blocksToText(section.lyrics));
      setLyricsFormatLineCount(null);
    }
  }, [section.id, section.type]);

  const applyLyricsText = (value: string) => {
    setLyricsText(value);
    patch({
      lyrics: textToLyrics(value),
      hymn_id: null,
    } as Partial<Section>);
  };

  const insertHymn = (hymn: Hymn) => {
    const lyrics = hymn.sections.map((s) => s.text);
    setLyricsText(blocksToText(lyrics));
    patch({
      hymn_id: hymn.id || null,
      song_title: hymn.title,
      author: hymn.author,
      hymn_number: hymn.number,
      lyrics,
    } as Partial<Section>);
    setHymnLibOpen(false);
  };

  const insertLiturgy = (text: LiturgyText) => {
    setLiturgyText(blocksToText(text.paragraphs));
    patch({
      liturgy_id: text.id || null,
      slide_title: text.title,
      paragraphs: text.paragraphs,
    } as Partial<Section>);
    setLiturgyLibOpen(false);
  };

  return (
    <div>
      <div className="editor-section">
        <Tag color="gold">{SECTION_TYPE_LABEL[section.type]}</Tag>
        <Form layout="vertical" style={{ marginTop: 12 }}>
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
              <Form.Item label="PPT 页面标题">
                <Input
                  value={section.slide_title}
                  onChange={(e) =>
                    patch({ slide_title: e.target.value } as Partial<Section>)
                  }
                  placeholder="输入礼文页标题"
                />
              </Form.Item>
              <Form.Item>
                <Button icon={<BookOutlined />} onClick={() => setLiturgyLibOpen(true)}>
                  从礼文库选择
                </Button>
              </Form.Item>
              <Form.Item label="礼文内容" extra="空行分隔不同段落">
                <TextArea
                  rows={10}
                  value={liturgyText}
                  onChange={(e) => {
                    const value = e.target.value;
                    setLiturgyText(value);
                    patch({
                      paragraphs: textToBlocks(value),
                      liturgy_id: null,
                    } as Partial<Section>);
                  }}
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
              <Form.Item label="歌词" extra="空行作为分页标志；每行一句">
                <Space wrap size={[6, 6]} style={{ marginBottom: 8 }}>
                  <Space.Compact>
                    <InputNumber
                      min={1}
                      max={6}
                      value={lyricsFormatLineCount}
                      placeholder="行数"
                      aria-label="每页歌词行数"
                      style={{ width: 86 }}
                      onChange={(v) => setLyricsFormatLineCount(v ?? null)}
                    />
                    <Tooltip title="清除现有空白行，并按指定行数插入分页空行">
                      <Button
                        icon={<FormatPainterOutlined />}
                        disabled={!lyricsFormatLineCount}
                        onClick={() => {
                          if (!lyricsFormatLineCount) return;
                          applyLyricsText(formatLyricsByLineCount(lyricsText, lyricsFormatLineCount));
                        }}
                      >
                        按行分页
                      </Button>
                    </Tooltip>
                  </Space.Compact>
                  <Tooltip title="将中英文标点替换为空格">
                    <Button
                      icon={<RetweetOutlined />}
                      onClick={() => applyLyricsText(replacePunctuationWithSpaces(lyricsText))}
                    >
                      标点→空格
                    </Button>
                  </Tooltip>
                  <Tooltip title="将所有“你”替换为“祢”">
                    <Button icon={<SwapOutlined />} onClick={() => applyLyricsText(lyricsText.replace(/你/g, "祢"))}>
                      你→祢
                    </Button>
                  </Tooltip>
                  <Tooltip title="将所有“他”替换为“祂”">
                    <Button icon={<SwapOutlined />} onClick={() => applyLyricsText(lyricsText.replace(/他/g, "祂"))}>
                      他→祂
                    </Button>
                  </Tooltip>
                </Space>
                <TextArea
                  rows={10}
                  value={lyricsText}
                  onChange={(e) => applyLyricsText(e.target.value)}
                />
              </Form.Item>
            </>
          )}

          {section.type === "announcement" && (
            <>
              <Form.Item label="PPT 页面标题">
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
              <Form.Item label="PPT 页面标题">
                <Input
                  value={section.slide_title}
                  onChange={(e) =>
                    patch({ slide_title: e.target.value } as Partial<Section>)
                  }
                  placeholder="输入媒体页标题"
                />
              </Form.Item>
              <Form.Item label="正文">
                <TextArea
                  rows={8}
                  value={section.body}
                  onChange={(e) => patch({ body: e.target.value } as Partial<Section>)}
                  placeholder="输入媒体页正文"
                />
              </Form.Item>
              <Form.Item label="绑定音频" extra="导出后会在页面右下角显示可编辑的小喇叭，支持 mp3 / wav">
                <MediaPicker
                  kind="audio"
                  projectId={projectId}
                  value={section.audio_ref}
                  onChange={(ref) => patch({ audio_ref: ref } as Partial<Section>)}
                />
              </Form.Item>
              <Form.Item label="播放时机">
                <Segmented
                  value={section.audio_trigger ?? "click"}
                  onChange={(v) => patch({ audio_trigger: v as any } as Partial<Section>)}
                  options={[
                    { label: "点击后播放", value: "click" },
                    { label: "进入页面自动播放", value: "auto" },
                  ]}
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
            </>
          )}
        </Form>

        <StylePanel
          section={section}
          projectId={projectId}
          effectiveStyle={effectiveStyle}
          onChange={onChange}
          onBlockLayoutOpenChange={onBlockLayoutOpenChange}
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
