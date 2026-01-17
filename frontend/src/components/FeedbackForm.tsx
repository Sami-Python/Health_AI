"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { X, Send } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { API_BASE_URL } from "@/lib/utils";

interface FeedbackFormProps {
    onClose: () => void;
}

export default function FeedbackForm({ onClose }: FeedbackFormProps) {
    const { user } = useAuth();
    const [category, setCategory] = useState<string>("general");
    const [message, setMessage] = useState<string>("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user || !message.trim()) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const token = await user.getIdToken();
            const res = await fetch(`${API_BASE_URL}/feedback`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({
                    category,
                    message: message.trim(),
                    page: window.location.pathname,
                }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to submit feedback");
            }

            setSuccess(true);
            setTimeout(() => {
                onClose();
            }, 1500);
        } catch (err: any) {
            setError(err.message);
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-white">Send Feedback</h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white transition-colors"
                        aria-label="Close"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {success ? (
                    <div className="text-center py-8">
                        <div className="inline-block p-3 bg-green-900/20 rounded-full mb-4">
                            <Send className="h-8 w-8 text-green-500" />
                        </div>
                        <p className="text-green-400 font-semibold">Feedback sent!</p>
                        <p className="text-slate-400 text-sm mt-2">Thank you for helping us improve.</p>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Category */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Category
                            </label>
                            <select
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="general">General Feedback</option>
                                <option value="bug">Bug Report</option>
                                <option value="feature_request">Feature Request</option>
                            </select>
                        </div>

                        {/* Message */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                Message
                            </label>
                            <textarea
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Tell us what you think..."
                                maxLength={500}
                                rows={5}
                                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                required
                            />
                            <p className="text-xs text-slate-500 mt-1 text-right">
                                {message.length}/500
                            </p>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="p-3 bg-red-950/50 border border-red-900 rounded text-red-200 text-sm">
                                Error: {error}
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-3 pt-2">
                            <Button
                                type="button"
                                variant="outline"
                                onClick={onClose}
                                className="flex-1 border-slate-700 hover:bg-slate-800 text-slate-300"
                            >
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                disabled={isSubmitting || !message.trim()}
                                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                            >
                                {isSubmitting ? (
                                    "Sending..."
                                ) : (
                                    <>
                                        <Send className="h-4 w-4 mr-2" />
                                        Send
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
