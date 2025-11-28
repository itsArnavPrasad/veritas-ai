import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "../../lib/utils";
import React from "react";

interface AntiGravityCardProps extends HTMLMotionProps<"div"> {
    children: React.ReactNode;
    className?: string;
    glowColor?: "blue" | "cyan" | "red" | "gold";
}

const glowColors = {
    blue: "hover:shadow-[0_0_20px_-5px_#3D89F5]",
    cyan: "hover:shadow-[0_0_20px_-5px_#9EE8FF]",
    red: "hover:shadow-[0_0_20px_-5px_#F85149]",
    gold: "hover:shadow-[0_0_20px_-5px_#F4C430]",
};

export const AntiGravityCard = React.forwardRef<HTMLDivElement, AntiGravityCardProps>(
    ({ children, className, glowColor = "cyan", ...props }, ref) => {
        return (
            <motion.div
                ref={ref}
                className={cn(
                    "relative bg-card-1 border border-white/10 rounded-xl p-6 backdrop-blur-md",
                    "transition-all duration-300 ease-out",
                    "hover:-translate-y-2 hover:border-white/20",
                    glowColors[glowColor],
                    className
                )}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                {...props}
            >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 rounded-xl pointer-events-none" />
                {children}
            </motion.div>
        );
    }
);

AntiGravityCard.displayName = "AntiGravityCard";
