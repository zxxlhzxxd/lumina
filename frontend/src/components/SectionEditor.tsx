import { Input, Switch, Segmented, InputNumber, Form, Tag } from "antd";
import type { Section } from "../types";
import { SECTION_TYPE_LABEL } from "../types";

const { TextArea } = Input;

interface Props {
  section: Section;
  onChange: (patch: Partial<Section>) => void;
}

// blank-line separated blocks <-> string[]
const blocksToText = (blocks: string[]) => blocks.join("\n\n");
const textToBlocks = (text: string) =>
  text.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);

// line separated items <-> string[]
const linesToText = (lines: string[]) => lines.join("\n");
const textToLines = (text: string) =>
  text.split("\n").map((s) => s.trim()).filter(Boolean);

export function SectionEditor({ section, onChange }: Props) {
  const patch = (p: Partial<Section>) => onChange(p);

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
                extra="如：以西结书4:1-5、结4:1-5、约翰福音3:16-18"
              >
                <Input
                  value={section.reference}
                  onChange={(e) => patch({ reference: e.target.value } as Partial<Section>)}
                  placeholder="输入圣经引用，自动逐节生成"
                />
              </Form.Item>
              <Form.Item label="起始角色">
                <Segmented
                  value={section.start_role}
                  onChange={(v) => patch({ start_role: v as any } as Partial<Section>)}
                  options={[
                    { label: "启 先读", value: "qi" },
                    { label: "应 先读", value: "ying" },
                  ]}
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
              <Form.Item label="经文引用" extra="如：约翰福音3:16-21（可跨章）">
                <Input
                  value={section.reference}
                  onChange={(e) => patch({ reference: e.target.value } as Partial<Section>)}
                  placeholder="输入圣经引用，按容量自动分页"
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
              <Form.Item label="礼文内容" extra="空行分隔不同段落">
                <TextArea
                  rows={10}
                  value={blocksToText(section.paragraphs)}
                  onChange={(e) =>
                    patch({ paragraphs: textToBlocks(e.target.value) } as Partial<Section>)
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
                    patch({ lyrics: textToBlocks(e.target.value) } as Partial<Section>)
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
              <Form.Item label="播放模式（音频，阶段二接入）">
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
      </div>
    </div>
  );
}
