import { useEffect, useMemo, useRef, useState } from "react";
import { Select, Space } from "antd";
import { api } from "../api";
import type { Book, ChapterInfo } from "../types";

interface Props {
  value: string;
  onChange: (reference: string) => void;
}

interface Parsed {
  bookId: number;
  sc: number;
  sv: number;
  ec: number;
  ev: number;
}

function parseReference(ref: string, books: Book[]): Parsed | null {
  const trimmed = ref.trim();
  if (!trimmed || books.length === 0) return null;

  let matched: { book: Book; aliasLen: number } | null = null;
  for (const b of books) {
    for (const name of [b.name, ...b.short_names]) {
      if (name && trimmed.startsWith(name)) {
        if (!matched || name.length > matched.aliasLen) {
          matched = { book: b, aliasLen: name.length };
        }
      }
    }
  }
  if (!matched) return null;

  const rest = trimmed.slice(matched.aliasLen).trim().split(",")[0].trim();
  const m = rest.match(/^(\d+)\s*:\s*(\d+)(?:\s*-\s*(?:(\d+)\s*:\s*)?(\d+))?$/);
  if (!m) return null;

  const sc = Number(m[1]);
  const sv = Number(m[2]);
  let ec = sc;
  let ev = sv;
  if (m[4] !== undefined) {
    ev = Number(m[4]);
    ec = m[3] !== undefined ? Number(m[3]) : sc;
  }
  return { bookId: matched.book.id, sc, sv, ec, ev };
}

function compose(bookName: string, sc: number, sv: number, ec: number, ev: number): string {
  if (sc === ec) {
    if (sv === ev) return `${bookName}${sc}:${sv}`;
    return `${bookName}${sc}:${sv}-${ev}`;
  }
  return `${bookName}${sc}:${sv}-${ec}:${ev}`;
}

const numberOptions = (n: number) =>
  Array.from({ length: Math.max(n, 1) }, (_, i) => ({ value: i + 1, label: String(i + 1) }));

export function ReferencePicker({ value, onChange }: Props) {
  const [books, setBooks] = useState<Book[]>([]);
  const [chapters, setChapters] = useState<ChapterInfo[]>([]);
  const [bookId, setBookId] = useState<number | undefined>();
  const [sc, setSc] = useState<number | undefined>();
  const [sv, setSv] = useState<number | undefined>();
  const [ec, setEc] = useState<number | undefined>();
  const [ev, setEv] = useState<number | undefined>();
  const initialized = useRef(false);

  useEffect(() => {
    let alive = true;
    api
      .listBooks()
      .then((bs) => {
        if (alive) setBooks(bs);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  // Initialize selections from an existing reference string (once books load).
  useEffect(() => {
    if (initialized.current || books.length === 0) return;
    initialized.current = true;
    const parsed = parseReference(value, books);
    if (parsed) {
      setBookId(parsed.bookId);
      setSc(parsed.sc);
      setSv(parsed.sv);
      setEc(parsed.ec);
      setEv(parsed.ev);
    }
  }, [books, value]);

  // Load chapter/verse metadata when the book changes.
  useEffect(() => {
    if (bookId === undefined) {
      setChapters([]);
      return;
    }
    let alive = true;
    api
      .listChapters(bookId)
      .then((cs) => {
        if (alive) setChapters(cs);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [bookId]);

  // Emit a normalized reference whenever a full selection exists.
  useEffect(() => {
    if (!initialized.current) return;
    if (bookId === undefined || sc === undefined || sv === undefined) return;
    const book = books.find((b) => b.id === bookId);
    if (!book) return;
    const next = compose(book.name, sc, sv, ec ?? sc, ev ?? sv);
    if (next !== value) onChange(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId, sc, sv, ec, ev]);

  const verseCount = (chapter: number | undefined) =>
    chapters.find((c) => c.chapter === chapter)?.verse_count ?? 1;

  const chapterOptions = useMemo(
    () => chapters.map((c) => ({ value: c.chapter, label: String(c.chapter) })),
    [chapters]
  );

  const handleBook = (id: number) => {
    setBookId(id);
    setSc(1);
    setSv(1);
    setEc(1);
    setEv(1);
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size={8}>
      <Select
        showSearch
        placeholder="选择书卷"
        style={{ width: "100%" }}
        value={bookId}
        onChange={handleBook}
        optionFilterProp="label"
        options={books.map((b) => ({ value: b.id, label: b.name }))}
      />
      <Space wrap size={8}>
        <Select
          showSearch
          placeholder="起始章"
          style={{ width: 96 }}
          value={sc}
          disabled={bookId === undefined}
          onChange={(v) => {
            setSc(v);
            if (ec === undefined || (ec ?? 0) < v) setEc(v);
          }}
          optionFilterProp="label"
          options={chapterOptions}
        />
        <span style={{ color: "#9fb3c8" }}>:</span>
        <Select
          showSearch
          placeholder="起始节"
          style={{ width: 96 }}
          value={sv}
          disabled={sc === undefined}
          onChange={setSv}
          optionFilterProp="label"
          options={numberOptions(verseCount(sc))}
        />
        <span style={{ color: "#9fb3c8" }}>至</span>
        <Select
          showSearch
          placeholder="结束章"
          style={{ width: 96 }}
          value={ec}
          disabled={bookId === undefined}
          onChange={setEc}
          optionFilterProp="label"
          options={chapterOptions}
        />
        <span style={{ color: "#9fb3c8" }}>:</span>
        <Select
          showSearch
          placeholder="结束节"
          style={{ width: 96 }}
          value={ev}
          disabled={ec === undefined}
          onChange={setEv}
          optionFilterProp="label"
          options={numberOptions(verseCount(ec))}
        />
      </Space>
    </Space>
  );
}
