import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layout } from "../components/layout/Layout";
import { PipelineNode } from "../components/ui/PipelineNode";
import { NeonButton } from "../components/ui/NeonButton";
import { Link, useLocation } from "react-router-dom";
import {
    FileText, Search, Brain, Image as ImageIcon, ShieldCheck, CheckCircle,
    Loader2, ArrowRight, Video, Eye, AlertTriangle
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Define the structure of the pipeline
const pipelineConfig = {
    lanes: [
        { id: "text", label: "Text Claims", icon: FileText, color: "cyan", y: 150 },
        { id: "image", label: "Visual Forensics", icon: ImageIcon, color: "gold", y: 250 },
        { id: "video", label: "Video Analysis", icon: Video, color: "red", y: 350 },
    ],
    stages: [
        { id: "preprocessing", label: "Preprocessing", x: 200 },
        { id: "extraction", label: "Extraction", x: 400 },
        { id: "retrieval", label: "Intelligence", x: 600 },
        { id: "fusion", label: "Fusion", x: 800 }, // Convergence point
        { id: "verdict", label: "Verdict", x: 1000 },
    ]
};

export const PipelineScreen: React.FC = () => {
    const location = useLocation();
    // Get inputs from state or sessionStorage fallback
    const inputs = location.state?.inputs || 
        (() => {
            try {
                const stored = sessionStorage.getItem("pipelineInputs");
                return stored ? JSON.parse(stored) : [
                    { id: "1", type: "text", content: "Sample claim" },
                    { id: "2", type: "image", content: "evidence.jpg" }
                ];
            } catch {
                return [
        { id: "1", type: "text", content: "Sample claim" },
        { id: "2", type: "image", content: "evidence.jpg" }
    ];
            }
        })();

    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    
    // State for image VLM analysis results
    const [imageAnalysisResults, setImageAnalysisResults] = useState<Map<string, any>>(new Map());
    const [analyzingImages, setAnalyzingImages] = useState<Set<string>>(new Set());
    const [activityLogs, setActivityLogs] = useState<Array<{ time: string; agent: string; message: string }>>([
        { time: "10:42:01", agent: "Orchestrator", message: "Initiating multimodal pipeline..." },
    ]);

    // Analyze images when component mounts
    useEffect(() => {
        const analyzeImages = async () => {
            const imageInputs = inputs.filter((input: any) => input.type === "image" && input.file_id);
            
            if (imageInputs.length > 0) {
                setActivityLogs((prev) => [
                    ...prev,
                    { 
                        time: new Date().toLocaleTimeString(), 
                        agent: "Preprocessor", 
                        message: `Inputs received: ${inputs.filter((i: any) => i.type === "text").length} Text, ${imageInputs.length} Image(s).` 
                    },
                ]);
            }
            
            for (const input of imageInputs) {
                if (imageAnalysisResults.has(input.id) || analyzingImages.has(input.id)) {
                    continue; // Already analyzed or analyzing
                }
                
                setAnalyzingImages((prev) => new Set(prev).add(input.id));
                setActivityLogs((prev) => [
                    ...prev,
                    { 
                        time: new Date().toLocaleTimeString(), 
                        agent: "VisionAgent", 
                        message: `Analyzing image: ${input.content} with Gemini VLM...` 
                    },
                ]);
                
                try {
                    const response = await fetch(`${API_BASE_URL}/api/v1/verify/image/by-file-id`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ file_id: input.file_id }),
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        setImageAnalysisResults((prev) => {
                            const newMap = new Map(prev);
                            newMap.set(input.id, data);
                            return newMap;
                        });
                        
                        const artifactStatus = data.vlm_ai_artifact_analysis?.artifact_detected ? "Detected" : "None";
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "VisionAgent", 
                                message: `Image analysis complete. AI Artifacts: ${artifactStatus}` 
                            },
                        ]);
                    } else {
                        const errorText = await response.text();
                        console.error(`Failed to analyze image ${input.id}:`, errorText);
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "VisionAgent", 
                                message: `Error analyzing image: ${errorText}` 
                            },
                        ]);
                    }
                } catch (error) {
                    console.error(`Error analyzing image ${input.id}:`, error);
                    setActivityLogs((prev) => [
                        ...prev,
                        { 
                            time: new Date().toLocaleTimeString(), 
                            agent: "VisionAgent", 
                            message: `Error: ${error instanceof Error ? error.message : "Unknown error"}` 
                        },
                    ]);
                } finally {
                    setAnalyzingImages((prev) => {
                        const newSet = new Set(prev);
                        newSet.delete(input.id);
                        return newSet;
                    });
                }
            }
        };
        
        analyzeImages();
    }, [inputs]);

    // Simulate progress
    useEffect(() => {
        const timer = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 100) {
                    clearInterval(timer);
                    setIsComplete(true);
                    return 100;
                }
                return prev + 0.5;
            });
        }, 50);
        return () => clearInterval(timer);
    }, []);

    // Calculate active stage based on progress
    const getActiveStage = (p: number) => {
        if (p < 20) return "preprocessing";
        if (p < 40) return "extraction";
        if (p < 60) return "retrieval";
        if (p < 80) return "fusion";
        return "verdict";
    };

    const activeStage = getActiveStage(progress);

    // Helper to generate SVG paths
    const generatePath = (startY: number, endY: number, startX: number, endX: number) => {
        const midX = (startX + endX) / 2;
        return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
    };

    return (
        <Layout className="h-screen overflow-hidden flex flex-col">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 z-20 p-6 text-center pointer-events-none">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-2xl font-bold text-white tracking-widest uppercase"
                >
                    Real-Time AI Verification Pipeline
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="text-ice-cyan/60 text-sm mt-2"
                >
                    Parallel multimodal analysis → Unified calibrated verdict
                </motion.p>
            </div>

            <div className="flex-1 flex relative">
                {/* Main Visualization Area */}
                <div ref={containerRef} className="flex-1 relative overflow-hidden bg-deep-bg perspective-1000">

                    {/* SVG Layer for Paths */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                        <defs>
                            <linearGradient id="gradient-flow" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#3D89F5" stopOpacity="0.2" />
                                <stop offset="100%" stopColor="#9EE8FF" stopOpacity="0.8" />
                            </linearGradient>
                        </defs>

                        {/* Draw paths for each lane */}
                        {pipelineConfig.lanes.map((lane) => {
                            // Only draw if this input type is present
                            const hasInput = inputs.some((i: any) => i.type === lane.id);
                            const opacity = hasInput ? 1 : 0.1;

                            // Path 1: Start to Preprocessing
                            const path1 = generatePath(lane.y, lane.y, 50, 200);
                            // Path 2: Preprocessing to Extraction
                            const path2 = generatePath(lane.y, lane.y, 200, 400);
                            // Path 3: Extraction to Retrieval
                            const path3 = generatePath(lane.y, lane.y, 400, 600);
                            // Path 4: Retrieval to Fusion (Convergence)
                            const path4 = generatePath(lane.y, 250, 600, 800); // Converge to center Y (250)

                            return (
                                <g key={lane.id} style={{ opacity }}>
                                    <path d={`${path1} ${path2} ${path3} ${path4}`} stroke="url(#gradient-flow)" strokeWidth="2" fill="none" />

                                    {/* Animated Flow Line */}
                                    {hasInput && (
                                        <motion.path
                                            d={`${path1} ${path2} ${path3} ${path4}`}
                                            stroke="#9EE8FF"
                                            strokeWidth="3"
                                            fill="none"
                                            initial={{ pathLength: 0 }}
                                            animate={{ pathLength: progress / 80 }} // Stop at fusion (80%)
                                            transition={{ duration: 0.1, ease: "linear" }}
                                            strokeLinecap="round"
                                            filter="url(#glow)"
                                        />
                                    )}
                                </g>
                            );
                        })}

                        {/* Path from Fusion to Verdict */}
                        <path d="M 800 250 L 1000 250" stroke="url(#gradient-flow)" strokeWidth="2" fill="none" opacity="0.5" />
                        <motion.path
                            d="M 800 250 L 1000 250"
                            stroke="#F85149" // Red for verdict/alert
                            strokeWidth="4"
                            fill="none"
                            initial={{ pathLength: 0 }}
                            animate={{ pathLength: Math.max(0, (progress - 80) / 20) }}
                            transition={{ duration: 0.1, ease: "linear" }}
                            strokeLinecap="round"
                        />
                    </svg>

                    {/* Nodes Layer */}
                    <div className="absolute inset-0 z-10">
                        {/* Parallel Nodes (Preprocessing, Extraction, Retrieval) */}
                        {pipelineConfig.lanes.map((lane) => {
                            const hasInput = inputs.some((i: any) => i.type === lane.id);
                            if (!hasInput) return null;

                            return (
                                <React.Fragment key={lane.id}>
                                    {/* Input Card */}
                                    <div className="absolute left-4" style={{ top: lane.y - 20 }}>
                                        <div className="bg-black/60 border border-white/10 rounded-lg p-2 flex items-center gap-2 backdrop-blur-sm">
                                            <lane.icon size={16} className={`text-${lane.color}-400`} />
                                            <span className="text-xs text-white font-mono uppercase">{lane.label}</span>
                                        </div>
                                    </div>

                                    {/* Preprocessing Node */}
                                    <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 200, top: lane.y }}>
                                        <PipelineNode
                                            icon={FileText}
                                            label="Preprocess"
                                            details={{ "Noise Level": "Low", "Format": "UTF-8", "Size": "12KB" }}
                                            status={progress > 0 && progress < 20 ? "processing" : progress >= 20 ? "completed" : "idle"}
                                            isActive={activeStage === "preprocessing"}
                                            size="sm"
                                        />
                                    </div>
                                    {/* Extraction Node */}
                                    <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 400, top: lane.y }}>
                                        {lane.id === "image" ? (() => {
                                            const imageInput = inputs.find((i: any) => i.type === "image");
                                            const analysis = imageInput ? imageAnalysisResults.get(imageInput.id) : null;
                                            const isAnalyzing = imageInput ? analyzingImages.has(imageInput.id) : false;
                                            
                                            const details: any = {};
                                            if (analysis?.vlm_description) {
                                                if (analysis.vlm_description.objects) {
                                                    details["Objects"] = analysis.vlm_description.objects.length;
                                                }
                                                if (analysis.vlm_description.visible_text) {
                                                    details["Text Found"] = analysis.vlm_description.visible_text.length > 0 ? "Yes" : "No";
                                                }
                                            }
                                            if (analysis?.vlm_ai_artifact_analysis) {
                                                details["AI Artifacts"] = analysis.vlm_ai_artifact_analysis.artifact_detected ? "Detected" : "None";
                                            }
                                            
                                            if (Object.keys(details).length === 0) {
                                                details["Status"] = isAnalyzing ? "Analyzing..." : "Pending";
                                            }
                                            
                                            return (
                                                <PipelineNode
                                                    icon={Search}
                                                    label="VLM Analysis"
                                                    details={details}
                                                    status={
                                                        isAnalyzing 
                                                            ? "processing" 
                                                            : analysis 
                                                                ? "completed" 
                                                                : progress > 20 && progress < 40 
                                                                    ? "processing" 
                                                                    : "idle"
                                                    }
                                                    isActive={activeStage === "extraction" || isAnalyzing}
                                                    size="sm"
                                                />
                                            );
                                        })() : (
                                        <PipelineNode
                                            icon={Search}
                                            label="Extract"
                                            details={{ "Claims": 3, "Entities": 5, "Sentiment": "Negative" }}
                                            status={progress > 20 && progress < 40 ? "processing" : progress >= 40 ? "completed" : "idle"}
                                            isActive={activeStage === "extraction"}
                                            size="sm"
                                        />
                                        )}
                                    </div>
                                    {/* Retrieval Node */}
                                    <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 600, top: lane.y }}>
                                        <PipelineNode
                                            icon={Brain}
                                            label="Retrieval"
                                            details={{ "Sources": 12, "Reliability": "High", "Matches": 8 }}
                                            status={progress > 40 && progress < 60 ? "processing" : progress >= 60 ? "completed" : "idle"}
                                            isActive={activeStage === "retrieval"}
                                            size="sm"
                                        />
                                    </div>
                                </React.Fragment>
                            );
                        })}

                        {/* Fusion Node (Converged) */}
                        <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 800, top: 250 }}>
                            <PipelineNode
                                icon={ShieldCheck}
                                label="Cross-Modal Fusion"
                                details={{ "Consistency": "85%", "Conflicts": 1, "Support": "Strong" }}
                                status={progress > 60 && progress < 80 ? "processing" : progress >= 80 ? "completed" : "idle"}
                                isActive={activeStage === "fusion"}
                                size="lg"
                            />
                        </div>

                        {/* Verdict Node (Final) */}
                        <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 1000, top: 250 }}>
                            <PipelineNode
                                icon={CheckCircle}
                                label="Calibrated Verdict"
                                details={{ "Score": "98%", "Verdict": "False", "Risk": "Critical" }}
                                status={progress >= 95 ? "danger" : "idle"} // Simulating a "False" verdict
                                isActive={activeStage === "verdict"}
                                size="lg"
                            />
                        </div>
                    </div>
                </div>

                {/* Right Panel: Agent Activity Log & Image Analysis */}
                <div className="w-96 border-l border-white/10 bg-black/40 backdrop-blur-xl flex flex-col z-20">
                    <div className="p-4 border-b border-white/10">
                        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                            <Loader2 className={`text-ice-cyan ${!isComplete ? "animate-spin" : ""}`} size={16} />
                            Analysis Results
                        </h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10">
                        {/* Image VLM Analysis Results */}
                        {inputs.filter((input: any) => input.type === "image").map((input: any) => {
                            const analysis = imageAnalysisResults.get(input.id);
                            const isAnalyzing = analyzingImages.has(input.id);
                            
                            return (
                                <motion.div
                                    key={input.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="p-4 rounded-lg bg-white/5 border border-white/10"
                                >
                                    <div className="flex items-center gap-2 mb-3">
                                        <ImageIcon size={16} className="text-saffron-gold" />
                                        <span className="text-sm font-semibold text-white">{input.content}</span>
                                        {isAnalyzing && (
                                            <Loader2 className="animate-spin text-ice-cyan ml-auto" size={14} />
                                        )}
                                    </div>
                                    
                                    {isAnalyzing && (
                                        <p className="text-xs text-text-secondary">Analyzing with Gemini VLM...</p>
                                    )}
                                    
                                    {analysis && (
                                        <div className="space-y-3">
                                            {/* VLM Description */}
                                            {analysis.vlm_description && (
                                                <div className="bg-black/30 p-3 rounded border border-white/5">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Eye size={14} className="text-ice-cyan" />
                                                        <span className="text-xs font-semibold text-ice-cyan">Image Description</span>
                                                    </div>
                                                    {analysis.vlm_description.error ? (
                                                        <p className="text-xs text-alert-red">{analysis.vlm_description.error}</p>
                                                    ) : (
                                                        <div className="space-y-2 text-xs">
                                                            <p className="text-white/90">{analysis.vlm_description.description || "No description available"}</p>
                                                            {analysis.vlm_description.objects && analysis.vlm_description.objects.length > 0 && (
                                                                <div>
                                                                    <span className="text-text-secondary">Objects: </span>
                                                                    <span className="text-white">{analysis.vlm_description.objects.join(", ")}</span>
                                                                </div>
                                                            )}
                                                            {analysis.vlm_description.visible_text && analysis.vlm_description.visible_text.length > 0 && (
                                                                <div>
                                                                    <span className="text-text-secondary">Text: </span>
                                                                    <span className="text-white">{analysis.vlm_description.visible_text.join(", ")}</span>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                            
                                            {/* AI Artifact Detection */}
                                            {analysis.vlm_ai_artifact_analysis && (
                                                <div className={`p-3 rounded border ${
                                                    analysis.vlm_ai_artifact_analysis.artifact_detected 
                                                        ? "bg-alert-red/10 border-alert-red/30" 
                                                        : "bg-black/30 border-white/5"
                                                }`}>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <AlertTriangle 
                                                            size={14} 
                                                            className={analysis.vlm_ai_artifact_analysis.artifact_detected ? "text-alert-red" : "text-ice-cyan"} 
                                                        />
                                                        <span className={`text-xs font-semibold ${
                                                            analysis.vlm_ai_artifact_analysis.artifact_detected ? "text-alert-red" : "text-ice-cyan"
                                                        }`}>
                                                            AI Artifact Detection
                                                        </span>
                                                    </div>
                                                    {analysis.vlm_ai_artifact_analysis.error ? (
                                                        <p className="text-xs text-alert-red">{analysis.vlm_ai_artifact_analysis.error}</p>
                                                    ) : (
                                                        <div className="space-y-1 text-xs">
                                                            <div className="flex items-center justify-between">
                                                                <span className="text-text-secondary">Detected:</span>
                                                                <span className={`font-semibold ${
                                                                    analysis.vlm_ai_artifact_analysis.artifact_detected ? "text-alert-red" : "text-ice-cyan"
                                                                }`}>
                                                                    {analysis.vlm_ai_artifact_analysis.artifact_detected ? "Yes" : "No"}
                                                                </span>
                                                            </div>
                                                            {analysis.vlm_ai_artifact_analysis.confidence !== undefined && (
                                                                <div className="flex items-center justify-between">
                                                                    <span className="text-text-secondary">Confidence:</span>
                                                                    <span className="text-white">
                                                                        {(analysis.vlm_ai_artifact_analysis.confidence * 100).toFixed(1)}%
                                                                    </span>
                                                                </div>
                                                            )}
                                                            {analysis.vlm_ai_artifact_analysis.artifacts && analysis.vlm_ai_artifact_analysis.artifacts.length > 0 && (
                                                                <div>
                                                                    <span className="text-text-secondary">Issues: </span>
                                                                    <span className="text-alert-red">
                                                                        {analysis.vlm_ai_artifact_analysis.artifacts.join(", ")}
                                                                    </span>
                                                                </div>
                                                            )}
                                                            {analysis.vlm_ai_artifact_analysis.explanation && 
                                                             !analysis.vlm_ai_artifact_analysis.explanation.toLowerCase().includes("failed") &&
                                                             !analysis.vlm_ai_artifact_analysis.explanation.toLowerCase().includes("error") &&
                                                             !analysis.vlm_ai_artifact_analysis.explanation.toLowerCase().includes("could not parse") && (
                                                                <p className="text-white/80 mt-2">
                                                                    {analysis.vlm_ai_artifact_analysis.explanation}
                                                                </p>
                                                            )}
                                                            {analysis.vlm_ai_artifact_analysis.explanation && 
                                                             (analysis.vlm_ai_artifact_analysis.explanation.toLowerCase().includes("failed") ||
                                                              analysis.vlm_ai_artifact_analysis.explanation.toLowerCase().includes("error") ||
                                                              analysis.vlm_ai_artifact_analysis.explanation.toLowerCase().includes("could not parse")) && (
                                                                <p className="text-text-secondary text-xs mt-2 italic">
                                                                    Analysis completed, but some details could not be extracted.
                                                                </p>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </motion.div>
                            );
                        })}
                        
                        {/* Activity Log */}
                        <div className="pt-4 border-t border-white/10 mt-4">
                            <h4 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
                                <Loader2 className={`text-ice-cyan ${!isComplete ? "animate-spin" : ""}`} size={12} />
                                Agent Activity
                            </h4>
                            <div className="space-y-2">
                                {activityLogs.map((log, i) => {
                            return (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                            className="p-2 rounded bg-white/5 border border-white/5 text-xs"
                                >
                                    <div className="flex justify-between text-text-secondary mb-1">
                                        <span className="text-ice-cyan font-mono">{log.agent}</span>
                                        <span>{log.time}</span>
                                    </div>
                                    <p className="text-white/80">{log.message}</p>
                                </motion.div>
                            );
                        })}
                            </div>
                        </div>
                    </div>

                    <AnimatePresence>
                        {isComplete && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-4 border-t border-white/10"
                            >
                                <Link to="/results">
                                    <NeonButton className="w-full flex items-center justify-center gap-2">
                                        View Results <ArrowRight size={16} />
                                    </NeonButton>
                                </Link>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </Layout>
    );
};
