"use client";

import { Pencil, Trash2, Trophy, Calendar, Flag, Timer, Activity } from "lucide-react";
import { Button } from "./ui/button";

interface Goal {
    id: string;
    activity_type: string;
    target_value: number;
    target_unit: string;
    period_type: string;
    description: string;
    current_value?: number;
    progress_percentage?: number;
    target_date?: string;
    frequency?: string;
    days_remaining?: number;
}

interface GoalCardProps {
    goal: Goal;
    onEdit: (goal: Goal) => void;
    onDelete: (id: string) => void;
}

export default function GoalCard({ goal, onEdit, onDelete }: GoalCardProps) {
    const isRace = goal.period_type === 'race';
    const progress = goal.progress_percentage || 0;
    const current = goal.current_value || 0;

    // Color logic based on progress
    const getProgressColor = (p: number) => {
        if (p >= 100) return "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]";
        if (p >= 75) return "bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]";
        if (p >= 40) return "bg-indigo-500";
        return "bg-slate-600";
    };

    // Calculate weeks/days text for Race
    let raceCountdown = null;
    if (isRace && goal.target_date) {
        // Backend should ideally send days_remaining, but we can also fallback calculate
        const days = goal.days_remaining !== undefined ? goal.days_remaining : 0;
        const weeks = Math.floor(days / 7);
        const extraDays = days % 7;
        raceCountdown = (
            <div className="flex flex-col items-center justify-center py-2">
                <div className="text-3xl font-bold text-white flex items-baseline gap-1">
                    {weeks} <span className="text-sm font-medium text-slate-500">w</span>
                    {extraDays > 0 && <span className="text-xl text-slate-400 ml-1">{extraDays} <span className="text-xs text-slate-600">d</span></span>}
                </div>
                <div className="text-xs text-slate-500 font-medium uppercase tracking-wider mt-1">
                    To Start Line
                </div>
            </div>
        );
    }

    return (
        <div className="group relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition-all hover:border-slate-700 hover:bg-slate-900/60 pb-3">
            {/* Background Glow for high progress */}
            {progress >= 100 && !isRace && (
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-transparent opacity-50 blur-xl"></div>
            )}
            {isRace && (
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-transparent opacity-30"></div>
            )}

            <div className="relative flex justify-between items-start mb-2">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${isRace ? 'bg-purple-500/20 text-purple-400' : (progress >= 100 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400')}`}>
                        {isRace ? <Flag className="h-5 w-5" /> : <Trophy className="h-5 w-5" />}
                    </div>
                    <div className="min-w-0"> {/* min-w-0 allows truncate to work */}
                        <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-slate-200 truncate">{goal.activity_type}</h3>
                            {isRace && <span className="text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20 px-1.5 rounded uppercase font-bold tracking-wider">Race</span>}
                        </div>
                        <p className="text-xs text-slate-500 uppercase tracking-wider font-medium truncate max-w-[120px]" title={goal.description}>{goal.description || 'No description'}</p>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-2 group-hover:translate-x-0 duration-200">
                    <Button variant="ghost" size="sm" onClick={() => onEdit(goal)} className="h-8 w-8 p-0 text-slate-500 hover:text-blue-400 hover:bg-blue-500/10">
                        <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => onDelete(goal.id)} className="h-8 w-8 p-0 text-slate-500 hover:text-red-400 hover:bg-red-500/10">
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Content: Countdown or Progress Bar */}
            {isRace ? (
                <div className="my-2 border-y border-slate-800/50 py-1 bg-slate-900/30 rounded">
                    {raceCountdown}
                </div>
            ) : (
                <div className="relative mb-2 mt-3">
                    <div className="flex justify-between text-sm font-medium mb-1.5">
                        <span className="text-slate-300">
                            {current} <span className="text-slate-500 text-xs">{goal.target_unit}</span>
                        </span>
                        <span className={progress >= 100 ? "text-emerald-400" : "text-slate-400"}>
                            {progress}%
                        </span>
                    </div>
                    <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all duration-1000 ease-out ${getProgressColor(progress)}`}
                            style={{ width: `${Math.min(progress, 100)}%` }}
                        ></div>
                    </div>
                </div>
            )}

            {/* Target Info */}
            <div className="flex justify-between items-center text-xs text-slate-500 mt-2 pt-1">
                <div className="flex items-center gap-1.5 truncate">
                    {isRace ? null : <div className="h-1.5 w-1.5 rounded-full bg-slate-600"></div>}
                    <span className="text-slate-400">{isRace ? 'Distance: ' : 'Target: '}</span>
                    <span className="text-slate-300 font-medium">{goal.target_value} {goal.target_unit}</span>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                    <Calendar className="h-3 w-3" />
                    {goal.period_type === 'target_date' ? goal.target_date : (goal.frequency || goal.period_type)}
                </div>
            </div>
        </div>
    );
}
