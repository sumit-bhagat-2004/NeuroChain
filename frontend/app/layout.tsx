'use client';

import type { Metadata } from "next";
import { WalletProvider } from "@/lib/WalletContext";
import "./globals.css";

// Note: Metadata can't be used in client components, but this layout is already client due to WalletProvider

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <WalletProvider>
          {children}
        </WalletProvider>
      </body>
    </html>
  );
}
