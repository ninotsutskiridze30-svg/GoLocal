import type { Metadata } from "next";
import { Fraunces, JetBrains_Mono, Manrope } from "next/font/google";
import { AmbientScene } from "@/components/AmbientScene";
import "./globals.css";

const display = Fraunces({ subsets: ["latin"], variable: "--font-fraunces", style: ["normal", "italic"], axes: ["SOFT", "WONK", "opsz"] });
const sans = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "GoLocal AI · Find something worth your night",
  description: "AI-powered discovery of local events, moods, budgets and small adventures in Tbilisi.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable} ${mono.variable} h-full antialiased`}>
      <body className="min-h-full bg-night font-sans text-paper">
        <AmbientScene />
        <div className="relative z-10 flex min-h-screen flex-col">{children}</div>
      </body>
    </html>
  );
}
