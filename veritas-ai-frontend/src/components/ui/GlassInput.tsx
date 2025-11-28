import { cn } from "../../lib/utils";
import React from "react";

interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    icon?: React.ReactNode;
}

export const GlassInput = React.forwardRef<HTMLInputElement, GlassInputProps>(
    ({ className, icon, ...props }, ref) => {
        return (
            <div className="relative group">
                {icon && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary group-focus-within:text-ice-cyan transition-colors duration-300">
                        {icon}
                    </div>
                )}
                <input
                    ref={ref}
                    className={cn(
                        "w-full bg-black/40 border border-white/10 rounded-lg py-3 px-4 text-text-primary placeholder:text-text-secondary/50",
                        "focus:outline-none focus:border-ice-cyan/50 focus:shadow-[0_0_15px_-5px_#9EE8FF]",
                        "transition-all duration-300 backdrop-blur-sm",
                        icon ? "pl-10" : "",
                        className
                    )}
                    {...props}
                />
                <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-500" />
            </div>
        );
    }
);

GlassInput.displayName = "GlassInput";
