// Types mirroring the backend domain model (snake_case, as serialized by the API).

export type SectionType =
  | "cover"
  | "responsive_reading"
  | "scripture"
  | "hymn"
  | "liturgy_text"
  | "announcement"
  | "media";

export type ReadingRole = "qi" | "ying";
export type PlayMode = "once" | "loop";
export type SlideSize = "16:9" | "4:3";

export interface TextStyle {
  font_family?: string | null;
  font_size?: number | null;
  color?: string | null;
  bold?: boolean | null;
  italic?: boolean | null;
  align?: "left" | "center" | "right" | null;
  line_spacing?: number | null;
}

export interface SectionStyle {
  background_color?: string | null;
  background_image?: string | null;
  background_video?: string | null;
  body?: TextStyle | null;
  title?: TextStyle | null;
  label?: TextStyle | null;
  margin?: number | null;
}

export interface SectionBase {
  id: string;
  type: SectionType;
  title: string;
  enabled: boolean;
  notes: string;
  style?: SectionStyle | null;
}

export interface CoverSection extends SectionBase {
  type: "cover";
  main_title: string;
  sub_title: string;
  extra: string;
}

export interface ResponsiveReadingSection extends SectionBase {
  type: "responsive_reading";
  reference: string;
  start_role: ReadingRole;
  show_verse_number: boolean;
  show_reference: boolean;
}

export interface ScriptureSection extends SectionBase {
  type: "scripture";
  reference: string;
  show_verse_number: boolean;
  include_title_slide: boolean;
  pagination_mode: "auto" | "manual";
  chars_per_slide: number;
}

export interface HymnSection extends SectionBase {
  type: "hymn";
  hymn_id: string | null;
  song_title: string;
  author: string;
  hymn_number: string;
  lyrics: string[];
  lines_per_slide: number;
  include_title_slide: boolean;
}

export interface LiturgyTextSection extends SectionBase {
  type: "liturgy_text";
  liturgy_id: string | null;
  paragraphs: string[];
  chars_per_slide: number;
}

export interface AnnouncementSection extends SectionBase {
  type: "announcement";
  heading: string;
  items: string[];
}

export interface MediaSection extends SectionBase {
  type: "media";
  caption: string;
  audio_ref: string | null;
  play_mode: PlayMode;
  video_ref: string | null;
}

export type Section =
  | CoverSection
  | ResponsiveReadingSection
  | ScriptureSection
  | HymnSection
  | LiturgyTextSection
  | AnnouncementSection
  | MediaSection;

export interface Project {
  schema_version?: number;
  id: string;
  name: string;
  date: string | null;
  slide_size: SlideSize;
  theme_id: string | null;
  sections: Section[];
  meta: { pastor: string; theme_scripture: string; notes: string };
  created_at?: string;
  updated_at?: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  date: string | null;
  section_count: number;
  updated_at?: string;
}

export interface Book {
  id: number;
  name: string;
  short_names: string[];
  order: number;
  chapter_count: number;
}

export interface ChapterInfo {
  chapter: number;
  verse_count: number;
}

export interface TemplateSummary {
  id: string;
  name: string;
  builtin: boolean;
  description: string;
  section_count: number;
}

export interface HymnLyricSection {
  order: number;
  label: string;
  text: string;
}

export interface Hymn {
  id: string;
  title: string;
  author: string;
  number: string;
  source: string;
  builtin: boolean;
  sections: HymnLyricSection[];
}

export interface HymnSummary {
  id: string;
  title: string;
  author: string;
  number: string;
  builtin: boolean;
}

export interface LiturgyText {
  id: string;
  title: string;
  builtin: boolean;
  paragraphs: string[];
}

export interface LiturgyTextSummary {
  id: string;
  title: string;
  builtin: boolean;
  paragraph_count: number;
}

export interface Theme {
  id: string;
  name: string;
  builtin: boolean;
  default_style?: SectionStyle | null;
  type_styles: Record<string, SectionStyle>;
}

export interface ThemeSummary {
  id: string;
  name: string;
  builtin: boolean;
  is_default: boolean;
}

export interface ThemeListResponse {
  default_id: string;
  themes: ThemeSummary[];
}

export interface SlideModel {
  kind: string;
  section_id: string;
  section_type: string;
  index: number;
  title: string | null;
  subtitle: string | null;
  label: string | null;
  reference: string | null;
  body: string | null;
  style?: SectionStyle | null;
}

export interface ValidationIssue {
  level: "warning" | "error";
  section_id: string;
  message: string;
}

export const SECTION_TYPE_LABEL: Record<SectionType, string> = {
  cover: "封面/标题",
  responsive_reading: "启应经文",
  scripture: "经文",
  hymn: "赞美诗",
  liturgy_text: "礼文",
  announcement: "家事报告",
  media: "媒体",
};
