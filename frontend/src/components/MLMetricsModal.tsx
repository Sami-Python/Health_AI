"use client";

import { useEffect, useState } from "react";
import { X, Activity, Brain, Calendar } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { fetchWithRetry } from "@/lib/utils";
import Skeleton from "./ui/Skeleton";

interface MLMetrics {
    r2: number;
    mae: number;
    last_trained: string;
    top_features?: Record<string, number>;
    data_points?: number;
}

// Map technical Garmin/XGBoost feature names to human-readable Finnish
const featureNameMap: Record<string, string> = {
    "bodyBatteryHighestValue": "Yön latautuminen (max)",
    "bodyBatteryDuringSleep": "Unenaikainen latautuva akku",
    "poor_night_flag": "Heikon palautumisen varoitus",
    "stressPercentage": "Päivittäinen stressitaso",
    "bodyBatteryAtWakeTime": "Vireystila herätessä",
    "stressDuration": "Stressin kesto",
    "restStressDuration": "Lepohetkien stressi",
    "totalSleep_minutes": "Unen yhteiskesto",
    "averageStressLevel": "Keskimääräinen stressi",
    "workout_calories_roll_7d": "Viimeisen viikon kuormitus",
    "restingHeartRate": "Leposyke",
    "avgWakingRespirationValue": "Hengitystiheys",
    "totalSteps": "Askeleet",
    "measurableAsleepDuration": "Syvä/kevyt uni"
};

interface MLMetricsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function MLMetricsModal({ isOpen, onClose }: MLMetricsModalProps) {
    const { user } = useAuth();
    const [metrics, setMetrics] = useState<MLMetrics | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && user) {
            setLoading(true);
            user.getIdToken().then((token) => {
                fetchWithRetry(`${process.env.NEXT_PUBLIC_API_URL}/ai/model-metrics`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })
                    .then((res) => res.json())
                    .then((data) => {
                        setMetrics(data);
                        setLoading(false);
                    })
                    .catch((err) => {
                        console.error("Failed to fetch metrics", err);
                        setLoading(false);
                    });
            });
        }
    }, [isOpen, user]);

    if (!isOpen) return null;

    // Color coding logic
    const getR2Color = (r2: number) => {
        if (r2 >= 0.8) return "text-green-400 bg-green-400/20 border-green-400/30";
        if (r2 >= 0.5) return "text-yellow-400 bg-yellow-400/20 border-yellow-400/30";
        return "text-red-400 bg-red-400/20 border-red-400/30";
    };

    const getBarColor = (r2: number) => {
        if (r2 >= 0.8) return "bg-green-500";
        if (r2 >= 0.5) return "bg-yellow-500";
        return "bg-red-500";
    };

    const r2Percentage = metrics ? Math.round(metrics.r2 * 100) : 0;
    const r2ColorClass = metrics ? getR2Color(metrics.r2) : "";
    const barColorClass = metrics ? getBarColor(metrics.r2) : "bg-slate-700";

    const topDrivers = metrics?.top_features ? Object.entries(metrics.top_features).slice(0, 5) : [];

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-500/20 rounded-lg">
                            <Brain className="h-5 w-5 text-purple-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">AI Model Health</h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {loading ? (
                        <div className="space-y-6">
                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <Skeleton className="h-3 w-24" />
                                    <Skeleton className="h-8 w-16 rounded-full" />
                                </div>
                                <Skeleton className="h-3 w-full rounded-full" />
                                <Skeleton className="h-3 w-48" />
                            </div>
                            <Skeleton className="h-[200px] rounded-xl" />
                        </div>
                    ) : metrics ? (
                        <>
                            {/* R2 Score Section */}
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-slate-400">Accuracy (R² Score)</span>
                                    <span className={`text-lg font-bold px-3 py-1 rounded-full border ${r2ColorClass}`}>
                                        {r2Percentage}%
                                    </span>
                                </div>
                                <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${barColorClass} transition-all duration-1000 ease-out`}
                                        style={{ width: `${r2Percentage}%` }}
                                    ></div>
                                </div>
                                <p className="text-xs text-slate-500">
                                    Explains {r2Percentage}% of the variance in your recovery data.
                                    {metrics.r2 >= 0.8 ? " Excellent predictive power." : metrics.r2 >= 0.5 ? " Moderate accuracy." : " Needs more training data."}
                                </p>
                            </div>

                            {/* Top Drivers Section */}
                            {topDrivers.length > 0 && (
                                <div className="space-y-3 p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                        <Activity className="h-3 w-3" />
                                        Drivers of your Recovery
                                    </h4>
                                    <div className="space-y-2">
                                        {topDrivers.map(([key, val], idx) => (
                                            <div key={key} className="flex flex-col gap-1">
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-slate-300">{featureNameMap[key] || key}</span>
                                                    <span className="text-purple-400 font-mono">{(val * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="h-1 w-full bg-slate-700/50 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-purple-500/50 rounded-full"
                                                        style={{ width: `${(val / (topDrivers[0][1] as number)) * 100}%` }}
                                                    ></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <p className="text-[10px] text-slate-500 italic mt-2">
                                        These factors have the strongest influence on the AI's predictions for your readiness.
                                    </p>
                                </div>
                            )}

                            {/* MAE & Training Stats */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                                    <div className="flex items-center gap-2 mb-2 text-slate-400">
                                        <Activity className="h-4 w-4" />
                                        <span className="text-xs font-medium uppercase tracking-wider">MAE Error</span>
                                    </div>
                                    <p className="text-2xl font-bold text-white">{metrics.mae.toFixed(2)}</p>
                                    <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">
                                        Avg deviation: ~{metrics.mae.toFixed(1)} points on 0-100 scale.
                                    </p>
                                </div>

                                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                                    <div className="flex items-center gap-2 mb-2 text-slate-400">
                                        <Calendar className="h-4 w-4" />
                                        <span className="text-xs font-medium uppercase tracking-wider">Update Status</span>
                                    </div>
                                    <p className="text-sm font-bold text-white break-words">{metrics.last_trained}</p>
                                    <p className="text-[10px] text-slate-500 mt-1">
                                        Trained on {metrics.data_points || '--'} days of data.
                                    </p>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="text-center text-slate-500 py-4">No metrics available</div>
                    )}
                </div>

                <div className="p-4 bg-slate-950/50 border-t border-slate-800 text-center">
                    <p className="text-xs text-slate-600">Health AI v1.0 • XGBoost 2.0 • SHAP Insights</p>
                </div>
            </div>
        </div>
    );
}
