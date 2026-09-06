# Design Patterns — Complete Reference

Design patterns are reusable solutions to commonly occurring problems in software design. Popularised by the "Gang of Four" (GoF) book.

---

## Creational Patterns

### Singleton

Ensures one instance exists. Thread-safe implementation:

```java
public enum AppConfig {
    INSTANCE;
    private final Properties props = loadProperties();
    public String get(String key) { return props.getProperty(key); }
}
```

**When to use:** Shared resources — connection pools, configuration, loggers.
**Downsides:** Global state is hard to test, hides dependencies. Prefer DI container-managed singletons.

---

### Factory Method

```java
interface Notification { void send(String message); }
class EmailNotification implements Notification { ... }
class PushNotification  implements Notification { ... }

class NotificationFactory {
    static Notification create(String channel) {
        return switch(channel) {
            case "EMAIL" -> new EmailNotification();
            case "PUSH"  -> new PushNotification();
            default -> throw new IllegalArgumentException("Unknown channel: " + channel);
        };
    }
}
```

**When to use:** When creation logic is complex or varies by type.

---

### Abstract Factory

Returns a **family** of related objects. Example: UI toolkit factory returning Button, Checkbox, TextField that all look consistent (Windows style vs Mac style).

---

### Builder

```java
HttpRequest request = new HttpRequest.Builder("https://api.example.com/users")
    .method("POST")
    .header("Content-Type", "application/json")
    .body(jsonPayload)
    .timeout(30_000)
    .build();
```

**When to use:** Objects with many optional parameters, immutable objects, step-by-step construction.

---

### Prototype

Clone an existing object rather than creating from scratch. Use when construction is expensive.

---

## Structural Patterns

### Adapter

Converts an incompatible interface into the expected one.

```java
// Legacy payment API with different interface
class LegacyPaymentGateway {
    void doPayment(String cardNo, int amountCents) { ... }
}

// Your app expects this interface
interface PaymentProcessor {
    void process(PaymentRequest req);
}

class LegacyPaymentAdapter implements PaymentProcessor {
    private LegacyPaymentGateway gateway = new LegacyPaymentGateway();
    public void process(PaymentRequest req) {
        gateway.doPayment(req.getCardNumber(), (int)(req.getAmount() * 100));
    }
}
```

---

### Decorator

Add behaviour dynamically without subclassing:

```java
// Core object
interface Logger { void log(String msg); }
class ConsoleLogger implements Logger {
    public void log(String msg) { System.out.println(msg); }
}

// Decorators
class TimestampDecorator implements Logger {
    private Logger wrapped;
    TimestampDecorator(Logger l) { wrapped = l; }
    public void log(String msg) { wrapped.log("[" + Instant.now() + "] " + msg); }
}
class LevelDecorator implements Logger {
    private Logger wrapped; private String level;
    public void log(String msg) { wrapped.log(level + ": " + msg); }
}

// Compose
Logger logger = new LevelDecorator(new TimestampDecorator(new ConsoleLogger()), "INFO");
```

---

### Facade

```java
// Subsystem is complex
class VideoEncoder { ... }
class AudioMixer   { ... }
class MetadataWriter { ... }

// Facade simplifies it
class VideoProcessingFacade {
    void process(String inputFile, String outputFile) {
        VideoEncoder encoder = new VideoEncoder();
        AudioMixer mixer = new AudioMixer();
        MetadataWriter writer = new MetadataWriter();
        encoder.encode(inputFile);
        mixer.normalize(inputFile);
        writer.write(outputFile);
    }
}
```

---

### Proxy

Controls access to another object (lazy loading, security, caching):

```java
interface Image { void display(); }
class RealImage implements Image {
    RealImage(String path) { loadFromDisk(path); }  // expensive
    public void display() { ... }
}
class ProxyImage implements Image {
    private RealImage real; private String path;
    ProxyImage(String path) { this.path = path; }
    public void display() {
        if (real == null) real = new RealImage(path);  // lazy load
        real.display();
    }
}
```

---

## Behavioral Patterns

### Strategy

```java
interface CompressionStrategy { byte[] compress(byte[] data); }
class ZipCompression  implements CompressionStrategy { ... }
class GzipCompression implements CompressionStrategy { ... }

class FileCompressor {
    private CompressionStrategy strategy;
    FileCompressor(CompressionStrategy s) { strategy = s; }
    byte[] compress(byte[] data) { return strategy.compress(data); }
}
// Swap at runtime based on file type or user preference
```

---

### Observer

```java
interface EventListener<T> { void onEvent(T event); }

class EventBus {
    private Map<String, List<EventListener>> listeners = new HashMap<>();

    <T> void subscribe(String type, EventListener<T> listener) {
        listeners.computeIfAbsent(type, k -> new ArrayList<>()).add(listener);
    }

    <T> void publish(String type, T event) {
        listeners.getOrDefault(type, List.of()).forEach(l -> l.onEvent(event));
    }
}
```

---

### Command

```java
interface Command { void execute(); void undo(); }

class MoveCommand implements Command {
    private Robot robot; private int dx, dy;
    public void execute() { robot.move(dx, dy); }
    public void undo()    { robot.move(-dx, -dy); }
}

class CommandHistory {
    private Deque<Command> history = new ArrayDeque<>();
    void execute(Command cmd) { cmd.execute(); history.push(cmd); }
    void undo() { if (!history.isEmpty()) history.pop().undo(); }
}
```

---

### State

```java
interface TrafficLightState {
    void handle(TrafficLight light);
}
class GreenState implements TrafficLightState {
    public void handle(TrafficLight light) {
        System.out.println("Green — Go");
        light.setState(new YellowState());
    }
}
class YellowState implements TrafficLightState { ... }
class RedState   implements TrafficLightState { ... }

class TrafficLight {
    private TrafficLightState state = new GreenState();
    void setState(TrafficLightState s) { state = s; }
    void change() { state.handle(this); }
}
```

---

### Chain of Responsibility

```java
abstract class Handler {
    private Handler next;
    Handler setNext(Handler h) { next = h; return h; }
    void handle(Request r) {
        if (canHandle(r)) process(r);
        else if (next != null) next.handle(r);
    }
    abstract boolean canHandle(Request r);
    abstract void process(Request r);
}
```

Used in: middleware pipelines, auth chains, logging frameworks.

---

### Template Method

Defines the skeleton of an algorithm in a base class; subclasses fill in specific steps.

```java
abstract class DataProcessor {
    final void process() {        // template method — final!
        readData();
        processData();
        writeData();
    }
    abstract void readData();
    abstract void processData();
    void writeData() { /* default implementation */ }
}
```

---

## Pattern Selection Guide

| Situation | Pattern |
|---|---|
| Need one global instance | Singleton (or DI) |
| Creation logic varies by type | Factory Method |
| Create families of objects | Abstract Factory |
| Many constructor params | Builder |
| Add behaviour without subclass | Decorator |
| Simplify complex subsystem | Facade |
| Multiple interchangeable algorithms | Strategy |
| Notify many dependents of change | Observer |
| Object changes behaviour by state | State |
| Undo/redo operations | Command |
| Convert incompatible interface | Adapter |
