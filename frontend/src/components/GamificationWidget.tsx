import React from 'react';
import { Target, Flame, Trophy, Award, Medal, Star } from "lucide-react";
import AnimateEntry from "./ui/AnimateEntry";

interface Badge {
    id: string;
    name: string;
    icon: string;
    level: string;
}

interface GamificationData {
    consistency_score: number;
    streak: number;
    badges: Badge[];
}

export default function GamificationWidget({ data }: { data: GamificationData | null }) {
    if (!data) return null;

    const getScoreColor = (score: number) => {
        if (score >= 95) return "from-amber-400 to-yellow-600";
        if (score >= 80) return "from-blue-400 to-indigo-600";
        if (score >= 60) return "from-emerald-400 to-teal-600";
        return "from-slate-400 to-slate-600";
    };

    const getBadgeStyle = (level: string) => {
        switch (level) {
            case 'gold': return "bg-gradient-to-br from-yellow-300 to-yellow-600 border-yellow-400 text-yellow-950";
            case 'silver': return "bg-gradient-to-br from-slate-300 to-slate-500 border-slate-400 text-slate-900";
            case 'bronze': return "bg-gradient-to-br from-orange-300 to-orange-600 border-orange-400 text-orange-950";
            case 'special': return "bg-gradient-to-br from-red-400 to-orange-500 border-red-400 text-white";
            default: return "bg-slate-800 border-slate-700 text-slate-300";
        }
    };

    // SVG Circle Math
    const radius = 36;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (data.consistency_score / 100) * circumference;

    return (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 backdrop-blur-sm flex flex-col md:flex-row items-center gap-6 shadow-xl relative overflow-hidden">
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl pointer-events-none"></div>

            {/* Left: Consistency Score Ring */}
            <div className="flex items-center gap-5 shrink-0">
                <div className="relative w-24 h-24 flex items-center justify-center">
                    {/* Background Ring */}
                    <svg className="w-full h-full transform -rotate-90">
                        <circle
                            cx="48"
                            cy="48"
                            r={radius}
                            className="stroke-slate-800"
                            strokeWidth="8"
                            fill="transparent"
                        />
                        {/* Progress Ring */}
                        <circle
                            cx="48"
                            cy="48"
                            r={radius}
                            className={`stroke-current text-blue-500 transition-all duration-1000 ease-out`}
                            strokeWidth="8"
                            fill="transparent"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="round"
                        />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center">
                        <span className="text-2xl font-bold text-white">{data.consistency_score}<span className="text-xs text-slate-400">%</span></span>
                    </div>
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Consistency</h3>
                    <p className="text-xs text-slate-500 mt-0.5">14-Day Average</p>

                    <div className="mt-3 flex items-center gap-2 bg-slate-800/80 rounded-full px-3 py-1 border border-slate-700/50 w-max">
                        <Flame className={`h-4 w-4 ${data.streak >= 3 ? 'text-orange-500' : 'text-slate-500'}`} />
                        <span className="text-sm font-medium text-slate-200">{data.streak} Day Streak</span>
                    </div>
                </div>
            </div>

            <div className="hidden md:block w-px h-16 bg-slate-800"></div>

            {/* Right: Badges */}
            <div className="flex-1 w-full">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                        <Trophy className="h-4 w-4 text-emerald-400" />
                        Trophies & Badges
                    </h3>
                    <span className="text-xs text-slate-500">{data.badges.length} Unlocked</span>
                </div>

                <div className="flex flex-wrap gap-2">
                    {data.badges.length > 0 ? (
                        data.badges.map((badge) => (
                            <div
                                key={badge.id}
                                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border shadow-sm ${getBadgeStyle(badge.level)}`}
                                title={badge.name}
                            >
                                <span className="text-base leading-none">{badge.icon}</span>
                                <span className="text-xs font-bold whitespace-nowrap">{badge.name}</span>
                            </div>
                        ))
                    ) : (
                        <div className="text-sm text-slate-500 bg-slate-800/50 px-3 py-2 rounded-lg border border-slate-800 w-full flex items-center gap-2 italic">
                            <Star className="h-4 w-4 opacity-50" />
                            Keep training to unlock badges!
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
