import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import RecoveryChart from "./charts/RecoveryChart";
import LoadChart from "./charts/LoadChart";
import PerformanceChart from "./charts/PerformanceChart";
import { Info } from "lucide-react";
import Skeleton from "./ui/Skeleton";
import AIInsightCard from "./AIInsightCard";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";

// Helper for Info Tooltip
function InfoTooltip({ text }: { text: string }) {
    return (
        <div className="group relative ml-2 inline-block">
            <Info className="h-4 w-4 text-slate-500 hover:text-blue-400 cursor-help" />
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-64 -translate-x-1/2 rounded-lg border border-slate-700 bg-slate-900 p-2 text-xs text-slate-200 shadow-xl group-hover:block z-50">
                {text}
                <div className="absolute -bottom-1 left-1/2 -ml-1 h-2 w-2 rotate-45 border-r border-b border-slate-700 bg-slate-900"></div>
            </div>
        </div>
    );
}

export default function ChartsSection() {
    const { user } = useAuth();
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!user) return;
        const fetchData = async () => {
            try {
                const token = await user.getIdToken();
                const res = await fetchWithRetry(`${API_BASE_URL}/metrics/history`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (!res.ok) throw new Error("Failed to fetch history");
                const json = await res.json();
                setData(json);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [user]);

    if (loading) return (
        <div className="space-y-6">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-24 w-full rounded-2xl" />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Skeleton className="h-[350px] rounded-xl" />
                <Skeleton className="h-[350px] rounded-xl" />
                <Skeleton className="col-span-1 lg:col-span-2 h-[400px] rounded-xl" />
            </div>
        </div>
    );
    if (error) return <div className="text-red-400 text-sm p-4 text-center">Failed to load charts: {error}</div>;

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent flex items-center">
                Performance Analytics
            </h2>

            {/* AI Insight Card */}
            <div className="mb-6">
                <AIInsightCard />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 1. Recovery Chart */}
                <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm h-[350px]">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        Recovery Status
                        <InfoTooltip text="Comparison of Body Battery (max daily value) vs. Sleep Duration. Helps visualize if your recovery matches your sleep volume." />
                    </h3>
                    <div className="h-[250px]">
                        <RecoveryChart data={data} />
                    </div>
                </div>

                {/* 2. Load Chart */}
                <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm h-[350px]">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        Daily Load
                        <InfoTooltip text="Daily training load (proxy from calories/duration). High bars indicate strenuous training days." />
                    </h3>
                    <div className="h-[250px]">
                        <LoadChart data={data} />
                    </div>
                </div>

                {/* 3. Performance Chart (Full Width) */}
                <div className="col-span-1 lg:col-span-2 p-6 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm min-h-[480px]">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        Performance Management
                        <InfoTooltip text="Tracks Fitness (CTL), Fatigue (ATL), and Form (TSB) over time to optimize training peaks and avoid overtraining." />
                    </h3>
                    <div className="h-[300px]">
                        <PerformanceChart data={data} />
                    </div>
                </div>
            </div>
        </div>
    );
}
