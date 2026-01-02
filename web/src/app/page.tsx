import Link from "next/link";
import { Button } from "@/components/ui/button";

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

        <div className="flex gap-4">
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
        </div>
      </div>
    </div>
  );
}
