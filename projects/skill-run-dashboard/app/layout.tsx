import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "XRefKit Skill Run Dashboard",
  description: "Local dashboard for XRefKit Skill run logs",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
