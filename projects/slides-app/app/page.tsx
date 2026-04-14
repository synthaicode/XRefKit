import Link from "next/link";
import { listDecks } from "../lib/decks";

export default async function HomePage() {
  const decks = await listDecks();

  return (
    <main className="home-shell">
      <section className="home-hero">
        <p className="home-kicker">XRefKit Slides App</p>
        <h1>MDX deck viewer for repository-managed presentations</h1>
        <p className="home-copy">
          `projects/slides-app` hosts an isolated slide app so XRefKit can keep
          its knowledge repository structure while adding a DexCode-style viewer.
        </p>
      </section>

      <section className="deck-grid">
        {decks.map((deck) => (
          <Link key={deck.slug} href={`/${deck.slug}`} className="deck-tile">
            <span className="deck-pill">{deck.slideCount} slides</span>
            <h2>{deck.title}</h2>
            <p>{deck.description}</p>
            <span className="deck-source">{deck.sourceLabel}</span>
          </Link>
        ))}
      </section>
    </main>
  );
}
