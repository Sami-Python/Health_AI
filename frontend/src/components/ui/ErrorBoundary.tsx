"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
    children?: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="p-6 rounded-xl border border-red-900/50 bg-red-950/20 flex flex-col items-center justify-center text-center gap-2 min-h-[200px]">
                    <AlertTriangle className="h-8 w-8 text-red-500 mb-2" />
                    <h3 className="text-lg font-semibold text-red-400">Something went wrong</h3>
                    <p className="text-sm text-slate-400 max-w-sm">
                        We couldn't load this component. Please try refreshing the page.
                    </p>
                    {process.env.NODE_ENV === 'development' && this.state.error && (
                        <pre className="mt-4 p-2 bg-black/50 rounded text-xs text-red-300 overflow-auto w-full text-left">
                            {this.state.error.message}
                        </pre>
                    )}
                </div>
            );
        }

        return this.props.children;
    }
}
