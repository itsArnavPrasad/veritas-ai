import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, useNavigate } from "react-router-dom";
import { Layout } from "../components/layout/Layout";
import { AntiGravityCard } from "../components/ui/AntiGravityCard";
import { HoloBadge } from "../components/ui/HoloBadge";
import { 
    CheckCircle, 
    XCircle, 
    ChevronDown, 
    ChevronUp, 
    Image as ImageIcon, 
    Clock, 
    Globe, 
    FileText, 
    AlertTriangle, 
    ShieldCheck,
    Video,
    Brain,
    Eye,
    Loader2,
    ArrowLeft,
    TrendingUp,
    TrendingDown,
    AlertCircle
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const ResultsPage: React.FC = () => {
    const { verificationId } = useParams<{ verificationId: string }>();
    const navigate = useNavigate();
    const [results, setResults] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["verdict"]));

    useEffect(() => {
        if (!verificationId) {
            setError("No verification ID provided");
            setLoading(false);
            return;
        }

        const fetchResults = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${API_BASE_URL}/api/v1/result/${verificationId}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to fetch results: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log("Results data:", data);
                console.log("Input files:", data.input_files);
                setResults(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load results");
            } finally {
                setLoading(false);
            }
        };

        fetchResults();
    }, [verificationId]);

    const toggleSection = (section: string) => {
        setExpandedSections((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(section)) {
                newSet.delete(section);
            } else {
                newSet.add(section);
            }
            return newSet;
        });
    };

    if (loading) {
        return (
            <Layout className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <Loader2 className="animate-spin text-ice-cyan mx-auto mb-4" size={48} />
                    <p className="text-text-secondary">Loading results...</p>
                </div>
            </Layout>
        );
    }

    if (error || !results) {
        return (
            <Layout className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <AlertCircle className="text-alert-red mx-auto mb-4" size={48} />
                    <p className="text-alert-red mb-4">{error || "Results not found"}</p>
                    <button
                        onClick={() => navigate("/pipeline")}
                        className="px-4 py-2 bg-ice-cyan/20 text-ice-cyan rounded-lg hover:bg-ice-cyan/30 transition-colors"
                    >
                        Back to Pipeline
                    </button>
                </div>
            </Layout>
        );
    }

    // Get results from new structure (separate files) or legacy structure (all_outputs)
    const fusionResults = results.fusion_results || {};
    const textAnalysis = results.text_analysis || results.all_outputs?.text_analysis;
    const imageAnalysis = results.image_analysis || results.all_outputs?.image_analysis;
    const videoAnalysis = results.video_analysis || results.all_outputs?.video_analysis;
    const inputFiles = results.input_files || [];
    
    // Get image and video files
    const imageFile = inputFiles.find((f: any) => f.type === "image");
    const videoFile = inputFiles.find((f: any) => f.type === "video");

    // Extract individual claim findings from text analysis
    const extractIndividualClaimFindings = (textAnalysis: any): any[] => {
        // First, check if it's already in structured_data (easier path)
        if (textAnalysis?.structured_data?.verifier_ensemble_result?.individual_claim_findings) {
            const findings = textAnalysis.structured_data.verifier_ensemble_result.individual_claim_findings;
            if (Array.isArray(findings) && findings.length > 0) {
                return findings;
            }
        }

        // Fallback: parse from coordinator_response
        if (!textAnalysis?.coordinator_response || !Array.isArray(textAnalysis.coordinator_response)) {
            return [];
        }

        // Find the last item with author "final_verifier_agent"
        const finalVerifierResponse = textAnalysis.coordinator_response
            .filter((item: any) => item.author === "final_verifier_agent")
            .pop();

        if (!finalVerifierResponse?.content?.parts?.[0]?.text) {
            return [];
        }

        try {
            // Parse the JSON string from the text field
            const textContent = finalVerifierResponse.content.parts[0].text;
            let parsedContent;
            
            // Try to parse as JSON (it might be a JSON string)
            if (typeof textContent === 'string') {
                // Remove markdown code blocks if present
                let cleanedText = textContent;
                if (cleanedText.includes('```json')) {
                    const jsonStart = cleanedText.indexOf('```json') + 7;
                    const jsonEnd = cleanedText.indexOf('```', jsonStart);
                    cleanedText = cleanedText.substring(jsonStart, jsonEnd).trim();
                } else if (cleanedText.includes('```')) {
                    const jsonStart = cleanedText.indexOf('```') + 3;
                    const jsonEnd = cleanedText.indexOf('```', jsonStart);
                    cleanedText = cleanedText.substring(jsonStart, jsonEnd).trim();
                }
                
                // Try to find JSON object
                const firstBrace = cleanedText.indexOf('{');
                const lastBrace = cleanedText.lastIndexOf('}');
                if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
                    cleanedText = cleanedText.substring(firstBrace, lastBrace + 1);
                }
                
                parsedContent = JSON.parse(cleanedText);
            } else {
                parsedContent = textContent;
            }

            // Extract individual_claim_findings
            if (parsedContent?.individual_claim_findings && Array.isArray(parsedContent.individual_claim_findings)) {
                return parsedContent.individual_claim_findings;
            }
        } catch (error) {
            console.error("Error parsing individual claim findings:", error);
        }

        return [];
    };

    const individualClaimFindings = textAnalysis ? extractIndividualClaimFindings(textAnalysis) : [];

    // Get calibrated verdict
    const calibratedVerdict = fusionResults.calibrated_verdict || {};
    const verdict = calibratedVerdict.verdict || results.verdict || "UNCERTAIN";
    const confidence = calibratedVerdict.confidence || results.confidence || 0;
    const reasoning = calibratedVerdict.reasoning || results.explanation || "";

    // Determine verdict variant
    const getVerdictVariant = (v: string) => {
        if (v === "LIKELY_TRUE" || v === "Verified") return "success";
        if (v === "LIKELY_FALSE" || v === "False") return "danger";
        return "warning";
    };

    const verdictVariant = getVerdictVariant(verdict);
    const verdictIcon = verdictVariant === "success" ? CheckCircle : verdictVariant === "danger" ? XCircle : AlertCircle;
    
    // Get color classes based on verdict
    const getVerdictColorClasses = () => {
        if (verdictVariant === "success") {
            return {
                bg: "bg-royal-blue/20",
                border: "border-royal-blue/50",
                text: "text-royal-blue",
                shadow: "shadow-[0_0_50px_-10px_rgba(59,130,246,0.3)]"
            };
        } else if (verdictVariant === "danger") {
            return {
                bg: "bg-alert-red/20",
                border: "border-alert-red/50",
                text: "text-alert-red",
                shadow: "shadow-[0_0_50px_-10px_rgba(248,81,73,0.3)]"
            };
        } else {
            return {
                bg: "bg-saffron-gold/20",
                border: "border-saffron-gold/50",
                text: "text-saffron-gold",
                shadow: "shadow-[0_0_50px_-10px_rgba(255,193,7,0.3)]"
            };
        }
    };
    
    const colorClasses = getVerdictColorClasses();

    return (
        <Layout className="pb-20">
            {/* Back Button */}
            <div className="mb-6">
                <button
                    onClick={() => navigate("/pipeline")}
                    className="flex items-center gap-2 text-text-secondary hover:text-white transition-colors"
                >
                    <ArrowLeft size={16} />
                    <span>Back to Pipeline</span>
                </button>
            </div>

            {/* Top Section: Unified Verdict */}
            <div className="flex flex-col items-center mb-12">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5 }}
                    className="relative w-full max-w-4xl"
                >
                    <div className={`absolute inset-0 ${colorClasses.bg} blur-3xl rounded-full`} />
                    <div className={`relative bg-black/60 border ${colorClasses.border} backdrop-blur-xl px-8 py-8 rounded-2xl flex flex-col md:flex-row items-center gap-8 ${colorClasses.shadow}`}>
                        <div className="flex-shrink-0">
                            {React.createElement(verdictIcon, { 
                                className: `${colorClasses.text} w-20 h-20` 
                            })}
                        </div>
                        <div className="flex-1 text-center md:text-left">
                            <HoloBadge variant={verdictVariant} className="mb-2">
                                {verdict.replace(/_/g, " ").toUpperCase()}
                            </HoloBadge>
                            <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">
                                Calibrated Verdict
                            </h1>
                            <p className="text-text-secondary text-lg">
                                {reasoning || "Analysis complete"}
                            </p>
                        </div>

                        {/* Confidence Meter */}
                        <div className="w-full md:w-48">
                            <div className="flex justify-between text-sm mb-2">
                                <span className="text-text-secondary">Confidence</span>
                                <span className={`${colorClasses.text} font-bold`}>
                                    {(confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${confidence * 100}%` }}
                                    transition={{ duration: 1, delay: 0.5 }}
                                    className="h-full shadow-[0_0_10px_currentColor]"
                                    style={{
                                        backgroundColor: verdictVariant === "success" ? "#3B82F6" : 
                                                       verdictVariant === "danger" ? "#F85149" : "#FFC107"
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Input Analysis */}
                <div className="lg:col-span-2 space-y-6">
                    <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                        <Brain className="text-ice-cyan" />
                        Input Analysis
                    </h2>

                    {/* Text Analysis */}
                    {textAnalysis && (
                        <AntiGravityCard glowColor="cyan" className="transition-all duration-300">
                            <div
                                className="flex justify-between items-start cursor-pointer"
                                onClick={() => toggleSection("text")}
                            >
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="p-2 rounded-lg bg-white/5 text-ice-cyan mt-1">
                                        <FileText size={20} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="text-lg font-medium text-white">Text Analysis</h3>
                                            {textAnalysis.coordinator_output?.misinformation_analysis && (
                                                <HoloBadge variant={getVerdictVariant(textAnalysis.coordinator_output.misinformation_analysis.verdict)}>
                                                    {textAnalysis.coordinator_output.misinformation_analysis.verdict}
                                                </HoloBadge>
                                            )}
                                        </div>
                                        {textAnalysis.coordinator_output?.comprehensive_answer && (
                                            <p className="text-text-secondary text-sm line-clamp-2">
                                                {textAnalysis.coordinator_output.comprehensive_answer.substring(0, 150)}...
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <button className="text-text-secondary hover:text-white transition-colors">
                                    {expandedSections.has("text") ? <ChevronUp /> : <ChevronDown />}
                                </button>
                            </div>

                            {expandedSections.has("text") && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    className="mt-6 pt-6 border-t border-white/10 space-y-4"
                                >
                                    {textAnalysis.coordinator_output?.comprehensive_answer && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-white mb-2">Comprehensive Answer</h4>
                                            <p className="text-white/90 text-sm">{textAnalysis.coordinator_output.comprehensive_answer}</p>
                                        </div>
                                    )}
                                    {textAnalysis.coordinator_output?.misinformation_analysis && (
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                                                <span className="text-xs text-text-secondary block mb-1">Truth Score</span>
                                                <span className="text-sm text-white">
                                                    {(textAnalysis.coordinator_output.misinformation_analysis.overall_truth_score * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                            <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                                                <span className="text-xs text-text-secondary block mb-1">Confidence</span>
                                                <span className="text-sm text-white">
                                                    {(textAnalysis.coordinator_output.misinformation_analysis.overall_confidence * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                    
                                    {/* Individual Claim Findings */}
                                    {individualClaimFindings.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                                                <FileText size={16} className="text-ice-cyan" />
                                                Individual Claim Findings
                                            </h4>
                                            <div className="space-y-3">
                                                {individualClaimFindings.map((claim: any, idx: number) => (
                                                    <div 
                                                        key={idx} 
                                                        className="bg-black/40 p-4 rounded-lg border border-white/10 hover:border-white/20 transition-colors"
                                                    >
                                                        <div className="flex items-start justify-between gap-3 mb-2">
                                                            <div className="flex-1">
                                                                <h5 className="text-sm font-medium text-white mb-1">
                                                                    Claim {idx + 1}
                                                                </h5>
                                                                <p className="text-xs text-white/90 mb-2">
                                                                    {claim.claim_text}
                                                                </p>
                                                            </div>
                                                            <div className="flex-shrink-0">
                                                                <div className={`px-2 py-1 rounded text-xs font-semibold ${
                                                                    claim.truth_score === 0 
                                                                        ? "bg-alert-red/20 text-alert-red border border-alert-red/30"
                                                                        : claim.truth_score >= 0.7
                                                                        ? "bg-royal-blue/20 text-royal-blue border border-royal-blue/30"
                                                                        : "bg-saffron-gold/20 text-saffron-gold border border-saffron-gold/30"
                                                                }`}>
                                                                    {(claim.truth_score * 100).toFixed(0)}%
                                                                </div>
                                                            </div>
                                                        </div>
                                                        
                                                        {claim.finding && (
                                                            <div className="mb-2">
                                                                <span className="text-xs text-text-secondary block mb-1">Finding:</span>
                                                                <p className="text-xs text-white/80">
                                                                    {claim.finding}
                                                                </p>
                                                            </div>
                                                        )}
                                                        
                                                        {claim.sources && Array.isArray(claim.sources) && claim.sources.length > 0 && (
                                                            <div>
                                                                <span className="text-xs text-text-secondary block mb-1">Sources:</span>
                                                                <div className="flex flex-wrap gap-1.5">
                                                                    {claim.sources.map((source: string, sourceIdx: number) => (
                                                                        <span 
                                                                            key={sourceIdx}
                                                                            className="px-2 py-0.5 bg-white/5 rounded text-xs text-white/70 border border-white/10"
                                                                        >
                                                                            {source}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AntiGravityCard>
                    )}

                    {/* Image Analysis */}
                    {imageAnalysis && (
                        <AntiGravityCard glowColor="gold" className="transition-all duration-300">
                            <div
                                className="flex justify-between items-start cursor-pointer"
                                onClick={() => toggleSection("image")}
                            >
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="p-2 rounded-lg bg-white/5 text-saffron-gold mt-1">
                                        <ImageIcon size={20} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="text-lg font-medium text-white">Image Analysis</h3>
                                            {imageAnalysis.vlm_ai_artifact_analysis?.artifact_detected && (
                                                <HoloBadge variant="danger">AI Artifacts Detected</HoloBadge>
                                            )}
                                        </div>
                                        {imageAnalysis.vlm_description?.description && (
                                            <p className="text-text-secondary text-sm line-clamp-2">
                                                {imageAnalysis.vlm_description.description.substring(0, 150)}...
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <button className="text-text-secondary hover:text-white transition-colors">
                                    {expandedSections.has("image") ? <ChevronUp /> : <ChevronDown />}
                                </button>
                            </div>

                            {expandedSections.has("image") && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    className="mt-6 pt-6 border-t border-white/10 space-y-4"
                                >
                                    {/* Display Image */}
                                    {imageFile ? (
                                        <div className="mb-4">
                                            <h4 className="text-sm font-semibold text-white mb-2">Image</h4>
                                            <div className="relative rounded-lg overflow-hidden border border-white/10 bg-black/20">
                                                <img 
                                                    src={`${API_BASE_URL}${imageFile.path}`}
                                                    alt="Analyzed image"
                                                    className="w-full h-auto max-h-96 object-contain"
                                                    onError={(e) => {
                                                        console.error("Image load error:", `${API_BASE_URL}${imageFile.path}`);
                                                        console.error("Image file:", imageFile);
                                                        console.error("API_BASE_URL:", API_BASE_URL);
                                                    }}
                                                    onLoad={() => {
                                                        console.log("Image loaded successfully:", `${API_BASE_URL}${imageFile.path}`);
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ) : imageAnalysis ? (
                                        <div className="mb-4 text-xs text-text-secondary">
                                            Image analysis available but file not found. Input files: {inputFiles.length > 0 ? JSON.stringify(inputFiles) : "none"}
                                        </div>
                                    ) : null}
                                    {imageAnalysis.vlm_description && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-white mb-2">Description</h4>
                                            <p className="text-white/90 text-sm">{imageAnalysis.vlm_description.description}</p>
                                        </div>
                                    )}
                                    {imageAnalysis.vlm_description?.objects && imageAnalysis.vlm_description.objects.length > 0 && (
                                    <div>
                                            <h4 className="text-sm font-semibold text-white mb-2">Objects Detected</h4>
                                            <div className="flex flex-wrap gap-2">
                                                {imageAnalysis.vlm_description.objects.map((obj: string, idx: number) => (
                                                    <span key={idx} className="px-2 py-1 bg-white/5 rounded text-xs text-white">
                                                        {obj}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {imageAnalysis.vlm_ai_artifact_analysis && (
                                        <div className={`p-3 rounded border ${
                                            imageAnalysis.vlm_ai_artifact_analysis.artifact_detected
                                                ? "bg-alert-red/10 border-alert-red/30"
                                                : "bg-ice-cyan/10 border-ice-cyan/30"
                                        }`}>
                                            <div className="flex items-center gap-2 mb-2">
                                                <AlertTriangle 
                                                    size={14} 
                                                    className={imageAnalysis.vlm_ai_artifact_analysis.artifact_detected ? "text-alert-red" : "text-ice-cyan"} 
                                                />
                                                <span className={`text-xs font-semibold ${
                                                    imageAnalysis.vlm_ai_artifact_analysis.artifact_detected ? "text-alert-red" : "text-ice-cyan"
                                                }`}>
                                                    AI Artifact Detection
                                                </span>
                                            </div>
                                            <p className="text-xs text-white/90">
                                                {imageAnalysis.vlm_ai_artifact_analysis.artifact_detected ? "Yes" : "No"} - {
                                                    imageAnalysis.vlm_ai_artifact_analysis.explanation || "No artifacts detected"
                                                }
                                            </p>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AntiGravityCard>
                    )}

                    {/* Video Analysis */}
                    {videoAnalysis?.video_analysis && (
                        <AntiGravityCard glowColor="red" className="transition-all duration-300">
                            <div
                                className="flex justify-between items-start cursor-pointer"
                                onClick={() => toggleSection("video")}
                            >
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="p-2 rounded-lg bg-white/5 text-alert-red mt-1">
                                        <Video size={20} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-1">
                                            <h3 className="text-lg font-medium text-white">Video Analysis</h3>
                                            {videoAnalysis.video_analysis.authenticity_verdict && (
                                                <HoloBadge variant={getVerdictVariant(videoAnalysis.video_analysis.authenticity_verdict)}>
                                                    {videoAnalysis.video_analysis.authenticity_verdict}
                                            </HoloBadge>
                                            )}
                                        </div>
                                        {videoAnalysis.video_analysis.video_description && (
                                            <p className="text-text-secondary text-sm line-clamp-2">
                                                {videoAnalysis.video_analysis.video_description.substring(0, 150)}...
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <button className="text-text-secondary hover:text-white transition-colors">
                                    {expandedSections.has("video") ? <ChevronUp /> : <ChevronDown />}
                                </button>
                            </div>

                            {expandedSections.has("video") && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    className="mt-6 pt-6 border-t border-white/10 space-y-4"
                                >
                                    {videoAnalysis.video_analysis.video_description && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-white mb-2">Video Description</h4>
                                            <p className="text-white/90 text-sm">{videoAnalysis.video_analysis.video_description}</p>
                                        </div>
                                    )}
                                    {videoAnalysis.video_analysis.overall_authenticity_score !== undefined && (
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                                                <span className="text-xs text-text-secondary block mb-1">Authenticity Score</span>
                                                <span className="text-sm text-white">
                                                    {(videoAnalysis.video_analysis.overall_authenticity_score * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                            <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                                                <span className="text-xs text-text-secondary block mb-1">Verdict</span>
                                                <span className="text-sm text-white">
                                                    {videoAnalysis.video_analysis.authenticity_verdict || "N/A"}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                    {videoAnalysis.video_analysis.claims && videoAnalysis.video_analysis.claims.length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-semibold text-white mb-2">Extracted Claims</h4>
                                            <div className="space-y-2">
                                                {videoAnalysis.video_analysis.claims.map((claim: any, idx: number) => (
                                                    <div key={idx} className="p-2 bg-black/30 rounded border border-white/5">
                                                        <p className="text-xs text-white/90">{claim.claim_text}</p>
                                                        {claim.timestamp && (
                                                            <span className="text-xs text-text-secondary">@{claim.timestamp}</span>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AntiGravityCard>
                    )}
                </div>

                {/* Right Column: Cross-Modal Fusion & Summary */}
                <div className="space-y-8">
                    {/* Cross-Modal Fusion */}
                    {fusionResults && (
                    <div>
                        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                            <ShieldCheck className="text-ice-cyan" />
                                Cross-Modal Fusion
                        </h2>
                        <AntiGravityCard glowColor="blue">
                            <div className="space-y-4">
                                    {/* Content Relevance */}
                                    {fusionResults.content_relevance && (
                                        <div className={`p-3 rounded-lg border ${
                                            fusionResults.content_relevance.is_relevant
                                                ? "bg-ice-cyan/10 border-ice-cyan/30"
                                                : "bg-alert-red/10 border-alert-red/30"
                                        }`}>
                                            <div className="flex items-center gap-2 mb-2">
                                                <Eye size={16} className={
                                                    fusionResults.content_relevance.is_relevant ? "text-ice-cyan" : "text-alert-red"
                                                } />
                                                <span className={`text-sm font-medium ${
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
                                                    <p className="text-white/80 mt-2 text-xs">
                                                        {fusionResults.content_relevance.explanation}
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
                                                            {fusionResults.fusion_analysis.key_findings.slice(0, 3).map((finding: string, idx: number) => (
                                                                <li key={idx}>{finding}</li>
                                                            ))}
                                                        </ul>
                                    </div>
                                                )}
                                                {fusionResults.fusion_analysis.conflicts && fusionResults.fusion_analysis.conflicts.length > 0 && (
                                                    <div>
                                                        <span className="text-alert-red">Conflicts: </span>
                                                        <ul className="list-disc list-inside mt-1 text-alert-red/80">
                                                            {fusionResults.fusion_analysis.conflicts.slice(0, 2).map((conflict: string, idx: number) => (
                                                                <li key={idx}>{conflict}</li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                            </div>
                        </AntiGravityCard>
                    </div>
                    )}

                    {/* Summary Stats */}
                    <div>
                        <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                            <TrendingUp className="text-ice-cyan" />
                            Summary
                        </h2>
                        <AntiGravityCard glowColor="cyan">
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-text-secondary text-sm">Overall Verdict</span>
                                    <HoloBadge variant={verdictVariant} className="text-xs">
                                        {verdict.replace(/_/g, " ")}
                                    </HoloBadge>
                                            </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-text-secondary text-sm">Confidence</span>
                                    <span className="text-white font-semibold">{(confidence * 100).toFixed(0)}%</span>
                                        </div>
                                {results.timestamp && (
                                    <div className="flex justify-between items-center">
                                        <span className="text-text-secondary text-sm">Analyzed</span>
                                        <span className="text-white text-xs">
                                            {new Date(results.timestamp).toLocaleString()}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </AntiGravityCard>
                    </div>
                </div>
            </div>
        </Layout>
    );
};
