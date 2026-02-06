"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X, Mail } from "lucide-react";

export default function WaitlistPopup() {
    const [isVisible, setIsVisible] = useState(false);
    const [email, setEmail] = useState("");

    useEffect(() => {
        // Check if user has previously closed the popup
        const hasClosedPopup = localStorage.getItem("waitlist-popup-closed");
        if (!hasClosedPopup) {
            setIsVisible(true);
        }
    }, []);

    const handleClose = () => {
        setIsVisible(false);
        localStorage.setItem("waitlist-popup-closed", "true");
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Open default email client with pre-filled information
        const subject = encodeURIComponent("Waitlist Signup");
        const body = encodeURIComponent(
            `I would like to join the waitlist!\n\nMy email: ${email}\n\nPlease add me to your waitlist and notify me when Personal AI Coach is available.`
        );

        // Create a temporary anchor element to trigger mailto
        const mailtoLink = document.createElement('a');
        mailtoLink.href = `mailto:info@personalaicoach.ai?subject=${subject}&body=${body}`;
        mailtoLink.click();

        // Close popup after submission
        handleClose();
    };

    const handleContactUs = () => {
        const subject = encodeURIComponent("Contact Request");

        // Create a temporary anchor element to trigger mailto
        const mailtoLink = document.createElement('a');
        mailtoLink.href = `mailto:info@personalaicoach.ai?subject=${subject}`;
        mailtoLink.click();
    };

    const handleBackdropClick = (e: React.MouseEvent) => {
        // Only close if clicking the backdrop itself, not the modal content
        if (e.target === e.currentTarget) {
            handleClose();
        }
    };

    if (!isVisible) return null;

    return (
        <div
            onClick={handleBackdropClick}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-200"
        >
            <div className="relative w-full max-w-md mx-4 bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl border border-slate-700 p-8 animate-in zoom-in-95 duration-300">
                {/* Close Button */}
                <button
                    onClick={handleClose}
                    className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
                    aria-label="Close popup"
                >
                    <X className="h-6 w-6" />
                </button>

                {/* Content */}
                <div className="text-center space-y-6">
                    {/* Icon */}
                    <div className="flex justify-center">
                        <div className="p-3 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-full">
                            <Mail className="h-8 w-8 text-white" />
                        </div>
                    </div>

                    {/* Heading */}
                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                            Coming Soon!
                        </h2>
                        <p className="text-slate-300 text-lg">
                            Personal AI Coach is launching soon
                        </p>
                    </div>

                    {/* Description */}
                    <p className="text-slate-400 text-sm">
                        Join our waitlist to be the first to know when we launch. Get exclusive early access and special offers!
                    </p>

                    {/* Email Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="Enter your email"
                                required
                                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            />
                        </div>

                        <Button
                            type="submit"
                            size="lg"
                            className="w-full bg-gradient-to-r from-blue-500 to-emerald-500 hover:from-blue-600 hover:to-emerald-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all"
                        >
                            Join Waitlist
                        </Button>
                    </form>

                    {/* Contact Link */}
                    <div className="pt-4 border-t border-slate-700">
                        <button
                            onClick={handleContactUs}
                            className="text-sm text-slate-400 hover:text-blue-400 transition-colors underline-offset-4 hover:underline"
                        >
                            Have questions? Contact us
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
