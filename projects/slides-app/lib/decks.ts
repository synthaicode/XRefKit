import fs from "node:fs/promises";
import path from "node:path";
import { cache } from "react";
import matter from "gray-matter";
import { compileMDX } from "next-mdx-remote/rsc";
import aiOrganizationConfig from "../decks/ai-organization/deck.config";
import aiCharacteristicsConfig from "../decks/ai-characteristics/deck.config";
import businessExecutionFoundationConfig from "../decks/business-execution-foundation/deck.config";
import effectiveAiUseConfig from "../decks/effective-ai-use/deck.config";
import { getMdxComponents } from "../components/mdx";
import type { DeckConfig } from "./deck-config";

export type SlideSummary = {
  number: number;
  title: string;
  notes: string;
  thumbnailUrl: string;
  sourcePath: string;
};

export type DeckDetail = {
  slug: string;
  title: string;
  description: string;
  sourceLabel: string;
  assetDir: string;
  slides: SlideSummary[];
};

const DECKS: DeckConfig[] = [
  aiCharacteristicsConfig,
  effectiveAiUseConfig,
  aiOrganizationConfig,
  businessExecutionFoundationConfig,
];

function deckDir(slug: string) {
  return path.join(process.cwd(), "decks", slug);
}

function toAssetUrl(slug: string, image: string) {
  return `/api/decks/${slug}/assets/${image}`;
}

async function loadSlideSummaries(slug: string) {
  const files = (await fs.readdir(deckDir(slug)))
    .filter((file) => file.endsWith(".mdx"))
    .sort((a, b) => a.localeCompare(b, "en"));

  return Promise.all(
    files.map(async (file, index) => {
      const sourcePath = path.join(deckDir(slug), file);
      const source = await fs.readFile(sourcePath, "utf8");
      const { data } = matter(source);

      return {
        number: index + 1,
        title: String(data.title ?? file),
        notes: String(data.notes ?? ""),
        thumbnailUrl: toAssetUrl(slug, String(data.image ?? "")),
        sourcePath,
      } satisfies SlideSummary;
    }),
  );
}

const loadDecks = cache(async () => {
  const deckDetails = await Promise.all(
    DECKS.map(async (config) => ({
      ...config,
      slides: await loadSlideSummaries(config.slug),
    })),
  );

  return deckDetails;
});

export async function listDecks() {
  const decks = await loadDecks();
  return decks.map((deck) => ({
    slug: deck.slug,
    title: deck.title,
    description: deck.description,
    sourceLabel: deck.sourceLabel,
    slideCount: deck.slides.length,
  }));
}

export async function getDeckBySlug(slug: string): Promise<DeckDetail | null> {
  const decks = await loadDecks();
  return decks.find((deck) => deck.slug === slug) ?? null;
}

export async function getCompiledSlide(slug: string, slideNumber: number) {
  const deck = await getDeckBySlug(slug);
  if (!deck) {
    return null;
  }

  const slide = deck.slides[slideNumber - 1];
  if (!slide) {
    return null;
  }

  const source = await fs.readFile(slide.sourcePath, "utf8");
  const { content } = await compileMDX({
    source,
    components: getMdxComponents(slug),
    options: {
      parseFrontmatter: true,
    },
  });

  return content;
}
