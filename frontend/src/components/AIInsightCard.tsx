import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Sparkles } from "lucide-react";
import Skeleton from "./ui/Skeleton";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";

export default function AIInsightCard() {
    const { user } = useAuth();
    const [insight, setInsight] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) return;

        const fetchInsight = async () => {
            try {
                const token = await user.getIdToken();
                const res = await fetchWithRetry(`${API_BASE_URL}/ai/insight`, {
                    headers: { Authorization: `Bearer ${token}` }
                });

                if (res.ok) {
                    const json = await res.json();
                    setInsight(json.insight);
                } else {
                    setInsight("AI ei tavoitettavissa juuri nyt.");
                }
            } catch (err) {
                console.error("Failed to fetch insight", err);
                setInsight("AI-yhteysvirhe.");
            } finally {
                setLoading(false);
            }
        };

        fetchInsight();
    }, [user]);

    return (
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900 to-violet-900 p-1 shadow-lg border border-indigo-700/50">
            <div className="absolute top-0 right-0 -mt-4 -mr-4 h-24 w-24 rounded-full bg-white/10 blur-xl"></div>

            <div className="relative rounded-xl bg-slate-950/40 p-5 backdrop-blur-sm">
                <div className="flex items-start gap-4">
                    <div className="rounded-full bg-indigo-500/20 p-2 text-indigo-300">
                        <Sparkles className="h-6 w-6" />
                    </div>

                    <div className="flex-1">
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-indigo-200 mb-1">
                            Your Personal AI Coach is ready for you
                        </h3>

                        {loading ? (
                            <div className="space-y-2 mt-2">
                                <Skeleton className="h-4 w-[90%] bg-indigo-500/20" />
                                <Skeleton className="h-4 w-[60%] bg-indigo-500/20" />
                            </div>
                        ) : (
                            <p className="text-lg font-medium text-white italic leading-relaxed">
                                "{insight}"
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
