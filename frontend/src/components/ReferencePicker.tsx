import { useEffect, useMemo, useRef, useState } from "react";
import { Button, Popover, Spin } from "antd";
import {
  BookOutlined,
  DownOutlined,
  LeftOutlined,
  RightOutlined,
} from "@ant-design/icons";
import { api } from "../api";
import type { Book, ChapterInfo } from "../types";

interface Props {
  value: string;
  onChange: (reference: string) => void;
}

interface VersePoint {
  chapter: number;
  verse: number;
}

interface Parsed {
  bookId: number;
  start: VersePoint;
  end: VersePoint;
}

type PickerView = "books" | "chapters" | "verses";

function parseReference(ref: string, books: Book[]): Parsed | null {
  const trimmed = ref.trim();
  if (!trimmed || books.length === 0) return null;

  let matched: { book: Book; aliasLen: number } | null = null;
  for (const book of books) {
    for (const name of [book.name, ...book.short_names]) {
      if (name && trimmed.startsWith(name)) {
        if (!matched || name.length > matched.aliasLen) {
          matched = { book, aliasLen: name.length };
        }
      }
    }
  }
  if (!matched) return null;

  const rest = trimmed.slice(matched.aliasLen).trim();
  const match = rest.match(
    /^(\d+)\s*:\s*(\d+)(?:\s*-\s*(?:(\d+)\s*:\s*)?(\d+))?$/
  );
  if (!match) return null;

  const start = { chapter: Number(match[1]), verse: Number(match[2]) };
  const end = {
    chapter: match[3] === undefined ? start.chapter : Number(match[3]),
    verse: match[4] === undefined ? start.verse : Number(match[4]),
  };
  return { bookId: matched.book.id, start, end };
}

function compose(bookName: string, start: VersePoint, end: VersePoint): string {
  if (start.chapter === end.chapter) {
    if (start.verse === end.verse) {
      return `${bookName}${start.chapter}:${start.verse}`;
    }
    return `${bookName}${start.chapter}:${start.verse}-${end.verse}`;
  }
  return `${bookName}${start.chapter}:${start.verse}-${end.chapter}:${end.verse}`;
}

function comparePoints(a: VersePoint, b: VersePoint): number {
  return a.chapter === b.chapter ? a.verse - b.verse : a.chapter - b.chapter;
}

function samePoint(a: VersePoint | null, b: VersePoint): boolean {
  return !!a && a.chapter === b.chapter && a.verse === b.verse;
}

function bookShortName(book: Book): string {
  return book.short_names[0] || book.name.slice(0, 2);
}

