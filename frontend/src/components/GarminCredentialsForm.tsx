"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Lock, CheckCircle, XCircle, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { useGarminStatus } from "@/hooks/useGarminStatus";

export default function GarminCredentialsForm() {
    const { user } = useAuth();
    const { status, refreshStatus } = useGarminStatus();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;

        setLoading(true);

        try {
            const token = await user.getIdToken();
            const res = await fetchWithRetry(`${API_BASE_URL}/garmin/credentials`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();

            if (res.ok) {
                toast.success("Garmin credentials saved securely!");
                setPassword(""); // Clear password field
                refreshStatus(); // Refresh status
            } else {
                toast.error(data.detail || "Failed to save credentials");
            }
        } catch (e: any) {
            toast.error(e.message || "Network error");
        } finally {
            setLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (!confirm("Are you sure you want to disconnect your Garmin account?")) return;
        if (!user) return;

        setLoading(true);

        try {
            const token = await user.getIdToken();
            const res = await fetchWithRetry(`${API_BASE_URL}/garmin/credentials`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                toast.success("Garmin account disconnected");
                setUsername("");
                setPassword("");
                refreshStatus();
            } else {
                const data = await res.json();
                toast.error(data.detail || "Failed to disconnect");
            }
        } catch (e: any) {
            toast.error(e.message || "Network error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/60 to-slate-950/60 p-6 backdrop-blur-md">
            <div className="mb-6">
                <h3 className="text-xl font-bold flex items-center gap-3 text-slate-100">
                    <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                        <Lock className="h-5 w-5" />
                    </div>
                    Garmin Connection
                </h3>
                <p className="text-sm text-slate-400 mt-2">
                    Connect your Garmin account to automatically sync your workouts and metrics.
                </p>
            </div>

            {/* Status Badge */}
            <div className="mb-4">
                {status?.connected ? (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-green-900/20 border border-green-800/30">
                        <CheckCircle className="h-5 w-5 text-green-400" />
                        <div>
                            <p className="text-sm font-medium text-green-300">Connected</p>
                            <p className="text-xs text-green-400/70">{status.username}</p>
                        </div>
                    </div>
                ) : (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                        <XCircle className="h-5 w-5 text-slate-400" />
                        <p className="text-sm text-slate-400">Not connected</p>
                    </div>
                )}
            </div>

            {/* Form */}
            <form onSubmit={handleSave} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Garmin Username or Email
                    </label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="username or email@example.com"
                        required
                        className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Garmin Password
                    </label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                    />
                    <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        Encrypted with AES-256 before storage
                    </p>
                </div>

                <div className="flex gap-3">
                    <Button
                        type="submit"
                        disabled={loading || !username || !password}
                        className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <Lock className="mr-2 h-4 w-4" />
                                {status?.connected ? "Update Credentials" : "Connect Garmin"}
                            </>
                        )}
                    </Button>

                    {status?.connected && (
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleDisconnect}
                            disabled={loading}
                            className="border-red-800/50 text-red-400 hover:bg-red-900/20"
                        >
                            Disconnect
                        </Button>
                    )}
                </div>
            </form>

            {/* Security Notice */}
            <div className="mt-4 p-3 rounded-lg bg-blue-900/10 border border-blue-800/30">
                <p className="text-xs text-blue-300/80">
                    🔒 <strong>Security:</strong> Your password is encrypted before transmission and storage.
                    Only you can access your Garmin data.
                </p>
            </div>
        </div>
    );
}
