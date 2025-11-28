import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layout } from "../components/layout/Layout";
import { AntiGravityCard } from "../components/ui/AntiGravityCard";
import { GlassInput } from "../components/ui/GlassInput";
import { NeonButton } from "../components/ui/NeonButton";
import { useNavigate } from "react-router-dom";
import { FileText, Image as ImageIcon, Video, Plus, X, ArrowRight, Upload, Clock } from "lucide-react";
import { cn } from "../lib/utils";
import { HistoryPanel } from "../components/ui/HistoryPanel";
import { TwitterMapSection } from "../components/ui/TwitterMapSection";

type InputType = "text" | "image" | "video";

interface InputItem {
    id: string;
    type: InputType;
    content: string; // Text content or filename
    file?: File;
    file_id?: string; // File ID returned from upload API
    file_path?: string; // File path returned from upload API
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const LandingPage: React.FC = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<InputType>("text");
    const [inputs, setInputs] = useState<InputItem[]>([]);
    const [inputValue, setInputValue] = useState("");
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<string>("");

    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

    const addInput = () => {
        if (!inputValue.trim()) return;

        const newItem: InputItem = {
            id: Math.random().toString(36).substr(2, 9),
            type: activeTab,
            content: inputValue,
        };

        setInputs([...inputs, newItem]);
        setInputValue("");
    };

