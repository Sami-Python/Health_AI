"use client";

import { useState, useRef, useEffect } from "react";
import { User, Settings, LogOut, Menu } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "./ui/button";

export default function UserMenu() {
    const { user, signOut } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    if (!user) return null;

    return (
        <div className="relative" ref={menuRef}>
            <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(!isOpen)}
                className="text-slate-400 hover:text-white hover:bg-slate-800 rounded-full h-10 w-10"
            >
                <Menu className="h-6 w-6" />
            </Button>

            {isOpen && (
                <div className="absolute right-0 top-12 w-56 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                    <div className="px-4 py-3 border-b border-slate-800 mb-2">
                        <p className="text-sm font-medium text-white truncate">{user.displayName || "User"}</p>
                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                    </div>

                    <div className="space-y-1 px-2">
                        <button className="w-full flex items-center gap-3 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors text-left">
                            <User className="h-4 w-4" />
                            Profile
                        </button>
                        <button className="w-full flex items-center gap-3 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors text-left">
                            <Settings className="h-4 w-4" />
                            Settings
                        </button>
                    </div>

                    <div className="my-2 border-t border-slate-800"></div>

                    <div className="px-2">
                        <button
                            onClick={() => signOut()}
                            className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-400 hover:bg-red-950/30 hover:text-red-300 rounded-lg transition-colors text-left"
                        >
                            <LogOut className="h-4 w-4" />
                            Sign Out
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
