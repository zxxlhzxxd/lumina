// Client-side section factory. Mirrors the backend defaults in
// backend/app/domain/sections.py so newly added sections match what the
// server would have produced from a template.
import type { Section, SectionType } from "./types";
import { SECTION_TYPE_LABEL } from "./types";

export function makeSection(type: SectionType): Section {
  const base = {
    id: crypto.randomUUID(),
    title: SECTION_TYPE_LABEL[type],
    enabled: true,
    notes: "",
  };

  switch (type) {
    case "cover":
      return { ...base, type, main_title: "", sub_title: "", extra: "" };
    case "responsive_reading":
      return {
        ...base,
        type,
        reference: "",
        start_role: "qi",
        show_verse_number: true,
        show_reference: true,
      };
    case "scripture":
      return {
        ...base,
        type,
        reference: "",
        show_verse_number: true,
        include_title_slide: true,
        pagination_mode: "auto",
        chars_per_slide: 140,
      };
    case "hymn":
      return {
        ...base,
        type,
        hymn_id: null,
        song_title: "",
        author: "",
        hymn_number: "",
        lyrics: [],
        lines_per_slide: 2,
        include_title_slide: true,
      };
    case "liturgy_text":
      return { ...base, type, liturgy_id: null, paragraphs: [], chars_per_slide: 160 };
    case "announcement":
      return { ...base, type, heading: "", items: [] };
    case "media":
      return {
        ...base,
        type,
        caption: "",
        audio_ref: null,
        play_mode: "once",
        audio_trigger: "click",
        video_ref: null,
      };
  }
}
