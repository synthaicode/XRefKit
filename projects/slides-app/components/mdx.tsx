import type { ComponentPropsWithoutRef } from "react";

function createAssetUrl(deckSlug: string, src: string) {
  return `/api/decks/${deckSlug}/assets/${src}`;
}

export function getMdxComponents(deckSlug: string) {
  function SlideImage({
    src,
    alt,
    caption,
  }: {
    src: string;
    alt: string;
    caption?: string;
  }) {
    return (
      <figure className="slide-figure">
        <img src={createAssetUrl(deckSlug, src)} alt={alt} className="slide-image" />
        {caption ? <figcaption>{caption}</figcaption> : null}
      </figure>
    );
  }

  function Callout(props: ComponentPropsWithoutRef<"div">) {
    return <div {...props} className="slide-callout" />;
  }

  return {
    SlideImage,
    Callout,
  };
}
