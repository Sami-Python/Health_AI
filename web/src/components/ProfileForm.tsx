"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/utils";
import { UserProfile } from "@/types/user";

export default function ProfileForm() {
    const { user } = useAuth();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const [formData, setFormData] = useState<UserProfile>({
        age: undefined,
        weight: undefined,
        height: undefined,
        gender: "Male",
        resting_heart_rate: undefined,
        max_heart_rate: undefined,
    });

    useEffect(() => {
        if (!user) return;

        async function fetchProfile() {
            try {
                const token = await user?.getIdToken();
                const res = await fetch(`${API_BASE_URL}/profile`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    // Merge with default/empty state to ensure controlled inputs
                    if (Object.keys(data).length > 0) {
                        setFormData(prev => ({ ...prev, ...data }));
                    }
                }
            } catch (err) {
                console.error("Failed to fetch profile", err);
            } finally {
                setFetching(false);
            }
        }
        fetchProfile();
    }, [user]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        if (!user) return;

        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_BASE_URL}/profile`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify(formData),
            });

            if (!res.ok) throw new Error("Failed to update profile");

            setMessage({ type: 'success', text: "Profile updated successfully!" });
        } catch (err: any) {
            setMessage({ type: 'error', text: err.message || "Something went wrong" });
        } finally {
            setLoading(false);
        }
    };

    const inputClass = "w-full rounded bg-slate-800 p-2 text-white border border-slate-700 focus:border-blue-500 focus:outline-none placeholder-slate-500";
    const labelClass = "block text-xs uppercase tracking-wide font-bold text-slate-500 mb-1";

    if (fetching) return <div className="text-slate-400 p-8 text-center">Loading profile...</div>;

    return (
        <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-slate-800 bg-slate-900/50 p-6 shadow-sm backdrop-blur-sm max-w-2xl mx-auto">
            <div>
                <h2 className="text-xl font-semibold text-white mb-1">Your Profile</h2>
                <p className="text-sm text-slate-400">Manage your physiological data for better AI insights.</p>
            </div>

            {message && (
                <div className={`rounded p-3 text-sm border ${message.type === 'success' ? 'bg-green-900/30 text-green-200 border-green-800' : 'bg-red-900/30 text-red-200 border-red-800'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Physiological Data */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-blue-400 border-b border-slate-800 pb-1">Physiology</h3>

                    <div>
                        <label className={labelClass}>Age</label>
                        <input
                            type="number"
                            className={inputClass}
                            value={formData.age || ''}
                            onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || undefined })}
                            placeholder="Years"
                        />
                    </div>
                    <div>
                        <label className={labelClass}>Gender</label>
                        <div className="relative">
                            <select
                                className={inputClass + " appearance-none"}
                                value={formData.gender || 'Male'}
                                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                            >
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className={labelClass}>Weight (kg)</label>
                            <input
                                type="number"
                                step="0.1"
                                className={inputClass}
                                value={formData.weight || ''}
                                onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) || undefined })}
                            />
                        </div>
                        <div>
                            <label className={labelClass}>Height (cm)</label>
                            <input
                                type="number"
                                className={inputClass}
                                value={formData.height || ''}
                                onChange={(e) => setFormData({ ...formData, height: parseFloat(e.target.value) || undefined })}
                            />
                        </div>
                    </div>
                </div>

                {/* Heart Rate Zones */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-red-400 border-b border-slate-800 pb-1">Heart Rate</h3>

                    <div>
                        <label className={labelClass}>Resting Heart Rate (bpm)</label>
                        <input
                            type="number"
                            className={inputClass}
                            value={formData.resting_heart_rate || ''}
                            onChange={(e) => setFormData({ ...formData, resting_heart_rate: parseInt(e.target.value) || undefined })}
                            placeholder="e.g. 55"
                        />
                        <p className="text-xs text-slate-500 mt-1">Found in your Garmin stats.</p>
                    </div>
                    <div>
                        <label className={labelClass}>Max Heart Rate (bpm)</label>
                        <input
                            type="number"
                            className={inputClass}
                            value={formData.max_heart_rate || ''}
                            onChange={(e) => setFormData({ ...formData, max_heart_rate: parseInt(e.target.value) || undefined })}
                            placeholder="e.g. 185"
                        />
                        <p className="text-xs text-slate-500 mt-1">220 - Age is a rough estimate.</p>
                    </div>
                </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end">
                <Button type="submit" disabled={loading} className="bg-blue-600 hover:bg-blue-500 text-white w-full sm:w-auto">
                    {loading ? 'Saving...' : 'Save Profile'}
                </Button>
            </div>

            <div className="flex justify-center pt-2">
                <Button type="button" variant="ghost" onClick={() => router.push("/")} className="text-slate-400 hover:text-white">
                    Back to Dashboard
                </Button>
            </div>
        </form>
    );
}
