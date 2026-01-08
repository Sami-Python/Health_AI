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

export function StatCard({ title, value, description, icon: Icon, trend, loading }: StatCardProps) {
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

    return (
        <div className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm backdrop-blur-sm transition-all duration-300 hover:border-slate-700 hover:shadow-lg hover:shadow-emerald-500/10 hover:-translate-y-1 active:scale-95">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100 mix-blend-overlay"></div>
            <div className="flex items-center justify-between mb-2 relative z-10">
                <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</h3>
                {Icon && <Icon className="h-4 w-4 text-emerald-500 transition-transform group-hover:scale-110" />}
            </div>

            <div className="flex items-baseline gap-2 relative z-10">
                <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
                {trend === 'up' && <span className="text-emerald-400 text-xs font-bold">▲</span>}
                {trend === 'down' && <span className="text-red-400 text-xs font-bold">▼</span>}
            </div>

            <div className="mt-2 text-xs text-slate-500 relative z-10">
                {description}
            </div>
        </div>
    );
}
