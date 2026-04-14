"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

type PresenterShellProps = {
  deckSlug: string;
  slideNumber: number;
  children: React.ReactNode;
};

const channelName = "xrefkit-slides-sync";

export function PresenterShell({
  deckSlug,
  slideNumber,
  children,
}: PresenterShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const channel = new BroadcastChannel(channelName);

    const onMessage = (event: MessageEvent<{ deck?: string; slide?: number }>) => {
      if (event.data.deck === deckSlug && event.data.slide) {
        router.replace(`${pathname}?slide=${event.data.slide}`);
      }
    };

    channel.addEventListener("message", onMessage);
    return () => {
      channel.removeEventListener("message", onMessage);
      channel.close();
    };
  }, [deckSlug, pathname, router]);

  useEffect(() => {
    const channel = new BroadcastChannel(channelName);

    function onKeyDown(event: KeyboardEvent) {
      const nextKeys = ["ArrowRight", "ArrowDown", " ", "Enter", "PageDown"];
      const prevKeys = ["ArrowLeft", "ArrowUp", "PageUp"];

      if (nextKeys.includes(event.key)) {
        channel.postMessage({ deck: deckSlug, slide: slideNumber + 1 });
      }

      if (prevKeys.includes(event.key) && slideNumber > 1) {
        channel.postMessage({ deck: deckSlug, slide: slideNumber - 1 });
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      channel.close();
    };
  }, [deckSlug, slideNumber]);

  return <main className="presenter-shell">{children}</main>;
}
