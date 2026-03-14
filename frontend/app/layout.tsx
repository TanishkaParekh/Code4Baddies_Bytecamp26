import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CascadeRx — Medication Safety Checker",
  description: "Find hidden drug cascade interactions that pairwise checkers miss.",
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
