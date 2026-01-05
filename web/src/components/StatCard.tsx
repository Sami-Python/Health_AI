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
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm backdrop-blur-sm">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</h3>
                {Icon && <Icon className="h-4 w-4 text-emerald-500" />}
            </div>

            <div className="flex items-baseline gap-2">
                <p className="text-3xl font-bold text-white">{value}</p>
                {trend === 'up' && <span className="text-emerald-400 text-xs">▲</span>}
                {trend === 'down' && <span className="text-red-400 text-xs">▼</span>}
            </div>

            <div className="mt-2 text-xs text-slate-500">
                {description}
            </div>
        </div>
    );
}
