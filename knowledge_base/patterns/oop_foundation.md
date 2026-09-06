# OOP Foundation — Complete Reference

---

## Classes & Objects

A **class** is a blueprint. An **object** is a runtime instance.

```java
// Blueprint
public class BankAccount {
    private String accountNumber;
    private double balance;
    private String owner;

    public BankAccount(String accountNumber, String owner) {
        this.accountNumber = accountNumber;
        this.owner = owner;
        this.balance = 0.0;
    }

    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Amount must be positive");
        balance += amount;
    }

    public void withdraw(double amount) {
        if (amount > balance) throw new InsufficientFundsException();
        balance -= amount;
    }

    public double getBalance() { return balance; }
}

// Instances
BankAccount aliceAccount = new BankAccount("ACC001", "Alice");
BankAccount bobAccount   = new BankAccount("ACC002", "Bob");
// Two objects, same class, independent state
```

---

## The Four Pillars

### 1. Encapsulation

Bundle data with the methods that operate on it. Restrict direct access.

**Why it matters:**
- Enforces invariants (can't set negative balance)
- Reduces coupling (implementation details can change without breaking callers)
- Makes code more maintainable

```java
// Bad — anyone can corrupt state
public class Counter { public int count; }
counter.count = -100;  // invalid state

// Good — protected by methods
public class Counter {
    private int count = 0;
    public void increment()       { count++; }
    public void decrement()       { if (count > 0) count--; }
    public int  getCount()        { return count; }
}
```

---

### 2. Inheritance

A subclass inherits behaviour from its parent and can extend or override it.

```java
abstract class Shape {
    protected String colour;
    abstract double area();
    void describe() {
        System.out.printf("A %s shape with area %.2f%n", colour, area());
    }
}

class Circle extends Shape {
    private double radius;
    Circle(String colour, double radius) {
        this.colour = colour;
        this.radius = radius;
    }
    double area() { return Math.PI * radius * radius; }
}

class Rectangle extends Shape {
    private double width, height;
    double area() { return width * height; }
}
```

**When to use:**
- IS-A relationship
- Subclass truly is a specialisation of parent
- Need to extend/override parent behaviour

**When NOT to use:**
- Just to reuse some methods (use composition instead)
- Deep inheritance hierarchies (> 3 levels is a smell)

---

### 3. Polymorphism

Same interface, different behaviour.

```java
List<Shape> shapes = new ArrayList<>();
shapes.add(new Circle("red", 5));
shapes.add(new Rectangle("blue", 3, 4));
shapes.add(new Triangle("green", 3, 4, 5));

double totalArea = shapes.stream()
    .mapToDouble(Shape::area)   // dispatches to correct subclass at runtime
    .sum();
```

**Runtime polymorphism:** Method resolution at runtime via virtual dispatch.
**Compile-time polymorphism:** Method overloading — same name, different signatures.

---

### 4. Abstraction

Hide implementation details. Expose only the interface.

```java
// Abstract class — partial implementation
abstract class Database {
    final void connect() {          // template method
        authenticate();
        openConnection();
    }
    abstract void authenticate();
    abstract void openConnection();
    abstract <T> Optional<T> findById(UUID id, Class<T> type);
}

// Interface — pure contract
interface Cache {
    void put(String key, Object value, Duration ttl);
    Optional<Object> get(String key);
    void evict(String key);
}
```

---

## Composition vs Inheritance

### Composition (HAS-A)

```java
// Bad: Logger inherits FileWriter just to reuse write()
class Logger extends FileWriter { ... }

// Good: Logger CONTAINS a writer
class Logger {
    private final Writer writer;
    private final Formatter formatter;

    Logger(Writer writer, Formatter formatter) {
        this.writer    = writer;
        this.formatter = formatter;
    }

    void log(Level level, String msg) {
        String formatted = formatter.format(level, msg);
        writer.write(formatted);
    }
}

// Mix and match at runtime:
Logger consoleLogger = new Logger(new ConsoleWriter(), new JsonFormatter());
Logger fileLogger    = new Logger(new FileWriter("app.log"), new PlainFormatter());
```

**Rule of thumb:** Default to composition. Use inheritance only when the IS-A relationship is genuine and stable.

---

## Association, Aggregation, Composition

**Association:** Objects know about each other (loose coupling).
```java
class Driver { Car car; }  // Driver uses a Car
```

**Aggregation (weak HAS-A):** Parent contains child, but child can exist independently.
```java
class Department { List<Employee> employees; }
// Employee can exist without Department
```

**Composition (strong HAS-A):** Child cannot exist without parent.
```java
class Order { List<OrderItem> items; }
// OrderItem cannot exist without Order — destroyed with Order
```

---

## UML Class Diagram Quick Reference

```
┌─────────────────┐
│   ClassName     │
├─────────────────┤
│ - field: Type   │  ← private
│ # field: Type   │  ← protected
│ + field: Type   │  ← public
├─────────────────┤
│ + method(): RT  │
└─────────────────┘

Relationships:
──────────────►  Association
──────────────▷  Inheritance (extends)
- - - - - - ─▷  Interface implementation
◇─────────────   Aggregation
◆─────────────   Composition
```
