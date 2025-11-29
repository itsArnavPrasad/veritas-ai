import React, { useState, useEffect, useRef } from "react";
import MapGL, { NavigationControl, useControl } from "react-map-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ScatterplotLayer } from "@deck.gl/layers";
import { NeonButton } from "./NeonButton";
import { GlassInput } from "./GlassInput";
import { Search, Twitter, ArrowUp, Loader2 } from "lucide-react";
import { AntiGravityCard } from "./AntiGravityCard";
import { motion, AnimatePresence } from "framer-motion";
import "mapbox-gl/dist/mapbox-gl.css";

// Token from Twitter_example
const MAPBOX_TOKEN = "pk.eyJ1IjoiYXRoMG0iLCJhIjoiY2szMDlnazFhMG5mMDNtbW1wc2o2OXJxaiJ9.gl8rnf3bAnnFOQdophEAeQ";

// API base URL - adjust based on your backend
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Tweet {
    text: string;
    username: string;
    tweet_id?: string;
    timestamp?: string;
    likes?: number;
    retweets?: number;
    replies?: number;
}

interface TweetCluster {
    cluster_id: string;
    coordinates: [number, number];
    count: number;
    sentiment: "positive" | "neutral" | "negative";
    text: string; // Headline text
    popularity_score: number;
    last_seen: string;
    top_tweets?: Tweet[];
}

