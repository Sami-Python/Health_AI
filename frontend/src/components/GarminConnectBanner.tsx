import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useGarminStatus } from "@/hooks/useGarminStatus";
import { PlugZap, ChevronRight } from "lucide-react";

export default function GarminConnectBanner() {
    const { status, loading } = useGarminStatus();

    // Don't show if loading or already connected
    if (loading || (status?.connected)) {
        return null;
    }

    return (
        <div className="relative overflow-hidden rounded-xl border border-blue-500/30 bg-gradient-to-r from-blue-900/40 to-indigo-900/40 p-4 md:p-6 backdrop-blur-sm animate-in fade-in slide-in-from-top-4 duration-500">
            {/* Background decorative elements */}
            <div className="absolute -top-12 -right-12 h-32 w-32 rounded-full bg-blue-500/20 blur-3xl"></div>
            <div className="absolute -bottom-12 -left-12 h-32 w-32 rounded-full bg-indigo-500/20 blur-3xl"></div>

            <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
                <div className="flex flex-col md:flex-row items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/40">
                        <PlugZap className="h-6 w-6" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">Connect your Garmin account</h3>
                        <p className="text-sm text-slate-300 max-w-md">
                            Sync your workouts, heart rate, and sleep data automatically to unlock personalized AI coaching insights.
                        </p>
                    </div>
                </div>

                <Link href="/settings">
                    <Button className="bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 group">
                        Connect Now
                        <ChevronRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                </Link>
            </div>
        </div>
    );
}