export function ReferencePicker({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<PickerView>("books");
  const [books, setBooks] = useState<Book[]>([]);
  const [booksLoading, setBooksLoading] = useState(true);
  const [booksError, setBooksError] = useState(false);
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null);
  const [chapters, setChapters] = useState<ChapterInfo[]>([]);
  const [chaptersLoading, setChaptersLoading] = useState(false);
  const [chaptersError, setChaptersError] = useState(false);
  const [visibleChapter, setVisibleChapter] = useState(1);
  const [draftStart, setDraftStart] = useState<VersePoint | null>(null);
  const [draftEnd, setDraftEnd] = useState<VersePoint | null>(null);
  const [awaitingEnd, setAwaitingEnd] = useState(false);
  const chapterCache = useRef(new Map<number, ChapterInfo[]>());
  const chapterRequest = useRef(0);

  const loadBooks = () => {
    setBooksLoading(true);
    setBooksError(false);
    api
      .listBooks()
      .then(setBooks)
      .catch(() => setBooksError(true))
      .finally(() => setBooksLoading(false));
  };

  useEffect(() => {
    loadBooks();
  }, []);

  const loadChapters = (bookId: number) => {
    const requestId = ++chapterRequest.current;
    const cached = chapterCache.current.get(bookId);
    if (cached) {
      setChapters(cached);
      setChaptersLoading(false);
      setChaptersError(false);
      return;
    }

    setChapters([]);
    setChaptersLoading(true);
    setChaptersError(false);
    api
      .listChapters(bookId)
      .then((items) => {
        chapterCache.current.set(bookId, items);
        if (requestId === chapterRequest.current) setChapters(items);
      })
      .catch(() => {
        if (requestId === chapterRequest.current) setChaptersError(true);
      })
      .finally(() => {
        if (requestId === chapterRequest.current) setChaptersLoading(false);
      });
  };

  useEffect(() => {
    if (selectedBookId !== null) loadChapters(selectedBookId);
  }, [selectedBookId]);

  const selectedBook = books.find((book) => book.id === selectedBookId) ?? null;
  const maxChapter = chapters.length
    ? chapters[chapters.length - 1].chapter
    : selectedBook?.chapter_count ?? 1;

  const resetDraftFromValue = () => {
    const parsed = parseReference(value, books);
    if (!parsed) {
      setView("books");
      setSelectedBookId(null);
      setChapters([]);
      setVisibleChapter(1);
      setDraftStart(null);
      setDraftEnd(null);
      setAwaitingEnd(false);
      return;
    }

    setSelectedBookId(parsed.bookId);
    setVisibleChapter(parsed.start.chapter);
    setDraftStart(parsed.start);
    setDraftEnd(parsed.end);
    setAwaitingEnd(false);
    setView("verses");
  };

  useEffect(() => {
    if (!open || books.length === 0 || selectedBookId !== null) return;
    const parsed = parseReference(value, books);
    if (!parsed) return;
    setSelectedBookId(parsed.bookId);
    setVisibleChapter(parsed.start.chapter);
    setDraftStart(parsed.start);
    setDraftEnd(parsed.end);
    setAwaitingEnd(false);
    setView("verses");
  }, [books, open, selectedBookId, value]);

  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen) resetDraftFromValue();
    setOpen(nextOpen);
  };

  const selectBook = (book: Book) => {
    setSelectedBookId(book.id);
    setVisibleChapter(1);
    setDraftStart(null);
    setDraftEnd(null);
    setAwaitingEnd(false);
    setView("chapters");
  };

  const selectChapter = (chapter: number) => {
    setVisibleChapter(chapter);
    setDraftStart(null);
    setDraftEnd(null);
    setAwaitingEnd(false);
    setView("verses");
  };

  const selectVerse = (point: VersePoint) => {
    if (!draftStart || draftEnd || !awaitingEnd) {
      setDraftStart(point);
      setDraftEnd(null);
      setAwaitingEnd(true);
      return;
    }

    if (comparePoints(draftStart, point) <= 0) {
      setDraftEnd(point);
    } else {
      setDraftStart(point);
      setDraftEnd(draftStart);
    }
    setAwaitingEnd(false);
  };

  const confirm = () => {
    if (!selectedBook || !draftStart || !draftEnd) return;
    const next = compose(selectedBook.name, draftStart, draftEnd);
    if (next !== value) onChange(next);
    setOpen(false);
  };

  const rangeLabel =
    selectedBook && draftStart
      ? draftEnd
        ? compose(selectedBook.name, draftStart, draftEnd)
        : `${selectedBook.name}${draftStart.chapter}:${draftStart.verse} 至 …`
      : "请选择起止经节";

  const oldTestament = useMemo(
    () => books.filter((book) => book.order <= 39),
    [books]
  );
  const newTestament = useMemo(
    () => books.filter((book) => book.order >= 40),
    [books]
  );

  const renderError = (retry: () => void, text: string) => (
    <div className="reference-picker__state">
      <span>{text}</span>
      <Button size="small" onClick={retry}>
        重试
      </Button>
    </div>
  );

  const renderBooks = () => {
    if (booksLoading) {
      return (
        <div className="reference-picker__state">
          <Spin />
        </div>
      );
    }
    if (booksError) return renderError(loadBooks, "无法加载经卷");

    const group = (title: string, items: Book[]) => (
      <section className="reference-picker__book-section" key={title}>
        <div className="reference-picker__section-title">{title}</div>
        <div className="reference-picker__book-grid">
          {items.map((book) => (
            <button
              type="button"
              className={`reference-picker__book-card${
                book.id === selectedBookId ? " is-selected" : ""
              }`}
              key={book.id}
              onClick={() => selectBook(book)}
            >
              <span className="reference-picker__book-short">
                {bookShortName(book)}
              </span>
              <span className="reference-picker__book-name">{book.name}</span>
            </button>
          ))}
        </div>
      </section>
    );

    return (
      <div className="reference-picker__scroll">
        {group("旧约", oldTestament)}
        {group("新约", newTestament)}
      </div>
    );
  };

  const renderChapters = () => {
    if (chaptersLoading) {
      return (
        <div className="reference-picker__state">
          <Spin />
        </div>
      );
    }
    if (chaptersError && selectedBookId !== null) {
      return renderError(
        () => loadChapters(selectedBookId),
        "无法加载章节信息"
      );
    }

    return (
      <div className="reference-picker__scroll">
        <div className="reference-picker__number-grid reference-picker__chapter-grid">
          {chapters.map(({ chapter }) => (
            <button
              type="button"
              key={chapter}
              className="reference-picker__number-cell"
              onClick={() => selectChapter(chapter)}
            >
              {chapter}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderVersePanel = (chapter: number) => {
    const info = chapters.find((item) => item.chapter === chapter);
    if (!info) return null;

    return (
      <section className="reference-picker__verse-panel" key={chapter}>
        <div className="reference-picker__verse-heading">第 {chapter} 章</div>
        <div className="reference-picker__number-grid reference-picker__verse-grid">
          {Array.from({ length: info.verse_count }, (_, index) => {
            const point = { chapter, verse: index + 1 };
            const isStart = samePoint(draftStart, point);
            const isEnd = samePoint(draftEnd, point);
            const isInRange =
              !!draftStart &&
              !!draftEnd &&
              comparePoints(point, draftStart) >= 0 &&
              comparePoints(point, draftEnd) <= 0;
            const classes = [
              "reference-picker__number-cell",
              isInRange ? "is-in-range" : "",
              isStart ? "is-start" : "",
              isEnd ? "is-end" : "",
            ]
              .filter(Boolean)
              .join(" ");

            return (
              <button
                type="button"
                key={point.verse}
                className={classes}
                onClick={() => selectVerse(point)}
              >
                {point.verse}
              </button>
            );
          })}
        </div>
      </section>
    );
  };

  const renderVerses = () => {
    if (chaptersLoading) {
      return (
        <div className="reference-picker__state">
          <Spin />
        </div>
      );
    }
    if (chaptersError && selectedBookId !== null) {
      return renderError(
        () => loadChapters(selectedBookId),
        "无法加载章节信息"
      );
    }

    const visible = [visibleChapter];
    if (visibleChapter < maxChapter) visible.push(visibleChapter + 1);

    return (
      <>
        <div className="reference-picker__chapter-controls">
          <Button
            type="text"
            icon={<LeftOutlined />}
            disabled={visibleChapter <= 1}
            aria-label="向前一章"
            onClick={() => setVisibleChapter((chapter) => chapter - 1)}
          />
          <span>
            {visible.length === 2
              ? `第 ${visible[0]}–${visible[1]} 章`
              : `第 ${visible[0]} 章`}
          </span>
          <Button
            type="text"
            icon={<RightOutlined />}
            disabled={visibleChapter >= maxChapter}
            aria-label="向后一章"
            onClick={() => setVisibleChapter((chapter) => chapter + 1)}
          />
        </div>
        <div className="reference-picker__verse-panels">
          {visible.map(renderVersePanel)}
        </div>
      </>
    );
  };

  const content = (
    <div className="reference-picker">
      <div className="reference-picker__header">
        <div className="reference-picker__title">
          {selectedBook?.name ?? "选择经卷"}
        </div>
        <div className="reference-picker__steps">
          <button
            type="button"
            className={view === "books" ? "is-active" : ""}
            onClick={() => setView("books")}
          >
            经卷
          </button>
          <button
            type="button"
            className={view === "chapters" ? "is-active" : ""}
            disabled={!selectedBook}
            onClick={() => setView("chapters")}
          >
            章
          </button>
          <button
            type="button"
            className={view === "verses" ? "is-active" : ""}
            disabled={!selectedBook}
            onClick={() => setView("verses")}
          >
            节
          </button>
        </div>
      </div>

      <div className="reference-picker__body">
        {view === "books" && renderBooks()}
        {view === "chapters" && renderChapters()}
        {view === "verses" && renderVerses()}
      </div>

      <div className="reference-picker__footer">
        <div className="reference-picker__selection">
          <span>{rangeLabel}</span>
          {awaitingEnd && <small>请选择结束经节</small>}
        </div>
        <div className="reference-picker__actions">
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button
            type="primary"
            disabled={!draftStart || !draftEnd}
            onClick={confirm}
          >
            确定
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      placement="bottomLeft"
      open={open}
      onOpenChange={handleOpenChange}
      overlayClassName="reference-picker-popover"
      arrow={false}
    >
      <button
        type="button"
        className={`reference-picker-trigger${open ? " is-open" : ""}`}
      >
        <span className={value ? "" : "is-placeholder"}>
          {value || "选择经卷与起止经节"}
        </span>
        {value ? <BookOutlined /> : <DownOutlined />}
      </button>
    </Popover>
  );
}
