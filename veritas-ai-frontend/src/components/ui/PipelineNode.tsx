import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import type { LucideIcon } from "lucide-react";

interface PipelineNodeProps {
    icon: LucideIcon;
    label: string;
    details?: Record<string, string | number>;
    status: "idle" | "processing" | "completed" | "warning" | "danger";
    isActive?: boolean;
    className?: string;
    size?: "sm" | "md" | "lg";
}

export const PipelineNode: React.FC<PipelineNodeProps> = ({
    icon: Icon,
    label,
    details,
    status,
    isActive = false,
    className,
    size = "md",
}) => {
    const [isHovered, setIsHovered] = useState(false);

    const sizeClasses = {
        sm: "w-10 h-10",
        md: "w-14 h-14",
        lg: "w-20 h-20",
    };

    const iconSizes = {
        sm: 16,
        md: 24,
        lg: 32,
    };

    const statusColors = {
        idle: "border-white/10 bg-black/40 text-text-secondary",
        processing: "border-ice-cyan bg-ice-cyan/10 text-ice-cyan shadow-[0_0_20px_-5px_#9EE8FF]",
        completed: "border-royal-blue bg-royal-blue/10 text-royal-blue shadow-[0_0_15px_-5px_#3D89F5]",
        warning: "border-saffron-gold bg-saffron-gold/10 text-saffron-gold shadow-[0_0_20px_-5px_#F4C430]",
        danger: "border-alert-red bg-alert-red/10 text-alert-red shadow-[0_0_20px_-5px_#F85149]",
    };

    return (
        <div
            className={cn("relative flex flex-col items-center group z-10", className)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            <motion.div
                initial={false}
                animate={{
                    scale: isActive || isHovered ? 1.1 : 1,
                    y: isActive || isHovered ? -5 : 0,
                }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={cn(
                    "rounded-full border backdrop-blur-md flex items-center justify-center transition-all duration-500 relative cursor-pointer",
                    sizeClasses[size],
                    statusColors[status]
                )}
            >
                {/* Inner Glow Pulse */}
                {status === "processing" && (
                    <motion.div
                        className="absolute inset-0 rounded-full bg-ice-cyan/20"
                        animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    />
                )}

                {/* Icon */}
                <Icon size={iconSizes[size]} className="relative z-10" />

                {/* 3D Depth Effect (Bottom Shadow) */}
                <div className="absolute -bottom-2 w-3/4 h-1 bg-black/50 blur-sm rounded-full" />
            </motion.div>

            {/* Label */}
            <motion.div
                className={cn(
                    "absolute top-full mt-3 text-center w-32 transition-colors duration-300",
                    isActive || isHovered ? "text-white font-medium" : "text-text-secondary/70 text-sm"
                )}
            >
                {label}
            </motion.div>

            {/* Tooltip */}
            <AnimatePresence>
                {isHovered && details && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.9 }}
                        transition={{ duration: 0.2 }}
                        className="absolute bottom-full mb-4 min-w-[180px] p-3 rounded-lg bg-black/90 border border-white/20 backdrop-blur-xl shadow-xl z-50 pointer-events-none"
                    >
                        <div className="space-y-2">
                            {Object.entries(details).map(([key, value]) => (
                                <div key={key} className="flex justify-between items-center text-xs border-b border-white/10 last:border-0 pb-1 last:pb-0">
                                    <span className="text-text-secondary">{key}:</span>
                                    <span className="text-ice-cyan font-mono font-medium">{value}</span>
                                </div>
                            ))}
                        </div>
                        {/* Arrow */}
                        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-white/20" />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
