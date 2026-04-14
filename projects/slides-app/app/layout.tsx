import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "XRefKit Slides App",
  description: "DexCode-style slide decks for XRefKit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
