import { NextRequest } from "next/server";
import fs from "node:fs/promises";
import path from "node:path";
import { getDeckBySlug } from "../../../../../../lib/decks";

const MIME_TYPES: Record<string, string> = {
  ".avif": "image/avif",
  ".gif": "image/gif",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ deck: string; assetPath: string[] }> },
) {
  const { deck: deckSlug, assetPath } = await context.params;
  const deck = await getDeckBySlug(deckSlug);

  if (!deck) {
    return new Response("Deck not found", { status: 404 });
  }

  const assetFile = path.resolve(deck.assetDir, ...assetPath);
  const assetRoot = path.resolve(deck.assetDir);

  if (!assetFile.startsWith(assetRoot)) {
    return new Response("Invalid asset path", { status: 400 });
  }

  try {
    const buffer = await fs.readFile(assetFile);
    const ext = path.extname(assetFile).toLowerCase();

    return new Response(buffer, {
      status: 200,
      headers: {
        "Content-Type": MIME_TYPES[ext] ?? "application/octet-stream",
        "Cache-Control": "public, max-age=3600",
      },
    });
  } catch {
    return new Response("Asset not found", { status: 404 });
  }
}
