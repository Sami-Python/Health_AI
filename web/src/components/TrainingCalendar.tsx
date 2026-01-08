"use client";

import { useState } from "react";
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isToday, addMonths, subMonths } from "date-fns";
import { ChevronLeft, ChevronRight, CheckCircle2, XCircle, Calendar as CalendarIcon, Trash2, RefreshCw, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DndContext, DragOverlay, useDraggable, useDroppable, DragEndEvent, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/utils";

// --- Types ---
interface TrainingCalendarProps {
    history: any[];
    planned: any[];
    onUpdate?: () => void; // Callback to refresh data
}

// --- Draggable Workout Item ---
function DraggableWorkout({ workout, isOverlay = false, onSelect }: { workout: any, isOverlay?: boolean, onSelect?: (workout: any) => void }) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: workout.id,
        data: workout,
        disabled: workout.type === 'history'
    });

    // Styles matching the original logic
    let statusColor = "bg-blue-500/10 border-blue-500/30 text-blue-400";
    let Icon = null;

    if (workout.type === 'history') {
        const load = workout.load || 0;
        if (load > 0) {
            statusColor = "bg-green-500/10 border-green-500/30 text-green-400";
            Icon = CheckCircle2;
        } else {
            statusColor = "bg-slate-700/30 border-slate-600/30 text-slate-400";
        }
    }

    const style = {
        transform: CSS.Translate.toString(transform),
        zIndex: isDragging ? 100 : 50,
        opacity: isDragging ? 0 : 1,
        touchAction: 'none' as React.CSSProperties['touchAction']
    };

    // History Item (Not Draggable or Locked)
    if (workout.type === 'history') {
        return (
            <div
                onClick={(e) => { e.stopPropagation(); onSelect && onSelect(workout); }}
                className={`text-xs p-1.5 rounded border ${statusColor} mb-1 cursor-pointer hover:brightness-110 active:scale-95 transition-all`}
            >
                <div className="flex items-center gap-1 font-semibold truncate">
                    {Icon && <Icon className="h-3 w-3" />}
                    <span className="truncate">{workout.type === 'history' ? `Load: ${workout.load || 0}` : workout.activity}</span>
                </div>
                <div className="text-[10px] opacity-70 mt-1 line-clamp-2 leading-tight">
                    R: {workout.readiness}% • S: {Math.round(workout.sleep_min / 60)}h
                </div>
            </div>
        )
    }

    return (
        <div
            ref={setNodeRef}
            {...listeners}
            {...attributes}
            style={style}
            onClick={(e) => {
                if (!isDragging) {
                    onSelect && onSelect(workout);
                }
            }}
            className={`
                text-xs p-1.5 rounded border mb-1 transition-all cursor-grab active:cursor-grabbing
                ${isOverlay ? 'shadow-2xl scale-105 bg-slate-800 z-50 w-full' : ''}
                ${statusColor} hover:bg-blue-500/20
            `}
        >
            <div className="flex items-center gap-1 font-semibold truncate">
                {Icon && <Icon className="h-3 w-3" />}
                <span className="truncate">{workout.activity}</span>
            </div>
            <div className="text-[10px] opacity-70 mt-1 line-clamp-2 leading-tight">
                {workout.structure_summary || (workout.load_estimate ? `Load: ${workout.load_estimate}` : '--')}
            </div>
        </div>
    );
}

// --- Droppable Day Cell ---
function DroppableDay({ date, children, isCurrentMonth, isDayToday }: { date: Date, children: React.ReactNode, isCurrentMonth: boolean, isDayToday: boolean }) {
    const dateStr = format(date, 'yyyy-MM-dd');
    const { setNodeRef, isOver } = useDroppable({
        id: dateStr,
        data: { date: dateStr }
    });

    return (
        <div
            ref={setNodeRef}
            className={`
                min-h-[100px] p-2 border-b border-r border-slate-800/50 relative group transition-colors
                ${!isCurrentMonth ? 'bg-slate-950/30 text-slate-600' : 'bg-transparent text-slate-300'}
                ${isDayToday ? 'bg-blue-500/5' : ''}
                ${isOver ? 'bg-blue-500/20 ring-2 ring-inset ring-blue-500/50' : 'hover:bg-slate-800/40'}
            `}
        >
            <div className={`
                text-xs font-medium w-6 h-6 flex items-center justify-center rounded-full mb-1
                ${isDayToday ? 'bg-blue-500 text-white' : ''}
            `}>
                {format(date, 'd')}
            </div>
            {children}
        </div>
    );
}

