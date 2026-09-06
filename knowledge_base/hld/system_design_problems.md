# System Design Problems — Reference Architectures

---

## URL Shortener (bit.ly)

### Scale
- 100M URLs created/day → ~1150 writes/sec
- 10:1 read/write ratio → 11,500 reads/sec

### Architecture

```
Client
  ↓
CDN (cache redirects for popular URLs)
  ↓
Load Balancer
  ↓
App Servers (stateless, horizontally scaled)
  ↓
Redis Cache (short_code → long_url, TTL 24h)
  ↓
PostgreSQL (source of truth)
```

### Short Code Generation
- Auto-increment ID → Base62 encode
- 6 characters = 62^6 ≈ 56 billion unique URLs
- Avoid sequential IDs leaking info → use hash or Snowflake ID

### Redirect Type
- 301 (Permanent) — browser caches, reduces server load, can't track clicks
- 302 (Temporary) — every redirect hits server, enables click tracking

### Database Schema
```sql
CREATE TABLE urls (
    id          BIGSERIAL PRIMARY KEY,
    short_code  VARCHAR(10) UNIQUE NOT NULL,
    long_url    TEXT NOT NULL,
    user_id     UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);
CREATE INDEX idx_short_code ON urls(short_code);
```

---

## Instagram

### Scale
- 500M DAU, 100M photos uploaded/day
- 4.2B likes/day

### Core Features
- Upload photos/videos
- Follow users
- Personalised feed
- Likes and comments

### Architecture

**Upload Flow:**
```
Client → API Gateway → Upload Service
           ↓
     Object Storage (S3-compatible)
           ↓
     CDN (CloudFront/Akamai)
     Media Processing Service (thumbnails, transcoding)
```

**Feed Generation:**

*Option 1: Pull (fan-out on read)*
- On feed request, fetch followed users' posts and merge
- Pro: simple writes; Con: slow reads for users following many people

*Option 2: Push (fan-out on write)*
- On post creation, push to each follower's feed timeline (Redis sorted set)
- Pro: fast reads; Con: celebrity problem (10M followers = 10M writes)

*Option 3: Hybrid*
- Regular users: push model
- Celebrities: pull model, merge at read time

**Database Choices:**
- Users/Follow graph: PostgreSQL
- Photos metadata: Cassandra (write-heavy, time-ordered)
- Feeds/timelines: Redis sorted sets (score = timestamp)
- Media storage: S3 + CDN

---

## Chat Application (WhatsApp)

### Scale
- 2B users, 100B messages/day

### Architecture

**Connection:**
- WebSocket persistent connections to chat servers
- Connection stored in connection registry (Redis): `user_id → server_id`

**Message Flow:**
```
Sender → Chat Server A
           ↓
     Message Queue (Kafka)
           ↓
     Chat Server B → Receiver (via WebSocket)
           ↓
     Message DB (Cassandra)
```

**Message Storage:**
- Cassandra: partition key = `(user1_id, user2_id)`, clustering = `timestamp DESC`
- Fast reads for conversation history

**Delivery Guarantees:**
- At-least-once delivery
- Message acknowledgement (single tick → double tick → blue tick)
- Offline: store in DB, deliver on reconnect

---

## Netflix / YouTube (Video Streaming)

### Architecture

**Upload:**
```
Uploader → Raw Storage (S3)
              ↓
       Transcoding Service (async workers)
       Generate: 360p, 720p, 1080p, 4K
              ↓
       Processed Storage (S3)
              ↓
           CDN
```

**Streaming:**
```
User → DNS → nearest CDN PoP → video chunks (adaptive bitrate)
```

**Adaptive Bitrate Streaming (ABR):** 
- Video split into segments (2-4s each)
- Client player switches quality based on available bandwidth
- Format: HLS or MPEG-DASH

**Recommendation System:**
- Collaborative filtering (users who watched X also watched Y)
- Content-based filtering (same genre/actors)
- A/B testing for recommendation models

---

## Uber / Lyft (Ride Sharing)

### Architecture

**Matching:**
```
Rider request → Location Service
                    ↓
              Quadtree / Geohash index
                    ↓
              Find nearby drivers (< 5km)
                    ↓
              Matching Service (assign optimal driver)
```

**Real-time Location Updates:**
- Drivers send GPS updates every 4 seconds
- Store in Redis with geospatial index: `GEOADD drivers lon lat driver_id`
- Find nearby: `GEORADIUSBYMEMBER`

**Trip Management:**
- State machine: `REQUESTED → ACCEPTED → EN_ROUTE → ARRIVED → IN_TRIP → COMPLETED`
- Kafka for trip events → Analytics, Billing, Notifications

---

## Rate Limiter

### Algorithms

**Token Bucket:**
- Bucket with capacity N, refills at rate R tokens/second
- Request takes a token; if empty, reject
- Allows bursts up to bucket capacity

**Sliding Window Log:**
- Store timestamps of each request in Redis sorted set
- Remove entries outside window
- Count remaining = current rate

**Sliding Window Counter (approximate):**
```
current_rate = prev_window_count × overlap_ratio + curr_window_count
```

### Distributed Implementation
```python
# Redis Lua script — atomic
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local count = redis.call('INCR', key)
if count == 1 then redis.call('EXPIRE', key, window) end
if count > limit then return 0 end
return 1
```

---

## Google Drive / Dropbox

### Architecture

**Upload:**
- Chunked upload (5MB chunks)
- Deduplication via content hash (SHA-256)
- Delta sync — only upload changed chunks

**Sync:**
```
Client (local FS watch)
  ↓
Sync Client (detects changes, chunks files)
  ↓
Upload API → Chunk Storage (S3)
  ↓
Metadata DB (PostgreSQL) — stores file tree, chunk references
  ↓
Notification Service → Other clients sync
```

**Database Schema:**
```sql
-- Files table
id, user_id, name, parent_folder_id, size, content_hash, version, updated_at

-- Chunks table
chunk_hash, storage_path, size

-- File_Chunks table
file_id, chunk_index, chunk_hash
```
