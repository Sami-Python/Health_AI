"use client";

import { LucideIcon } from "lucide-react";

interface StatCardProps {
    title: string;
    value: string | number;
    description: string;
    icon?: LucideIcon;
    trend?: "up" | "down" | "neutral";
    loading?: boolean;
}

export function StatCard({ title, value, description, icon: Icon, trend, loading, trendData }: StatCardProps & { trendData?: number[] }) {
    if (loading) {
        return (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm backdrop-blur-sm animate-pulse">
                <div className="flex justify-between items-start mb-2">
                    <div className="h-3 w-20 bg-slate-700 rounded mb-4"></div>
                </div>
                <div className="h-8 w-16 bg-slate-700 rounded mb-2"></div>
                <div className="h-3 w-32 bg-slate-700 rounded"></div>
            </div>
        )
    }

    // Sparkline Logic
    let sparklineSvg = null;
    if (trendData && trendData.length > 1) {
        const height = 40;
        const width = 120;
        const min = Math.min(...trendData);
        const max = Math.max(...trendData);
        const range = max - min || 1;

        // Calculate points
        const points = trendData.map((d, i) => {
            const x = (i / (trendData.length - 1)) * width;
            // Invert Y (SVG 0 is top)
            const normalizedY = (d - min) / range;
            const y = height - (normalizedY * height);
            return `${x},${y}`;
        }).join(" ");

        sparklineSvg = (
            <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
                <defs>
                    <linearGradient id={`grad-${title}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#818cf8" stopOpacity="0.5" />
                        <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
                    </linearGradient>
                </defs>
                <path
                    d={`M ${points}`}
                    fill="none"
                    stroke={trend === 'up' ? '#34d399' : '#818cf8'}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>
        );
    }

    return (
        <div className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm backdrop-blur-sm transition-all duration-300 hover:border-slate-700 hover:shadow-lg hover:shadow-emerald-500/10 hover:-translate-y-1 active:scale-95">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100 mix-blend-overlay"></div>

            <div className="flex justify-between items-start relative z-10">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</h3>
                        {Icon && <Icon className="h-4 w-4 text-emerald-500 transition-transform group-hover:scale-110" />}
                    </div>

                    <div className="flex items-baseline gap-2">
                        <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
                        {trend === 'up' && <span className="text-emerald-400 text-xs font-bold">▲</span>}
                        {trend === 'down' && <span className="text-red-400 text-xs font-bold">▼</span>}
                    </div>

                    <div className="mt-2 text-xs text-slate-500">
                        {description}
                    </div>
                </div>

                {/* Mini Sparkline Rendering */}
                {sparklineSvg && (
                    <div className="h-10 w-24 opacity-50 group-hover:opacity-100 transition-opacity self-end pb-1">
                        {sparklineSvg}
                    </div>
                )}
            </div>
        </div>
    );
}
