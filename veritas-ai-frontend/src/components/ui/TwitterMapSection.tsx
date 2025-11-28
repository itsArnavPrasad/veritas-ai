import React, { useState } from "react";
import Map, { NavigationControl, useControl } from "react-map-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ScatterplotLayer } from "@deck.gl/layers";
import { NeonButton } from "./NeonButton";
import { GlassInput } from "./GlassInput";
import { Search, Twitter, ArrowUp } from "lucide-react";
import { AntiGravityCard } from "./AntiGravityCard";
import { motion, AnimatePresence } from "framer-motion";
import "mapbox-gl/dist/mapbox-gl.css";

// Token from Twitter_example
const MAPBOX_TOKEN = "pk.eyJ1IjoiYXRoMG0iLCJhIjoiY2szMDlnazFhMG5mMDNtbW1wc2o2OXJxaiJ9.gl8rnf3bAnnFOQdophEAeQ";

interface TweetCluster {
    id: string;
    coordinates: [number, number];
    count: number;
    sentiment: "positive" | "neutral" | "negative";
    text: string; // Sample tweet text
}

// Mock data generator for "bomb blast" query
const generateMockClusters = (query: string): TweetCluster[] => {
    if (query.toLowerCase().includes("bomb") || query.toLowerCase().includes("blast")) {
        return [
            { id: "c1", coordinates: [72.8777, 19.0760], count: 25, sentiment: "negative", text: "Breaking: Reports of a blast in Juhu area. Stay safe Mumbai! #MumbaiBlast" }, // Mumbai
            { id: "c2", coordinates: [72.83, 19.15], count: 12, sentiment: "negative", text: "Hearing loud noises near Andheri. What is happening? #Mumbai" },
            { id: "c3", coordinates: [72.90, 19.05], count: 8, sentiment: "neutral", text: "Traffic diverted due to incident in Juhu. Avoid the route." },
        ];
    }
    return [];
};

function DeckGLOverlay(props: any) {
    const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay({
        interleaved: true,
        ...props
    }));
    overlay.setProps(props);
    return null;
}

interface TwitterMapSectionProps {
    onVerifyTweet: (text: string) => void;
}

export const TwitterMapSection: React.FC<TwitterMapSectionProps> = ({ onVerifyTweet }) => {
    const [query, setQuery] = useState("");
    const [clusters, setClusters] = useState<TweetCluster[]>([]);
    const [hoveredCluster, setHoveredCluster] = useState<TweetCluster | null>(null);
    const [viewState, setViewState] = useState({
        longitude: 78.9629,
        latitude: 20.5937,
        zoom: 3.5
    });

    const handleSearch = () => {
        if (!query.trim()) return;
        const results = generateMockClusters(query);
        setClusters(results);
        if (results.length > 0) {
            // Fly to the first cluster (Mumbai)
            setViewState({
                longitude: 72.8777,
                latitude: 19.0760,
                zoom: 10
            });
        }
    };

    const hoverTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

    // Clear timeout on unmount
    React.useEffect(() => {
        return () => {
            if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
        };
    }, []);

    const layers = [
        new ScatterplotLayer({
            id: "tweet-clusters",
            data: clusters,
            getPosition: (d: TweetCluster) => d.coordinates,
            getRadius: (d: TweetCluster) => 100 + (d.count * 20),
            getFillColor: (d: TweetCluster) => d.sentiment === "negative" ? [248, 81, 73] : [74, 222, 128], // Red or Green
            pickable: true,
            opacity: 0.8,
            stroked: true,
            getLineColor: [255, 255, 255],
            getLineWidth: 20,
            radiusScale: 6,
            radiusMinPixels: 10,
            radiusMaxPixels: 100,
            onHover: (info) => {
                if (info.object) {
                    // Hovering over an object: Clear timeout and show immediately
                    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                    setHoveredCluster(info.object);
                } else {
                    // Unhovering: Set timeout to hide
                    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                    hoverTimeoutRef.current = setTimeout(() => {
                        setHoveredCluster(null);
                    }, 5000); // 5 seconds delay
                }
            }
        })
    ];

    return (
        <div className="w-full max-w-6xl mx-auto mt-20 mb-20 relative z-10">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8 }}
            >
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Twitter className="text-ice-cyan" size={32} />
                            Live Threat Intelligence
                        </h2>
                        <p className="text-text-secondary mt-2">
                            Monitor real-time social signals and verify emerging threats.
                        </p>
                    </div>

                    <div className="flex gap-4 w-full max-w-md">
                        <GlassInput
                            placeholder="Query Twitter (e.g., 'bomb blast')..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                            icon={<Search size={18} />}
                        />
                        <NeonButton onClick={handleSearch}>Search</NeonButton>
                    </div>
                </div>

                <AntiGravityCard className="h-[600px] relative overflow-hidden p-0 border-0" glowColor="cyan">
                    <Map
                        {...viewState}
                        onMove={(evt: { viewState: any }) => setViewState(evt.viewState)}
                        mapStyle="mapbox://styles/mapbox/dark-v11"
                        mapboxAccessToken={MAPBOX_TOKEN}
                    >
                        <DeckGLOverlay layers={layers} />
                        <NavigationControl position="top-right" />
                    </Map>

                    {/* Hover Tooltip */}
                    <AnimatePresence>
                        {hoveredCluster && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.9, y: 10 }}
                                className="absolute bottom-6 left-6 z-20 max-w-sm"
                            >
                                <div className="bg-black/80 backdrop-blur-xl border border-white/10 p-4 rounded-xl shadow-2xl">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="text-white font-bold text-lg">Cluster Detected</h3>
                                        <span className="bg-alert-red/20 text-alert-red text-xs px-2 py-0.5 rounded-full border border-alert-red/30">
                                            High Severity
                                        </span>
                                    </div>
                                    <p className="text-text-secondary text-sm mb-3">
                                        {hoveredCluster.count} tweets related to incident in this area.
                                    </p>
                                    <div className="bg-white/5 p-3 rounded-lg mb-4 border border-white/5">
                                        <p className="text-white italic text-sm">"{hoveredCluster.text}"</p>
                                    </div>
                                    <NeonButton
                                        variant="primary"
                                        className="w-full flex items-center justify-center gap-2"
                                        onClick={() => onVerifyTweet(hoveredCluster.text)}
                                    >
                                        Verify This Cluster <ArrowUp size={16} />
                                    </NeonButton>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </AntiGravityCard>
            </motion.div>
        </div>
    );
};
