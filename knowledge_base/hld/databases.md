# Databases for System Design

---

## SQL vs NoSQL — Decision Framework

| Factor | SQL (Relational) | NoSQL |
|---|---|---|
| Data structure | Structured, tabular | Flexible, schema-less |
| Relationships | Strong FK relationships | Denormalised / embedded |
| ACID | Full ACID | Often BASE |
| Scaling | Vertical (primarily) | Horizontal |
| Query | Complex joins, aggregations | Simple key-based or document |
| Consistency | Strong | Tunable (eventual to strong) |
| Use cases | Finance, e-commerce, CRM | Social feeds, IoT, catalogs, caches |

**Choose SQL when:**
- Data has clear relationships (users → orders → items)
- You need ACID transactions (payments, inventory)
- Complex reporting queries
- Team knows SQL well

**Choose NoSQL when:**
- Flexible or evolving schema
- Massive write throughput (time-series, logs)
- Simple access patterns (lookup by key)
- Horizontal scaling is required from day one

---

## ACID Properties

**Atomicity:** Transaction succeeds completely or fails completely — no partial updates.

**Consistency:** Transaction brings DB from one valid state to another. All defined rules/constraints are satisfied.

**Isolation:** Concurrent transactions produce results as if they executed serially.
- Isolation levels: READ UNCOMMITTED → READ COMMITTED → REPEATABLE READ → SERIALIZABLE (increasing isolation, decreasing concurrency)

**Durability:** Committed transactions survive crashes. Written to WAL (Write-Ahead Log) before confirming to client.

---

## Indexes

**B-Tree Index:** Default index type. Supports range queries, equality, ORDER BY.
```sql
CREATE INDEX idx_email ON users(email);
-- Range query uses this index:
SELECT * FROM users WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31';
```

**Hash Index:** Equality only. Faster than B-tree for exact match, useless for ranges.

**Covering Index:** Index contains all columns needed for a query — avoids table access entirely.
```sql
CREATE INDEX idx_covering ON orders(user_id, status, created_at);
-- This query hits only the index:
SELECT status, created_at FROM orders WHERE user_id = 123;
```

**Composite Index:** Column order matters — leftmost prefix rule.
```sql
-- Index on (last_name, first_name)
-- Usable for: WHERE last_name = ?
-- Usable for: WHERE last_name = ? AND first_name = ?
-- NOT usable for: WHERE first_name = ?
```

**When NOT to index:**
- Small tables
- Columns with low cardinality (boolean, status with 3 values)
- Write-heavy tables (indexes slow down writes)

---

## NoSQL Types

### Document Store (MongoDB)
```json
{
  "_id": "user_123",
  "name": "Alice",
  "orders": [
    { "id": "ord_1", "total": 99.99, "items": [...] }
  ]
}
```
Good for: hierarchical data, content management, user profiles.

### Key-Value (Redis, DynamoDB)
- Ultra-fast O(1) lookup
- Redis: in-memory, rich data structures (lists, sets, sorted sets, hashes)
- DynamoDB: managed, serverless, scales to any throughput

### Wide-Column (Cassandra)
- Rows can have different columns
- Designed for time-series, write-heavy workloads
- Partition key determines which node stores data
- Clustering key determines sort order within partition

```sql
-- Cassandra schema for messages
CREATE TABLE messages (
    conversation_id UUID,
    timestamp TIMEUUID,
    sender_id UUID,
    content TEXT,
    PRIMARY KEY (conversation_id, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);
```

---

## Database Replication

**Synchronous replication:** Write confirmed only after replica acknowledges. Strong consistency, higher write latency.

**Asynchronous replication:** Write confirmed after leader writes. Faster, but replica may lag (replication lag).

**Read replicas:** Route read queries to replicas to reduce primary load.

---

## Sharding Strategy

```
Shard by user_id:
  - hash(user_id) % num_shards
  - Even distribution
  - Can't join across shards

Shard by geography:
  - US users → shard 1, EU users → shard 2
  - Lower latency for users
  - Uneven distribution risk

Shard by date:
  - Current month → hot shard
  - Good for archiving old data
```

---

## Common Interview Questions

1. **When would you denormalise a schema?**
   - When read performance is critical and write frequency is low
   - Reporting/analytics tables (data warehouses)
   - When joins are too expensive at scale

2. **How do you handle N+1 query problem?**
   - Use JOINs or batch loading (Dataloader pattern)

3. **PostgreSQL vs MySQL?**
   - PostgreSQL: better standards compliance, JSON support, advanced indexing, window functions
   - MySQL: faster for simple reads, widely deployed, more hosting options

4. **What is a write-ahead log (WAL)?**
   - Changes written to WAL first, then applied to data files
   - Enables crash recovery and replication
