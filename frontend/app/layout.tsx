import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LyricSync AI | Pro Audio Separation & Lyric Videos",
  description: "AI-powered vocal extraction and automatic lyric video generation for creators.",
};

import Providers from "./providers";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${outfit.variable} h-full antialiased dark`}
      suppressHydrationWarning
    >
      <body 
        className="min-h-full flex flex-col font-sans bg-background text-foreground"
        suppressHydrationWarning
      >
        <Providers>
          <Toaster position="top-center" />
          {children}
        </Providers>
      </body>
    </html>
  );
}
