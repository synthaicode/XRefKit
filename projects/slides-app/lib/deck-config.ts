export type DeckConfig = {
  slug: string;
  title: string;
  description: string;
  sourceLabel: string;
  assetDir: string;
};

export function defineDeckConfig(config: DeckConfig) {
  return config;
}
