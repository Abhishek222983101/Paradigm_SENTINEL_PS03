import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// SENTINEL Typography System
// Bricolage Grotesque - Aggressive, brutal headings
const bricolage = Bricolage_Grotesque({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["200", "300", "400", "500", "600", "700", "800"],
  display: "swap",
});

// JetBrains Mono - Terminal-grade data display
const jetbrains = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "SENTINEL | Financial Fraud Intelligence",
    template: "%s | SENTINEL",
  },
  description:
    "AI-Powered Financial Fraud Detection Platform. Real-time multi-modal deep learning for transaction security.",
  keywords: [
    "fraud detection",
    "financial security",
    "AI",
    "machine learning",
    "transaction monitoring",
    "cybersecurity",
  ],
  authors: [{ name: "Team Paradigm" }],
  creator: "Team Paradigm",
  publisher: "SENTINEL",
  robots: "index, follow",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://sentinel-fraud.ai",
    siteName: "SENTINEL",
    title: "SENTINEL | Financial Fraud Intelligence",
    description: "AI-Powered Financial Fraud Detection Platform",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "SENTINEL - Financial Fraud Intelligence Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "SENTINEL | Financial Fraud Intelligence",
    description: "AI-Powered Financial Fraud Detection Platform",
    images: ["/og-image.png"],
  },
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#050505" },
    { media: "(prefers-color-scheme: light)", color: "#050505" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${bricolage.variable} ${jetbrains.variable} h-full`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col bg-void text-white antialiased selection:bg-cyber-cyan selection:text-void">
        {/* Noise overlay for texture */}
        <div 
          className="fixed inset-0 pointer-events-none z-[100] opacity-[0.015]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
          aria-hidden="true"
        />
        
        {/* Main content */}
        <main className="flex-1 relative z-0">
          {children}
        </main>
      </body>
    </html>
  );
}