    const removeInput = (id: string) => {
        setInputs(inputs.filter((item) => item.id !== id));
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const newItem: InputItem = {
                id: Math.random().toString(36).substr(2, 9),
                type: activeTab,
                content: file.name,
                file: file,
            };
            setInputs([...inputs, newItem]);
        }
    };

    const handleVerifyTweet = (text: string) => {
        setActiveTab("text");
        setInputValue(text);
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    const uploadFile = async (file: File, type: "image" | "video"): Promise<{ file_id: string; file_path: string }> => {
        const formData = new FormData();
        formData.append("file", file);

        const endpoint = type === "image" 
            ? `${API_BASE_URL}/api/v1/upload/image`
            : `${API_BASE_URL}/api/v1/upload/video`;

        const response = await fetch(endpoint, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: "Upload failed" }));
            throw new Error(error.detail || "Failed to upload file");
        }

        const data = await response.json();
        return {
            file_id: data.file_id,
            file_path: data.file_path,
        };
    };

    const handleAnalyzeAll = async () => {
        if (inputs.length === 0) return;

        setIsUploading(true);
        setUploadProgress("Uploading files...");

        try {
            // Upload all image and video files first
            const updatedInputs = await Promise.all(
                inputs.map(async (input) => {
                    // If it's a file input and hasn't been uploaded yet
                    if ((input.type === "image" || input.type === "video") && input.file && !input.file_id) {
                        setUploadProgress(`Uploading ${input.content}...`);
                        const uploadResult = await uploadFile(input.file!, input.type);
                        return {
                            ...input,
                            file_id: uploadResult.file_id,
                            file_path: uploadResult.file_path,
                        };
                    }
                    return input;
                })
            );

            setInputs(updatedInputs);
            setUploadProgress("Files uploaded successfully!");

            // Navigate to pipeline with updated inputs after a brief delay
            setTimeout(() => {
                // Store inputs in sessionStorage as fallback
                sessionStorage.setItem("pipelineInputs", JSON.stringify(updatedInputs));
                // Navigate with state
                navigate("/pipeline", { state: { inputs: updatedInputs } });
            }, 500);
        } catch (error) {
            console.error("Error uploading files:", error);
            setUploadProgress(`Error: ${error instanceof Error ? error.message : "Upload failed"}`);
            setIsUploading(false);
            alert(`Failed to upload files: ${error instanceof Error ? error.message : "Unknown error"}`);
        }
    };

    return (
        <Layout className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)]">
            {/* History Button */}
            <div className="absolute top-6 right-6 z-50">
                <NeonButton
                    variant="secondary"
                    onClick={() => setIsHistoryOpen(true)}
                    className="flex items-center gap-2 !px-4 !py-2"
                >
                    <Clock size={18} /> History
                </NeonButton>
            </div>

            <HistoryPanel isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} />

            {/* Hero Section */}
            <motion.div
                initial={{ opacity: 0, y: -30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="text-center mb-12 relative z-10"
            >
                <h1 className="text-5xl md:text-6xl font-bold tracking-tighter mb-4 bg-clip-text text-transparent bg-gradient-to-b from-white to-white/50 drop-shadow-[0_0_30px_rgba(255,255,255,0.3)]">
                    Veritas AI
                </h1>
                <p className="text-lg md:text-xl text-text-secondary font-light tracking-wide max-w-2xl mx-auto">
                    Multimodal Truth Engine. Verify text, images, and video simultaneously.
                </p>
            </motion.div>

            <div className="w-full max-w-4xl grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Panel: Input Hub */}
                <div className="lg:col-span-2">
                    <AntiGravityCard className="h-full flex flex-col" glowColor="blue">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold text-white">Input Hub</h2>
                            <div className="flex gap-2 bg-black/40 p-1 rounded-lg border border-white/10">
                                {(["text", "image", "video"] as InputType[]).map((type) => (
                                    <button
                                        key={type}
                                        onClick={() => setActiveTab(type)}
                                        className={cn(
                                            "p-2 rounded-md transition-all duration-300",
                                            activeTab === type
                                                ? "bg-royal-blue/20 text-ice-cyan shadow-[0_0_10px_-5px_#3D89F5]"
                                                : "text-text-secondary hover:text-white hover:bg-white/5"
                                        )}
                                    >
                                        {type === "text" && <FileText size={18} />}
                                        {type === "image" && <ImageIcon size={18} />}
                                        {type === "video" && <Video size={18} />}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex-1 flex flex-col gap-4">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={activeTab}
                                    initial={{ opacity: 0, x: 10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                    transition={{ duration: 0.2 }}
                                    className="min-h-[120px]"
                                >
                                    {activeTab === "text" && (
                                        <div className="space-y-4">
                                            <p className="text-sm text-text-secondary">Enter the claim or text snippet to analyze.</p>
                                            <textarea
                                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3 px-4 text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-ice-cyan/50 focus:shadow-[0_0_15px_-5px_#9EE8FF] transition-all duration-300 backdrop-blur-sm resize-none h-[100px]"
                                                placeholder="Paste text here..."
                                                value={inputValue}
                                                onChange={(e) => setInputValue(e.target.value)}
                                                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), addInput())}
                                            />
                                        </div>
                                    )}
                                    {(activeTab === "image" || activeTab === "video") && (
                                        <div className="space-y-4">
                                            <p className="text-sm text-text-secondary">Upload a file to check for manipulation.</p>
                                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/10 rounded-lg cursor-pointer hover:border-ice-cyan/50 hover:bg-white/5 transition-all duration-300 group">
                                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                                    <Upload className="w-8 h-8 mb-3 text-text-secondary group-hover:text-ice-cyan transition-colors" />
                                                    <p className="text-sm text-text-secondary">Click to upload or drag and drop</p>
                                                </div>
                                                <input type="file" className="hidden" onChange={handleFileUpload} accept={activeTab === "image" ? "image/*" : "video/*"} />
                                            </label>
                                        </div>
                                    )}
                                </motion.div>
                            </AnimatePresence>

                            {/* Add Button for Text */}
                            {activeTab === "text" && (
                                <div className="flex justify-end">
                                    <NeonButton variant="secondary" onClick={addInput} className="flex items-center gap-2">
                                        <Plus size={16} /> Add to Analysis
                                    </NeonButton>
                                </div>
                            )}
                        </div>
                    </AntiGravityCard>
                </div>

                {/* Right Panel: Active Inputs */}
                <div className="lg:col-span-1">
                    <AntiGravityCard className="h-full flex flex-col bg-card-2/50" glowColor="cyan">
                        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            Analysis Queue
                            <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full text-ice-cyan">{inputs.length}</span>
                        </h2>

                        <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent min-h-[200px]">
                            <AnimatePresence>
                                {inputs.length === 0 && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="h-full flex flex-col items-center justify-center text-text-secondary opacity-50"
                                    >
                                        <div className="w-12 h-12 rounded-full border-2 border-dashed border-white/20 mb-2" />
                                        <p className="text-sm">No inputs added yet</p>
                                    </motion.div>
                                )}
                                {inputs.map((item) => (
                                    <motion.div
                                        key={item.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="group relative p-3 rounded-lg bg-white/5 border border-white/5 hover:border-white/20 transition-all"
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={cn(
                                                "p-2 rounded-md",
                                                item.type === "text" && "bg-ice-cyan/10 text-ice-cyan",
                                                item.type === "image" && "bg-saffron-gold/10 text-saffron-gold",
                                                item.type === "video" && "bg-alert-red/10 text-alert-red",
                                            )}>
                                                {item.type === "text" && <FileText size={16} />}
                                                {item.type === "image" && <ImageIcon size={16} />}
                                                {item.type === "video" && <Video size={16} />}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-white truncate">{item.content}</p>
                                                <p className="text-xs text-text-secondary capitalize">{item.type} Input</p>
                                            </div>
                                            <button
                                                onClick={() => removeInput(item.id)}
                                                className="text-text-secondary hover:text-alert-red transition-colors opacity-0 group-hover:opacity-100"
                                            >
                                                <X size={16} />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>

                        <div className="mt-6 pt-4 border-t border-white/10">
                            {isUploading && (
                                <div className="mb-3 text-center">
                                    <p className="text-xs text-ice-cyan">{uploadProgress}</p>
                                </div>
                            )}
                            <NeonButton
                                variant="primary"
                                className="w-full flex items-center justify-center gap-2"
                                disabled={inputs.length === 0 || isUploading}
                                onClick={handleAnalyzeAll}
                            >
                                {isUploading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-ice-cyan border-t-transparent rounded-full animate-spin" />
                                        Uploading...
                                    </>
                                ) : (
                                    <>
                                        Analyze All <ArrowRight size={16} />
                                    </>
                                )}
                            </NeonButton>
                        </div>
                    </AntiGravityCard>
                </div>
            </div>

            {/* Twitter Map Section */}
            <TwitterMapSection onVerifyTweet={handleVerifyTweet} />
        </Layout>
    );
};
