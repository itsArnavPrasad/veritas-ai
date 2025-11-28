import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-deep-bg text-white p-4">
                    <div className="max-w-md w-full bg-card-1 border border-alert-red/30 rounded-lg p-6">
                        <h2 className="text-2xl font-bold text-alert-red mb-4">Something went wrong</h2>
                        <p className="text-text-secondary mb-4">
                            {this.state.error?.message || "An unexpected error occurred"}
                        </p>
                        <button
                            onClick={() => window.location.reload()}
                            className="px-4 py-2 bg-royal-blue text-white rounded-lg hover:bg-royal-blue/80 transition-colors"
                        >
                            Reload Page
                        </button>
                        <details className="mt-4">
                            <summary className="cursor-pointer text-text-secondary text-sm">Error Details</summary>
                            <pre className="mt-2 text-xs bg-black/40 p-2 rounded overflow-auto max-h-40">
                                {this.state.error?.stack}
                            </pre>
                        </details>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

