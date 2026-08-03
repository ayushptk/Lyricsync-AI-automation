import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import { Toaster } from "react-hot-toast";
import "./globals.css";
import TransitionOverlay from "@/components/transitions/TransitionOverlay";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LyricSync AI | Cinematic Audio Separation",
  description: "AI-powered vocal extraction and cinematic lyric video generation.",
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
      className={`${inter.variable} ${manrope.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body
        className="min-h-full flex flex-col font-sans bg-background text-text-primary tracking-tight"
        suppressHydrationWarning
      >
        <Providers>
          <Toaster position="top-center" />
          {/* Geometric page transition overlay — fixed, z-9999, above everything */}
          <TransitionOverlay />
          {children}
        </Providers>
      </body>
    </html>
  );
}
