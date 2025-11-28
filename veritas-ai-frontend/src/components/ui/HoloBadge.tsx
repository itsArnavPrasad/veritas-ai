import { cn } from "../../lib/utils";
import React from "react";

interface HoloBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: "neutral" | "success" | "warning" | "danger" | "info";
    children: React.ReactNode;
}

const variants = {
    neutral: "bg-white/5 border-white/10 text-text-secondary shadow-[0_0_10px_-5px_rgba(255,255,255,0.2)]",
    success: "bg-green-500/10 border-green-500/30 text-green-400 shadow-[0_0_10px_-5px_rgba(74,222,128,0.4)]",
    warning: "bg-saffron-gold/10 border-saffron-gold/30 text-saffron-gold shadow-[0_0_10px_-5px_#F4C430]",
    danger: "bg-alert-red/10 border-alert-red/30 text-alert-red shadow-[0_0_10px_-5px_#F85149]",
    info: "bg-ice-cyan/10 border-ice-cyan/30 text-ice-cyan shadow-[0_0_10px_-5px_#9EE8FF]",
};

export const HoloBadge = React.forwardRef<HTMLSpanElement, HoloBadgeProps>(
    ({ className, variant = "neutral", children, ...props }, ref) => {
        return (
            <span
                ref={ref}
                className={cn(
                    "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border backdrop-blur-md",
                    variants[variant],
                    className
                )}
                {...props}
            >
                {children}
            </span>
        );
    }
);

HoloBadge.displayName = "HoloBadge";
