import { useState } from "react";
import { Button } from "./ui/button";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/utils";

interface ManualWorkoutFormProps {
    onSuccess: () => void;
    onCancel: () => void;
}

export default function ManualWorkoutForm({ onSuccess, onCancel }: ManualWorkoutFormProps) {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        date: new Date().toISOString().split('T')[0],
        activity: "Running",
        duration_min: 45,
        rpe: 5,
        notes: ""
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;
        setLoading(true);
        setError(null);

        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_BASE_URL}/workouts/manual`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    ...formData,
                    duration_min: Number(formData.duration_min),
                    rpe: Number(formData.rpe)
                })
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to log workout");
            }

            onSuccess();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (

        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-6 shadow-2xl w-full max-w-lg relative">
                <button
                    onClick={onCancel}
                    className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
                >
                    ✕
                </button>

                <h2 className="text-xl font-bold bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent mb-6">
                    Log Manual Workout
                </h2>

                {error && <div className="mb-4 p-3 bg-red-900/20 border border-red-900/50 text-red-200 rounded-lg text-sm">{error}</div>}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</label>
                            <input
                                type="date"
                                name="date"
                                value={formData.date}
                                onChange={handleChange}
                                className="w-full bg-slate-950/50 border border-slate-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 focus:outline-none transition-all"
                                required
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Activity</label>
                            <select
                                name="activity"
                                value={formData.activity}
                                onChange={handleChange}
                                className="w-full bg-slate-950/50 border border-slate-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 focus:outline-none transition-all"
                            >
                                {["Running", "Cycling", "Swimming", "Gym", "Walking", "XC Skiing", "Other"].map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Duration (min)</label>
                            <input
                                type="number"
                                name="duration_min"
                                value={formData.duration_min}
                                onChange={handleChange}
                                min="1"
                                className="w-full bg-slate-950/50 border border-slate-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 focus:outline-none transition-all"
                                required
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">RPE (1-10)</label>
                            <input
                                type="number"
                                name="rpe"
                                value={formData.rpe}
                                onChange={handleChange}
                                min="1" max="10"
                                className="w-full bg-slate-950/50 border border-slate-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 focus:outline-none transition-all"
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Notes</label>
                        <textarea
                            name="notes"
                            value={formData.notes}
                            onChange={handleChange}
                            className="w-full bg-slate-950/50 border border-slate-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500 focus:outline-none min-h-[100px] resize-none"
                            placeholder="How did it feel?"
                        />
                    </div>

                    <div className="flex gap-3 pt-4">
                        <Button type="button" onClick={onCancel} variant="outline" className="flex-1 border-slate-700 hover:bg-slate-800 text-slate-300 h-11">
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading} className="flex-1 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white font-bold border-none h-11 shadow-lg shadow-orange-900/20">
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save Workout
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
