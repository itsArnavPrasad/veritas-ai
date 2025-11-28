"""
Stream manager for handling real-time tweet streams and clusters
"""
import asyncio
import logging
import threading
import uuid
from typing import Dict, Optional, Callable
from collections import deque
from datetime import datetime
from queue import Queue as ThreadQueue

import random
import hashlib

from services.nitter_scraper import scrape_nitter_search
from services.location_extraction import extract_location_llm
from services.topic_extraction import extract_topic_llm
from services.geocoding import geocode_location_cached

logger = logging.getLogger(__name__)


class StreamManager:
    """Manages active streams and their cluster queues"""
    
    def __init__(self):
        self.active_streams: Dict[str, 'TweetStream'] = {}
        self.cluster_queues: Dict[str, ThreadQueue] = {}
    
    def create_stream(self, query: str) -> str:
        """Create a new stream and return stream_id"""
        stream_id = str(uuid.uuid4())
        cluster_queue = ThreadQueue()  # Thread-safe queue
        self.cluster_queues[stream_id] = cluster_queue
        
        def cluster_callback(cluster: Dict):
            """Synchronous callback to push to thread-safe queue"""
            if stream_id in self.cluster_queues:
                self.cluster_queues[stream_id].put(cluster)
                print(f"\n📤 CLUSTER UPDATE QUEUED")
                print(f"   Cluster ID: {cluster.get('cluster_id')}")
                print(f"   Location: {cluster.get('location', 'unknown')}")
                print(f"   Coordinates: ({cluster.get('centroid_lat', 0):.4f}, {cluster.get('centroid_lon', 0):.4f})")
                print(f"   Tweet Count: {cluster.get('tweet_count', 0)}")
                print(f"   Popularity Score: {cluster.get('popularity_score', 0):.2f}")
        
        stream = TweetStream(
            stream_id=stream_id,
            query=query,
            cluster_callback=cluster_callback
        )
        self.active_streams[stream_id] = stream
        stream.start()
        
        logger.info(f"Created stream {stream_id} for query: {query}")
        print(f"\n🚀 STREAM CREATED")
        print(f"   Stream ID: {stream_id}")
        print(f"   Query: '{query}'")
        print(f"   Status: ACTIVE\n")
        return stream_id
    
    def get_cluster_queue(self, stream_id: str) -> Optional[ThreadQueue]:
        """Get cluster queue for stream"""
        return self.cluster_queues.get(stream_id)
    
    def stop_stream(self, stream_id: str):
        """Stop a stream"""
        if stream_id in self.active_streams:
            self.active_streams[stream_id].stop()
            del self.active_streams[stream_id]
        if stream_id in self.cluster_queues:
            del self.cluster_queues[stream_id]
        logger.info(f"Stopped stream {stream_id}")
    
    def is_stream_active(self, stream_id: str) -> bool:
        """Check if stream is active"""
        return stream_id in self.active_streams


# Global stream manager instance
stream_manager = StreamManager()


