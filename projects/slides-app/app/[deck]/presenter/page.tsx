import Link from "next/link";
import { notFound } from "next/navigation";
import { PresenterShell } from "../../../components/presenter-shell";
import { getCompiledSlide, getDeckBySlug } from "../../../lib/decks";

type PresenterPageProps = {
  params: Promise<{ deck: string }>;
  searchParams: Promise<{ slide?: string }>;
};

export default async function PresenterPage({
  params,
  searchParams,
}: PresenterPageProps) {
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
    <PresenterShell deckSlug={deck.slug} slideNumber={slideNumber}>
      <div className="presenter-frame">
        <div className="presenter-topbar">
          <span>
            {deck.title} / {slideNumber} / {deck.slides.length}
          </span>
          <Link href={`/${deck.slug}?slide=${slideNumber}`}>Back to viewer</Link>
        </div>
        <article className="slide-stage presenter-stage">{content}</article>
        <p className="presenter-caption">{currentSlide.title}</p>
      </div>
    </PresenterShell>
  );
}