// --- Droppable Trash ---
function DroppableTrash({ visible }: { visible: boolean }) {
    const { setNodeRef, isOver } = useDroppable({
        id: 'trash',
        data: { type: 'trash' }
    });

    if (!visible) return null;

    return (
        <div
            ref={setNodeRef}
            className={`
                fixed bottom-8 left-1/2 -translate-x-1/2 z-50 
                flex items-center gap-3 px-6 py-4 rounded-full border-2 
                transition-all duration-300 shadow-2xl
                ${isOver
                    ? 'bg-red-600 border-red-400 text-white scale-110'
                    : 'bg-slate-900 border-red-800 text-red-400 hover:bg-red-950/50'}
            `}
        >
            <Trash2 className="h-6 w-6" />
            <span className="font-bold">Drop here to delete</span>
        </div>
    );
}


export default function TrainingCalendar({ history = [], planned = [], onUpdate }: TrainingCalendarProps) {
    const { user } = useAuth();
    const [currentDate, setCurrentDate] = useState(new Date());
    const [activeId, setActiveId] = useState<string | null>(null);
    const [selectedWorkout, setSelectedWorkout] = useState<any | null>(null);

    // Modal State
    const [deleteCandidate, setDeleteCandidate] = useState<any | null>(null);
    const [isRegenerating, setIsRegenerating] = useState(false);
    const [modalError, setModalError] = useState<string | null>(null);

    // Use PointerSensor for better compatibility (replaces Mouse/Touch)
    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
    );

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));
    const resetToToday = () => setCurrentDate(new Date());

    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
    const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });
    const calendarDays = eachDayOfInterval({ start: startDate, end: endDate });

    const getWorkoutForDay = (day: Date) => {
        const dayStr = format(day, 'yyyy-MM-dd');
        const hist = history.find(h => h.date === dayStr);
        const plan = planned.find(p => p.date === dayStr);
        if (hist && (hist.load > 0)) return { ...hist, type: 'history' };
        if (plan) return { ...plan, type: 'planned' };
        if (hist) return { ...hist, type: 'history' };
        return null;
    };

    const handleDragStart = (event: any) => {
        setActiveId(event.active.id);
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;
        setActiveId(null);

        if (!over || !user) return;

        const workoutId = active.id as string;
        const targetId = over.id as string;

        // Find the workout object
        const workout = planned.find(p => p.id === workoutId);
        if (!workout) return;

        if (targetId === 'trash') {
            setDeleteCandidate(workout);
            return;
        }

        // If dropped on a day (targetId is date string)
        if (targetId !== workout.date) {
            try {
                const token = await user.getIdToken();
                const res = await fetch(`${API_BASE_URL}/workouts/${workoutId}`, {
                    method: 'PATCH',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ date: targetId })
                });

                if (res.ok) {
                    if (onUpdate) onUpdate();
                } else {
                    console.error("Failed to move workout");
                }
            } catch (e) {
                console.error("Drag Error", e);
            }
        }
    };

    const handleAction = async (action: 'delete' | 'regenerate') => {
        if (!user || !deleteCandidate) return;
        setModalError(null);
        setIsRegenerating(true);

        try {
            const token = await user.getIdToken();
            const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

            if (action === 'delete') {
                await fetch(`${API_BASE_URL}/workouts/${deleteCandidate.id}`, { method: 'DELETE', headers });
            } else {
                // Regenerate
                // 1. Delete old
                await fetch(`${API_BASE_URL}/workouts/${deleteCandidate.id}`, { method: 'DELETE', headers });

                // 2. Generate new
                const resGen = await fetch(`${API_BASE_URL}/plans/generate`, {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        days: 1,
                        rejected_plan_details: {
                            activity: deleteCandidate.activity,
                            description: deleteCandidate.structure_summary || deleteCandidate.description
                        }
                    })
                });

                if (resGen.status === 429) {
                    setModalError("You have reached the daily limit of 5 requests.");
                    setIsRegenerating(false);
                    return;
                }

                if (!resGen.ok) throw new Error("Regeneration failed");
            }

            // Success
            setDeleteCandidate(null);
            if (onUpdate) onUpdate();
        } catch (e: any) {
            setModalError(e.message || "Action failed");
        } finally {
            if (!modalError) setIsRegenerating(false); // Only stop loading if checked
        }
    };

    const activeWorkout = activeId ? planned.find(p => p.id === activeId) : null;

    return (
        <DndContext
            sensors={sensors}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden relative">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/80">
                    <div className="flex items-center gap-2">
                        <CalendarIcon className="h-5 w-5 text-blue-400" />
                        <h2 className="text-lg font-semibold text-white capitalize">
                            {format(currentDate, 'MMMM yyyy')}
                        </h2>
                    </div>
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon" onClick={prevMonth} className="h-8 w-8 text-slate-400 hover:text-white"><ChevronLeft className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={resetToToday} className="text-xs text-slate-400 hover:text-white">Today</Button>
                        <Button variant="ghost" size="icon" onClick={nextMonth} className="h-8 w-8 text-slate-400 hover:text-white"><ChevronRight className="h-4 w-4" /></Button>
                    </div>
                </div>

                {/* Days Grid */}
                <div className="grid grid-cols-7 border-b border-slate-800 bg-slate-900/30">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                        <div key={day} className="py-2 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">{day}</div>
                    ))}
                </div>

                <div className="grid grid-cols-7 bg-slate-800/20">
                    {calendarDays.map((day) => {
                        const workout = getWorkoutForDay(day);
                        const isCurrentMonth = isSameMonth(day, monthStart);
                        const isDayToday = isToday(day);
                        return (
                            <DroppableDay key={day.toISOString()} date={day} isCurrentMonth={isCurrentMonth} isDayToday={isDayToday}>
                                {workout && <DraggableWorkout workout={workout} onSelect={setSelectedWorkout} />}
                            </DroppableDay>
                        );
                    })}
                </div>

                <DroppableTrash visible={!!activeId} />

                {/* Overlay for Drag */}
                <DragOverlay>
                    {activeWorkout ? (
                        <div className="opacity-90 min-w-[120px]">
                            <DraggableWorkout workout={activeWorkout} isOverlay />
                        </div>
                    ) : null}
                </DragOverlay>

                {/* Regeneration Modal */}
                {deleteCandidate && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in">
                        <div className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
                            <div className="text-center">
                                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-900/20">
                                    <Trash2 className="h-6 w-6 text-red-500" />
                                </div>
                                <h3 className="text-lg font-bold text-white mb-2">Discard Workout?</h3>
                                <p className="text-sm text-slate-400 mb-6">
                                    Do you want to permanently delete this session, or regenerate a new one?
                                </p>

                                {modalError && (
                                    <div className="mb-4 p-3 rounded bg-red-950/50 border border-red-900/50 text-red-200 text-xs flex items-center gap-2 text-left">
                                        <AlertTriangle className="h-4 w-4 shrink-0" />
                                        {modalError}
                                    </div>
                                )}

                                <div className="grid grid-cols-2 gap-3">
                                    <Button
                                        variant="outline"
                                        onClick={() => handleAction('delete')}
                                        disabled={isRegenerating}
                                        className="border-red-900/30 text-red-400 hover:bg-red-950 hover:text-red-300"
                                    >
                                        Delete Only
                                    </Button>
                                    <Button
                                        onClick={() => handleAction('regenerate')}
                                        disabled={isRegenerating}
                                        className="bg-blue-600 hover:bg-blue-700 text-white"
                                    >
                                        {isRegenerating ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                                        Regenerate
                                    </Button>
                                </div>

                                <div className="mt-4 text-[10px] text-slate-500">
                                    You can generate max 5 training requests per day.
                                </div>

                                <button
                                    onClick={() => { setDeleteCandidate(null); setModalError(null); }}
                                    className="absolute top-4 right-4 text-slate-500 hover:text-white"
                                >
                                    <XCircle className="h-5 w-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                )}

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
        </DndContext>
    );
}

// Dummy export to keep file valid if unused previously
export { TrainingCalendar };
