import Link from "next/link";
import { Button } from "@/components/ui/button";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Health AI Coach",
  description: "Your personnel AI powered endurance coach.",
  openGraph: {
    title: "Health AI Coach",
    description: "Your personnel AI powered endurance coach. Train smarter, not harder.",
    url: "https://personal-ai-coach-92c39.web.app",
    siteName: "Health AI",
    images: [
      {
        url: "/hero-fitness.png",
        width: 1200,
        height: 630,
      },
    ],
    locale: "en_US",
    type: "website",
  },
};

export default function Home() {
  return (
    <div className="flex h-screen flex-col items-center justify-center bg-slate-950 text-white">
      <div className="flex max-w-xl flex-col items-center space-y-8 text-center">
        <h1 className="text-5xl font-bold tracking-tighter bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Personal AI Coach
        </h1>
        <p className="text-xl text-slate-400">
          Your intelligent training companion. Powered by Data, Guided by AI.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/login">
            <Button size="lg" className="px-8 font-semibold">
              Log In
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button size="lg" variant="outline" className="px-8">
              Go to Dashboard
            </Button>
          </Link>
          <a href="/personal-ai-coach.apk" download>
            <Button size="lg" className="px-8 bg-emerald-600 hover:bg-emerald-500 text-white border-none shadow-lg shadow-emerald-500/20">
              Download for Android
            </Button>
          </a>
        </div>
      </div>
    </div>
  );
}
