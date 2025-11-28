"""
Pathway streaming service for real-time tweet processing and clustering
"""
import os
import logging
import threading
import time
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import uuid

import pathway as pw
from pathway.io.python import ConnectorSubject

from services.nitter_scraper import scrape_nitter_search
from services.location_extraction import extract_location_llm
from services.geocoding import geocode_location_cached

logger = logging.getLogger(__name__)

# Try to import embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class TweetScraperSubject(ConnectorSubject):
    """Pathway connector subject for Nitter tweet scraping"""
    
    def __init__(
        self,
        query: str,
        seen_ids: set,
        refresh_interval: int = 10,
    ) -> None:
        super().__init__()
        self.query = query
        self.seen_ids = seen_ids
        self.refresh_interval = refresh_interval
    
    def run(self) -> None:
        """Run the scraper and emit tweets"""
        for tweet in scrape_nitter_search(
            self.query,
            self.seen_ids,
            self.refresh_interval
        ):
            self.next(
                tweet_id=tweet['tweet_id'],
                text=tweet['text'],
                username=tweet['username'],
                timestamp=tweet['timestamp'],
                likes=tweet['likes'],
                retweets=tweet['retweets'],
                replies=tweet['replies'],
                tweet_url=tweet['tweet_url'],
                media_urls=json.dumps(tweet['media_urls']),
            )


class TweetSchema(pw.Schema):
    """Schema for tweet data"""
    tweet_id: str = pw.column_definition(primary_key=True)
    text: str
    username: str
    timestamp: str
    likes: int
    retweets: int
    replies: int
    tweet_url: str
    media_urls: str


# Global embedding model (lazy loaded)
_embedding_model = None


def get_embedding_model():
    """Get or create embedding model"""
    global _embedding_model
    if _embedding_model is None:
        if EMBEDDINGS_AVAILABLE:
            try:
                _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence-transformers model")
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformers: {e}")
                _embedding_model = False
        else:
            _embedding_model = False
    return _embedding_model if _embedding_model else None


@pw.udf
def extract_location_udf(text: str) -> str:
    """UDF for location extraction"""
    try:
        return extract_location_llm(text)
    except Exception as e:
        logger.warning(f"Location extraction error: {e}")
        return "unknown"


@pw.udf
def geocode_location_udf(location: str) -> str:
    """UDF for geocoding - returns JSON string of [lat, lon] or empty"""
    if not location or location == "unknown":
        return ""
    try:
        result = geocode_location_cached(location)
        if result:
            return json.dumps([result[0], result[1]])
        return ""
    except Exception as e:
        logger.warning(f"Geocoding error: {e}")
        return ""


@pw.udf
def compute_popularity(likes: int, retweets: int, replies: int) -> float:
    """Compute popularity score"""
    return float(likes + 2 * retweets + 0.5 * replies)


@pw.udf
def parse_coords(coords_json: str) -> tuple[float, float] | None:
    """Parse coordinates from JSON string"""
    if not coords_json:
        return None
    try:
        coords = json.loads(coords_json)
        return (float(coords[0]), float(coords[1]))
    except:
        return None


class PathwayStreamProcessor:
    """Pathway stream processor for tweets - simplified version"""
    
    def __init__(
        self,
        query: str,
        stream_id: str,
        backend_url: str = "http://localhost:8000",
        cluster_callback: Optional[Callable[[Dict], None]] = None
    ):
        self.query = query
        self.stream_id = stream_id
        self.backend_url = backend_url
        self.cluster_callback = cluster_callback
        self.seen_ids: set = set()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the Pathway processing"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_pathway, daemon=True)
        self.thread.start()
        logger.info(f"Started Pathway processor for stream {self.stream_id}")
    
    def stop(self):
        """Stop the Pathway processing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped Pathway processor for stream {self.stream_id}")
    
    def _run_pathway(self):
        """Run Pathway processing pipeline"""
        try:
            # Create connector subject
            subject = TweetScraperSubject(
                query=self.query,
                seen_ids=self.seen_ids,
                refresh_interval=10
            )
            
            # Read tweets into Pathway table
            tweets = pw.io.python.read(subject, schema=TweetSchema)
            
            # Enrich tweets with location
            tweets_with_location = tweets.select(
                *pw.this,
                location=extract_location_udf(pw.this.text)
            )
            
            # Geocode locations (returns JSON string)
            tweets_with_coords_json = tweets_with_location.select(
                *pw.this,
                coords_json=geocode_location_udf(pw.this.location)
            )
            
            # Filter out tweets without coordinates
            geocoded_tweets = tweets_with_coords_json.filter(
                pw.this.coords_json != ""
            )
            
            # Parse coordinates
            tweets_with_coords = geocoded_tweets.select(
                *pw.this,
                coords=parse_coords(pw.this.coords_json)
            ).filter(
                pw.this.coords.is_not_none()
            )
            
            # Add popularity score
            tweets_with_popularity = tweets_with_coords.select(
                *pw.this,
                popularity=compute_popularity(
                    pw.this.likes,
                    pw.this.retweets,
                    pw.this.replies
                )
            )
            
            # Simple clustering: group by location
            # Create location-based clusters
            clusters = tweets_with_popularity.groupby(
                location=pw.this.location
            ).reduce(
                centroid_lat=pw.reducers.avg(pw.this.coords[0]),
                centroid_lon=pw.reducers.avg(pw.this.coords[1]),
                popularity_score=pw.reducers.sum(pw.this.popularity),
                tweet_count=pw.reducers.count(),
                last_seen=pw.reducers.max(pw.this.timestamp),
                top_tweet=pw.reducers.sorted_tuple(pw.this.text, key=pw.this.popularity, reverse=True, limit=1)
            )
            
            # Add cluster ID and format
            clusters_formatted = clusters.select(
                cluster_id=pw.apply(
                    lambda loc: f"{self.stream_id}_{hash(loc) % 1000000}",
                    pw.this.location
                ),
                stream_id=pw.apply(lambda: self.stream_id),
                centroid_lat=pw.this.centroid_lat,
                centroid_lon=pw.this.centroid_lon,
                headline=pw.apply(
                    lambda tweets: tweets[0] if tweets and len(tweets) > 0 else "No headline",
                    pw.this.top_tweet
                ),
                top_tweets=pw.apply(
                    lambda tweets: json.dumps(list(tweets[:3]) if tweets else []),
                    pw.this.top_tweet
                ),
                popularity_score=pw.this.popularity_score,
                last_seen=pw.this.last_seen,
                tweet_count=pw.this.tweet_count
            )
            
            # Send clusters to backend via HTTP
            cluster_endpoint = f"{self.backend_url}/api/v1/_clusters/{self.stream_id}"
            pw.io.http.write(
                clusters_formatted,
                cluster_endpoint,
                method="POST",
                format="json"
            )
            
            # Run Pathway
            pw.run(monitoring_level=pw.MonitoringLevel.NONE)
            
        except Exception as e:
            logger.error(f"Pathway processing error: {e}")
            import traceback
            traceback.print_exc()
            self.running = False


def create_pathway_stream(
    query: str,
    stream_id: str,
    backend_url: str = "http://localhost:8000",
    cluster_callback: Optional[Callable[[Dict], None]] = None
) -> PathwayStreamProcessor:
    """
    Create and return a Pathway stream processor
    
    Args:
        query: Search query
        stream_id: Unique stream ID
        backend_url: Backend API URL
        cluster_callback: Callback function for cluster updates (optional)
    
    Returns:
        PathwayStreamProcessor instance
    """
    processor = PathwayStreamProcessor(query, stream_id, backend_url, cluster_callback)
    return processor

