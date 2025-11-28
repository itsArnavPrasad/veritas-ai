import React, { useState } from "react";
import { motion } from "framer-motion";
import { Layout } from "../components/layout/Layout";
import { AntiGravityCard } from "../components/ui/AntiGravityCard";
import { HoloBadge } from "../components/ui/HoloBadge";
import { CheckCircle, XCircle, ChevronDown, ChevronUp, Image as ImageIcon, Clock, Globe, FileText, AlertTriangle, ShieldCheck } from "lucide-react";

const inputResults = [
    {
        id: "1",
        type: "text",
        content: "The image shows a recent protest in Paris where police used tear gas.",
        status: "False",
        confidence: 98,
        details: "Text claims contradict visual evidence and verified news sources."
    },
    {
        id: "2",
        type: "image",
        content: "protest_scene.jpg",
        status: "Misleading",
        confidence: 92,
        details: "Image is from a 2018 movie set, not a real event."
    }
];

const crossModalAnalysis = [
    {
        type: "conflict",
        message: "Text claim 'recent protest' conflicts with Image origin (2018).",
        severity: "high"
    },
    {
        type: "match",
        message: "Visual elements match 'Paris' location data.",
        severity: "low"
    }
];

import { useLocation } from "react-router-dom";

export const ResultsPage: React.FC = () => {
    const location = useLocation();
    const historyItem = location.state?.historyItem;
    const [expandedItem, setExpandedItem] = useState<string | null>("1");

    // If historyItem exists, override the default display (mock logic)
    const displayTitle = historyItem ? "Historical Verification" : "False Context Detected";
    const displayVerdict = historyItem ? historyItem.verdict : "False Context Detected";
    const displayContent = historyItem ? historyItem.title : "The provided text claims do not align with the visual evidence. The image is out of context (2018 film set).";

    const verdictVariant = displayVerdict === "Verified" ? "success" : displayVerdict === "False" ? "danger" : "warning";

    return (
        <Layout className="pb-20">
            {/* Top Section: Unified Verdict */}
            <div className="flex flex-col items-center mb-12">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    className="relative w-full max-w-3xl"
                >
                    <div className="absolute inset-0 bg-alert-red/20 blur-3xl rounded-full" />
                    <div className="relative bg-black/60 border border-alert-red/50 backdrop-blur-xl px-8 py-8 rounded-2xl flex flex-col md:flex-row items-center gap-8 shadow-[0_0_50px_-10px_rgba(248,81,73,0.3)]">
                        <div className="flex-shrink-0">
                            <XCircle className="text-alert-red w-20 h-20" />
                        </div>
                        <div className="flex-1 text-center md:text-left">
                            <HoloBadge variant={verdictVariant} className="mb-2">{displayVerdict.toUpperCase()}</HoloBadge>
                            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                                {displayTitle}
                            </h1>
                            <p className="text-text-secondary text-lg">
                                {displayContent}
                            </p>
                        </div>

                        {/* Confidence Meter */}
                        <div className="w-full md:w-48">
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-text-secondary">Confidence</span>
                                <span className="text-alert-red font-bold">95%</span>
                            </div>
                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "95%" }}
                                    transition={{ duration: 1, delay: 0.5 }}
                                    className="h-full bg-alert-red shadow-[0_0_10px_#F85149]"
                                />
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Input Breakdown */}
                <div className="lg:col-span-2 space-y-6">
                    <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                        <CheckCircle className="text-ice-cyan" />
                        Input Analysis
                    </h2>
                    {inputResults.map((item) => (
                        <AntiGravityCard
                            key={item.id}
                            glowColor={item.status === "False" || item.status === "Misleading" ? "red" : "gold"}
                            className={`transition-all duration-300 ${expandedItem === item.id ? "ring-1 ring-white/20" : ""}`}
                        >
                            <div
                                className="flex justify-between items-start cursor-pointer"
                                onClick={() => setExpandedItem(expandedItem === item.id ? null : item.id)}
                            >
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="p-2 rounded-lg bg-white/5 text-ice-cyan mt-1">
                                        {item.type === "text" && <FileText size={20} />}
                                        {item.type === "image" && <ImageIcon size={20} />}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="text-lg font-medium text-white capitalize">{item.type} Input</h3>
                                            <HoloBadge variant={item.status === "False" || item.status === "Misleading" ? "danger" : "warning"}>
                                                {item.status}
                                            </HoloBadge>
                                        </div>
                                        <p className="text-text-secondary text-sm line-clamp-1">{item.content}</p>
                                    </div>
                                </div>
                                <button className="text-text-secondary hover:text-white transition-colors">
                                    {expandedItem === item.id ? <ChevronUp /> : <ChevronDown />}
                                </button>
                            </div>

                            {/* Expanded Details */}
                            {expandedItem === item.id && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="mt-6 pt-6 border-t border-white/10"
                                >
                                    <p className="text-white mb-4">{item.details}</p>

                                    {item.type === "image" && (
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                                                <span className="text-xs text-text-secondary block mb-1">Reverse Search</span>
                                                <span className="text-sm text-royal-blue flex items-center gap-1"><Globe size={12} /> 12 Matches Found</span>
                                            </div>
                                            <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                                                <span className="text-xs text-text-secondary block mb-1">Creation Date</span>
                                                <span className="text-sm text-white flex items-center gap-1"><Clock size={12} /> Oct 2018</span>
                                            </div>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AntiGravityCard>
                    ))}
                </div>

                {/* Right Column: Cross-Modal & Forensics */}
                <div className="space-y-8">
                    {/* Cross-Modal Consistency */}
                    <div>
                        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                            <ShieldCheck className="text-ice-cyan" />
                            Cross-Modal Check
                        </h2>
                        <AntiGravityCard glowColor="blue">
                            <div className="space-y-4">
                                {crossModalAnalysis.map((analysis, i) => (
                                    <div key={i} className={`p-3 rounded-lg border ${analysis.type === "conflict"
                                        ? "bg-alert-red/10 border-alert-red/30"
                                        : "bg-green-500/10 border-green-500/30"
                                        }`}>
                                        <div className="flex items-center gap-2 mb-1">
                                            {analysis.type === "conflict" ? (
                                                <AlertTriangle size={16} className="text-alert-red" />
                                            ) : (
                                                <CheckCircle size={16} className="text-green-400" />
                                            )}
                                            <span className={`text-sm font-medium ${analysis.type === "conflict" ? "text-alert-red" : "text-green-400"
                                                }`}>
                                                {analysis.type === "conflict" ? "Consistency Error" : "Verified Match"}
                                            </span>
                                        </div>
                                        <p className="text-sm text-white/90">{analysis.message}</p>
                                    </div>
                                ))}
                            </div>
                        </AntiGravityCard>
                    </div>

                    {/* Provenance Timeline */}
                    <div>
                        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                            <Clock className="text-ice-cyan" />
                            Timeline
                        </h2>
                        <AntiGravityCard glowColor="cyan" className="relative overflow-hidden">
                            <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-white/10" />
                            <div className="space-y-6 relative">
                                {[
                                    { date: "2018-05-12", event: "Image first appeared (Movie Set)", source: "imdb.com", type: "Origin" },
                                    { date: "2023-11-24", event: "Text claim posted", source: "twitter.com", type: "Spread" },
                                    { date: "2023-11-25", event: "Analysis Requested", source: "Veritas System", type: "Alert" },
                                ].map((item, i) => (
                                    <div key={i} className="flex gap-4 items-start ml-2">
                                        <div className="w-2 h-2 rounded-full bg-ice-cyan mt-2 shadow-[0_0_10px_#9EE8FF]" />
                                        <div>
                                            <span className="text-xs text-text-secondary block mb-0.5">{item.date}</span>
                                            <p className="text-sm text-white font-medium">{item.event}</p>
                                            <div className="flex items-center gap-1 text-xs text-royal-blue mt-1">
                                                <Globe size={10} /> {item.source}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </AntiGravityCard>
                    </div>
                </div>
            </div>
        </Layout>
    );
};