interface ClusterUpdate {
    type: string;
    stream_id?: string;
    cluster?: {
        cluster_id: string;
        centroid_lat: number;
        centroid_lon: number;
        headline: string;
        top_tweets: string | string[] | Tweet[];
        popularity_score: number;
        last_seen: string;
        tweet_count: number;
    };
}

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
    const [clusters, setClusters] = useState<Map<string, TweetCluster>>(new Map());
    const [hoveredCluster, setHoveredCluster] = useState<TweetCluster | null>(null);
    const [streamId, setStreamId] = useState<string | null>(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);
    const [viewState, setViewState] = useState({
        longitude: 78.9629,
        latitude: 20.5937,
        zoom: 3.5
    });

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    const handleStopStream = async () => {
        if (!streamId) return;
        
        try {
            // Stop the stream on backend
            const response = await fetch(`${API_BASE_URL}/api/v1/stop_stream`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ stream_id: streamId }),
            });
            
            if (!response.ok) {
                console.error("Failed to stop stream");
            }
        } catch (error) {
            console.error("Error stopping stream:", error);
        } finally {
            // Close EventSource connection
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
            
            // Reset state
            setIsStreaming(false);
            setStreamId(null);
        }
    };

    const handleSearch = async () => {
        // If already streaming, stop it
        if (isStreaming && streamId) {
            await handleStopStream();
            return;
        }
        
        if (!query.trim()) return;
        
        // Stop existing stream if any
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
        
        setIsLoading(true);
        setClusters(new Map());
        
        try {
            // Start new stream
            const response = await fetch(`${API_BASE_URL}/api/v1/start_stream`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query: query.trim() }),
            });
            
            if (!response.ok) {
                throw new Error("Failed to start stream");
            }
            
            const data = await response.json();
            const newStreamId = data.stream_id;
            setStreamId(newStreamId);
            setIsStreaming(true);
            setIsLoading(false);
            
            // Connect to SSE stream
            const eventSource = new EventSource(`${API_BASE_URL}/api/v1/stream/${newStreamId}`);
            eventSourceRef.current = eventSource;
            
            eventSource.onmessage = (event) => {
                try {
                    const update: ClusterUpdate = JSON.parse(event.data);
                    
                    if (update.type === "cluster_update" && update.cluster) {
                        const cluster = update.cluster;
                        
                        // Parse top_tweets - handle both old format (strings) and new format (objects)
                        let topTweets: Tweet[] = [];
                        if (typeof cluster.top_tweets === "string") {
                            try {
                                const parsed = JSON.parse(cluster.top_tweets);
                                if (Array.isArray(parsed)) {
                                    // Check if it's array of strings or objects
                                    topTweets = parsed.map((item: any) => {
                                        if (typeof item === "string") {
                                            return { text: item, username: "unknown" };
                                        } else {
                                            return item as Tweet;
                                        }
                                    });
                                } else {
                                    topTweets = [{ text: parsed, username: "unknown" }];
                                }
                            } catch {
                                topTweets = [{ text: cluster.top_tweets, username: "unknown" }];
                            }
                        } else if (Array.isArray(cluster.top_tweets)) {
                            // Handle array of strings or objects
                            topTweets = cluster.top_tweets.map((item: any) => {
                                if (typeof item === "string") {
                                    return { text: item, username: "unknown" };
                                } else {
                                    return item as Tweet;
                                }
                            });
                        }
                        
                        const tweetCluster: TweetCluster = {
                            cluster_id: cluster.cluster_id,
                            coordinates: [cluster.centroid_lon, cluster.centroid_lat],
                            count: cluster.tweet_count,
                            sentiment: "negative", // Default for now
                            text: cluster.headline,
                            popularity_score: cluster.popularity_score,
                            last_seen: cluster.last_seen,
                            top_tweets: topTweets,
                        };
                        
                        // Update clusters map
                        setClusters((prev) => {
                            const newMap = new Map(prev);
                            const isFirstCluster = prev.size === 0;
                            newMap.set(cluster.cluster_id, tweetCluster);
                            
                            // Fly to first cluster
                            if (isFirstCluster) {
                                setViewState({
                                    longitude: cluster.centroid_lon,
                                    latitude: cluster.centroid_lat,
                                    zoom: 10
                                });
                            }
                            
                            return newMap;
                        });
                    }
                } catch (error) {
                    console.error("Error parsing SSE message:", error);
                }
            };
            
            eventSource.onerror = (error) => {
                console.error("SSE error:", error);
                setIsStreaming(false);
                eventSource.close();
            };
            
        } catch (error) {
            console.error("Error starting stream:", error);
            setIsLoading(false);
            setIsStreaming(false);
        }
    };

    const hoverTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

    // Clear timeout on unmount
    React.useEffect(() => {
        return () => {
            if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
        };
    }, []);

    // Function to generate consistent, vibrant, and easily distinguishable colors from cluster_id
    const getClusterColor = (clusterId: string): [number, number, number] => {
        // Create a strong hash from cluster_id for consistency
        let hash = 0;
        for (let i = 0; i < clusterId.length; i++) {
            const char = clusterId.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        
        // Use hash to generate distinct colors
        // Strategy: Use golden ratio spacing for hue to maximize color separation
        const goldenRatio = 0.618033988749895;
        const hue = (Math.abs(hash) * goldenRatio) % 360;
        
        // High saturation (80-100%) for vibrant, distinct colors
        const saturation = 80 + (Math.abs(hash >> 8) % 20); // 80-100%
        
        // Medium-high lightness (55-75%) for visibility on dark map
        const lightness = 55 + (Math.abs(hash >> 16) % 20); // 55-75%
        
        // Convert HSL to RGB
        const h = hue / 360;
        const s = saturation / 100;
        const l = lightness / 100;
        
        const hue2rgb = (p: number, q: number, t: number): number => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
            return p;
        };
        
        let r, g, b;
        
        if (s === 0) {
            // Achromatic (grayscale)
            r = g = b = l;
        } else {
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1 / 3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1 / 3);
        }
        
        return [
            Math.round(r * 255),
            Math.round(g * 255),
            Math.round(b * 255)
        ];
    };
    
    const clusterArray = Array.from(clusters.values());
    
    const layers = [
        new ScatterplotLayer({
            id: "tweet-clusters",
            data: clusterArray,
            getPosition: (d: TweetCluster) => d.coordinates,
            getRadius: (d: TweetCluster) => Math.min(100 + (d.count * 20), 500),
            getFillColor: (d: TweetCluster) => {
                // Use randomized but consistent color based on cluster_id
                return getClusterColor(d.cluster_id);
            },
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
                            Live News Intelligence
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
                            disabled={isLoading || isStreaming}
                        />
                        <NeonButton 
                            onClick={handleSearch}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="animate-spin" size={16} />
                                    Starting...
                                </>
                            ) : isStreaming ? (
                                <>
                                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2" />
                                    Stop Streaming
                                </>
                            ) : (
                                "Search"
                            )}
                        </NeonButton>
                    </div>
                </div>

                <AntiGravityCard className="h-[600px] relative overflow-hidden p-0 border-0" glowColor="cyan">
                    {MAPBOX_TOKEN ? (
                        <MapGL
                            {...viewState}
                            onMove={(evt: { viewState: any }) => setViewState(evt.viewState)}
                            mapStyle="mapbox://styles/mapbox/dark-v11"
                            mapboxAccessToken={MAPBOX_TOKEN}
                        >
                            <DeckGLOverlay layers={layers} />
                            <NavigationControl position="top-right" />
                        </MapGL>
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-text-secondary">
                            <p>Mapbox token not configured</p>
                        </div>
                    )}

                    {/* Hover Tooltip */}
                    <AnimatePresence>
                        {hoveredCluster && (() => {
                            // Find the tweet with the most likes
                            const getMostLikedTweet = (): Tweet | null => {
                                if (!hoveredCluster.top_tweets || hoveredCluster.top_tweets.length === 0) {
                                    return null;
                                }
                                
                                // Find tweet with maximum likes
                                let mostLiked: Tweet | null = null;
                                let maxLikes = -1;
                                
                                for (const tweet of hoveredCluster.top_tweets) {
                                    const tweetObj = typeof tweet === 'string' 
                                        ? { text: tweet, username: 'unknown', likes: 0 }
                                        : tweet;
                                    const likes = tweetObj.likes || 0;
                                    
                                    if (likes > maxLikes) {
                                        maxLikes = likes;
                                        mostLiked = tweetObj;
                                    }
                                }
                                
                                return mostLiked;
                            };
                            
                            const mostLikedTweet = getMostLikedTweet();
                            const headlineText = mostLikedTweet 
                                ? mostLikedTweet.text 
                                : hoveredCluster.text;
                            const headlineUsername = mostLikedTweet 
                                ? mostLikedTweet.username 
                                : 'unknown';
                            
                            return (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.9, y: 10 }}
                                    animate={{ opacity: 1, scale: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.9, y: 10 }}
                                    className="absolute bottom-6 left-6 z-20 max-w-md w-96"
                                >
                                    <div className="bg-black/80 backdrop-blur-xl border border-white/10 p-4 rounded-xl shadow-2xl max-h-[500px] flex flex-col">
                                        <div className="flex justify-between items-start mb-2">
                                            <h3 className="text-white font-bold text-lg">Cluster Detected</h3>
                                            <span className="bg-alert-red/20 text-alert-red text-xs px-2 py-0.5 rounded-full border border-alert-red/30">
                                                High Severity
                                            </span>
                                        </div>
                                        <p className="text-text-secondary text-sm mb-3">
                                            {hoveredCluster.count} tweets • Popularity: {hoveredCluster.popularity_score.toFixed(1)}
                                        </p>
                                        <div className="bg-white/5 p-3 rounded-lg mb-4 border border-white/5">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-ice-cyan text-xs font-semibold">
                                                    @{headlineUsername}
                                                </span>
                                                {mostLikedTweet && (mostLikedTweet.likes || mostLikedTweet.retweets || mostLikedTweet.replies) && (
                                                    <span className="text-text-secondary text-xs">
                                                        {mostLikedTweet.likes || 0}❤️ • {mostLikedTweet.retweets || 0}🔄 • {mostLikedTweet.replies || 0}💬
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-white text-sm leading-relaxed break-words whitespace-pre-wrap">
                                                {headlineText}
                                            </p>
                                        </div>
                                    {hoveredCluster.top_tweets && hoveredCluster.top_tweets.length > 0 && (
                                        <div className="bg-white/5 p-2 rounded mb-3 border border-white/5 flex-1 min-h-0 flex flex-col">
                                            <p className="text-text-secondary text-xs mb-2 font-semibold">
                                                All Tweets ({hoveredCluster.top_tweets.length}):
                                            </p>
                                            <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar min-h-0">
                                                {hoveredCluster.top_tweets.map((tweet, idx) => (
                                                    <div key={idx} className="bg-black/30 p-2 rounded border border-white/5">
                                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                                            <span className="text-ice-cyan text-xs font-semibold">
                                                                @{typeof tweet === 'string' ? 'unknown' : tweet.username}
                                                            </span>
                                                            {typeof tweet !== 'string' && (tweet.likes || tweet.retweets || tweet.replies) && (
                                                                <span className="text-text-secondary text-xs">
                                                                    {tweet.likes || 0}❤️ • {tweet.retweets || 0}🔄 • {tweet.replies || 0}💬
                                                                </span>
                                                            )}
                                                        </div>
                                                        <p className="text-white text-xs leading-relaxed break-words">
                                                            {typeof tweet === 'string' ? tweet : tweet.text}
                                                        </p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    <NeonButton
                                        variant="primary"
                                        className="w-full flex items-center justify-center gap-2"
                                        onClick={() => onVerifyTweet(headlineText)}
                                    >
                                        Verify Now <ArrowUp size={16} />
                                    </NeonButton>
                                </div>
                            </motion.div>
                            );
                        })()}
                    </AnimatePresence>
                </AntiGravityCard>
            </motion.div>
        </div>
    );
};
