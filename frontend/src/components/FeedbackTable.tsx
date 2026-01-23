"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL, fetchWithRetry } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";

interface FeedbackItem {
    id: string; // Firestore ID if available, or just index? Backend returns dictionary list.
    user_id: string;
    category: string;
    message: string;
    page: string;
    timestamp?: string; // Depends on backend fields
    status?: string;
}

export default function FeedbackTable() {
    const { user } = useAuth();
    const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            fetchFeedback();
        }
    }, [user]);

    const fetchFeedback = async () => {
        try {
            const token = await user?.getIdToken();
            const headers = { 'Authorization': `Bearer ${token}` };

            // Default limit 100
            const res = await fetchWithRetry(`${API_BASE_URL}/admin/feedback?limit=100`, { headers });

            if (res.ok) {
                const data = await res.json();
                // Data format: { total: 123, feedback: [...] }
                setFeedback(data.feedback);
            } else {
                if (res.status === 403) {
                    toast.error("Access Denied: You are not an admin.");
                } else {
                    toast.error("Failed to fetch feedback");
                }
            }
        } catch (e) {
            console.error(e);
            toast.error("Error loading feedback");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-4 text-center text-slate-400">Loading feedback...</div>;

    if (feedback.length === 0) {
        return <div className="p-8 text-center text-slate-500 border border-dashed border-slate-700 rounded-lg">No feedback found.</div>;
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-sm text-slate-400">
                <thead className="bg-slate-900 text-xs uppercase text-slate-200">
                    <tr>
                        <th className="px-6 py-3">Category</th>
                        <th className="px-6 py-3">Message</th>
                        <th className="px-6 py-3">Page</th>
                        <th className="px-6 py-3">User ID</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 bg-slate-900/50">
                    {feedback.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                            <td className="px-6 py-4 font-medium text-white">
                                <span className={`px-2 py-1 rounded-full text-xs ${item.category === 'bug' ? 'bg-red-500/10 text-red-400' :
                                        item.category === 'feature_request' ? 'bg-blue-500/10 text-blue-400' :
                                            'bg-slate-700 text-slate-300'
                                    }`}>
                                    {item.category}
                                </span>
                            </td>
                            <td className="px-6 py-4 text-slate-300 max-w-md truncate" title={item.message}>
                                {item.message}
                            </td>
                            <td className="px-6 py-4 font-mono text-xs">{item.page || '-'}</td>
                            <td className="px-6 py-4 font-mono text-xs truncate max-w-[100px]" title={item.user_id}>
                                {item.user_id}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
