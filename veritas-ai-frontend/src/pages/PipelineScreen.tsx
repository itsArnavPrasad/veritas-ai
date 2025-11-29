import React, { useState, useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layout } from "../components/layout/Layout";
import { PipelineNode } from "../components/ui/PipelineNode";
import { NeonButton } from "../components/ui/NeonButton";
import { Link, useLocation } from "react-router-dom";
import {
    FileText, Search, Brain, Image as ImageIcon, ShieldCheck, CheckCircle,
    Loader2, ArrowRight, Video, Eye, AlertTriangle
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Define the structure of the pipeline
// Text pipeline stages based on FINAL_WORKFLOW_PIPELINE.md
// Spacing: 180px between stages, starting at 180px from left to prevent label overlap and give space for "Text Claims" box
const textPipelineStages = [
    { id: "preprocessing", label: "Preprocess", x: 180 },
    { id: "claim_extraction", label: "Claim Extract", x: 360 },
    { id: "claims_combination", label: "Combine", x: 540 },
    { id: "severity_source", label: "Severity", x: 720 },
    { id: "question_generation", label: "Questions", x: 900 },
    { id: "web_search", label: "Search", x: 1080 },
    { id: "comprehensive_synthesis", label: "Synthesis", x: 1260 },
    { id: "evidence_analysis", label: "Evidence", x: 1440 },
    { id: "final_verification", label: "Verdict", x: 1620 },
];

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
    const inputs = useMemo(() => {
        return location.state?.inputs || 
        (() => {
            try {
                const stored = sessionStorage.getItem("pipelineInputs");
                    return stored ? JSON.parse(stored) : [];
            } catch {
                    return [];
            }
        })();
    }, [location.state?.inputs]);

    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    
    // State for image VLM analysis results
    const [imageAnalysisResults, setImageAnalysisResults] = useState<Map<string, any>>(new Map());
    const [analyzingImages, setAnalyzingImages] = useState<Set<string>>(new Set());
    // State for video analysis results
    const [videoAnalysisResults, setVideoAnalysisResults] = useState<Map<string, any>>(new Map());
    const [analyzingVideos, setAnalyzingVideos] = useState<Set<string>>(new Set());
    // State for text coordinator agent results
    const [textAnalysisResults, setTextAnalysisResults] = useState<Map<string, any>>(new Map());
    const [analyzingTexts, setAnalyzingTexts] = useState<Set<string>>(new Set());
    // State for cross-modal fusion
    const [fusionResults, setFusionResults] = useState<any>(null);
    const [isFusing, setIsFusing] = useState(false);
    const [fusionInitiated, setFusionInitiated] = useState(false);
    const [activityLogs, setActivityLogs] = useState<Array<{ time: string; agent: string; message: string }>>([
        { time: "10:42:01", agent: "Orchestrator", message: "Initiating multimodal pipeline..." },
    ]);

    // Use ref to track if analysis has been initiated to prevent duplicate calls
    const analysisInitiated = useRef<Set<string>>(new Set());

    // Analyze images, videos, and text when component mounts
    useEffect(() => {
        const analyzeInputs = async () => {
            const imageInputs = inputs.filter((input: any) => input.type === "image" && input.file_id);
            const videoInputs = inputs.filter((input: any) => input.type === "video" && input.file_id);
            const textInputs = inputs.filter((input: any) => input.type === "text" && input.content);
            
            if (imageInputs.length > 0 || videoInputs.length > 0 || textInputs.length > 0) {
                setActivityLogs((prev) => [
                    ...prev,
                    { 
                        time: new Date().toLocaleTimeString(), 
                        agent: "Preprocessor", 
                        message: `Inputs received: ${textInputs.length} Text, ${imageInputs.length} Image(s), ${videoInputs.length} Video(s).` 
                    },
                ]);
            }
            
            // Analyze images
            for (const input of imageInputs) {
                const inputKey = `image-${input.id}`;
                if (imageAnalysisResults.has(input.id) || analyzingImages.has(input.id) || analysisInitiated.current.has(inputKey)) {
                    continue; // Already analyzed or analyzing
                }
                
                analysisInitiated.current.add(inputKey);
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
            
            // Analyze videos
            for (const input of videoInputs) {
                const inputKey = `video-${input.id}`;
                if (videoAnalysisResults.has(input.id) || analyzingVideos.has(input.id) || analysisInitiated.current.has(inputKey)) {
                    continue; // Already analyzed or analyzing
                }
                
                analysisInitiated.current.add(inputKey);
                setAnalyzingVideos((prev) => new Set(prev).add(input.id));
                setActivityLogs((prev) => [
                    ...prev,
                    { 
                        time: new Date().toLocaleTimeString(), 
                        agent: "VideoAgent", 
                        message: `Analyzing video: ${input.content} with Gemini...` 
                    },
                ]);
                
                try {
                    const response = await fetch(`${API_BASE_URL}/api/v1/verify/video/by-file-id`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ file_id: input.file_id }),
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        setVideoAnalysisResults((prev) => {
                            const newMap = new Map(prev);
                            newMap.set(input.id, data);
                            return newMap;
                        });
                        
                        const authenticityVerdict = data.video_analysis?.authenticity_verdict || "UNCERTAIN";
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "VideoAgent", 
                                message: `Video analysis complete. Authenticity: ${authenticityVerdict}` 
                            },
                        ]);
                    } else {
                        const errorText = await response.text();
                        console.error(`Failed to analyze video ${input.id}:`, errorText);
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "VideoAgent", 
                                message: `Error analyzing video: ${errorText}` 
                            },
                        ]);
                    }
                } catch (error) {
                    console.error(`Error analyzing video ${input.id}:`, error);
                    setActivityLogs((prev) => [
                        ...prev,
                        { 
                            time: new Date().toLocaleTimeString(), 
                            agent: "VideoAgent", 
                            message: `Error: ${error instanceof Error ? error.message : "Unknown error"}` 
                        },
                    ]);
                } finally {
                    setAnalyzingVideos((prev) => {
                        const newSet = new Set(prev);
                        newSet.delete(input.id);
                        return newSet;
                    });
                }
            }
            
            // Analyze text inputs with coordinator agent
            for (const input of textInputs) {
                const inputKey = `text-${input.id}`;
                if (textAnalysisResults.has(input.id) || analyzingTexts.has(input.id) || analysisInitiated.current.has(inputKey)) {
                    continue; // Already analyzed or analyzing
                }
                
                analysisInitiated.current.add(inputKey);
                setAnalyzingTexts((prev) => new Set(prev).add(input.id));
                setActivityLogs((prev) => [
                    ...prev,
                    { 
                        time: new Date().toLocaleTimeString(), 
                        agent: "Coordinator", 
                        message: `Analyzing text with coordinator agent...` 
                    },
                ]);
                
                try {
                    const response = await fetch(`${API_BASE_URL}/api/v1/verify/text/by-content`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ text: input.content }),
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log("Text analysis results:", data);
                        setTextAnalysisResults((prev) => {
                            const newMap = new Map(prev);
                            newMap.set(input.id, data);
                            return newMap;
                        });
                        
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "Coordinator", 
                                message: `Text analysis complete. Claims extracted and verified.` 
                            },
                        ]);
                    } else {
                        const errorText = await response.text();
                        console.error(`Failed to analyze text ${input.id}:`, errorText);
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "Coordinator", 
                                message: `Error analyzing text: ${errorText}` 
                            },
                        ]);
                    }
                } catch (error) {
                    console.error(`Error analyzing text ${input.id}:`, error);
                    setActivityLogs((prev) => [
                        ...prev,
                        { 
                            time: new Date().toLocaleTimeString(), 
                            agent: "Coordinator", 
                            message: `Error: ${error instanceof Error ? error.message : "Unknown error"}` 
                        },
                    ]);
                } finally {
                    setAnalyzingTexts((prev) => {
                        const newSet = new Set(prev);
                        newSet.delete(input.id);
                        return newSet;
                    });
                }
            }
        };
        
        analyzeInputs();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty dependency array - only run once on mount

    // Trigger cross-modal fusion when all analyses are complete
    useEffect(() => {
        const textInputs = inputs.filter((input: any) => input.type === "text" && input.content);
        const imageInputs = inputs.filter((input: any) => input.type === "image" && input.file_id);
        const videoInputs = inputs.filter((input: any) => input.type === "video" && input.file_id);
        
        // Check if all analyses are complete
        const allTextsComplete = textInputs.length === 0 || textInputs.every((input: any) => 
            textAnalysisResults.has(input.id) && !analyzingTexts.has(input.id)
        );
        const allImagesComplete = imageInputs.length === 0 || imageInputs.every((input: any) => 
            imageAnalysisResults.has(input.id) && !analyzingImages.has(input.id)
        );
        const allVideosComplete = videoInputs.length === 0 || videoInputs.every((input: any) => 
            videoAnalysisResults.has(input.id) && !analyzingVideos.has(input.id)
        );
        
        const allComplete = allTextsComplete && allImagesComplete && allVideosComplete;
        const hasAnyInput = textInputs.length > 0 || imageInputs.length > 0 || videoInputs.length > 0;
        
        // Trigger fusion when all analyses are complete
        if (allComplete && hasAnyInput && !fusionInitiated && !isFusing) {
            setFusionInitiated(true);
            setIsFusing(true);
            
            setActivityLogs((prev) => [
                ...prev,
                { 
                    time: new Date().toLocaleTimeString(), 
                    agent: "Fusion", 
                    message: `All analyses complete. Performing cross-modal fusion...` 
                },
            ]);
            
            (async () => {
                try {
                    // Collect all analysis results
                    const textAnalysis = textInputs.length > 0 && textInputs[0] 
                        ? textAnalysisResults.get(textInputs[0].id) 
                        : null;
                    const imageAnalysis = imageInputs.length > 0 && imageInputs[0] 
                        ? imageAnalysisResults.get(imageInputs[0].id) 
                        : null;
                    const videoAnalysis = videoInputs.length > 0 && videoInputs[0] 
                        ? videoAnalysisResults.get(videoInputs[0].id) 
                        : null;
                    
                    // Get verification_id from any analysis result
                    const verificationId = textAnalysis?.verification_id || 
                                         imageAnalysis?.verification_id || 
                                         videoAnalysis?.verification_id;
                    
                    const response = await fetch(`${API_BASE_URL}/api/v1/verify/cross-modal-fusion`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            text_analysis: textAnalysis,
                            image_analysis: imageAnalysis,
                            video_analysis: videoAnalysis,
                            verification_id: verificationId
                        }),
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        setFusionResults(data.fusion_results);
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "Fusion", 
                                message: `Cross-modal fusion complete. Verdict: ${data.fusion_results?.calibrated_verdict?.verdict || "N/A"}` 
                            },
                        ]);
                        setIsComplete(true);
                    } else {
                        const errorText = await response.text();
                        console.error(`Failed to perform fusion:`, errorText);
                        setActivityLogs((prev) => [
                            ...prev,
                            { 
                                time: new Date().toLocaleTimeString(), 
                                agent: "Fusion", 
                                message: `Error in fusion: ${errorText}` 
                            },
                        ]);
                    }
                } catch (error) {
                    console.error(`Error performing fusion:`, error);
                    setActivityLogs((prev) => [
                        ...prev,
                        { 
                            time: new Date().toLocaleTimeString(), 
                            agent: "Fusion", 
                            message: `Error: ${error instanceof Error ? error.message : "Unknown error"}` 
                        },
                    ]);
                } finally {
                    setIsFusing(false);
                }
            })();
        }
    }, [inputs, textAnalysisResults, analyzingTexts, videoAnalysisResults, analyzingVideos, imageAnalysisResults, analyzingImages, fusionInitiated, isFusing]);

    // Calculate progress based on actual pipeline completion for text
    useEffect(() => {
        const textInput = inputs.find((i: any) => i.type === "text");
        if (textInput) {
            const analysis = textAnalysisResults.get(textInput.id);
            const structuredData = analysis?.structured_data;
            
            if (structuredData) {
                // Count completed stages
                let completedStages = 0;
                const totalStages = textPipelineStages.length;
                
                if (structuredData.preprocess_data) completedStages++;
                if (structuredData.claim_extraction) completedStages++;
                if (structuredData.combined_claims) completedStages++;
                if (structuredData.severity_source_suggestion) completedStages++;
                if (structuredData.chain1_queries || structuredData.chain2_queries || structuredData.chain3_queries) completedStages++;
                if (structuredData.web_search_results) completedStages++;
                if (structuredData.comprehensive_search_results) completedStages++;
                if (structuredData.evidence_analysis) completedStages++;
                if (structuredData.verifier_ensemble_result) {
                    completedStages++;
                    // Don't set isComplete here - wait for fusion to complete
                }
                
                const calculatedProgress = (completedStages / totalStages) * 100;
                setProgress(calculatedProgress);
            } else if (analyzingTexts.has(textInput.id)) {
                // If analyzing, show some progress
                setProgress(10);
            }
        } else {
            // For non-text inputs, use the old progress simulation
        const timer = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 100) {
                    clearInterval(timer);
                    // Don't set isComplete here - wait for fusion to complete
                    return 100;
                }
                return prev + 0.5;
            });
        }, 50);
        return () => clearInterval(timer);
        }
    }, [inputs, textAnalysisResults, analyzingTexts]);

    // Calculate active stage based on progress (for image/video pipelines)
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

    // Helper function to extract details for each pipeline stage from structured_data
    const getTextStageDetails = (stageId: string, structuredData: any): Record<string, string | number> => {
        if (!structuredData) return { "Status": "Pending" };

        switch (stageId) {
            case "preprocessing":
                const preprocess = structuredData.preprocess_data;
                if (preprocess) {
                    return {
                        "Language": preprocess.language || "N/A",
                        "Entities": Array.isArray(preprocess.entities) ? preprocess.entities.length : 0,
                        "Title": preprocess.title ? (preprocess.title.length > 20 ? preprocess.title.substring(0, 20) + "..." : preprocess.title) : "N/A",
                    };
                }
                return { "Status": "Pending" };

            case "claim_extraction":
                const claims = structuredData.claim_extraction;
                if (claims) {
                    const claimsList = Array.isArray(claims.claims) ? claims.claims : [];
                    return {
                        "Claims": claimsList.length,
                        "Risk Level": claimsList.length > 0 && claimsList[0].risk_hint ? claimsList[0].risk_hint.toUpperCase() : "N/A",
                    };
                }
                return { "Status": "Pending" };

            case "claims_combination":
                const combined = structuredData.combined_claims;
                if (combined) {
                    // Try to parse if it's a JSON string
                    let parsed: any = null;
                    if (typeof combined === 'string') {
                        try {
                            const jsonMatch = combined.match(/```json\s*([\s\S]*?)\s*```/) || combined.match(/\{[\s\S]*\}/);
                            if (jsonMatch) {
                                parsed = JSON.parse(jsonMatch[1] || jsonMatch[0]);
                            }
                        } catch (e) {
                            // If parsing fails, just show it exists
                        }
                    } else {
                        parsed = combined;
                    }
                    if (parsed) {
                        return {
                            "Claim ID": parsed.claim_id || "N/A",
                            "Entities": Array.isArray(parsed.entities) ? parsed.entities.length : 0,
                        };
                    }
                    return { "Status": "Combined" };
                }
                return { "Status": "Pending" };

            case "severity_source":
                const severity = structuredData.severity_source_suggestion;
                if (severity) {
                    return {
                        "Category": severity.severity?.category || "N/A",
                        "Severity": severity.severity?.severity_score ? (severity.severity.severity_score * 100).toFixed(0) + "%" : "N/A",
                        "Source Pools": Array.isArray(severity.recommended_source_pools) ? severity.recommended_source_pools.length : 0,
                    };
                }
                return { "Status": "Pending" };

            case "question_generation":
                const chain1 = structuredData.chain1_queries;
                const chain2 = structuredData.chain2_queries;
                const chain3 = structuredData.chain3_queries;
                const totalQueries = 
                    (Array.isArray(chain1?.queries) ? chain1.queries.length : 0) +
                    (Array.isArray(chain2?.queries) ? chain2.queries.length : 0) +
                    (Array.isArray(chain3?.queries) ? chain3.queries.length : 0);
                if (totalQueries > 0) {
                    return {
                        "Total Queries": totalQueries,
                        "Chain 1": Array.isArray(chain1?.queries) ? chain1.queries.length : 0,
                        "Chain 2": Array.isArray(chain2?.queries) ? chain2.queries.length : 0,
                        "Chain 3": Array.isArray(chain3?.queries) ? chain3.queries.length : 0,
                    };
                }
                return { "Status": "Pending" };

            case "web_search":
                const webSearch = structuredData.web_search_results;
                if (webSearch) {
                    return {
                        "Queries Processed": Array.isArray(webSearch.query_results) ? webSearch.query_results.length : 0,
                        "Evidence Items": webSearch.total_evidence_items || 0,
                    };
                }
                return { "Status": "Pending" };

            case "comprehensive_synthesis":
                const synthesis = structuredData.comprehensive_search_results;
                if (synthesis) {
                    return {
                        "Queries": Array.isArray(synthesis.query_results) ? synthesis.query_results.length : 0,
                        "Answer": synthesis.comprehensive_answer ? "Generated" : "Pending",
                    };
                }
                return { "Status": "Pending" };

            case "evidence_analysis":
                const evidence = structuredData.evidence_analysis;
                if (evidence) {
                    return {
                        "Analyses": Array.isArray(evidence.analyses) ? evidence.analyses.length : 0,
                        "Status": "Complete",
                    };
                }
                return { "Status": "Pending" };

            case "final_verification":
                const verifier = structuredData.verifier_ensemble_result;
                if (verifier) {
                    const verdict = verifier.misinformation_analysis?.verdict || "N/A";
                    const truthScore = verifier.misinformation_analysis?.overall_truth_score;
                    return {
                        "Verdict": verdict,
                        "Truth Score": truthScore !== undefined ? (truthScore * 100).toFixed(0) + "%" : "N/A",
                        "Confidence": verifier.misinformation_analysis?.overall_confidence ? (verifier.misinformation_analysis.overall_confidence * 100).toFixed(0) + "%" : "N/A",
                    };
                }
                return { "Status": "Pending" };

            default:
                return { "Status": "Pending" };
        }
    };

    // Helper to get stage status based on structured_data
    const getTextStageStatus = (stageId: string, structuredData: any, isAnalyzing: boolean): "idle" | "processing" | "completed" | "warning" | "danger" => {
        if (isAnalyzing) return "processing";
        
        // Check if this stage and all previous stages are complete
        const stageIndex = textPipelineStages.findIndex(s => s.id === stageId);
        if (stageIndex === -1) return "idle";

        // Check if this stage has data
        let hasData = false;
        switch (stageId) {
            case "preprocessing":
                hasData = !!structuredData?.preprocess_data;
                break;
            case "claim_extraction":
                hasData = !!structuredData?.claim_extraction;
                break;
            case "claims_combination":
                hasData = !!structuredData?.combined_claims;
                break;
            case "severity_source":
                hasData = !!structuredData?.severity_source_suggestion;
                break;
            case "question_generation":
                hasData = !!(structuredData?.chain1_queries || structuredData?.chain2_queries || structuredData?.chain3_queries);
                break;
            case "web_search":
                hasData = !!structuredData?.web_search_results;
                break;
            case "comprehensive_synthesis":
                hasData = !!structuredData?.comprehensive_search_results;
                break;
            case "evidence_analysis":
                hasData = !!structuredData?.evidence_analysis;
                break;
            case "final_verification":
                hasData = !!structuredData?.verifier_ensemble_result;
                const verdict = structuredData?.verifier_ensemble_result?.misinformation_analysis?.verdict;
                if (hasData && verdict === "LIKELY_FALSE") return "danger";
                if (hasData && verdict === "LIKELY_TRUE") return "completed";
                if (hasData) return "warning";
                break;
        }

        if (hasData) return "completed";
        return "idle";
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

            <div className="flex-1 flex relative min-h-0">
                {/* Main Visualization Area */}
                <div ref={containerRef} className="flex-1 relative overflow-x-auto overflow-y-hidden bg-deep-bg perspective-1000 min-h-0">

                    {/* SVG Layer for Paths */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none z-0" style={{ minWidth: "2200px" }}>
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

                            if (lane.id === "text") {
                                // Text pipeline: 9 stages connected sequentially
                                const textStages = textPipelineStages;
                                const paths: string[] = [];
                                for (let i = 0; i < textStages.length - 1; i++) {
                                    const startX = i === 0 ? 140 : textStages[i].x;
                                    const endX = textStages[i + 1].x;
                                    paths.push(generatePath(lane.y, lane.y, startX, endX));
                                }
                                const fullPath = paths.join(" ");

                            return (
                                <g key={lane.id} style={{ opacity }}>
                                        <path d={fullPath} stroke="url(#gradient-flow)" strokeWidth="2" fill="none" />
                                        {hasInput && (
                                            <motion.path
                                                d={fullPath}
                                                stroke="#9EE8FF"
                                                strokeWidth="3"
                                                fill="none"
                                                initial={{ pathLength: 0 }}
                                                animate={{ pathLength: Math.min(progress / 100, 1) }}
                                                transition={{ duration: 0.1, ease: "linear" }}
                                                strokeLinecap="round"
                                                filter="url(#glow)"
                                            />
                                        )}
                                    </g>
                                );
                            } else {
                                // Image/Video pipeline: Direct path from input to VLM Analysis, then to fusion
                                // Input at ~50px, VLM Analysis at 400px, Fusion at 1800px (after text final verdict)
                                const path1 = generatePath(lane.y, lane.y, 50, 400);
                                const path2 = generatePath(lane.y, 250, 400, 1800);

                                return (
                                    <g key={lane.id} style={{ opacity }}>
                                        <path d={`${path1} ${path2}`} stroke="url(#gradient-flow)" strokeWidth="2" fill="none" />
                                    {hasInput && (
                                        <motion.path
                                                d={`${path1} ${path2}`}
                                            stroke="#9EE8FF"
                                            strokeWidth="3"
                                            fill="none"
                                            initial={{ pathLength: 0 }}
                                                animate={{ pathLength: progress / 80 }}
                                            transition={{ duration: 0.1, ease: "linear" }}
                                            strokeLinecap="round"
                                            filter="url(#glow)"
                                        />
                                    )}
                                </g>
                            );
                            }
                        })}

                        {/* Path from Text Final Verdict to Fusion */}
                        {inputs.some((i: any) => i.type === "text") && (
                            <g>
                                <path d="M 1620 150 L 1800 250" stroke="url(#gradient-flow)" strokeWidth="2" fill="none" opacity="0.5" />
                        <motion.path
                                    d="M 1620 150 L 1800 250"
                                    stroke="#9EE8FF"
                                    strokeWidth="3"
                                    fill="none"
                                    initial={{ pathLength: 0 }}
                                    animate={{ pathLength: Math.min(progress / 100, 1) }}
                                    transition={{ duration: 0.1, ease: "linear" }}
                                    strokeLinecap="round"
                                    filter="url(#glow)"
                                />
                            </g>
                        )}

                        {/* Path from Fusion to Calibrated Verdict */}
                        {(inputs.some((i: any) => i.type === "text") || inputs.some((i: any) => i.type === "image") || inputs.some((i: any) => i.type === "video")) && (
                            <>
                                <path d="M 1800 250 L 2000 250" stroke="url(#gradient-flow)" strokeWidth="2" fill="none" opacity="0.5" />
                                <motion.path
                                    d="M 1800 250 L 2000 250"
                                    stroke="#F85149"
                            strokeWidth="4"
                            fill="none"
                            initial={{ pathLength: 0 }}
                            animate={{ pathLength: Math.max(0, (progress - 80) / 20) }}
                            transition={{ duration: 0.1, ease: "linear" }}
                            strokeLinecap="round"
                        />
                            </>
                        )}
                    </svg>

                    {/* Nodes Layer */}
                    <div className="absolute inset-0 z-10">
                        {/* Render nodes for each lane */}
                        {pipelineConfig.lanes.map((lane) => {
                            const hasInput = inputs.some((i: any) => i.type === lane.id);
                            if (!hasInput) return null;

                            // Text pipeline: render all 9 stages
                            if (lane.id === "text") {
                                const textInput = inputs.find((i: any) => i.type === "text");
                                const analysis = textInput ? textAnalysisResults.get(textInput.id) : null;
                                const isAnalyzing = textInput ? analyzingTexts.has(textInput.id) : false;
                                const structuredData = analysis?.structured_data;

                                // Stage icons mapping
                                const stageIcons: Record<string, LucideIcon> = {
                                    preprocessing: FileText,
                                    claim_extraction: Brain,
                                    claims_combination: Brain,
                                    severity_source: ShieldCheck,
                                    question_generation: Search,
                                    web_search: Search,
                                    comprehensive_synthesis: Brain,
                                    evidence_analysis: Eye,
                                    final_verification: CheckCircle,
                                };

                            return (
                                <React.Fragment key={lane.id}>
                                    {/* Input Card */}
                                        <div className="absolute left-0 z-20" style={{ top: lane.y - 20, maxWidth: '140px' }}>
                                        <div className="bg-black/60 border border-white/10 rounded-lg p-2 flex items-center gap-2 backdrop-blur-sm">
                                                <lane.icon size={16} className="text-cyan-400" />
                                            <span className="text-xs text-white font-mono uppercase">{lane.label}</span>
                                        </div>
                                    </div>

                                        {/* Render all 9 text pipeline stages */}
                                        {textPipelineStages.map((stage) => {
                                            const Icon = stageIcons[stage.id] || FileText;
                                            const details = getTextStageDetails(stage.id, structuredData);
                                            const status = getTextStageStatus(stage.id, structuredData, isAnalyzing);
                                            const isActive = isAnalyzing || status === "processing" || status === "completed";

                                            return (
                                                <div
                                                    key={stage.id}
                                                    className="absolute -translate-x-1/2 -translate-y-1/2"
                                                    style={{ left: stage.x, top: lane.y }}
                                                >
                                        <PipelineNode
                                                        icon={Icon}
                                                        label={stage.label}
                                                        details={details}
                                                        status={status}
                                                        isActive={isActive}
                                                        size={stage.id === "final_verification" ? "lg" : "sm"}
                                        />
                                    </div>
                                            );
                                        })}
                                    </React.Fragment>
                                );
                            }

                            // Image/Video pipeline: original 3-stage layout
                            return (
                                <React.Fragment key={lane.id}>
                                    {/* Input Card */}
                                    <div className="absolute left-0 z-20" style={{ top: lane.y - 20 }}>
                                        <div className="bg-black/60 border border-white/10 rounded-lg p-2 flex items-center gap-2 backdrop-blur-sm">
                                            <lane.icon size={16} className={`text-${lane.color}-400`} />
                                            <span className="text-xs text-white font-mono uppercase">{lane.label}</span>
                                        </div>
                                    </div>

                                    {/* VLM Analysis Node - Only node for image/video */}
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
                                                                    : "idle"
                                                    }
                                                    isActive={isAnalyzing}
                                                    size="sm"
                                                />
                                            );
                                        })() : (() => {
                                            // Video: Only VLM Analysis
                                            const videoInput = inputs.find((i: any) => i.type === "video");
                                            const analysis = videoInput ? videoAnalysisResults.get(videoInput.id) : null;
                                            const isAnalyzing = videoInput ? analyzingVideos.has(videoInput.id) : false;
                                            const videoAnalysis = analysis?.video_analysis;
                                            
                                            const details: any = {};
                                            if (videoAnalysis) {
                                                if (videoAnalysis.authenticity_verdict) {
                                                    details["Authenticity"] = videoAnalysis.authenticity_verdict;
                                                }
                                                if (videoAnalysis.claims) {
                                                    details["Claims"] = videoAnalysis.claims.length;
                                                }
                                                if (videoAnalysis.overall_authenticity_score !== undefined) {
                                                    details["Score"] = (videoAnalysis.overall_authenticity_score * 100).toFixed(0) + "%";
                                                }
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
                                                                    : "idle"
                                                    }
                                                    isActive={isAnalyzing}
                                                    size="sm"
                                                />
                                            );
                                        })()}
                                    </div>
                                </React.Fragment>
                            );
                        })}

                        {/* Fusion Node (Converged) - For text, image, and/or video */}
                        {(inputs.some((i: any) => i.type === "text") || inputs.some((i: any) => i.type === "image") || inputs.some((i: any) => i.type === "video")) && (
                            <>
                                <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 1800, top: 250 }}>
                                    {(() => {
                                        const fusionDetails: any = {};
                                        if (fusionResults) {
                                            const relevance = fusionResults.content_relevance;
                                            const verdict = fusionResults.calibrated_verdict;
                                            if (relevance) {
                                                fusionDetails["Relevance"] = relevance.is_relevant ? "Yes" : "No";
                                                fusionDetails["Rel. Score"] = (relevance.relevance_score * 100).toFixed(0) + "%";
                                            }
                                            if (verdict) {
                                                fusionDetails["Verdict"] = verdict.verdict;
                                                fusionDetails["Confidence"] = (verdict.confidence * 100).toFixed(0) + "%";
                                            }
                                        } else {
                                            fusionDetails["Status"] = isFusing ? "Fusing..." : "Pending";
                                        }
                                        
                                        return (
                            <PipelineNode
                                icon={ShieldCheck}
                                label="Cross-Modal Fusion"
                                                details={fusionDetails}
                                                status={
                                                    isFusing 
                                                        ? "processing" 
                                                        : fusionResults 
                                                            ? "completed" 
                                                            : "idle"
                                                }
                                                isActive={isFusing || !!fusionResults}
                                size="lg"
                            />
                                        );
                                    })()}
                        </div>

                        {/* Verdict Node (Final) */}
                                <div className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: 2000, top: 250 }}>
                                    {(() => {
                                        const verdictDetails: any = {};
                                        if (fusionResults?.calibrated_verdict) {
                                            const verdict = fusionResults.calibrated_verdict;
                                            verdictDetails["Verdict"] = verdict.verdict;
                                            verdictDetails["Confidence"] = (verdict.confidence * 100).toFixed(0) + "%";
                                            if (fusionResults.content_relevance) {
                                                verdictDetails["Relevance"] = fusionResults.content_relevance.is_relevant ? "Yes" : "No";
                                            }
                                        } else {
                                            verdictDetails["Status"] = isFusing ? "Processing..." : "Pending";
                                        }
                                        
                                        const verdictStatus = fusionResults?.calibrated_verdict?.verdict === "LIKELY_FALSE" 
                                            ? "danger" 
                                            : fusionResults?.calibrated_verdict?.verdict === "LIKELY_TRUE"
                                            ? "completed"
                                            : fusionResults
                                            ? "warning"
                                            : "idle";
                                        
                                        return (
                            <PipelineNode
                                icon={CheckCircle}
                                label="Calibrated Verdict"
                                                details={verdictDetails}
                                                status={verdictStatus}
                                                isActive={!!fusionResults}
                                size="lg"
                            />
                                        );
                                    })()}
                        </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Right Panel: Analysis Results */}
                <div className="w-96 border-l border-white/10 bg-black/40 backdrop-blur-xl flex flex-col z-20 min-h-0">
                    <div className="p-4 border-b border-white/10 flex-shrink-0">
                        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                            <Loader2 className={`text-ice-cyan ${!isComplete ? "animate-spin" : ""}`} size={16} />
                            Analysis Results
                        </h3>
                    </div>
                    <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4 scrollbar-thin scrollbar-thumb-white/10 min-h-0">
                        {/* Text Coordinator Agent Results */}
                        {inputs.filter((input: any) => input.type === "text").map((input: any) => {
                            const analysis = textAnalysisResults.get(input.id);
                            const isAnalyzing = analyzingTexts.has(input.id);
                            
                            return (
                                <motion.div
                                    key={input.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="p-4 rounded-lg bg-white/5 border border-white/10"
                                >
                                    <div className="flex items-center gap-2 mb-3">
                                        <FileText size={16} className="text-ice-cyan" />
                                        <span className="text-sm font-semibold text-white">Text Analysis</span>
                                        {isAnalyzing && (
                                            <Loader2 className="animate-spin text-ice-cyan ml-auto" size={14} />
                                        )}
                                    </div>
                                    
                                    {isAnalyzing && (
                                        <p className="text-xs text-text-secondary">Analyzing with coordinator agent...</p>
                                    )}
                                    
                                    {analysis && (
                                        <div className="space-y-3">
                                            {/* Coordinator Response */}
                                            {analysis.structured_data && Object.keys(analysis.structured_data).length > 0 && (
                                                <div className="bg-black/30 p-3 rounded border border-white/5">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Brain size={14} className="text-ice-cyan" />
                                                        <span className="text-xs font-semibold text-ice-cyan">Coordinator Analysis</span>
                                                    </div>
                                                    <div className="space-y-2 text-xs">
                                                        {analysis.structured_data.preprocess_data && (
                                                            <div>
                                                                <span className="text-text-secondary">Preprocessed: </span>
                                                                <span className="text-white">✓</span>
                                                            </div>
                                                        )}
                                                        {analysis.structured_data.claim_extraction && (
                                                            <div>
                                                                <span className="text-text-secondary">Claims Extracted: </span>
                                                                <span className="text-white">
                                                                    {Array.isArray(analysis.structured_data.claim_extraction?.claims) 
                                                                        ? analysis.structured_data.claim_extraction.claims.length 
                                                                        : "N/A"}
                                                                </span>
                                                            </div>
                                                        )}
                                                        {analysis.structured_data.combined_claims && (
                                                            <div>
                                                                <span className="text-text-secondary">Combined Claims: </span>
                                                                <span className="text-white">✓</span>
                                                            </div>
                                                        )}
                                                        {analysis.structured_data.verifier_ensemble && (
                                                            <div>
                                                                <span className="text-text-secondary">Verification: </span>
                                                                <span className="text-white">Complete</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {analysis.coordinator_response?.error && (
                                                <div className="bg-alert-red/10 p-3 rounded border border-alert-red/30">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <AlertTriangle size={14} className="text-alert-red" />
                                                        <span className="text-xs font-semibold text-alert-red">Error</span>
                                                    </div>
                                                    <p className="text-xs text-alert-red">{analysis.coordinator_response.error}</p>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </motion.div>
                            );
                        })}
                        
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
                        
                        {/* Video Analysis Results */}
                        {inputs.filter((input: any) => input.type === "video").map((input: any) => {
                            const analysis = videoAnalysisResults.get(input.id);
                            const isAnalyzing = analyzingVideos.has(input.id);
                            const videoAnalysis = analysis?.video_analysis;
                            
                            return (
                                <motion.div
                                    key={input.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="p-4 rounded-lg bg-white/5 border border-white/10"
                                >
                                    <div className="flex items-center gap-2 mb-3">
                                        <Video size={16} className="text-alert-red" />
                                        <span className="text-sm font-semibold text-white">{input.content}</span>
                                        {isAnalyzing && (
                                            <Loader2 className="animate-spin text-ice-cyan ml-auto" size={14} />
                                        )}
                                    </div>
                                    
                                    {isAnalyzing && (
                                        <p className="text-xs text-text-secondary">Analyzing with Gemini...</p>
                                    )}
                                    
                                    {videoAnalysis && (
                                        <div className="space-y-3">
                                            {/* Video Description */}
                                            {videoAnalysis.video_description && (
                                                <div className="bg-black/30 p-3 rounded border border-white/5">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Eye size={14} className="text-ice-cyan" />
                                                        <span className="text-xs font-semibold text-ice-cyan">Video Description</span>
                                                    </div>
                                                    <p className="text-xs text-white/90">{videoAnalysis.video_description}</p>
                                                </div>
                                            )}
                                            
                                            {/* Authenticity Analysis */}
                                            {videoAnalysis.overall_authenticity_score !== undefined && (
                                                <div className={`p-3 rounded border ${
                                                    videoAnalysis.authenticity_verdict === "LIKELY_MANIPULATED"
                                                        ? "bg-alert-red/10 border-alert-red/30"
                                                        : videoAnalysis.authenticity_verdict === "SUSPICIOUS"
                                                        ? "bg-saffron-gold/10 border-saffron-gold/30"
                                                        : "bg-black/30 border-white/5"
                                                }`}>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <ShieldCheck 
                                                            size={14} 
                                                            className={
                                                                videoAnalysis.authenticity_verdict === "LIKELY_MANIPULATED" ? "text-alert-red" :
                                                                videoAnalysis.authenticity_verdict === "SUSPICIOUS" ? "text-saffron-gold" :
                                                                "text-ice-cyan"
                                                            } 
                                                        />
                                                        <span className={`text-xs font-semibold ${
                                                            videoAnalysis.authenticity_verdict === "LIKELY_MANIPULATED" ? "text-alert-red" :
                                                            videoAnalysis.authenticity_verdict === "SUSPICIOUS" ? "text-saffron-gold" :
                                                            "text-ice-cyan"
                                                        }`}>
                                                            Authenticity: {videoAnalysis.authenticity_verdict || "UNCERTAIN"}
                                                        </span>
                                                    </div>
                                                    <div className="space-y-1 text-xs">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-text-secondary">Score:</span>
                                                            <span className="text-white">
                                                                {(videoAnalysis.overall_authenticity_score * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                        {videoAnalysis.risk_factors && videoAnalysis.risk_factors.length > 0 && (
                                                            <div>
                                                                <span className="text-text-secondary">Risk Factors: </span>
                                                                <span className="text-alert-red">
                                                                    {videoAnalysis.risk_factors.join(", ")}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {/* Claims */}
                                            {videoAnalysis.claims && videoAnalysis.claims.length > 0 && (
                                                <div className="bg-black/30 p-3 rounded border border-white/5">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <Brain size={14} className="text-ice-cyan" />
                                                        <span className="text-xs font-semibold text-ice-cyan">Extracted Claims ({videoAnalysis.claims.length})</span>
                                                    </div>
                                                    <div className="space-y-2">
                                                        {videoAnalysis.claims.map((claim: any, idx: number) => (
                                                            <div key={idx} className="text-xs border-b border-white/5 last:border-0 pb-2 last:pb-0">
                                                                <div className="flex items-start gap-2">
                                                                    <span className="text-text-secondary">{idx + 1}.</span>
                                                                    <div className="flex-1">
                                                                        <p className="text-white/90">{claim.claim_text}</p>
                                                                        {claim.timestamp && (
                                                                            <span className="text-text-secondary text-xs">@{claim.timestamp}</span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {/* Error Display */}
                                            {videoAnalysis.error && (
                                                <div className="bg-alert-red/10 border border-alert-red/30 p-3 rounded">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <AlertTriangle size={14} className="text-alert-red" />
                                                        <span className="text-xs font-semibold text-alert-red">Error</span>
                                                    </div>
                                                    <p className="text-xs text-alert-red">{videoAnalysis.error}</p>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </motion.div>
                            );
                        })}
                        
                        {/* Cross-Modal Fusion Results */}
                        {fusionResults && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-4 rounded-lg bg-white/5 border border-white/10"
                            >
                                <div className="flex items-center gap-2 mb-3">
                                    <ShieldCheck size={16} className="text-ice-cyan" />
                                    <span className="text-sm font-semibold text-white">Cross-Modal Fusion</span>
                                    {isFusing && (
                                        <Loader2 className="animate-spin text-ice-cyan ml-auto" size={14} />
                                    )}
                            </div>
                                
                                <div className="space-y-3">
                                    {/* Content Relevance */}
                                    {fusionResults.content_relevance && (
                                        <div className={`p-3 rounded border ${
                                            fusionResults.content_relevance.is_relevant
                                                ? "bg-black/30 border-white/5"
                                                : "bg-alert-red/10 border-alert-red/30"
                                        }`}>
                                            <div className="flex items-center gap-2 mb-2">
                                                <Eye size={14} className={
                                                    fusionResults.content_relevance.is_relevant ? "text-ice-cyan" : "text-alert-red"
                                                } />
                                                <span className={`text-xs font-semibold ${
                                                    fusionResults.content_relevance.is_relevant ? "text-ice-cyan" : "text-alert-red"
                                                }`}>
                                                    Content Relevance
                                                </span>
                        </div>
                                            <div className="space-y-1 text-xs">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-text-secondary">Relevant:</span>
                                                    <span className={`font-semibold ${
                                                        fusionResults.content_relevance.is_relevant ? "text-ice-cyan" : "text-alert-red"
                                                    }`}>
                                                        {fusionResults.content_relevance.is_relevant ? "Yes" : "No"}
                                                    </span>
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-text-secondary">Score:</span>
                                                    <span className="text-white">
                                                        {(fusionResults.content_relevance.relevance_score * 100).toFixed(1)}%
                                                    </span>
                                                </div>
                                                {fusionResults.content_relevance.explanation && (
                                                    <p className="text-white/80 mt-2">
                                                        {fusionResults.content_relevance.explanation}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Calibrated Verdict */}
                                    {fusionResults.calibrated_verdict && (
                                        <div className={`p-3 rounded border ${
                                            fusionResults.calibrated_verdict.verdict === "LIKELY_FALSE"
                                                ? "bg-alert-red/10 border-alert-red/30"
                                                : fusionResults.calibrated_verdict.verdict === "LIKELY_TRUE"
                                                ? "bg-royal-blue/10 border-royal-blue/30"
                                                : "bg-saffron-gold/10 border-saffron-gold/30"
                                        }`}>
                                            <div className="flex items-center gap-2 mb-2">
                                                <CheckCircle 
                                                    size={14} 
                                                    className={
                                                        fusionResults.calibrated_verdict.verdict === "LIKELY_FALSE" ? "text-alert-red" :
                                                        fusionResults.calibrated_verdict.verdict === "LIKELY_TRUE" ? "text-royal-blue" :
                                                        "text-saffron-gold"
                                                    } 
                                                />
                                                <span className={`text-xs font-semibold ${
                                                    fusionResults.calibrated_verdict.verdict === "LIKELY_FALSE" ? "text-alert-red" :
                                                    fusionResults.calibrated_verdict.verdict === "LIKELY_TRUE" ? "text-royal-blue" :
                                                    "text-saffron-gold"
                                                }`}>
                                                    Calibrated Verdict: {fusionResults.calibrated_verdict.verdict}
                                                </span>
                                            </div>
                                            <div className="space-y-1 text-xs">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-text-secondary">Confidence:</span>
                                                    <span className="text-white">
                                                        {(fusionResults.calibrated_verdict.confidence * 100).toFixed(1)}%
                                                    </span>
                                                </div>
                                                {fusionResults.calibrated_verdict.reasoning && (
                                                    <p className="text-white/80 mt-2">
                                                        {fusionResults.calibrated_verdict.reasoning}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Fusion Analysis */}
                                    {fusionResults.fusion_analysis && (
                                        <div className="bg-black/30 p-3 rounded border border-white/5">
                                            <div className="flex items-center gap-2 mb-2">
                                                <Brain size={14} className="text-ice-cyan" />
                                                <span className="text-xs font-semibold text-ice-cyan">Fusion Analysis</span>
                                            </div>
                                            <div className="space-y-2 text-xs">
                                                {fusionResults.fusion_analysis.modalities_agreement && (
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-text-secondary">Agreement:</span>
                                                        <span className="text-white">{fusionResults.fusion_analysis.modalities_agreement}</span>
                                                    </div>
                                                )}
                                                {fusionResults.fusion_analysis.key_findings && fusionResults.fusion_analysis.key_findings.length > 0 && (
                                                    <div>
                                                        <span className="text-text-secondary">Key Findings: </span>
                                                        <ul className="list-disc list-inside mt-1 text-white/80">
                                                            {fusionResults.fusion_analysis.key_findings.map((finding: string, idx: number) => (
                                                                <li key={idx}>{finding}</li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                                {fusionResults.fusion_analysis.conflicts && fusionResults.fusion_analysis.conflicts.length > 0 && (
                                                    <div>
                                                        <span className="text-alert-red">Conflicts: </span>
                                                        <ul className="list-disc list-inside mt-1 text-alert-red/80">
                                                            {fusionResults.fusion_analysis.conflicts.map((conflict: string, idx: number) => (
                                                                <li key={idx}>{conflict}</li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </div>

                    <AnimatePresence>
                        {fusionResults && !isFusing && (
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
