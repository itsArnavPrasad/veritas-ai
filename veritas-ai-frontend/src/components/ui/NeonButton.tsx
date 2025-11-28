import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "../../lib/utils";
import React from "react";

interface NeonButtonProps extends HTMLMotionProps<"button"> {
    variant?: "primary" | "secondary" | "danger";
    children: React.ReactNode;
}

const variants = {
    primary: "bg-royal-blue text-white shadow-[0_0_15px_-3px_#3D89F5] hover:shadow-[0_0_25px_-5px_#3D89F5] border-transparent",
    secondary: "bg-transparent text-ice-cyan border-ice-cyan/50 shadow-[0_0_10px_-3px_#9EE8FF] hover:shadow-[0_0_20px_-5px_#9EE8FF] hover:bg-ice-cyan/10",
    danger: "bg-transparent text-alert-red border-alert-red/50 shadow-[0_0_10px_-3px_#F85149] hover:shadow-[0_0_20px_-5px_#F85149] hover:bg-alert-red/10",
};

export const NeonButton = React.forwardRef<HTMLButtonElement, NeonButtonProps>(
    ({ className, variant = "primary", children, ...props }, ref) => {
        return (
            <motion.button
                ref={ref}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={cn(
                    "relative px-6 py-3 rounded-lg font-medium tracking-wide transition-all duration-300 border",
                    variants[variant],
                    className
                )}
                {...props}
            >
                {children}
            </motion.button>
        );
    }
);

NeonButton.displayName = "NeonButton";
