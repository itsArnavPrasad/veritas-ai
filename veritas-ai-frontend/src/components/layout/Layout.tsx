import React from "react";
import { Background3D } from "./Background3D";
import { cn } from "../../lib/utils";

interface LayoutProps {
    children: React.ReactNode;
    className?: string;
}

export const Layout: React.FC<LayoutProps> = ({ children, className }) => {
    return (
        <div className="min-h-screen relative overflow-hidden text-text-primary font-sans selection:bg-royal-blue/30">
            <Background3D />

            {/* Grid Overlay */}
            <div className="fixed inset-0 z-0 pointer-events-none bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_at_center,black_40%,transparent_100%)]" />

            <main className={cn("relative z-10 container mx-auto px-4 py-8", className)}>
                {children}
            </main>
        </div>
    );
};
