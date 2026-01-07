"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import AddGoalForm from "@/components/AddGoalForm";
import { StatCard } from "@/components/StatCard";
import ManualWorkoutForm from "@/components/ManualWorkoutForm";
import UserMenu from "@/components/UserMenu";
import ChartsSection from "@/components/ChartsSection";
import TrainingCalendar from "@/components/TrainingCalendar";
import GeneratePlanModal from "@/components/GeneratePlanModal";
import { Activity, Battery, Calendar, TrendingUp, Plus, RefreshCw, History, Brain, Pencil, Trash2, XCircle } from "lucide-react";
import AnimateEntry from "@/components/ui/AnimateEntry";



// ... [Existing useEffects]



// ... [Existing Render Logic]



import { API_BASE_URL } from "@/lib/utils";

export default function DashboardPage() {
    const { user, loading, signOut } = useAuth();
    const router = useRouter();
    const [goals, setGoals] = useState<any>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);

    // New stats data
    const [readiness, setReadiness] = useState<any>(null);
    const [nextWorkout, setNextWorkout] = useState<any>(null);
    const [weeklyStats, setWeeklyStats] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    // Full history for calendar (using same endpoint for now but maybe we need more data)
    // The previous call had limit=5. We need a separate state for full history or increase limit.
    // Full history for calendar
    const [fullHistory, setFullHistory] = useState<any[]>([]);
    const [plannedWorkouts, setPlannedWorkouts] = useState<any[]>([]);

    // UI State
    const [showManualForm, setShowManualForm] = useState(false);
    const [showGenerateModal, setShowGenerateModal] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    // Edit Goal State
    const [editingGoal, setEditingGoal] = useState<any | null>(null);

    const handleDeleteGoal = async (goalId: string) => {
        if (!confirm('Are you sure you want to delete this goal?')) return;
        if (!user) return;

        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_BASE_URL}/goals/${goalId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                fetchData(); // Refresh list
            }
        } catch (e) {
            console.error("Delete failed", e);
        }
    };

    useEffect(() => {
        if (!loading && !user) {
            router.push("/login");
        }
    }, [user, loading, router]);

    const fetchData = useCallback(async () => {
        if (user) {
            try {
                const token = await user.getIdToken();
                const headers = { Authorization: `Bearer ${token}` };

                // 1. Get Goals
                const resGoals = await fetch(`${API_BASE_URL}/goals`, { headers });
                if (resGoals.ok) setGoals(await resGoals.json());

                // 2. Get Readiness
                const resReady = await fetch(`${API_BASE_URL}/readiness`, { headers });
                if (resReady.ok) setReadiness(await resReady.json());

                // 3. Get Next Workout
                const resNext = await fetch(`${API_BASE_URL}/next-workout`, { headers });
                if (resNext.ok) setNextWorkout(await resNext.json());

                // 4. Get Weekly Stats
                const resWeekly = await fetch(`${API_BASE_URL}/workouts/weekly-status`, { headers });
                if (resWeekly.ok) setWeeklyStats(await resWeekly.json());

                // 5. Get Recent History for Widget
                const resHistory = await fetch(`${API_BASE_URL}/plans/history?limit=5`, { headers });
                if (resHistory.ok) setHistory(await resHistory.json());

                // 6. Get Full History for Calendar (re-using metrics/history endpoint which returns 30 days)
                // Ideally backend should support date range, but for now 30 days is a start.
                const resFullHistory = await fetch(`${API_BASE_URL}/metrics/history`, { headers });
                if (resFullHistory.ok) setFullHistory(await resFullHistory.json());

                // 7. Get Planned Workouts
                const resPlanned = await fetch(`${API_BASE_URL}/workouts/upcoming`, { headers });
                if (resPlanned.ok) setPlannedWorkouts(await resPlanned.json());

            } catch (err: any) {
                setFetchError(err.message);
                console.error("Fetch error", err);
            }
        }
    }, [user]);

    const handleRefresh = async () => {
        if (!user) return;
        setRefreshing(true);
        try {
            const token = await user.getIdToken();
            await fetch(`${API_BASE_URL}/system/refresh`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });
            // Reload data after refresh
            await fetchData();
        } catch (e) {
            console.error("Refresh failed", e);
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    if (loading || !user) {
        return <div className="flex h-screen items-center justify-center text-slate-400">Loading...</div>;
    }



    return (
        <div className="min-h-screen bg-slate-950 p-8 text-white">
            {showGenerateModal && (
                <GeneratePlanModal
                    onClose={() => setShowGenerateModal(false)}
                    onSuccess={() => {
                        fetchData();
                    }}
                />
            )}
            <div className="mx-auto max-w-6xl space-y-8">
                <AnimateEntry>
                    <div className="flex items-center justify-between border-b border-slate-800 pb-6">
                        <div>
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">Dashboard</h1>
                            <p className="text-slate-400 mt-1">Welcome back, {user.displayName}</p>
                        </div>
                        <UserMenu />
                    </div>
                </AnimateEntry>

                <AnimateEntry delay={0.1}>
                    <div className="flex flex-wrap gap-4 items-center justify-between">
                        <div className="flex gap-2">
                            <Button
                                onClick={() => setShowGenerateModal(true)}
                                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold shadow-lg shadow-purple-500/20 shadow-glow"
                            >
                                <Brain className="mr-2 h-4 w-4" /> AI Coach
                            </Button>
                            <Button
                                onClick={() => setShowManualForm(!showManualForm)}
                                className="bg-orange-500 hover:bg-orange-600 text-white font-semibold shadow-lg shadow-orange-500/20"
                            >
                                <Plus className="mr-2 h-4 w-4" /> Log Workout
                            </Button>
                            <Button
                                variant="outline"
                                onClick={handleRefresh}
                                disabled={refreshing}
                                className="bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white border-slate-700"
                            >
                                <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                                {refreshing ? 'Syncing...' : 'Refresh Data'}
                            </Button>
                        </div>
                    </div>
                </AnimateEntry>

                {/* Stats Grid */}
                <AnimateEntry delay={0.2}>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <StatCard
                            title="Readiness"
                            value={readiness ? `${readiness.readiness}%` : "--"}
                            description="Body Battery Estimate"
                            icon={Battery}
                            trend={readiness?.readiness > 80 ? 'up' : 'neutral'}
                            loading={!readiness}
                        />
                        <StatCard
                            title="Weekly Load"
                            value={weeklyStats ? weeklyStats.current_load : "--"}
                            description={`Planned: ${weeklyStats?.planned_load || '--'}`}
                            icon={Activity}
                            loading={!weeklyStats}
                        />
                        <StatCard
                            title="Next Workout"
                            value={nextWorkout?.content?.activity || "Rest Day"}
                            description={nextWorkout?.date || "No upcoming sessions"}
                            icon={Calendar}
                            loading={!nextWorkout && nextWorkout !== undefined}
                        />
                        <StatCard
                            title="Active Goals"
                            value={goals ? goals.length : 0}
                            description="Training Targets"
                            icon={TrendingUp}
                            loading={!goals}
                        />
                    </div>
                </AnimateEntry>

                {/* Calendar Section */}
                <AnimateEntry delay={0.3}>
                    <TrainingCalendar history={fullHistory} planned={plannedWorkouts} />
                </AnimateEntry>

                <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                    {/* Main Content Area */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* 1. Charts Section */}
                        <AnimateEntry delay={0.4}>
                            <ChartsSection />
                        </AnimateEntry>

                        {/* 2. Manual Workout Form Toggle */}
                        {showManualForm && (
                            <AnimateEntry>
                                <ManualWorkoutForm
                                    onSuccess={() => {
                                        setShowManualForm(false);
                                        fetchData();
                                    }}
                                    onCancel={() => setShowManualForm(false)}
                                />
                            </AnimateEntry>
                        )}

                        <AnimateEntry delay={0.5}>
                            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm relative">
                                <h2 className="mb-4 text-xl font-semibold flex items-center gap-2">
                                    <span>🎯</span> Your Active Goals
                                </h2>

                                {fetchError ? (
                                    <div className="rounded bg-red-900/20 p-4 text-red-400 border border-red-900/50">Error fetching data: {fetchError}</div>
                                ) : goals ? (
                                    <div className="space-y-4">
                                        {Array.isArray(goals) && goals.length === 0 ? (
                                            <p className="text-slate-500 italic">No active goals found. Set one up!</p>
                                        ) : (
                                            <div className="grid gap-4">
                                                {goals.map((g: any) => (
                                                    <div key={g.id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-black/40 p-4 transition-colors hover:border-slate-700 group">
                                                        <div>
                                                            <div className="flex items-center gap-2">
                                                                <p className="font-semibold text-white">{g.activity_type || g.type}</p>
                                                                {/* Edit/Delete Actions (Visible on Hover/Mobile) */}
                                                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <button
                                                                        onClick={() => setEditingGoal(g)}
                                                                        className="p-1 hover:text-blue-400 text-slate-500" title="Edit">
                                                                        <Pencil className="h-3 w-3" />
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeleteGoal(g.id)}
                                                                        className="p-1 hover:text-red-400 text-slate-500" title="Delete">
                                                                        <Trash2 className="h-3 w-3" />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                            <p className="text-sm text-slate-400">{g.description || 'No description'}</p>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-2xl font-bold text-emerald-400">
                                                                {g.target_value} <span className="text-sm font-normal text-slate-500">{g.target_unit}</span>
                                                            </div>
                                                            <div className="text-xs uppercase tracking-wide text-slate-600 font-bold">
                                                                {g.period_type === 'target_date' ? (g.target_date || 'No Date') : (g.frequency || g.period_type)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-2 text-slate-500 animate-pulse">
                                        <div className="h-4 w-4 rounded-full bg-slate-600"></div>
                                        Fetching secured data...
                                    </div>
                                )}
                            </div>
                        </AnimateEntry>

                        {/* Recent History Section */}
                        <AnimateEntry delay={0.6}>
                            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 backdrop-blur-sm">
                                <h2 className="mb-4 text-xl font-semibold flex items-center gap-2">
                                    <History className="text-purple-400" /> Recent Coaching Plans
                                </h2>
                                <div className="space-y-4">
                                    {history.length > 0 ? (
                                        history.map((plan: any) => (
                                            <div key={plan.id} className="border-l-2 border-slate-700 pl-4 py-1 hover:border-blue-500 transition-colors">
                                                <p className="text-sm text-slate-400">{new Date(plan.timestamp).toLocaleDateString()} &bull; Readiness: {plan.charge}</p>
                                                <p className="text-slate-200 mt-1 line-clamp-2">{plan.advice}</p>
                                            </div>
                                        ))
                                    ) : (
                                        <p className="text-slate-500 italic">No history available.</p>
                                    )}
                                </div>
                            </div>
                        </AnimateEntry>
                    </div>

                    {/* Sidebar / Actions */}
                    <AnimateEntry delay={0.4} className="space-y-6">
                        <AddGoalForm onSuccess={fetchData} />
                    </AnimateEntry>
                </div>
            </div>
            {/* Edit Goal Modal */}
            {editingGoal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in">
                    <div className="w-full max-w-lg relative">
                        <button
                            onClick={() => setEditingGoal(null)}
                            className="absolute -top-12 right-0 text-slate-400 hover:text-white"
                        >
                            <XCircle className="h-8 w-8" />
                        </button>
                        <AddGoalForm
                            goalId={editingGoal.id}
                            initialData={editingGoal}
                            onSuccess={() => {
                                setEditingGoal(null);
                                fetchData();
                            }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

