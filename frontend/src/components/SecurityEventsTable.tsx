
import { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/utils";
import { AlertTriangle, Clock, RefreshCw, Smartphone, ShieldAlert } from "lucide-react";
import toast from "react-hot-toast";

interface SecurityEvent {
    id: string;
    type: string;
    ip: string;
    path: string;
    limit?: string;
    user_agent: string;
    timestamp: string;
}

export default function SecurityEventsTable() {
    const { user } = useAuth();
    const [events, setEvents] = useState<SecurityEvent[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchEvents = async () => {
        setLoading(true);
        try {
            const token = await user?.getIdToken();
            if (!token) return;

            const res = await fetch(`${API_BASE_URL}/admin/security-events?limit=50`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) throw new Error("Failed to fetch events");

            const data = await res.json();
            setEvents(data.events || []);
        } catch (error) {
            console.error(error);
            toast.error("Failed to load security logs");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEvents();
    }, [user]);

    const handleRevokeTokens = async (uid: string) => {
        if (!confirm("Are you sure you want to force logout this user?")) return;

        try {
            const token = await user?.getIdToken();
            const res = await fetch(`${API_BASE_URL}/admin/revoke-tokens/${uid}`, {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` }
            });

            if (!res.ok) throw new Error("Failed to revoke");
            toast.success("User forced out successfully. Tokens revoked.");
        } catch (e) {
            toast.error("Failed to force logout");
        }
    };

    if (loading) {
        return (
            <div className="space-y-4 animate-pulse">
                {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-16 bg-slate-900/50 rounded-xl border border-slate-800" />
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-end">
                <button
                    onClick={fetchEvents}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                    <RefreshCw className="h-4 w-4" /> Refresh Logs
                </button>
            </div>

            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                        <tr>
                            <th className="p-4 font-medium">Type</th>
                            <th className="p-4 font-medium">Path / Limit</th>
                            <th className="p-4 font-medium">IP Address</th>
                            <th className="p-4 font-medium">Time</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {events.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="p-8 text-center text-slate-500">
                                    No security events found.
                                </td>
                            </tr>
                        ) : (
                            events.map((event) => (
                                <tr key={event.id} className="hover:bg-slate-800/30 transition-colors">
                                    <td className="p-4 align-top">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-red-500/10 text-red-500 rounded-lg">
                                                <ShieldAlert className="h-4 w-4" />
                                            </div>
                                            <span className="font-mono text-red-200">{event.type}</span>
                                        </div>
                                    </td>
                                    <td className="p-4 align-top max-w-xs">
                                        <div className="flex flex-col gap-1">
                                            <code className="text-slate-300 bg-slate-950 px-2 py-1 rounded w-fit">
                                                {event.path}
                                            </code>
                                            {event.limit && (
                                                <span className="text-xs text-orange-400">
                                                    Limit exceeded: {event.limit}
                                                </span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="p-4 align-top">
                                        <div className="font-mono text-slate-300">{event.ip}</div>
                                        <div className="text-xs text-slate-500 truncate mt-1 max-w-[200px]" title={event.user_agent}>
                                            {event.user_agent}
                                        </div>
                                    </td>
                                    <td className="p-4 align-top text-slate-400 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <Clock className="h-3 w-3" />
                                            {new Date(event.timestamp).toLocaleString()}
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
