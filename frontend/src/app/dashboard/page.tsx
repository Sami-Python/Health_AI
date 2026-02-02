"use client";

import { useAuth } from "@/context/AuthContext";
import ChatInterface from "@/components/ChatInterface";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import AddGoalForm from "@/components/AddGoalForm";
import { StatCard } from "@/components/StatCard";
import GoalCard from "@/components/GoalCard";
import ManualWorkoutForm from "@/components/ManualWorkoutForm";
import UserMenu from "@/components/UserMenu";
import ChartsSection from "@/components/ChartsSection";
import TrainingCalendar from "@/components/TrainingCalendar";
import GeneratePlanModal from "@/components/GeneratePlanModal";
import { Activity, Battery, Calendar, TrendingUp, Plus, RefreshCw, History, Brain, XCircle } from "lucide-react";
import AnimateEntry from "@/components/ui/AnimateEntry";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";
import Skeleton from "@/components/ui/Skeleton";
import toast from "react-hot-toast";

export default function DashboardPage() {
    const { user, loading } = useAuth();
    const router = useRouter();
    const [goals, setGoals] = useState<any>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);

    // New stats data
    const [readiness, setReadiness] = useState<any>(null);
    const [nextWorkout, setNextWorkout] = useState<any>(null);
    const [weeklyStats, setWeeklyStats] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    // Full history for calendar and sparklines
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
            const res = await fetchWithRetry(`${API_BASE_URL}/goals/${goalId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                toast.success('Goal deleted successfully');
                fetchData(); // Refresh list
            } else {
                toast.error('Failed to delete goal');
            }
        } catch (e) {
            console.error("Delete failed", e);
            toast.error('An error occurred while deleting goal');
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
                const resGoals = await fetchWithRetry(`${API_BASE_URL}/goals`, { headers });
                if (resGoals.ok) setGoals(await resGoals.json());

                // 2. Get Readiness
                const resReady = await fetchWithRetry(`${API_BASE_URL}/readiness`, { headers });
                if (resReady.ok) setReadiness(await resReady.json());

                // 3. Get Next Workout
                const resNext = await fetchWithRetry(`${API_BASE_URL}/next-workout`, { headers });
                if (resNext.ok) setNextWorkout(await resNext.json());

                // 4. Get Weekly Stats
                const resWeekly = await fetchWithRetry(`${API_BASE_URL}/workouts/weekly-status`, { headers });
                if (resWeekly.ok) setWeeklyStats(await resWeekly.json());

                // 5. Get Recent History for Widget
                const resHistory = await fetchWithRetry(`${API_BASE_URL}/plans/history?limit=5`, { headers });
                if (resHistory.ok) setHistory(await resHistory.json());

                // 6. Get Full History
                const resFullHistory = await fetchWithRetry(`${API_BASE_URL}/metrics/history`, { headers });
                if (resFullHistory.ok) setFullHistory(await resFullHistory.json());

                // 7. Get Planned Workouts
                const resPlanned = await fetchWithRetry(`${API_BASE_URL}/workouts/upcoming`, { headers });
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
            const res = await fetchWithRetry(`${API_BASE_URL}/system/refresh`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                await fetchData();
                toast.success('Data refreshed successfully!');
            } else {
                const error = await res.json();
                toast.error(error.detail || 'Failed to refresh data');
            }
        } catch (e: any) {
            console.error("Refresh failed", e);
            toast.error(e.message || 'An error occurred while refreshing data');
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

    // Sparkline Data Preparation
    // fullHistory is likely sorted oldest to newest (pandas tail).
    const last7Days = fullHistory && fullHistory.length > 0 ? fullHistory.slice(-7) : [];
    const readinessSpark = last7Days.map((m: any) => m.readiness);
    const loadSpark = last7Days.map((m: any) => m.load);

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
            <div className="mx-auto max-w-7xl space-y-8">
                <AnimateEntry>
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-slate-800 pb-6">
                        <div className="text-center md:text-left">
                            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">Dashboard</h1>
                            <p className="text-slate-400 mt-1">Welcome back, {user.displayName}</p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="hidden md:block text-right text-xs text-slate-500 mr-2">
                                <p>Last synced: Just now</p>
                            </div>
                            <UserMenu />
                        </div>
                    </div>
                </AnimateEntry>

                <AnimateEntry delay={0.1}>
                    <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-slate-900/30 p-4 rounded-xl border border-slate-800/50 backdrop-blur-sm">
                        <div className="flex flex-wrap justify-center sm:justify-start gap-3 w-full">
                            <Button
                                onClick={() => setShowGenerateModal(true)}
                                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold shadow-lg shadow-purple-500/20 border-0"
                            >
                                <Brain className="mr-2 h-4 w-4" /> AI Coach
                            </Button>
                            <Button
                                onClick={() => setShowManualForm(!showManualForm)}
                                className="bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 shadow-sm"
                            >
                                <Plus className="mr-2 h-4 w-4" /> Log Workout
                            </Button>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className="text-slate-400 hover:text-white hover:bg-slate-800"
                        >
                            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                            {refreshing ? 'Syncing...' : 'Refresh'}
                        </Button>
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
                            trendData={readinessSpark}
                        />
                        <StatCard
                            title="Weekly Load"
                            value={weeklyStats ? Math.round(weeklyStats.current_load) : "--"}
                            description={`Planned: ${weeklyStats?.planned_load !== undefined ? Math.round(weeklyStats.planned_load) : '--'}`}
                            icon={Activity}
                            loading={!weeklyStats}
                            trendData={loadSpark}
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
                    <TrainingCalendar history={fullHistory} planned={plannedWorkouts} onUpdate={fetchData} />
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
                            <div className="rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/60 to-slate-950/60 p-6 backdrop-blur-md relative overflow-hidden group/card transition-all hover:border-slate-700">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl -z-10 group-hover/card:bg-blue-500/10 transition-colors"></div>

                                <h2 className="mb-6 text-xl font-bold flex items-center gap-3 text-slate-100">
                                    <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                                        <TrendingUp className="h-5 w-5" />
                                    </div>
                                    Your Active Goals
                                </h2>

                                {fetchError ? (
                                    <div className="rounded-lg bg-red-950/30 p-4 text-red-400 border border-red-900/50 text-sm">
                                        Error fetching data: {fetchError}
                                    </div>
                                ) : goals ? (
                                    <div className="space-y-4">
                                        {Array.isArray(goals) && goals.length === 0 ? (
                                            <div className="text-center py-8 border border-dashed border-slate-800 rounded-xl">
                                                <p className="text-slate-500">No active goals found.</p>
                                                <Button
                                                    variant="link"
                                                    onClick={() => document.getElementById('add-goal-input')?.focus()}
                                                    className="text-blue-400"
                                                >
                                                    Set your first goal
                                                </Button>
                                            </div>
                                        ) : (
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
                                                {goals.map((g: any) => (
                                                    <GoalCard
                                                        key={g.id}
                                                        goal={g}
                                                        onEdit={setEditingGoal}
                                                        onDelete={handleDeleteGoal}
                                                    />
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-4">
                                        {[1, 2].map(i => <Skeleton key={i} className="h-32 rounded-xl" />)}
                                    </div>
                                )}
                            </div>
                        </AnimateEntry>

                        {/* Recent History Section */}
                        <AnimateEntry delay={0.6}>
                            <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 backdrop-blur-sm">
                                <h2 className="mb-4 text-lg font-semibold flex items-center gap-2 text-slate-300">
                                    <History className="h-5 w-5 text-purple-400" /> Recent Plans
                                </h2>
                                <div className="space-y-4">
                                    {history.length > 0 ? (
                                        history.map((plan: any) => (
                                            <div key={plan.id} className="relative pl-6 py-2 group">
                                                <div className="absolute left-0 top-3 w-1.5 h-1.5 rounded-full bg-slate-700 group-hover:bg-purple-500 transition-colors shadow-[0_0_8px_rgba(168,85,247,0)] group-hover:shadow-[0_0_8px_rgba(168,85,247,0.5)]"></div>
                                                <div className="border-l border-slate-800 absolute left-[3px] top-6 bottom-[-10px] group-last:hidden"></div>
                                                <p className="text-xs text-slate-500 mb-1 font-mono uppercase tracking-wider">
                                                    {new Date(plan.timestamp).toLocaleDateString()} &bull; <span className={plan.charge > 80 ? "text-green-400" : "text-yellow-400"}>Ready: {plan.charge}%</span>
                                                </p>
                                                <p className="text-sm text-slate-300 line-clamp-2 group-hover:text-white transition-colors">{plan.advice}</p>
                                            </div>
                                        ))
                                    ) : (goals === null) ? (
                                        <div className="space-y-4">
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="flex gap-4">
                                                    <Skeleton className="h-3 w-3 rounded-full shrink-0" />
                                                    <div className="space-y-2 w-full">
                                                        <Skeleton className="h-3 w-24" />
                                                        <Skeleton className="h-3 w-full" />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="text-slate-500 italic text-sm">No history available yet.</p>
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

            <ChatInterface />
        </div>
    );
}

