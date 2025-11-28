import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Clock, ChevronRight, Search } from "lucide-react";

import { HoloBadge } from "./HoloBadge";
import { Link } from "react-router-dom";

interface HistoryItem {
    id: string;
    title: string;
    source: string;
    timestamp: string;
    verdict: "Verified" | "Misleading" | "False";
    type: "text" | "image" | "video" | "url";
}

const mockHistory: HistoryItem[] = [
    {
        id: "hist-1",
        title: "Deepfake video of politician speech",
        source: "twitter.com",
        timestamp: "2 hours ago",
        verdict: "False",
        type: "video"
    },
    {
        id: "hist-2",
        title: "Image of wildfire in Australia",
        source: "news-daily.com",
        timestamp: "5 hours ago",
        verdict: "Verified",
        type: "image"
    },
    {
        id: "hist-3",
        title: "Quote attributed to CEO",
        source: "linkedin.com",
        timestamp: "1 day ago",
        verdict: "Misleading",
        type: "text"
    },
    {
        id: "hist-4",
        title: "New tech product launch leak",
        source: "tech-insider.net",
        timestamp: "2 days ago",
        verdict: "False",
        type: "url"
    },
    {
        id: "hist-5",
        title: "Historical photo of 1920s Paris",
        source: "archive.org",
        timestamp: "3 days ago",
        verdict: "Verified",
        type: "image"
    }
];

interface HistoryPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({ isOpen, onClose }) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
                    />

                    {/* Panel */}
                    <motion.div
                        initial={{ x: "100%" }}
                        animate={{ x: 0 }}
                        exit={{ x: "100%" }}
                        transition={{ type: "spring", damping: 25, stiffness: 200 }}
                        className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-black/80 border-l border-white/10 backdrop-blur-xl z-50 shadow-[-20px_0_50px_rgba(0,0,0,0.5)] flex flex-col"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-white/10 flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                                <Clock className="text-ice-cyan" />
                                Verification History
                            </h2>
                            <button
                                onClick={onClose}
                                className="p-2 rounded-full hover:bg-white/10 text-text-secondary hover:text-white transition-colors"
                            >
                                <X size={20} />
                            </button>
                        </div>

                        {/* Search (Mock) */}
                        <div className="p-4 border-b border-white/5">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" size={16} />
                                <input
                                    type="text"
                                    placeholder="Search history..."
                                    className="w-full bg-white/5 border border-white/10 rounded-lg py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-ice-cyan/50 transition-colors"
                                />
                            </div>
                        </div>

                        {/* List */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                            {mockHistory.map((item) => (
                                <Link
                                    to="/results"
                                    state={{ historyItem: item }}
                                    key={item.id}
                                    onClick={onClose}
                                    className="block group"
                                >
                                    <div className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-ice-cyan/30 hover:bg-white/10 transition-all duration-300 relative overflow-hidden">
                                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />

                                        <div className="flex justify-between items-start mb-2">
                                            <HoloBadge variant={
                                                item.verdict === "Verified" ? "success" :
                                                    item.verdict === "False" ? "danger" : "warning"
                                            }>
                                                {item.verdict}
                                            </HoloBadge>
                                            <span className="text-xs text-text-secondary">{item.timestamp}</span>
                                        </div>

                                        <h3 className="text-white font-medium mb-1 group-hover:text-ice-cyan transition-colors line-clamp-2">
                                            {item.title}
                                        </h3>

                                        <div className="flex items-center justify-between mt-3">
                                            <span className="text-xs text-royal-blue bg-royal-blue/10 px-2 py-0.5 rounded uppercase tracking-wider">
                                                {item.type}
                                            </span>
                                            <span className="text-xs text-text-secondary flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                                                View Report <ChevronRight size={12} />
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-white/10 text-center">
                            <button className="text-sm text-ice-cyan hover:text-white transition-colors">
                                Clear History
                            </button>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};
