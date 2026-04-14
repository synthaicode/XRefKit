"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import type { DeckDetail, SlideSummary } from "../lib/decks";

type SlideViewerShellProps = {
  deck: DeckDetail;
  currentSlide: SlideSummary;
  slideNumber: number;
  children: React.ReactNode;
};

const channelName = "xrefkit-slides-sync";

export function SlideViewerShell({
  deck,
  currentSlide,
  slideNumber,
  children,
}: SlideViewerShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const channel = new BroadcastChannel(channelName);
    channel.postMessage({ deck: deck.slug, slide: slideNumber });
    return () => channel.close();
  }, [deck.slug, slideNumber]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (target && /input|textarea|select/i.test(target.tagName)) {
        return;
      }

      const nextKeys = ["ArrowRight", "ArrowDown", " ", "Enter", "PageDown"];
      const prevKeys = ["ArrowLeft", "ArrowUp", "PageUp"];

      if (nextKeys.includes(event.key) && slideNumber < deck.slides.length) {
        event.preventDefault();
        router.push(`${pathname}?slide=${slideNumber + 1}`);
      }

      if (prevKeys.includes(event.key) && slideNumber > 1) {
        event.preventDefault();
        router.push(`${pathname}?slide=${slideNumber - 1}`);
      }

      if (event.key === "Home") {
        event.preventDefault();
        router.push(`${pathname}?slide=1`);
      }

      if (event.key === "End") {
        event.preventDefault();
        router.push(`${pathname}?slide=${deck.slides.length}`);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [deck.slides.length, pathname, router, slideNumber]);

  return (
    <main className="viewer-shell">
      <aside className="viewer-sidebar">
        <div className="sidebar-header">
          <Link href="/" className="back-link">
            All decks
          </Link>
          <h1>{deck.title}</h1>
          <p>{deck.description}</p>
        </div>

        <nav className="thumb-list" aria-label="Slides">
          {deck.slides.map((slide) => {
            const isActive = slide.number === slideNumber;
            return (
              <Link
                key={slide.number}
                href={`/${deck.slug}?slide=${slide.number}`}
                className={isActive ? "thumb-card active" : "thumb-card"}
              >
                <span className="thumb-index">
                  {String(slide.number).padStart(2, "0")}
                </span>
                <img
                  src={slide.thumbnailUrl}
                  alt={slide.title}
                  className="thumb-image"
                />
                <span className="thumb-title">{slide.title}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      <section className="viewer-main">
        <header className="viewer-topbar">
          <div>
            <p className="slide-counter">
              Slide {slideNumber} / {deck.slides.length}
            </p>
            <h2>{currentSlide.title}</h2>
          </div>

          <div className="viewer-actions">
            <Link href={`/${deck.slug}/presenter?slide=${slideNumber}`}>
              Presenter
            </Link>
            <Link
              href={`/${deck.slug}?slide=${Math.max(1, slideNumber - 1)}`}
              aria-disabled={slideNumber === 1}
            >
              Prev
            </Link>
            <Link
              href={`/${deck.slug}?slide=${Math.min(deck.slides.length, slideNumber + 1)}`}
              aria-disabled={slideNumber === deck.slides.length}
            >
              Next
            </Link>
          </div>
        </header>

        <article className="slide-stage">{children}</article>

        <section className="notes-panel">
          <p className="notes-label">Speaker Notes</p>
          <p className="notes-body">{currentSlide.notes}</p>
        </section>
      </section>
    </main>
  );
}
