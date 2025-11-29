# Pathway Framework, Map Visualization, and Twitter Integration

## Overview

This document provides a comprehensive guide to the Pathway-based real-time Twitter streaming, clustering, and map visualization system implemented in VeritasAI. The system enables real-time monitoring of Twitter/X content, extracts location and topic information, clusters related tweets, and visualizes them on an interactive map.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Pathway Framework Implementation](#pathway-framework-implementation)
3. [Twitter Scraping (Nitter)](#twitter-scraping-nitter)
4. [Location & Topic Extraction](#location--topic-extraction)
5. [Geocoding Service](#geocoding-service)
6. [Stream Management](#stream-management)
7. [Clustering Algorithm](#clustering-algorithm)
8. [Map Visualization (Frontend)](#map-visualization-frontend)
9. [API Endpoints](#api-endpoints)
10. [Data Flow](#data-flow)
11. [Configuration & Setup](#configuration--setup)

---

## Architecture Overview

The system follows a **real-time streaming architecture** with the following components:

```
┌─────────────────┐
│  Frontend (React)│
│  TwitterMapSection│
└────────┬─────────┘
         │ SSE (Server-Sent Events)
         ▼
┌─────────────────┐
│  FastAPI Backend │
│  Stream Router   │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│ Stream Manager  │
│  (TweetStream)  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────────┐
│ Nitter │ │ LLM Services │
│ Scraper│ │ (Gemini API) │
└───┬────┘ └──────┬───────┘
    │             │
    ▼             ▼
┌─────────────────────┐
│  Tweet Processing   │
│  - Location Extract │
│  - Topic Extract    │
│  - Geocoding        │
│  - Clustering       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Cluster Updates    │
│  (via Queue)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SSE Stream to       │
│  Frontend            │
└─────────────────────┘
```

### Key Components

1. **Frontend (`TwitterMapSection.tsx`)**: React component with Mapbox GL and Deck.gl for map visualization
2. **Backend API (`routers/stream.py`)**: FastAPI endpoints for stream management and SSE
3. **Stream Manager (`services/stream_manager.py`)**: Manages active streams and cluster queues
4. **Tweet Stream (`services/stream_manager.py::TweetStream`)**: Processes tweets and creates clusters
5. **Nitter Scraper (`services/nitter_scraper.py`)**: Scrapes Twitter/X via Nitter instances
6. **Location Extraction (`services/location_extraction.py`)**: Uses Gemini LLM to extract locations
7. **Topic Extraction (`services/topic_extraction.py`)**: Uses Gemini LLM to extract topics
8. **Geocoding (`services/geocoding.py`)**: Converts location strings to coordinates

---

## Pathway Framework Implementation

### Overview

The system includes a **Pathway-based implementation** (`services/pathway_stream.py`) that provides an alternative processing pipeline using the Pathway streaming data framework. While the current production system uses a simpler `TweetStream` implementation, the Pathway version demonstrates how to use Pathway for real-time data processing.

### Pathway Components

#### 1. **TweetScraperSubject** (ConnectorSubject)

A Pathway connector subject that wraps the Nitter scraper:

```python
class TweetScraperSubject(ConnectorSubject):
    """Pathway connector subject for Nitter tweet scraping"""
    
    def __init__(self, query: str, seen_ids: set, refresh_interval: int = 10):
        super().__init__()
        self.query = query
        self.seen_ids = seen_ids
        self.refresh_interval = refresh_interval
    
    def run(self) -> None:
        """Run the scraper and emit tweets"""
        for tweet in scrape_nitter_search(...):
            self.next(
                tweet_id=tweet['tweet_id'],
                text=tweet['text'],
                username=tweet['username'],
                # ... other fields
            )
```

**Purpose**: Acts as a Pathway input connector, converting the Nitter scraper generator into Pathway-compatible data streams.

#### 2. **TweetSchema**

Defines the schema for tweet data in Pathway:

```python
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
```

#### 3. **User-Defined Functions (UDFs)**

Pathway UDFs for data transformation:

- **`extract_location_udf`**: Extracts location from tweet text using LLM
- **`geocode_location_udf`**: Converts location strings to coordinates (returns JSON string)
- **`compute_popularity`**: Calculates popularity score: `likes + 2*retweets + 0.5*replies`
- **`parse_coords`**: Parses coordinates from JSON string

#### 4. **PathwayStreamProcessor**

The main Pathway processing pipeline:

```python
class PathwayStreamProcessor:
    def _run_pathway(self):
        # 1. Create connector subject
        subject = TweetScraperSubject(...)
        
        # 2. Read tweets into Pathway table
        tweets = pw.io.python.read(subject, schema=TweetSchema)
        
        # 3. Enrich with location
        tweets_with_location = tweets.select(
            *pw.this,
            location=extract_location_udf(pw.this.text)
        )
        
        # 4. Geocode locations
        tweets_with_coords_json = tweets_with_location.select(
            *pw.this,
            coords_json=geocode_location_udf(pw.this.location)
        )
        
        # 5. Filter out tweets without coordinates
        geocoded_tweets = tweets_with_coords_json.filter(
            pw.this.coords_json != ""
        )
        
        # 6. Parse coordinates
        tweets_with_coords = geocoded_tweets.select(
            *pw.this,
            coords=parse_coords(pw.this.coords_json)
        ).filter(pw.this.coords.is_not_none())
        
        # 7. Add popularity score
        tweets_with_popularity = tweets_with_coords.select(
            *pw.this,
            popularity=compute_popularity(...)
        )
        
        # 8. Cluster by location
        clusters = tweets_with_popularity.groupby(
            location=pw.this.location
        ).reduce(
            centroid_lat=pw.reducers.avg(pw.this.coords[0]),
            centroid_lon=pw.reducers.avg(pw.this.coords[1]),
            popularity_score=pw.reducers.sum(pw.this.popularity),
            tweet_count=pw.reducers.count(),
            last_seen=pw.reducers.max(pw.this.timestamp),
            top_tweet=pw.reducers.sorted_tuple(...)
        )
        
        # 9. Format and send to backend
        clusters_formatted = clusters.select(...)
        pw.io.http.write(clusters_formatted, cluster_endpoint, method="POST")
        
        # 10. Run Pathway
        pw.run(monitoring_level=pw.MonitoringLevel.NONE)
```

**Key Features**:
- **Incremental Processing**: Pathway automatically handles updates and incremental computation
- **Declarative Pipeline**: Data transformations are defined declaratively
- **Automatic Optimization**: Pathway optimizes the computation graph
- **HTTP Output**: Clusters are sent to backend via HTTP connector

### Pathway vs. Current Implementation

| Feature | Pathway Implementation | Current Implementation |
|---------|----------------------|----------------------|
| **Processing Model** | Declarative dataflow | Imperative Python |
| **Incremental Updates** | Automatic | Manual |
| **Scalability** | Distributed-ready | Single-threaded |
| **Complexity** | Higher (learning curve) | Lower (simpler) |
| **Performance** | Optimized by Pathway | Depends on implementation |
| **State Management** | Pathway-managed | Manual in-memory dict |

**Note**: The current production system uses the simpler `TweetStream` implementation for easier debugging and maintenance, but the Pathway version is available for future scaling.

---

## Twitter Scraping (Nitter)

### Overview

Since Twitter/X requires API keys and has strict rate limits, the system uses **Nitter** (an open-source Twitter frontend) to scrape public tweets without authentication.

### Implementation (`services/nitter_scraper.py`)

#### 1. **Multiple Nitter Instances**

The system maintains a list of Nitter instances for redundancy:

```python
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.it",
    "https://nitter.42l.fr",
    # ... more instances
]
```

**Purpose**: If one instance is blocked or down, the system automatically switches to another.

#### 2. **Selenium-Based Scraping**

Uses Selenium with Chrome (headless) to render JavaScript and scrape dynamic content:

```python
def setup_selenium_driver(headless: bool = True):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # ... anti-detection measures
    return webdriver.Chrome(options=chrome_options)
```

**Anti-Detection Measures**:
- Randomized User-Agents
- Removes `navigator.webdriver` property
- Realistic browser headers
- Rate limiting (120 seconds between requests)

#### 3. **Tweet Parsing**

Parses HTML from Nitter search results:

```python
def parse_tweet_from_timeline_item(timeline_item, base_url: str) -> Dict:
    """Extracts:
    - tweet_id (from URL)
    - text (tweet content)
    - username
    - timestamp
    - likes, retweets, replies
    - media_urls
    """
```

**Key Parsing Logic**:
- Finds `timeline-item` divs in search results
- Extracts tweet body, stats, and metadata
- Handles both search results and individual tweet pages
- Converts relative URLs to absolute

#### 4. **Continuous Streaming**

The scraper runs in a loop, continuously fetching new tweets:

```python
def scrape_nitter_search_selenium(...) -> Generator[Dict, None, None]:
    while True:
        # 1. Navigate to search URL
        driver.get(search_url)
        
        # 2. Wait for timeline to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "timeline"))
        )
        
        # 3. Parse HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        timeline_items = soup.find_all('div', class_='timeline-item')
        
        # 4. Yield new tweets
        for item in timeline_items:
            tweet_data = parse_tweet_from_timeline_item(item)
            if tweet_id not in seen_ids:
                seen_ids.add(tweet_id)
                yield tweet_data
        
        # 5. Wait before next request (rate limiting)
        time.sleep(refresh_interval)
```

**Rate Limiting**: 120 seconds between requests to avoid blocking.

---

## Location & Topic Extraction

### Location Extraction (`services/location_extraction.py`)

Uses **Google Gemini LLM** to intelligently extract locations from tweet text.

#### Prompt Strategy

The system uses a sophisticated prompt that considers:
1. **Explicit locations**: Direct mentions of cities, states, countries
2. **Context clues**: Organizations, institutions, events
   - "IIT Bombay" → Mumbai, India
   - "NIA" → India
3. **Implicit locations**: Events in specific countries
   - "13 Syrians killed" → Syria
4. **News context**: International events → relevant countries

#### Implementation

```python
def extract_location_llm(text: str) -> str:
    prompt = f"""Analyze this tweet and determine the most likely real-world location...
    [Detailed prompt with examples]
    """
    
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,  # Slightly creative for inference
            "max_output_tokens": 100,
        }
    )
    
    location = response.text.strip().lower()
    # Normalize and clean
    return _normalize_location(location)
```

#### Fallback Strategy

If Gemini fails or is unavailable, falls back to keyword matching:

```python
def _fallback_keyword_extraction(text: str) -> str:
    location_keywords = {
        "mumbai": "mumbai",
        "bombay": "mumbai",
        "delhi": "delhi",
        # ... extensive keyword list
    }
    # Match keywords in text
```

### Topic Extraction (`services/topic_extraction.py`)

Similar approach using Gemini to extract topics/themes:

```python
def extract_topic_llm(text: str) -> str:
    """Extracts topic like 'bomb blast', 'employment', 'protest'"""
    prompt = f"""Extract the main topic/theme (1-3 words max)...
    """
    # Returns: "bomb blast", "employment", "general", etc.
```

**Purpose**: Topics are used to create separate clusters for different topics at the same location (e.g., "bomb blast in Mumbai" vs. "employment in Mumbai" are separate clusters).

---

## Geocoding Service

### Overview (`services/geocoding.py`)

Converts location strings (e.g., "mumbai", "delhi") to latitude/longitude coordinates using **Nominatim** (OpenStreetMap geocoding service).

### Implementation

```python
@lru_cache(maxsize=1000)
def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """Geocodes location using Nominatim API"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    headers = {"User-Agent": "VeritasAI/1.0"}  # Required by Nominatim
    
    response = requests.get(url, params=params, headers=headers, timeout=10)
    data = response.json()
    
    if data:
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)
    return None
```

### Caching

- **LRU Cache**: In-memory cache with 1000 entries
- **Persistent Cache**: Additional in-memory dictionary for faster lookups
- **Rate Limiting**: 1.1 seconds between requests (Nominatim allows 1 req/sec)

### Error Handling

- Returns `None` if geocoding fails
- Logs warnings for debugging
- Handles network errors gracefully

---

## Stream Management

### StreamManager (`services/stream_manager.py`)

Manages multiple active streams and their cluster queues:

```python
class StreamManager:
    def __init__(self):
        self.active_streams: Dict[str, 'TweetStream'] = {}
        self.cluster_queues: Dict[str, ThreadQueue] = {}
    
    def create_stream(self, query: str) -> str:
        """Creates a new stream and returns stream_id"""
        stream_id = str(uuid.uuid4())
        cluster_queue = ThreadQueue()  # Thread-safe queue
        
        stream = TweetStream(stream_id, query, cluster_callback)
        self.active_streams[stream_id] = stream
        stream.start()
        
        return stream_id
```

**Key Features**:
- **Thread-Safe Queues**: Uses `queue.Queue` for thread-safe communication
- **Stream Lifecycle**: Tracks active streams and cleans up on stop
- **Callback System**: Each stream has a callback to push clusters to its queue

### TweetStream

The main processing class that handles tweet streaming and clustering:

```python
class TweetStream:
    def __init__(self, stream_id: str, query: str, cluster_callback: Callable):
        self.stream_id = stream_id
        self.query = query
        self.cluster_callback = cluster_callback
        self.seen_ids: set = set()  # Deduplication
        self.clusters: Dict[str, Dict] = {}  # In-memory clusters
    
    def _run_stream(self):
        """Main streaming loop"""
        for tweet in scrape_nitter_search(self.query, self.seen_ids):
            if not self.running:
                break
            self._process_tweet(tweet)
    
    def _process_tweet(self, tweet: Dict):
        """Processes a single tweet and updates clusters"""
        # 1. Extract location
        location = extract_location_llm(tweet['text'])
        
        # 2. Extract topic
        topic = extract_topic_llm(tweet['text'])
        
        # 3. Geocode
        coords = geocode_location_cached(location)
        
        # 4. Compute popularity
        popularity = tweet['likes'] + 2 * tweet['retweets'] + 0.5 * tweet['replies']
        
        # 5. Create/update cluster
        cluster_key = f"{topic.lower()}_{location.lower()}"
        # ... clustering logic
```

---

## Clustering Algorithm

### Cluster Key Strategy

Clusters are identified by a **composite key** combining topic and location:

```python
cluster_key = f"{topic.lower()}_{location.lower()}"
# Example: "bomb blast_mumbai"
```

**Why**: Different topics at the same location should be separate clusters (e.g., "bomb blast in Mumbai" vs. "employment in Mumbai").

### Coordinate Offset

To prevent overlapping clusters at the same location, the system applies a **deterministic offset** based on the cluster key hash:

```python
hash_value = int(hashlib.md5(cluster_key.encode()).hexdigest()[:8], 16)
offset_lat = (hash_value % 2000 - 1000) / 50000.0  # ±0.02 degrees (~2km)
offset_lon = ((hash_value // 2000) % 2000 - 1000) / 50000.0

lat = base_lat + offset_lat
lon = base_lon + offset_lon
```

**Purpose**: Ensures clusters at the same location but different topics are visually separated on the map (~2km apart).

### Cluster Data Structure

```python
cluster = {
    'cluster_id': f"{stream_id}_{len(clusters)}",
    'centroid_lat': lat,
    'centroid_lon': lon,
    'headline': tweet['text'],  # Full text of most-liked tweet
    'headline_username': tweet['username'],
    'top_tweets': [tweet_obj, ...],  # All tweets, sorted by popularity
    'popularity_score': sum of all tweet popularities,
    'last_seen': latest tweet timestamp,
    'tweet_count': number of tweets,
    'location': location,
    'topic': topic
}
```

### Cluster Updates

When a new tweet matches an existing cluster:

1. **Increment tweet count**
2. **Add popularity score**
3. **Update centroid** (weighted average of coordinates)
4. **Add tweet to top_tweets list** (sorted by popularity)
5. **Update headline** to most-liked tweet
6. **Emit cluster update** via callback

---

## Map Visualization (Frontend)

### Component: `TwitterMapSection.tsx`

A React component that visualizes tweet clusters on an interactive map.

### Technologies

- **Mapbox GL JS** (`react-map-gl`): Base map rendering
- **Deck.gl** (`@deck.gl/mapbox`): High-performance data visualization overlay
- **ScatterplotLayer**: Renders clusters as circles on the map

### Implementation

#### 1. **State Management**

```typescript
const [clusters, setClusters] = useState<Map<string, TweetCluster>>(new Map());
const [streamId, setStreamId] = useState<string | null>(null);
const [isStreaming, setIsStreaming] = useState(false);
const [viewState, setViewState] = useState({
    longitude: 78.9629,  // India center
    latitude: 20.5937,
    zoom: 3.5
});
```

#### 2. **Server-Sent Events (SSE) Connection**

```typescript
const eventSource = new EventSource(`${API_BASE_URL}/api/v1/stream/${streamId}`);

eventSource.onmessage = (event) => {
    const update: ClusterUpdate = JSON.parse(event.data);
    
    if (update.type === "cluster_update" && update.cluster) {
        // Update clusters map
        setClusters((prev) => {
            const newMap = new Map(prev);
            newMap.set(cluster.cluster_id, tweetCluster);
            return newMap;
        });
    }
};
```

#### 3. **Deck.gl ScatterplotLayer**

```typescript
const layers = [
    new ScatterplotLayer({
        id: "tweet-clusters",
        data: clusterArray,
        getPosition: (d: TweetCluster) => d.coordinates,
        getRadius: (d: TweetCluster) => Math.min(100 + (d.count * 20), 500),
        getFillColor: (d: TweetCluster) => getClusterColor(d.cluster_id),
        pickable: true,
        opacity: 0.8,
        onHover: (info) => {
            if (info.object) {
                setHoveredCluster(info.object);
            }
        }
    })
];
```

**Features**:
- **Dynamic Radius**: Based on tweet count (larger = more tweets)
- **Color Coding**: Consistent colors per cluster (based on cluster_id hash)
- **Hover Interaction**: Shows tooltip with cluster details

#### 4. **Cluster Color Generation**

```typescript
const getClusterColor = (clusterId: string): [number, number, number] => {
    // Hash cluster_id for consistency
    let hash = 0;
    for (let i = 0; i < clusterId.length; i++) {
        hash = ((hash << 5) - hash) + clusterId.charCodeAt(i);
    }
    
    // Use golden ratio for hue spacing (maximizes color separation)
    const goldenRatio = 0.618033988749895;
    const hue = (Math.abs(hash) * goldenRatio) % 360;
    const saturation = 80 + (Math.abs(hash >> 8) % 20);  // 80-100%
    const lightness = 55 + (Math.abs(hash >> 16) % 20);   // 55-75%
    
    // Convert HSL to RGB
    return hslToRgb(hue, saturation, lightness);
};
```

**Purpose**: Generates vibrant, distinguishable colors that are consistent for the same cluster.

#### 5. **Hover Tooltip**

Shows detailed cluster information on hover:
- Cluster ID and severity
- Tweet count and popularity score
- Headline tweet (most-liked)
- All tweets in cluster (scrollable)
- "Verify Now" button to trigger verification

---

## API Endpoints

### Stream Management (`routers/stream.py`)

#### 1. **POST `/api/v1/start_stream`**

Starts a new tweet stream for a query.

**Request**:
```json
{
    "query": "bomb blast"
}
```

**Response**:
```json
{
    "stream_id": "uuid-string"
}
```

**Implementation**:
```python
@router.post("/start_stream")
async def start_stream(request: StartStreamRequest):
    stream_id = stream_manager.create_stream(request.query)
    return {"stream_id": stream_id}
```

#### 2. **POST `/api/v1/stop_stream`**

Stops an active stream.

**Request**:
```json
{
    "stream_id": "uuid-string"
}
```

**Response**:
```json
{
    "status": "stopped",
    "stream_id": "uuid-string"
}
```

#### 3. **GET `/api/v1/stream/{stream_id}`**

Server-Sent Events (SSE) endpoint for real-time cluster updates.

**Response Format**:
```
data: {"type": "connected", "stream_id": "..."}

data: {"type": "cluster_update", "stream_id": "...", "cluster": {...}}

: heartbeat
```

**Implementation**:
```python
@router.get("/stream/{stream_id}")
async def stream_clusters(stream_id: str):
    async def cluster_event_generator():
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        
        while stream_manager.is_stream_active(stream_id):
            cluster = cluster_queue.get(timeout=1.0)
            yield f"data: {json.dumps({'type': 'cluster_update', 'cluster': cluster})}\n\n"
    
    return StreamingResponse(
        cluster_event_generator(),
        media_type="text/event-stream"
    )
```

#### 4. **POST `/api/v1/_clusters/{stream_id}`** (Internal)

Internal endpoint for Pathway to send cluster updates (if using Pathway implementation).

---

## Data Flow

### Complete Flow Diagram

```
1. User enters query in frontend
   ↓
2. Frontend calls POST /api/v1/start_stream
   ↓
3. Backend creates TweetStream and starts scraping
   ↓
4. Nitter scraper fetches tweets (every 120 seconds)
   ↓
5. For each new tweet:
   a. Extract location (Gemini LLM)
   b. Extract topic (Gemini LLM)
   c. Geocode location → coordinates
   d. Compute popularity score
   e. Create/update cluster
   f. Push cluster to queue
   ↓
6. SSE endpoint reads from queue
   ↓
7. Frontend receives cluster update via SSE
   ↓
8. Frontend updates map with new/updated cluster
   ↓
9. User hovers over cluster → tooltip shows details
   ↓
10. User clicks "Verify Now" → triggers verification
```

### Threading Model

- **Main Thread**: FastAPI event loop (handles HTTP requests)
- **TweetStream Thread**: Background thread running scraper loop
- **Queue Communication**: Thread-safe `queue.Queue` for cluster updates
- **SSE Generator**: Async generator reading from queue

---

## Configuration & Setup

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional
VITE_API_URL=http://localhost:8000  # Frontend API URL
```

### Dependencies

#### Backend (`requirements.txt`)
```
pathway>=0.27.0
fastapi
uvicorn
selenium
beautifulsoup4
google-generativeai
requests
python-dotenv
```

#### Frontend (`package.json`)
```json
{
    "dependencies": {
        "react-map-gl": "^7.x",
        "@deck.gl/mapbox": "^9.x",
        "@deck.gl/layers": "^9.x",
        "mapbox-gl": "^3.x",
        "framer-motion": "^10.x"
    }
}
```

### Setup Steps

1. **Install Backend Dependencies**:
   ```bash
   cd veritas-ai-backend
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd veritas-ai-frontend
   npm install
   ```

3. **Set Environment Variables**:
   ```bash
   export GEMINI_API_KEY=your_key
   ```

4. **Install ChromeDriver** (for Selenium):
   ```bash
   # macOS
   brew install chromedriver
   
   # Linux
   sudo apt-get install chromium-chromedriver
   ```

5. **Start Backend**:
   ```bash
   cd veritas-ai-backend
   uvicorn main:app --reload
   ```

6. **Start Frontend**:
   ```bash
   cd veritas-ai-frontend
   npm run dev
   ```

### Mapbox Token

The frontend uses a Mapbox token (hardcoded in `TwitterMapSection.tsx`). For production, move this to environment variables:

```typescript
const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || "default_token";
```

---

## Performance Considerations

### Rate Limiting

- **Nitter Scraping**: 120 seconds between requests
- **Geocoding**: 1.1 seconds between requests (Nominatim limit)
- **Gemini API**: No explicit rate limiting, but requests are sequential

### Caching

- **Geocoding**: LRU cache (1000 entries) + persistent in-memory cache
- **Seen Tweet IDs**: In-memory set per stream (prevents duplicates)

### Scalability

- **Current Implementation**: Single-threaded per stream (suitable for moderate load)
- **Pathway Implementation**: Designed for distributed processing (future scaling)

### Memory Management

- **Clusters**: Stored in-memory per stream (cleaned up on stream stop)
- **Tweet Lists**: All tweets stored in cluster (consider limiting for very large clusters)

---

## Troubleshooting

### Common Issues

1. **No tweets appearing**:
   - Check Nitter instance availability
   - Verify query is valid
   - Check Selenium/ChromeDriver installation

2. **Geocoding failures**:
   - Verify Nominatim API is accessible
   - Check rate limiting (1 req/sec)
   - Review location extraction logs

3. **SSE connection drops**:
   - Check network connectivity
   - Verify stream is still active
   - Review backend logs for errors

4. **Map not rendering**:
   - Verify Mapbox token is valid
   - Check browser console for errors
   - Ensure Deck.gl layers are properly configured

---

## Future Enhancements

1. **Pathway Integration**: Migrate to Pathway for better scalability
2. **Sentiment Analysis**: Add sentiment to clusters
3. **Time-based Filtering**: Filter clusters by recency
4. **Cluster Merging**: Merge nearby clusters with similar topics
5. **Real-time Alerts**: Notify users of high-severity clusters
6. **Historical View**: Time slider to view clusters at different times
7. **Export Functionality**: Export clusters as JSON/CSV

---

## References

- [Pathway Documentation](https://pathway.com/developers)
- [Nitter Instances](https://github.com/zedeus/nitter/wiki/Instances)
- [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/)
- [Deck.gl Documentation](https://deck.gl/docs)
- [Nominatim Geocoding](https://nominatim.org/release-docs/develop/api/Overview/)

---

## License

This implementation is part of the VeritasAI project.

