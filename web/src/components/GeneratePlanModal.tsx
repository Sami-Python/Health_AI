"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Brain, Sparkles, X, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import AnimateEntry from "./ui/AnimateEntry";

interface GeneratePlanModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

export default function GeneratePlanModal({ onClose, onSuccess }: GeneratePlanModalProps) {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [days, setDays] = useState(3);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!user) return;
        setLoading(true);
        setError(null);
        try {
            const token = await user.getIdToken();
            const res = await fetch("http://localhost:8000/plans/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ days })
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Generation failed");
            }

            onSuccess();
            onClose();
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <AnimateEntry className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 relative">
                <Button variant="ghost" size="icon" onClick={onClose} className="absolute right-2 top-2 text-slate-400 hover:text-white">
                    <X className="h-5 w-5" />
                </Button>

                <div className="text-center mb-6">
                    <div className="h-12 w-12 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Sparkles className="h-6 w-6 text-purple-400" />
                    </div>
                    <h2 className="text-xl font-bold text-white">Your Personalized Training Plan</h2>
                    <p className="text-sm text-slate-400 mt-1">
                        Smart training recommendations tailored to your recovery, load, and long-term goals.
                    </p>
                </div>

                <div className="space-y-4">
                    <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                        <label className="text-sm font-medium text-slate-300 mb-2 block">Looking ahead</label>
                        <div className="flex gap-2">
                            {[1, 3, 5, 7].map(d => (
                                <button
                                    key={d}
                                    onClick={() => setDays(d)}
                                    className={`
                                        flex-1 py-2 rounded text-sm font-medium transition-all
                                        ${days === d ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}
                                    `}
                                >
                                    {d} {d === 1 ? 'day' : 'days'}
                                </button>
                            ))}
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-900/20 border border-red-900/50 text-red-200 text-sm rounded">
                            {error}
                        </div>
                    )}

                    <Button
                        onClick={handleGenerate}
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-bold h-11"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Thinking...
                            </>
                        ) : (
                            <>
                                <Brain className="mr-2 h-5 w-5" />
                                Create Plan
                            </>
                        )}
                    </Button>
                </div>
            </AnimateEntry>
        </div>
    );
}