class TweetStream:
    """Simple tweet stream processor with clustering"""
    
    def __init__(
        self,
        stream_id: str,
        query: str,
        cluster_callback: Optional[Callable[[Dict], None]] = None
    ):
        self.stream_id = stream_id
        self.query = query
        self.cluster_callback = cluster_callback
        self.seen_ids: set = set()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # In-memory clustering: location -> cluster data
        self.clusters: Dict[str, Dict] = {}
        
    def start(self):
        """Start the stream"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_stream, daemon=True)
        self.thread.start()
        logger.info(f"Started tweet stream {self.stream_id}")
    
    def stop(self):
        """Stop the stream"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped tweet stream {self.stream_id}")
    
    def _run_stream(self):
        """Run the streaming and clustering loop"""
        try:
            for tweet in scrape_nitter_search(
                self.query,
                self.seen_ids,
                refresh_interval=120  # 2 minutes to avoid rate limiting
            ):
                if not self.running:
                    break
                
                # Process tweet
                self._process_tweet(tweet)
                
        except Exception as e:
            logger.error(f"Stream error: {e}")
            self.running = False
    
    def _process_tweet(self, tweet: Dict):
        """Process a single tweet and update clusters"""
        try:
            print(f"\n⚙️  PROCESSING TWEET")
            print(f"   Tweet ID: {tweet.get('tweet_id', 'unknown')}")
            print(f"   Text: {tweet.get('text', '')[:100]}...")
            
            # Extract location
            print(f"   🔍 Extracting location...")
            location = extract_location_llm(tweet['text'])
            print(f"   📍 Extracted location: '{location}'")
            
            if location == "unknown":
                print(f"   ⚠️  Location unknown, skipping tweet")
                return
            
            # Extract topic
            print(f"   🎯 Extracting topic...")
            topic = extract_topic_llm(tweet['text'])
            print(f"   📌 Extracted topic: '{topic}'")
            
            # Geocode
            print(f"   🌐 Geocoding location...")
            coords = geocode_location_cached(location)
            if not coords:
                print(f"   ❌ Geocoding failed, skipping tweet")
                return
            
            base_lat, base_lon = coords
            print(f"   ✅ Geocoded to: ({base_lat:.4f}, {base_lon:.4f})")
            
            # Compute popularity
            popularity = tweet['likes'] + 2 * tweet['retweets'] + 0.5 * tweet['replies']
            print(f"   📊 Popularity score: {popularity:.2f} (likes: {tweet['likes']}, RTs: {tweet['retweets']}, replies: {tweet['replies']})")
            
            # Create cluster key from topic + location (so different topics at same location are separate)
            cluster_key = f"{topic.lower()}_{location.lower()}"
            print(f"   🔑 Cluster key: '{cluster_key}'")
            
            # Calculate offset for clusters at the same location but different topics
            # Use hash of cluster_key to get consistent but different offsets
            hash_value = int(hashlib.md5(cluster_key.encode()).hexdigest()[:8], 16)
            # Offset in degrees: ~0.01 degrees ≈ 1km
            # Increased offset: ±0.02 degrees ≈ 2km separation for better visibility
            offset_lat = (hash_value % 2000 - 1000) / 50000.0  # ±0.02 degrees (~2km)
            offset_lon = ((hash_value // 2000) % 2000 - 1000) / 50000.0  # ±0.02 degrees (~2km)
            
            # Apply offset to base coordinates
            lat = base_lat + offset_lat
            lon = base_lon + offset_lon
            print(f"   📍 Final coordinates with offset: ({lat:.4f}, {lon:.4f}) [offset: ({offset_lat:.6f}, {offset_lon:.6f})]")
            
            if cluster_key not in self.clusters:
                # Create new cluster
                cluster_id = f"{self.stream_id}_{len(self.clusters)}"
                self.clusters[cluster_key] = {
                    'cluster_id': cluster_id,
                    'centroid_lat': lat,
                    'centroid_lon': lon,
                    'headline': tweet['text'][:200],  # First 200 chars
                    'top_tweets': [tweet['text']],
                    'popularity_score': popularity,
                    'last_seen': tweet['timestamp'],
                    'tweet_count': 1,
                    'location': location,
                    'topic': topic  # Store topic for reference
                }
                print(f"   ✨ Created NEW cluster: {cluster_id}")
                print(f"      Topic: {topic}")
                print(f"      Location: {location}")
                print(f"      Initial tweet count: 1")
            else:
                # Update existing cluster
                cluster = self.clusters[cluster_key]
                old_count = cluster['tweet_count']
                cluster['tweet_count'] += 1
                cluster['popularity_score'] += popularity
                cluster['last_seen'] = tweet['timestamp']
                
                # Update centroid (weighted average) - but keep the offset consistent
                # The offset is based on cluster_key hash, so it stays the same
                # We just average the base coordinates, then reapply offset
                n = cluster['tweet_count']
                # Recalculate offset (should be same since cluster_key is same)
                hash_value_cluster = int(hashlib.md5(cluster_key.encode()).hexdigest()[:8], 16)
                offset_lat_cluster = (hash_value_cluster % 2000 - 1000) / 50000.0  # ±0.02 degrees (~2km)
                offset_lon_cluster = ((hash_value_cluster // 2000) % 2000 - 1000) / 50000.0  # ±0.02 degrees (~2km)
                
                # Calculate base coordinates (remove offset from current centroid)
                base_lat_cluster = cluster['centroid_lat'] - offset_lat_cluster
                base_lon_cluster = cluster['centroid_lon'] - offset_lon_cluster
                # Average with new base coordinates
                new_base_lat = (base_lat_cluster * (n-1) + base_lat) / n
                new_base_lon = (base_lon_cluster * (n-1) + base_lon) / n
                # Reapply offset
                cluster['centroid_lat'] = new_base_lat + offset_lat_cluster
                cluster['centroid_lon'] = new_base_lon + offset_lon_cluster
                
                # Add to top tweets (keep top 3)
                cluster['top_tweets'].append(tweet['text'])
                cluster['top_tweets'] = sorted(
                    cluster['top_tweets'],
                    key=lambda t: len(t),
                    reverse=True
                )[:3]
                
                # Update headline to most popular tweet
                if popularity > cluster['popularity_score'] / cluster['tweet_count']:
                    cluster['headline'] = tweet['text'][:200]
                
                print(f"   🔄 Updated EXISTING cluster: {cluster['cluster_id']}")
                print(f"      Tweet count: {old_count} → {cluster['tweet_count']}")
                print(f"      Total popularity: {cluster['popularity_score']:.2f}")
            
            # Emit cluster update
            if self.cluster_callback:
                try:
                    print(f"   📤 Emitting cluster update...")
                    self.cluster_callback(self.clusters[cluster_key].copy())
                    print(f"   ✅ Cluster update emitted successfully")
                except Exception as e:
                    logger.error(f"Cluster callback error: {e}")
                    print(f"   ❌ Cluster callback error: {e}")
            
        except Exception as e:
            logger.error(f"Error processing tweet: {e}")
            print(f"   ❌ Error processing tweet: {e}")
            import traceback
            traceback.print_exc()

