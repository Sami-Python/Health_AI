"use client";

import { useState } from "react";
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths, isToday } from "date-fns";
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle, Calendar as CalendarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TrainingCalendarProps {
    history: any[]; // Past workouts
    planned?: any[]; // Future plans (optional for now)
}

export default function TrainingCalendar({ history = [], planned = [] }: TrainingCalendarProps) {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedWorkout, setSelectedWorkout] = useState<any | null>(null);

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));
    const resetToToday = () => setCurrentDate(new Date());

    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const startDate = startOfWeek(monthStart, { weekStartsOn: 1 }); // Monday start
    const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });

    const calendarDays = eachDayOfInterval({ start: startDate, end: endDate });

    // Helper to find workout for a day
    const getWorkoutForDay = (day: Date) => {
        const dayStr = format(day, 'yyyy-MM-dd');
        const hist = history.find(h => h.date === dayStr);
        const plan = planned.find(p => p.date === dayStr);

        // If explicitly a planned workout exists for today, show it UNLESS history has significant load
        if (hist && (hist.load > 0)) {
            return { ...hist, type: 'history' };
        }

        // If plan exists, show plan (even if history exists but load is 0)
        if (plan) return { ...plan, type: 'planned' };

        // Fallback to history (empty)
        if (hist) return { ...hist, type: 'history' };

        return null;
    };

    return (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80">
                <div className="flex items-center gap-2">
                    <CalendarIcon className="h-5 w-5 text-blue-400" />
                    <h2 className="text-lg font-semibold text-white capitalize">
                        {format(currentDate, 'MMMM yyyy')}
                    </h2>
                </div>
                <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" onClick={prevMonth} className="h-8 w-8 text-slate-400 hover:text-white">
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={resetToToday} className="text-xs text-slate-400 hover:text-white">
                        Today
                    </Button>
                    <Button variant="ghost" size="icon" onClick={nextMonth} className="h-8 w-8 text-slate-400 hover:text-white">
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Days Header */}
            <div className="grid grid-cols-7 border-b border-slate-800 bg-slate-900/30">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                    <div key={day} className="py-2 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        {day}
                    </div>
                ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 bg-slate-800/20">
                {calendarDays.map((day, dayIdx) => {
                    const workout = getWorkoutForDay(day);
                    const isCurrentMonth = isSameMonth(day, monthStart);
                    const isDayToday = isToday(day);

                    // Determine Status Color
                    let statusColor = "";
                    let Icon = null;

                    if (workout) {
                        if (workout.type === 'history') {
                            const load = workout.load || 0;
                            if (load > 0) {
                                statusColor = "bg-green-500/10 border-green-500/30 text-green-400";
                                Icon = CheckCircle2;
                            } else {
                                statusColor = "bg-slate-700/30 border-slate-600/30 text-slate-400";
                            }
                        } else if (workout.type === 'planned') {
                            statusColor = "bg-blue-500/10 border-blue-500/30 text-blue-400";
                            // Icon = CalendarIcon; // Or something else
                        }
                    }

                    return (
                        <div
                            key={day.toString()}
                            className={`
                                min-h-[100px] p-2 border-b border-r border-slate-800/50 relative group transition-colors hover:bg-slate-800/40
                                ${!isCurrentMonth ? 'bg-slate-950/30 text-slate-600' : 'bg-transparent text-slate-300'}
                                ${isDayToday ? 'bg-blue-500/5' : ''}
                            `}
                        >
                            {/* Date Number */}
                            <div className={`
                                text-xs font-medium w-6 h-6 flex items-center justify-center rounded-full mb-1
                                ${isDayToday ? 'bg-blue-500 text-white' : ''}
                            `}>
                                {format(day, 'd')}
                            </div>

                            {/* Workout Content */}
                            {workout && (
                                <div
                                    className={`
                                        text-xs p-1.5 rounded border ${statusColor} mb-1 transition-all cursor-pointer hover:brightness-110 active:scale-95
                                    `}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setSelectedWorkout(workout);
                                    }}
                                >
                                    <div className="flex items-center gap-1 font-semibold truncate">
                                        {Icon && <Icon className="h-3 w-3" />}
                                        <span className="truncate">
                                            {workout.type === 'history' ? `Load: ${workout.load || 0}` : workout.activity}
                                        </span>
                                    </div>
                                    <div className="text-[10px] opacity-70 mt-1 line-clamp-2 leading-tight">
                                        {workout.type === 'history' ? (
                                            <>R: {workout.readiness}% • S: {Math.round(workout.sleep_min / 60)}h</>
                                        ) : (
                                            <>
                                                {workout.structure || workout.structure_summary || (workout.load_estimate ? `Est. Load: ${workout.load_estimate}` : '--')}
                                            </>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Detail Modal */}
            {selectedWorkout && (
                <div
                    className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                    onClick={() => setSelectedWorkout(null)}
                >
                    <div
                        className="w-full max-w-sm bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-6 relative animate-in fade-in zoom-in-95 duration-200"
                        onClick={e => e.stopPropagation()}
                    >
                        <button
                            onClick={() => setSelectedWorkout(null)}
                            className="absolute right-3 top-3 text-slate-400 hover:text-white"
                        >
                            <XCircle className="h-6 w-6" />
                        </button>

                        <div className="mb-4">
                            <span className={`
                                px-2 py-1 rounded text-xs font-bold uppercase tracking-wider
                                ${selectedWorkout.type === 'planned' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'}
                            `}>
                                {selectedWorkout.type === 'planned' ? 'Planned Workout' : 'Completed Log'}
                            </span>
                            <h3 className="text-xl font-bold text-white mt-2">
                                {selectedWorkout.activity || "Workout"}
                            </h3>
                            <p className="text-slate-400 text-sm">
                                {format(new Date(selectedWorkout.date), 'EEEE, d MMMM yyyy')}
                            </p>
                        </div>

                        <div className="space-y-4 text-sm text-slate-300">
                            {selectedWorkout.description && (
                                <p className="italic border-l-2 border-slate-700 pl-3">
                                    "{selectedWorkout.description}"
                                </p>
                            )}

                            {(selectedWorkout.structure || selectedWorkout.structure_summary) && (
                                <div>
                                    <div className="text-slate-500 font-semibold text-xs uppercase mb-1">Structure</div>
                                    <div className="font-mono bg-slate-950/50 p-2 rounded text-blue-300 whitespace-pre-wrap">
                                        {selectedWorkout.structure || selectedWorkout.structure_summary}
                                    </div>
                                </div>
                            )}

                            {selectedWorkout.tips && (
                                <div>
                                    <div className="text-slate-500 font-semibold text-xs uppercase mb-1">Tips</div>
                                    <p className="text-slate-400">
                                        {selectedWorkout.tips}
                                    </p>
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-slate-800">
                                <div>
                                    <div className="text-xs text-slate-500">Duration</div>
                                    <div className="font-semibold">{selectedWorkout.duration_min || selectedWorkout.duration || 0} min</div>
                                </div>
                                <div>
                                    <div className="text-xs text-slate-500">Load Estimate</div>
                                    <div className="font-semibold">{selectedWorkout.load_estimate || selectedWorkout.load || 0}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
