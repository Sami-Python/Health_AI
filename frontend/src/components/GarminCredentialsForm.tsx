"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Lock, CheckCircle, XCircle, Loader2, ShieldCheck } from "lucide-react";
import toast from "react-hot-toast";
import { useGarminStatus } from "@/hooks/useGarminStatus";

export default function GarminCredentialsForm() {
    const { user } = useAuth();
    const { status, refreshStatus } = useGarminStatus();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);

    // 2FA / MFA state
    const [mfaStep, setMfaStep] = useState(false);
    const [mfaSessionId, setMfaSessionId] = useState("");
    const [mfaCode, setMfaCode] = useState("");
    const [mfaLoading, setMfaLoading] = useState(false);

    const handleConnect = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user || !username || !password) return;
        setLoading(true);

        try {
            const token = await user.getIdToken();
            const res = await fetchWithRetry(`${API_BASE_URL}/garmin/connect`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();

            if (!res.ok) {
                toast.error(data.detail || "Yhdistäminen epäonnistui");
                return;
            }

            if (data.status === "connected") {
                toast.success("✅ Garmin yhdistetty onnistuneesti!");
                setPassword("");
                setUsername("");
                refreshStatus();
            } else if (data.status === "mfa_required") {
                // Switch to MFA input step
                setMfaSessionId(data.session_id);
                setMfaStep(true);
                toast("🔐 Kaksivaiheinen tunnistus vaaditaan – tarkista sähköpostisi tai tekstiviestisi.", { icon: "🔐" });
            }
        } catch (e: any) {
            toast.error(e.message || "Verkkovirhe");
        } finally {
            setLoading(false);
        }
    };

    const handleMfaSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user || !mfaCode.trim()) return;
        setMfaLoading(true);

        try {
            const token = await user.getIdToken();
            const res = await fetchWithRetry(`${API_BASE_URL}/garmin/connect/mfa`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ session_id: mfaSessionId, mfa_code: mfaCode.trim() })
            });
            const data = await res.json();

            if (res.ok && data.status === "connected") {
                toast.success("✅ Garmin yhdistetty 2FA:n kautta!");
                setMfaStep(false);
                setMfaCode("");
                setPassword("");
                setUsername("");
                refreshStatus();
            } else {
                toast.error(data.detail || "Koodi virheellinen tai vanhentunut");
            }
        } catch (e: any) {
            toast.error(e.message || "Verkkovirhe");
        } finally {
            setMfaLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (!confirm("Haluatko varmasti katkaista Garmin-yhteyden?")) return;
        if (!user) return;

        setLoading(true);
        try {
            const token = await user.getIdToken();
            const res = await fetchWithRetry(`${API_BASE_URL}/garmin/credentials`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.ok) {
                toast.success("Garmin-yhteys katkaistu");
                setUsername("");
                setPassword("");
                setMfaStep(false);
                setMfaCode("");
                refreshStatus();
            } else {
                const data = await res.json();
                toast.error(data.detail || "Katkaisu epäonnistui");
            }
        } catch (e: any) {
            toast.error(e.message || "Verkkovirhe");
        } finally {
            setLoading(false);
        }
    };

    const cancelMfa = () => {
        setMfaStep(false);
        setMfaCode("");
        setMfaSessionId("");
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

            {/* ── MFA Step ─────────────────────────────────────── */}
            {mfaStep ? (
                <form onSubmit={handleMfaSubmit} className="space-y-4">
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-900/20 border border-amber-700/30">
                        <ShieldCheck className="h-5 w-5 text-amber-400 shrink-0" />
                        <p className="text-sm text-amber-300">
                            Garmin vaatii kaksivaiheisen tunnistuksen. Syötä sähköpostiisi tai puhelimeesi lähetetty koodi.
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Vahvistuskoodi (MFA)
                        </label>
                        <input
                            type="text"
                            value={mfaCode}
                            onChange={(e) => setMfaCode(e.target.value)}
                            placeholder="123456"
                            maxLength={8}
                            required
                            autoFocus
                            className="w-full px-4 py-3 bg-slate-800/50 border border-amber-700/50 rounded-lg text-white text-center text-2xl tracking-[0.5em] placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                        />
                    </div>

                    <div className="flex gap-3">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={cancelMfa}
                            className="flex-1 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
                        >
                            Peruuta
                        </Button>
                        <Button
                            type="submit"
                            disabled={mfaLoading || mfaCode.length < 4}
                            className="flex-1 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white"
                        >
                            {mfaLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Vahvistetaan...
                                </>
                            ) : (
                                <>
                                    <ShieldCheck className="mr-2 h-4 w-4" />
                                    Vahvista koodi
                                </>
                            )}
                        </Button>
                    </div>
                </form>
            ) : (
                /* ── Credentials Form ─────────────────────────── */
                <form onSubmit={handleConnect} className="space-y-4">
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
                                    Yhdistetään...
                                </>
                            ) : (
                                <>
                                    <Lock className="mr-2 h-4 w-4" />
                                    {status?.connected ? "Päivitä" : "Yhdistä"}
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
                                Katkaise
                            </Button>
                        )}
                    </div>
                </form>
            )}

            {/* Security Notice */}
            <div className="mt-4 p-3 rounded-lg bg-blue-900/10 border border-blue-800/30">
                <p className="text-xs text-blue-300/80">
                    🔒 <strong>Tietoturva:</strong> Salasanasi salataan AES-256:lla ennen lähettämistä ja tallennusta.
                    OAuth2-tokenit salataan myös – salasanaa ei tarvita uusintakirjautumiseen.
                </p>
            </div>
        </div>
    );
}
