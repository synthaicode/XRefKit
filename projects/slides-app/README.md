# XRefKit Slides App

This app adds a DexCode-style slide viewer under `projects/slides-app/`.

## License note

This app includes an implementation approach derived from `co-r-e/dexcode`.
See [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

## Start

```powershell
cd projects/slides-app
npm install
npm run dev
```

Open `http://localhost:3000`.

## Current scope

- isolated Next.js app under `projects/`
- deck listing page
- MDX slide files under `decks/<deck>/`
- sidebar thumbnails
- `?slide=N` deep links
- speaker notes panel
- presenter route with BroadcastChannel sync
- asset streaming from existing repository folders

## Add another deck

1. Create `decks/<slug>/deck.config.ts`
2. Add numbered `.mdx` slide files
3. Point `assetDir` to an existing repository asset folder
4. Register the deck in `lib/decks.ts`
