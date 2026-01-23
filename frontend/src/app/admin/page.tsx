"use client";

import AdminGuard from "@/components/AdminGuard";
import FeedbackTable from "@/components/FeedbackTable";
import { Shield, Users, MessageSquare } from "lucide-react";
import { useState } from "react";
import AnimateEntry from "@/components/ui/AnimateEntry";

export default function AdminPage() {
    const [activeTab, setActiveTab] = useState<'feedback' | 'users'>('feedback');

    return (
        <AdminGuard>
            <div className="min-h-screen bg-slate-950 p-8 text-white">
                <div className="mx-auto max-w-7xl space-y-8">
                    <AnimateEntry>
                        <div className="flex items-center gap-4 border-b border-slate-800 pb-6 mb-8">
                            <div className="p-3 bg-red-500/10 rounded-xl text-red-500">
                                <Shield className="h-8 w-8" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
                                    Admin Dashboard
                                </h1>
                                <p className="text-slate-400 mt-1">System Monitoring & Support</p>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="flex gap-4 mb-8">
                            <button
                                onClick={() => setActiveTab('feedback')}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'feedback'
                                        ? 'bg-slate-800 text-white'
                                        : 'text-slate-500 hover:text-slate-300'
                                    }`}
                            >
                                <MessageSquare className="h-4 w-4" /> Feedback
                            </button>
                            <button
                                onClick={() => setActiveTab('users')}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${activeTab === 'users'
                                        ? 'bg-slate-800 text-white'
                                        : 'text-slate-500 hover:text-slate-300'
                                    }`}
                            >
                                <Users className="h-4 w-4" /> Users (Coming Soon)
                            </button>
                        </div>

                        {/* Content */}
                        {activeTab === 'feedback' && (
                            <div className="space-y-4">
                                <h2 className="text-xl font-semibold text-slate-200">User Feedback</h2>
                                <FeedbackTable />
                            </div>
                        )}

                        {activeTab === 'users' && (
                            <div className="p-12 text-center border dashed border-slate-800 rounded-xl text-slate-500">
                                <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>User management interface is under construction.</p>
                            </div>
                        )}

                    </AnimateEntry>
                </div>
            </div>
        </AdminGuard>
    );
}
