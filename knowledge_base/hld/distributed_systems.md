# Distributed Systems — Complete Reference

---

## CAP Theorem

States that a distributed data store can only guarantee **two** of three properties:

- **C — Consistency:** Every read receives the most recent write or an error
- **A — Availability:** Every request receives a (non-error) response, without guarantee it's the most recent
- **P — Partition Tolerance:** System continues to operate despite network partitions

**Since P is unavoidable in real distributed systems, the real choice is C vs A:**

| System | Trade-off | Examples |
|---|---|---|
| CP | Consistency + Partition | HBase, Zookeeper, etcd, MongoDB (strong mode) |
| AP | Availability + Partition | Cassandra, CouchDB, DynamoDB (eventual) |

**PACELC Extension:** Even when no partition, there's a trade-off between Latency (L) and Consistency (C).

---

## Consistency Models

**Strong Consistency:** Every read sees the latest write (like a single server). Cost: higher latency.

**Eventual Consistency:** Given no new updates, all replicas will eventually converge. Amazon shopping cart uses this — you might briefly see stale cart data.

**Read-your-writes:** You always see your own writes. Others may not yet.

**Causal Consistency:** Operations causally related are seen in order.

---

## Scaling Strategies

### Vertical Scaling (Scale Up)
Add more CPU/RAM/SSD to existing server.
- Pros: simple, no code changes
- Cons: hardware limits, single point of failure, expensive

### Horizontal Scaling (Scale Out)
Add more servers, distribute load.
- Pros: theoretically unlimited, fault-tolerant
- Cons: complex, need stateless services, data consistency harder

### Stateless Services
Store session state in external store (Redis) not in-process memory. Enables horizontal scaling.

---

## Replication

**Purpose:** Redundancy (HA) + read scaling.

**Leader-Follower (Master-Replica):**
- All writes go to leader
- Reads can go to followers
- Replication lag: followers may serve stale data

**Multi-Leader:**
- Multiple nodes accept writes
- Conflict resolution required (last-write-wins, CRDTs)

**Leaderless (Dynamo-style):**
- Any node accepts writes
- Quorum: W + R > N for strong consistency

---

## Sharding (Horizontal Partitioning)

Split data across multiple database nodes based on a **shard key**.

**Range sharding:** Users A-M on shard 1, N-Z on shard 2.
- Con: hotspots if distribution is uneven

**Hash sharding:** `shard = hash(user_id) % N`
- Pro: even distribution
- Con: range queries span all shards

**Consistent Hashing:** Map shard keys on a ring. Adding/removing a node only rebalances a fraction of keys. Used by Cassandra, Amazon DynamoDB.

---

## Distributed Transactions

**2-Phase Commit (2PC):**
1. Prepare phase: coordinator asks all participants to prepare
2. Commit phase: if all say yes, commit; else abort
- Con: blocking if coordinator crashes

**Saga Pattern:**
- Series of local transactions, each publishing events
- On failure: compensating transactions undo previous steps
- Preferred in microservices

---

## Consensus Algorithms

**Raft:** Leader election + log replication. Used by etcd, CockroachDB.

**Paxos:** Foundational consensus algorithm. Complex, used in Chubby (Google).

---

## Distributed Caching

**Cache-aside (lazy loading):**
```
1. App checks cache
2. Cache miss → read from DB → write to cache
3. Return data
```

**Write-through:**
```
Write to cache AND DB simultaneously
→ Cache always consistent, higher write latency
```

**Write-back (write-behind):**
```
Write to cache only → async flush to DB
→ Fast writes, risk of data loss on cache crash
```

**Cache Invalidation Strategies:**
- TTL-based expiry
- Event-based (write invalidates cache)
- Cache-aside (invalidate on write, repopulate on next read)

---

## Common Interview Questions

1. **Design a distributed counter (e.g., likes on a post)**
   - Redis INCR (atomic, single node) vs distributed counter with conflict resolution

2. **How would you ensure exactly-once processing in a message queue?**
   - Idempotency keys + deduplication table

3. **What is a split-brain problem?**
   - Two nodes each think they're the leader after a partition. Fencing tokens prevent this.

4. **How does Cassandra handle write conflicts?**
   - Last-write-wins using timestamps (not safe for counter increments)
