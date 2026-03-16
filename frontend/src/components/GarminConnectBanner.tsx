import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useGarminStatus } from "@/hooks/useGarminStatus";
import { PlugZap, ChevronRight, Lock, Key } from "lucide-react";

export default function GarminConnectBanner() {
    const { status, loading } = useGarminStatus();

    // 1. Show MFA required banner if connected but needs re-auth
    if (!loading && status?.connected && status?.garmin_mfa_required) {
        return (
            <div className="relative overflow-hidden rounded-xl border border-red-500/30 bg-gradient-to-r from-red-900/40 to-orange-900/40 p-4 md:p-6 backdrop-blur-sm animate-in fade-in slide-in-from-top-4 duration-500">
                <div className="absolute -top-12 -right-12 h-32 w-32 rounded-full bg-red-500/20 blur-3xl"></div>
                <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-4 text-center md:text-left">
                    <div className="flex flex-col md:flex-row items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-500/20 text-red-400 ring-1 ring-red-500/40">
                            <Key className="h-6 w-6" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Garmin Connection Expired</h3>
                            <p className="text-sm text-slate-300 max-w-md">
                                Your Garmin session has expired and requires re-authentication. Please reconnect to keep your data syncing.
                            </p>
                        </div>
                    </div>

                    <Link href="/settings">
                        <Button className="bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-500/20 group">
                            Reconnect Now
                            <ChevronRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                        </Button>
                    </Link>
                </div>
            </div>
        );
    }

    // 2. Don't show if loading or already fully connected
    if (loading || status?.connected) {
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
