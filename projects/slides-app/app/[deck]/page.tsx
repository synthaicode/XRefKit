import { notFound } from "next/navigation";
import { getCompiledSlide, getDeckBySlug } from "../../lib/decks";
import { SlideViewerShell } from "../../components/slide-viewer-shell";

type DeckPageProps = {
  params: Promise<{ deck: string }>;
  searchParams: Promise<{ slide?: string }>;
};

export default async function DeckPage({
  params,
  searchParams,
}: DeckPageProps) {
  const { deck: deckSlug } = await params;
  const query = await searchParams;
  const deck = await getDeckBySlug(deckSlug);

  if (!deck) {
    notFound();
  }

  const rawSlide = Number.parseInt(query.slide ?? "1", 10);
  const slideNumber = Number.isFinite(rawSlide)
    ? Math.min(Math.max(rawSlide, 1), deck.slides.length)
    : 1;
  const currentSlide = deck.slides[slideNumber - 1];

  const content = await getCompiledSlide(deck.slug, slideNumber);

  return (
    <SlideViewerShell
      deck={deck}
      currentSlide={currentSlide}
      slideNumber={slideNumber}
    >
      {content}
    </SlideViewerShell>
  );
}
