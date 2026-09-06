"""
Complete Knowledge Graph for DesignMentor AI.

Defines every concept, its phase/category, difficulty, content payload,
and prerequisite edges.  This data is consumed by the DB seeder.
"""

from app.models.curriculum import Phase, DifficultyLevel, ConceptCategory

# ─────────────────────────────────────────────────────────────────────────────
# TOPICS
# ─────────────────────────────────────────────────────────────────────────────

TOPICS: list[dict] = [
    {"name": "OOP Foundation",        "slug": "oop-foundation",        "phase": Phase.FOUNDATION, "order_index": 1,  "description": "Core object-oriented programming concepts"},
    {"name": "SOLID Principles",      "slug": "solid-principles",      "phase": Phase.LLD,        "order_index": 2,  "description": "The five SOLID design principles"},
    {"name": "Design Principles",     "slug": "design-principles",     "phase": Phase.LLD,        "order_index": 3,  "description": "DRY, KISS, YAGNI and other core principles"},
    {"name": "Creational Patterns",   "slug": "creational-patterns",   "phase": Phase.LLD,        "order_index": 4,  "description": "Patterns that deal with object creation"},
    {"name": "Structural Patterns",   "slug": "structural-patterns",   "phase": Phase.LLD,        "order_index": 5,  "description": "Patterns that deal with object composition"},
    {"name": "Behavioral Patterns",   "slug": "behavioral-patterns",   "phase": Phase.LLD,        "order_index": 6,  "description": "Patterns that deal with object communication"},
    {"name": "LLD Problems",          "slug": "lld-problems",          "phase": Phase.LLD,        "order_index": 7,  "description": "Real-world low-level design problems"},
    {"name": "System Design Basics",  "slug": "system-design-basics",  "phase": Phase.HLD,        "order_index": 8,  "description": "Fundamentals of system design"},
    {"name": "Networking",            "slug": "networking",            "phase": Phase.HLD,        "order_index": 9,  "description": "Networking fundamentals for system design"},
    {"name": "Databases",             "slug": "databases",             "phase": Phase.HLD,        "order_index": 10, "description": "SQL, NoSQL and when to choose which"},
    {"name": "Caching",               "slug": "caching",               "phase": Phase.HLD,        "order_index": 11, "description": "Caching strategies, Redis, invalidation"},
    {"name": "Distributed Systems",   "slug": "distributed-systems",   "phase": Phase.HLD,        "order_index": 12, "description": "Scaling, replication, CAP theorem"},
    {"name": "HLD Components",        "slug": "hld-components",        "phase": Phase.HLD,        "order_index": 13, "description": "Load balancers, API gateways, message queues"},
    {"name": "HLD Problems",          "slug": "hld-problems",          "phase": Phase.HLD,        "order_index": 14, "description": "Real-world high-level design problems"},
]

# ─────────────────────────────────────────────────────────────────────────────
# CONCEPTS
# key fields: slug, topic_slug, category, difficulty, description,
#             content (rich JSON), order_index, mastery_threshold
# ─────────────────────────────────────────────────────────────────────────────

CONCEPTS: list[dict] = [

    # ── OOP FOUNDATION ───────────────────────────────────────────────────
    {
        "slug": "classes-and-objects",
        "topic_slug": "oop-foundation",
        "name": "Classes & Objects",
        "category": ConceptCategory.OOP,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "The fundamental building blocks of OOP — blueprints (classes) and their instances (objects).",
        "order_index": 1,
        "mastery_threshold": 70.0,
        "estimated_minutes": 10,
        "content": {
            "explanation": "A class is a blueprint that defines state (fields) and behaviour (methods). An object is a runtime instance of a class with its own copy of state.",
            "analogy": "A class is like an architectural blueprint; an object is the actual building constructed from it.",
            "key_points": ["Classes encapsulate data + behaviour", "Objects are heap-allocated instances", "Constructor initialises state", "Multiple objects can share the same class"],
            "code_example": {
                "language": "java",
                "bad": "// Scattered global variables\nString carBrand = \"Toyota\";\nint carSpeed = 0;",
                "good": "public class Car {\n    private String brand;\n    private int speed;\n\n    public Car(String brand) {\n        this.brand = brand;\n        this.speed = 0;\n    }\n\n    public void accelerate(int amount) {\n        speed += amount;\n    }\n}"
            },
            "interview_questions": [
                "What is the difference between a class and an object?",
                "What happens in memory when you create an object?"
            ]
        }
    },
    {
        "slug": "encapsulation",
        "topic_slug": "oop-foundation",
        "name": "Encapsulation",
        "category": ConceptCategory.OOP,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Hiding internal state and requiring access through well-defined interfaces.",
        "order_index": 2,
        "mastery_threshold": 70.0,
        "estimated_minutes": 12,
        "content": {
            "explanation": "Encapsulation bundles data and the methods that operate on that data, and restricts direct access to some of the object's components. This prevents accidental modification and enforces invariants.",
            "analogy": "A bank account — you can't directly change the balance field; you must use deposit() or withdraw() which enforce rules.",
            "key_points": ["Use private fields", "Expose via getters/setters with validation", "Invariants are enforced at one place", "Reduces coupling"],
            "code_example": {
                "language": "java",
                "bad": "public class BankAccount {\n    public double balance;\n}",
                "good": "public class BankAccount {\n    private double balance;\n\n    public void deposit(double amount) {\n        if (amount <= 0) throw new IllegalArgumentException(\"Must be positive\");\n        balance += amount;\n    }\n\n    public double getBalance() { return balance; }\n}"
            },
            "interview_questions": [
                "Why is encapsulation important?",
                "Can you break encapsulation? Give an example."
            ]
        }
    },
    {
        "slug": "inheritance",
        "topic_slug": "oop-foundation",
        "name": "Inheritance",
        "category": ConceptCategory.OOP,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "A mechanism to create a new class by extending an existing one, inheriting its fields and methods.",
        "order_index": 3,
        "mastery_threshold": 70.0,
        "estimated_minutes": 15,
        "content": {
            "explanation": "Inheritance allows a subclass to inherit state and behaviour from a parent class. It enables code reuse but introduces tight coupling between parent and child.",
            "analogy": "A SavingsAccount IS-A BankAccount — it inherits all bank account behaviour and adds interest calculation.",
            "key_points": ["IS-A relationship", "Single inheritance in Java/C#", "Method overriding", "super keyword", "Fragile base class problem"],
            "code_example": {
                "language": "java",
                "good": "public class Animal {\n    protected String name;\n    public void eat() { System.out.println(name + \" eats\"); }\n}\n\npublic class Dog extends Animal {\n    public void bark() { System.out.println(name + \" barks\"); }\n}"
            },
            "interview_questions": [
                "When should you use inheritance vs composition?",
                "What is the diamond problem?"
            ]
        }
    },
    {
        "slug": "polymorphism",
        "topic_slug": "oop-foundation",
        "name": "Polymorphism",
        "category": ConceptCategory.OOP,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "The ability of different objects to be treated as instances of the same type through a common interface.",
        "order_index": 4,
        "mastery_threshold": 72.0,
        "estimated_minutes": 15,
        "content": {
            "explanation": "Polymorphism means 'many forms'. It lets you program to an abstraction, allowing different implementations to be swapped without changing client code. Runtime (dynamic) polymorphism uses method overriding; compile-time (static) uses method overloading.",
            "analogy": "A TV remote 'speaks to' many different TV brands — same interface, different implementations.",
            "key_points": ["Runtime polymorphism via overriding", "Compile-time via overloading", "Liskov Substitution relies on this", "Enables open/closed design"],
            "code_example": {
                "language": "java",
                "good": "List<Shape> shapes = List.of(new Circle(), new Rectangle());\nfor (Shape s : shapes) {\n    s.draw();  // each draws differently\n}"
            },
            "interview_questions": [
                "What is the difference between overriding and overloading?",
                "How does dynamic dispatch work?"
            ]
        }
    },
    {
        "slug": "abstraction",
        "topic_slug": "oop-foundation",
        "name": "Abstraction",
        "category": ConceptCategory.OOP,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Exposing only essential behaviour and hiding implementation details.",
        "order_index": 5,
        "mastery_threshold": 70.0,
        "estimated_minutes": 12,
        "content": {
            "explanation": "Abstraction lets you work with concepts at a high level without worrying about low-level implementation. Abstract classes and interfaces are the main tools.",
            "analogy": "Driving a car — you use the steering wheel and pedals without knowing the engine internals.",
            "key_points": ["Abstract classes vs interfaces", "Hide complexity", "Define contracts", "Allow multiple implementations"],
            "code_example": {
                "language": "java",
                "good": "public interface PaymentGateway {\n    PaymentResult charge(double amount, String cardToken);\n    void refund(String transactionId);\n}\n// Client code only depends on the interface"
            },
            "interview_questions": ["Difference between abstract class and interface?", "When would you use an abstract class instead of an interface?"]
        }
    },
    {
        "slug": "interfaces-and-composition",
        "topic_slug": "oop-foundation",
        "name": "Interfaces & Composition",
        "category": ConceptCategory.OOP,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Programming to interfaces and preferring composition over inheritance.",
        "order_index": 6,
        "mastery_threshold": 72.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "Composition means a class CONTAINS another object instead of inheriting from it. This leads to more flexible, testable designs. 'Favour composition over inheritance' is a core design principle.",
            "analogy": "A Car HAS-A Engine rather than IS-AN Engine.",
            "key_points": ["HAS-A vs IS-A", "Composition leads to loose coupling", "Interfaces define contracts", "Dependency injection relies on composition"],
            "code_example": {
                "language": "java",
                "bad": "class Logger extends FileWriter {}",
                "good": "class Logger {\n    private final Writer writer;\n    public Logger(Writer writer) { this.writer = writer; }\n    public void log(String msg) { writer.write(msg); }\n}"
            },
            "interview_questions": ["Why prefer composition over inheritance?", "What is the role of interfaces in composition?"]
        }
    },

    # ── SOLID PRINCIPLES ─────────────────────────────────────────────────
    {
        "slug": "single-responsibility",
        "topic_slug": "solid-principles",
        "name": "Single Responsibility Principle",
        "category": ConceptCategory.SOLID,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "A class should have only one reason to change.",
        "order_index": 7,
        "mastery_threshold": 75.0,
        "estimated_minutes": 15,
        "content": {
            "explanation": "SRP states that every module/class should have responsibility over a single part of the functionality. If a class changes for two different reasons, it violates SRP.",
            "analogy": "A chef should cook, not also be the cashier and janitor.",
            "key_points": ["One class = one responsibility", "Easier to test", "Easier to maintain", "Cohesion vs coupling"],
            "code_example": {
                "language": "java",
                "bad": "class UserService {\n    void registerUser(User u) {...}\n    void sendWelcomeEmail(User u) {...}\n    void saveToDatabase(User u) {...}\n}",
                "good": "class UserRegistration { void register(User u) {...} }\nclass EmailService { void sendWelcome(User u) {...} }\nclass UserRepository { void save(User u) {...} }"
            },
            "interview_questions": ["How do you identify SRP violations?", "What is cohesion?"]
        }
    },
    {
        "slug": "open-closed",
        "topic_slug": "solid-principles",
        "name": "Open/Closed Principle",
        "category": ConceptCategory.SOLID,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Software entities should be open for extension but closed for modification.",
        "order_index": 8,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "OCP means you should be able to add new behaviour without modifying existing code. Achieved through abstraction and polymorphism — adding a new class that implements an interface rather than editing existing logic.",
            "analogy": "A power strip — you extend it by plugging in new devices without rewiring the strip itself.",
            "key_points": ["Extend via new classes, not modification", "Relies on abstractions", "Strategy pattern is a classic OCP example", "Reduces regression risk"],
            "code_example": {
                "language": "java",
                "bad": "class DiscountCalculator {\n    double calculate(String type, double price) {\n        if (type.equals(\"STUDENT\")) return price * 0.8;\n        if (type.equals(\"EMPLOYEE\")) return price * 0.7;\n        return price;\n    }\n}",
                "good": "interface DiscountStrategy { double apply(double price); }\nclass StudentDiscount implements DiscountStrategy { ... }\nclass EmployeeDiscount implements DiscountStrategy { ... }\nclass DiscountCalculator {\n    double calculate(DiscountStrategy strategy, double price) {\n        return strategy.apply(price);\n    }\n}"
            },
            "interview_questions": ["How does OCP relate to the Strategy pattern?", "Can OCP be over-applied?"]
        }
    },
    {
        "slug": "liskov-substitution",
        "topic_slug": "solid-principles",
        "name": "Liskov Substitution Principle",
        "category": ConceptCategory.SOLID,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Subtypes must be substitutable for their base types without altering program correctness.",
        "order_index": 9,
        "mastery_threshold": 75.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "If S is a subtype of T, objects of type T may be replaced by objects of type S without breaking the program. Violations usually occur when a subclass throws unexpected exceptions or weakens postconditions.",
            "analogy": "If you order 'a vehicle' and receive a car, it should work as a vehicle. If it can't drive on roads, LSP is violated.",
            "key_points": ["Subtypes must honour parent contracts", "Don't strengthen preconditions", "Don't weaken postconditions", "Square/Rectangle is the classic violation"],
            "code_example": {
                "language": "java",
                "bad": "class Rectangle { setWidth(int w); setHeight(int h); }\nclass Square extends Rectangle {\n    // Overrides setWidth to also set height — breaks contracts!\n}",
                "good": "interface Shape { int area(); }\nclass Rectangle implements Shape {...}\nclass Square implements Shape {...}"
            },
            "interview_questions": ["Give a real example of an LSP violation.", "How does LSP relate to polymorphism?"]
        }
    },
    {
        "slug": "interface-segregation",
        "topic_slug": "solid-principles",
        "name": "Interface Segregation Principle",
        "category": ConceptCategory.SOLID,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Clients should not be forced to depend on interfaces they do not use.",
        "order_index": 10,
        "mastery_threshold": 75.0,
        "estimated_minutes": 15,
        "content": {
            "explanation": "ISP says keep interfaces small and focused. A large 'fat' interface forces implementors to provide methods they don't need. Break large interfaces into role-specific ones.",
            "analogy": "A printer should not need to implement fax() just because it shares an interface with a fax machine.",
            "key_points": ["Fat interfaces are a code smell", "Role interfaces", "Clients depend only on what they use", "Enables mocking in tests"],
            "code_example": {
                "language": "java",
                "bad": "interface Worker { void work(); void eat(); void sleep(); }",
                "good": "interface Workable { void work(); }\ninterface Eatable { void eat(); }\ninterface Sleepable { void sleep(); }"
            },
            "interview_questions": ["How does ISP reduce coupling?"]
        }
    },
    {
        "slug": "dependency-inversion",
        "topic_slug": "solid-principles",
        "name": "Dependency Inversion Principle",
        "category": ConceptCategory.SOLID,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "High-level modules should not depend on low-level modules. Both should depend on abstractions.",
        "order_index": 11,
        "mastery_threshold": 75.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "DIP states that you should program to abstractions, not concretions. High-level business logic should not import low-level database or infrastructure classes directly — they should both depend on an interface.",
            "analogy": "An electrical outlet doesn't care what device you plug in — it provides a standard interface (abstraction). The device depends on the outlet contract, not the other way.",
            "key_points": ["Program to interfaces", "Invert the dependency direction", "Foundation of dependency injection frameworks", "Enables easy testing and swapping of implementations"],
            "code_example": {
                "language": "java",
                "bad": "class OrderService {\n    private MySQLOrderRepository repo = new MySQLOrderRepository();\n}",
                "good": "class OrderService {\n    private final OrderRepository repo;\n    public OrderService(OrderRepository repo) { this.repo = repo; }\n}"
            },
            "interview_questions": ["What is the difference between DIP and dependency injection?", "How does DIP enable unit testing?"]
        }
    },

    # ── DESIGN PRINCIPLES ────────────────────────────────────────────────
    {
        "slug": "dry-principle",
        "topic_slug": "design-principles",
        "name": "DRY — Don't Repeat Yourself",
        "category": ConceptCategory.DESIGN_PRINCIPLES,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Every piece of knowledge must have a single, unambiguous representation in the system.",
        "order_index": 12,
        "mastery_threshold": 70.0,
        "estimated_minutes": 10,
        "content": {
            "explanation": "DRY means avoiding duplication of logic, not just copy-pasted code. If you change a rule in one place, you shouldn't need to hunt down 10 other places.",
            "key_points": ["Extract repeated logic into functions", "Single source of truth", "Applies to data, logic, and configuration"],
            "interview_questions": ["Can over-applying DRY cause problems?"]
        }
    },
    {
        "slug": "kiss-yagni",
        "topic_slug": "design-principles",
        "name": "KISS & YAGNI",
        "category": ConceptCategory.DESIGN_PRINCIPLES,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Keep It Simple Stupid. You Aren't Gonna Need It.",
        "order_index": 13,
        "mastery_threshold": 70.0,
        "estimated_minutes": 10,
        "content": {
            "explanation": "KISS: the simplest solution that works is usually best. YAGNI: don't build features you don't need yet. Both fight over-engineering.",
            "key_points": ["Avoid premature abstraction", "Build what's needed now", "Refactor when requirements actually change"],
            "interview_questions": ["When does YAGNI conflict with scalability?"]
        }
    },
    {
        "slug": "dependency-injection",
        "topic_slug": "design-principles",
        "name": "Dependency Injection",
        "category": ConceptCategory.DESIGN_PRINCIPLES,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Passing dependencies into a class rather than creating them internally.",
        "order_index": 14,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "DI is a technique where an object's dependencies are provided externally (by a container or caller) instead of being created inside the object. Three types: constructor injection, setter injection, interface injection.",
            "analogy": "Instead of a coffee machine making its own water, you supply water from outside.",
            "key_points": ["Constructor injection is preferred", "IoC containers (Spring, FastAPI Depends)", "Enables mocking in tests", "Implements DIP"],
            "code_example": {
                "language": "python",
                "good": "class OrderService:\n    def __init__(self, repo: OrderRepository):\n        self.repo = repo\n\n# Caller injects:\nservice = OrderService(repo=PostgresOrderRepository())"
            },
            "interview_questions": ["What is the difference between DI and DIP?", "What is an IoC container?"]
        }
    },

    # ── CREATIONAL PATTERNS ───────────────────────────────────────────────
    {
        "slug": "singleton-pattern",
        "topic_slug": "creational-patterns",
        "name": "Singleton Pattern",
        "category": ConceptCategory.CREATIONAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Ensures a class has only one instance and provides a global access point.",
        "order_index": 15,
        "mastery_threshold": 75.0,
        "estimated_minutes": 15,
        "content": {
            "explanation": "Singleton restricts instantiation of a class to one object. Common uses: config managers, connection pools, loggers. Must be thread-safe in concurrent environments.",
            "key_points": ["Private constructor", "Static getInstance()", "Thread-safety with double-checked locking or enum approach", "Often overused — consider DI instead"],
            "code_example": {
                "language": "java",
                "good": "public enum DatabaseConnection {\n    INSTANCE;\n    public Connection getConnection() { ... }\n}"
            },
            "interview_questions": ["How do you make a Singleton thread-safe?", "What are the downsides of Singleton?"]
        }
    },
    {
        "slug": "factory-pattern",
        "topic_slug": "creational-patterns",
        "name": "Factory Pattern",
        "category": ConceptCategory.CREATIONAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Defines an interface for creating objects but lets subclasses decide which class to instantiate.",
        "order_index": 16,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "Factory method decouples the creation of objects from their usage. The client calls a factory method; the factory decides which concrete class to instantiate based on input.",
            "analogy": "A vehicle factory — you ask for 'a vehicle', it decides whether to produce a Car, Bike, or Truck based on your spec.",
            "key_points": ["Decouples creation from use", "Open/Closed — add new products without changing client", "Static factory vs Factory Method Pattern"],
            "code_example": {
                "language": "java",
                "good": "interface Notification { void send(String msg); }\nclass EmailNotification implements Notification {...}\nclass SMSNotification implements Notification {...}\n\nclass NotificationFactory {\n    static Notification create(String type) {\n        return switch(type) {\n            case \"EMAIL\" -> new EmailNotification();\n            case \"SMS\"   -> new SMSNotification();\n            default -> throw new IllegalArgumentException(type);\n        };\n    }\n}"
            },
            "interview_questions": ["When would you use Factory vs Abstract Factory?"]
        }
    },
    {
        "slug": "builder-pattern",
        "topic_slug": "creational-patterns",
        "name": "Builder Pattern",
        "category": ConceptCategory.CREATIONAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Separates the construction of a complex object from its representation.",
        "order_index": 17,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "Builder is used when an object requires many optional parameters or complex construction steps. It avoids telescoping constructors and makes construction readable.",
            "key_points": ["Fluent API / method chaining", "Immutable objects", "Avoids telescoping constructors", "Director optional"],
            "code_example": {
                "language": "java",
                "good": "Pizza pizza = new Pizza.Builder(\"Large\")\n    .addTopping(\"Cheese\")\n    .addTopping(\"Mushrooms\")\n    .extraCrispy(true)\n    .build();"
            },
            "interview_questions": ["When would you use Builder over a constructor with many params?"]
        }
    },

    # ── STRUCTURAL PATTERNS ───────────────────────────────────────────────
    {
        "slug": "adapter-pattern",
        "topic_slug": "structural-patterns",
        "name": "Adapter Pattern",
        "category": ConceptCategory.STRUCTURAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Converts the interface of a class into another interface clients expect.",
        "order_index": 18,
        "mastery_threshold": 75.0,
        "estimated_minutes": 15,
        "content": {
            "explanation": "Adapter acts as a bridge between incompatible interfaces. The adapter wraps an existing class and exposes a new interface that the client expects.",
            "analogy": "A travel power adapter — same device, different socket interface.",
            "key_points": ["Structural compatibility", "Object adapter vs class adapter", "Common when integrating third-party libraries"],
            "code_example": {
                "language": "java",
                "good": "interface MediaPlayer { void play(String file); }\nclass VLCPlayer { void playVLC(String file) {...} }\n\nclass VLCAdapter implements MediaPlayer {\n    private VLCPlayer vlc = new VLCPlayer();\n    public void play(String file) { vlc.playVLC(file); }\n}"
            },
            "interview_questions": ["Adapter vs Facade — what is the difference?"]
        }
    },
    {
        "slug": "decorator-pattern",
        "topic_slug": "structural-patterns",
        "name": "Decorator Pattern",
        "category": ConceptCategory.STRUCTURAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Attaches additional responsibilities to an object dynamically.",
        "order_index": 19,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "Decorator wraps an object to extend its behaviour without subclassing. Each decorator adds a layer — like wrapping gift boxes. Java I/O streams are a classic example.",
            "key_points": ["Wraps the original object", "Same interface as wrapped object", "Composable", "Alternative to subclassing for extension"],
            "code_example": {
                "language": "java",
                "good": "interface Coffee { double cost(); }\nclass BasicCoffee implements Coffee { public double cost() { return 1.0; } }\nclass MilkDecorator implements Coffee {\n    private Coffee coffee;\n    public MilkDecorator(Coffee c) { this.coffee = c; }\n    public double cost() { return coffee.cost() + 0.5; }\n}"
            },
            "interview_questions": ["How does Decorator differ from inheritance?"]
        }
    },
    {
        "slug": "facade-pattern",
        "topic_slug": "structural-patterns",
        "name": "Facade Pattern",
        "category": ConceptCategory.STRUCTURAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Provides a simplified interface to a complex subsystem.",
        "order_index": 20,
        "mastery_threshold": 75.0,
        "estimated_minutes": 12,
        "content": {
            "explanation": "Facade hides the complexity of a subsystem behind a simple interface. Clients use the facade instead of calling multiple subsystem classes directly.",
            "analogy": "A hotel concierge — you say 'book me a taxi', and the concierge handles the taxi company, payment, and timing.",
            "key_points": ["Simplifies client code", "Reduces subsystem coupling", "Doesn't prevent direct subsystem access"],
            "interview_questions": ["When would you NOT use a Facade?"]
        }
    },

    # ── BEHAVIORAL PATTERNS ───────────────────────────────────────────────
    {
        "slug": "strategy-pattern",
        "topic_slug": "behavioral-patterns",
        "name": "Strategy Pattern",
        "category": ConceptCategory.BEHAVIORAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Defines a family of algorithms, encapsulates each one, and makes them interchangeable.",
        "order_index": 21,
        "mastery_threshold": 77.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "Strategy encapsulates an algorithm behind an interface. The context object holds a reference to a strategy and delegates algorithm execution to it. This is the classic OCP implementation.",
            "analogy": "A navigation app — you choose 'fastest', 'shortest', or 'avoid tolls' route strategy without changing the app core.",
            "key_points": ["Encapsulates algorithms", "Runtime-swappable", "Eliminates if-else chains", "Used in sorting, payment processing, compression"],
            "code_example": {
                "language": "java",
                "good": "interface SortStrategy { void sort(int[] arr); }\nclass QuickSort implements SortStrategy {...}\nclass MergeSort implements SortStrategy {...}\n\nclass Sorter {\n    private SortStrategy strategy;\n    public Sorter(SortStrategy s) { strategy = s; }\n    public void sort(int[] arr) { strategy.sort(arr); }\n}"
            },
            "interview_questions": ["How does Strategy relate to OCP?", "Strategy vs State — what is the difference?"]
        }
    },
    {
        "slug": "observer-pattern",
        "topic_slug": "behavioral-patterns",
        "name": "Observer Pattern",
        "category": ConceptCategory.BEHAVIORAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Defines a one-to-many dependency so when one object changes state, all dependents are notified.",
        "order_index": 22,
        "mastery_threshold": 77.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "Observer (publish-subscribe) lets a subject maintain a list of observers and notifies them automatically of state changes. Foundation of event systems, MVC, reactive programming.",
            "analogy": "A YouTube channel — subscribers (observers) are notified when the channel (subject) uploads a new video.",
            "key_points": ["Subject maintains observer list", "Push vs pull notification", "Loose coupling between subject and observers", "Basis of event-driven architecture"],
            "code_example": {
                "language": "java",
                "good": "interface Observer { void update(Event event); }\nclass EventBus {\n    private List<Observer> observers = new ArrayList<>();\n    public void subscribe(Observer o) { observers.add(o); }\n    public void publish(Event e) { observers.forEach(o -> o.update(e)); }\n}"
            },
            "interview_questions": ["How does Observer relate to event-driven architecture?", "What is the difference between push and pull Observer?"]
        }
    },
    {
        "slug": "command-pattern",
        "topic_slug": "behavioral-patterns",
        "name": "Command Pattern",
        "category": ConceptCategory.BEHAVIORAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Encapsulates a request as an object, allowing undo/redo, queuing, and logging of operations.",
        "order_index": 23,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "Command turns operations into objects. Each command encapsulates a receiver and the action to perform. This allows undo stacks, job queues, and transaction logs.",
            "key_points": ["Encapsulates operations as objects", "Supports undo/redo", "Enables job queuing", "Decouples invoker from receiver"],
            "interview_questions": ["Where is the Command pattern used in real systems?"]
        }
    },
    {
        "slug": "state-pattern",
        "topic_slug": "behavioral-patterns",
        "name": "State Pattern",
        "category": ConceptCategory.BEHAVIORAL_PATTERNS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Allows an object to alter its behaviour when its internal state changes.",
        "order_index": 24,
        "mastery_threshold": 75.0,
        "estimated_minutes": 18,
        "content": {
            "explanation": "State pattern externalises state-specific behaviour into separate classes. The context delegates to its current state object. Eliminates large if/switch on state.",
            "analogy": "A vending machine behaves differently when idle, when money is inserted, when item is dispensing.",
            "key_points": ["State objects encapsulate behaviour", "Context delegates to current state", "Clean state transitions", "Used in order workflows, TCP connections"],
            "interview_questions": ["State vs Strategy — when to use which?"]
        }
    },

    # ── LLD PROBLEMS ──────────────────────────────────────────────────────
    {
        "slug": "lld-parking-lot",
        "topic_slug": "lld-problems",
        "name": "Design: Parking Lot",
        "category": ConceptCategory.LLD_PROBLEMS,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Design a multi-floor parking lot system with vehicle types and ticket management.",
        "order_index": 25,
        "mastery_threshold": 70.0,
        "estimated_minutes": 45,
        "content": {
            "problem_statement": "Design a parking lot system that supports multiple floors, multiple spot sizes (compact, large, handicapped), different vehicle types, and ticket-based entry/exit.",
            "entities": ["ParkingLot", "ParkingFloor", "ParkingSpot", "Vehicle", "Car", "Bike", "Truck", "Ticket", "ParkingAttendant"],
            "patterns_used": ["Factory (vehicle creation)", "Strategy (pricing)", "Singleton (ParkingLot)"],
            "key_design_decisions": ["How to find the nearest available spot?", "How to handle multiple vehicle sizes?", "How to calculate parking fee?"],
            "class_diagram": {
                "Vehicle": {"type": "abstract", "fields": ["licensePlate", "vehicleType"], "children": ["Car", "Bike", "Truck"]},
                "ParkingSpot": {"fields": ["spotId", "size", "isOccupied", "vehicle"]},
                "ParkingFloor": {"fields": ["floorId", "spots: List<ParkingSpot>"], "methods": ["findAvailableSpot(vehicleType)"]},
                "ParkingLot": {"fields": ["floors: List<ParkingFloor>"], "methods": ["park(vehicle)", "unpark(ticket)"]}
            }
        }
    },
    {
        "slug": "lld-elevator",
        "topic_slug": "lld-problems",
        "name": "Design: Elevator System",
        "category": ConceptCategory.LLD_PROBLEMS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Design an elevator control system for a multi-floor building.",
        "order_index": 26,
        "mastery_threshold": 72.0,
        "estimated_minutes": 50,
        "content": {
            "problem_statement": "Design an elevator system for a building with N floors and K elevators. Handle requests from floors and inside elevators efficiently.",
            "entities": ["ElevatorSystem", "Elevator", "Request", "ElevatorController", "Door"],
            "patterns_used": ["State (elevator states: IDLE, MOVING_UP, MOVING_DOWN, OPEN)", "Strategy (scheduling: FCFS, SCAN)", "Observer (floor requests)"],
            "key_design_decisions": ["Which scheduling algorithm to use?", "How to handle simultaneous requests?", "How to model elevator state machine?"]
        }
    },
    {
        "slug": "lld-splitwise",
        "topic_slug": "lld-problems",
        "name": "Design: Splitwise",
        "category": ConceptCategory.LLD_PROBLEMS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Design an expense splitting application.",
        "order_index": 27,
        "mastery_threshold": 75.0,
        "estimated_minutes": 60,
        "content": {
            "problem_statement": "Design Splitwise — track expenses among a group of friends, support equal/exact/percentage splits, and calculate net balances.",
            "entities": ["User", "Group", "Expense", "Split", "Balance"],
            "patterns_used": ["Strategy (split types)", "Observer (notifications)"],
            "key_design_decisions": ["How to minimise the number of transactions to settle all debts?", "How to handle group vs individual expenses?"]
        }
    },

    # ── HLD: SYSTEM DESIGN BASICS ────────────────────────────────────────
    {
        "slug": "system-design-fundamentals",
        "topic_slug": "system-design-basics",
        "name": "System Design Fundamentals",
        "category": ConceptCategory.SYSTEM_DESIGN_BASICS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Functional vs non-functional requirements, scalability, availability, reliability.",
        "order_index": 28,
        "mastery_threshold": 75.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "System design starts with understanding requirements. Functional requirements define what the system does; non-functional requirements define how well it does it.",
            "key_concepts": {
                "scalability": "Ability to handle growing load by adding resources",
                "availability": "Percentage of time system is operational (99.9% = 8.7 hours downtime/year)",
                "reliability": "Probability system performs correctly over a time period",
                "latency": "Time to complete a single request",
                "throughput": "Requests per second the system can handle"
            },
            "interview_questions": ["What is the difference between availability and reliability?", "How do you estimate scale for a system design problem?"]
        }
    },
    {
        "slug": "networking-basics",
        "topic_slug": "networking",
        "name": "Networking for System Design",
        "category": ConceptCategory.NETWORKING,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "HTTP, TCP/IP, DNS, REST APIs, WebSockets.",
        "order_index": 29,
        "mastery_threshold": 75.0,
        "estimated_minutes": 25,
        "content": {
            "explanation": "Understanding networking is essential for HLD. Know how HTTP/HTTPS works, what DNS does, the difference between TCP and UDP, and when to use REST vs WebSockets.",
            "key_concepts": {
                "http": "Stateless request-response protocol on top of TCP",
                "https": "HTTP with TLS encryption",
                "tcp": "Reliable, ordered, connection-oriented (three-way handshake)",
                "udp": "Fast, unreliable, connectionless",
                "dns": "Translates domain names to IP addresses",
                "rest": "Architectural style using HTTP verbs for resource operations",
                "websockets": "Full-duplex persistent connection for real-time communication"
            },
            "interview_questions": ["When would you use WebSockets over HTTP polling?", "What happens when you type a URL in a browser?"]
        }
    },
    {
        "slug": "sql-databases",
        "topic_slug": "databases",
        "name": "SQL Databases",
        "category": ConceptCategory.DATABASES,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Relational databases, ACID, indexes, transactions, normalization.",
        "order_index": 30,
        "mastery_threshold": 77.0,
        "estimated_minutes": 30,
        "content": {
            "explanation": "Relational databases store data in tables with strict schemas. ACID properties guarantee correctness. Indexes speed up queries. Transactions group operations atomically.",
            "key_concepts": {
                "ACID": "Atomicity, Consistency, Isolation, Durability",
                "indexes": "B-tree or hash structures that speed up reads at the cost of write overhead",
                "joins": "Combine rows from multiple tables based on related columns",
                "normalization": "Eliminate data redundancy by organising data into separate tables",
                "transactions": "Group of operations that succeed or fail together"
            },
            "interview_questions": ["When would you denormalize a schema?", "What is a covering index?"]
        }
    },
    {
        "slug": "nosql-databases",
        "topic_slug": "databases",
        "name": "NoSQL Databases",
        "category": ConceptCategory.DATABASES,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Document, key-value, wide-column, and graph databases. When to choose NoSQL.",
        "order_index": 31,
        "mastery_threshold": 77.0,
        "estimated_minutes": 25,
        "content": {
            "explanation": "NoSQL databases sacrifice some ACID guarantees for horizontal scalability, flexibility, and performance. Different types suit different use cases.",
            "key_concepts": {
                "document": "MongoDB — flexible JSON documents, good for hierarchical data",
                "key-value": "Redis, DynamoDB — fast lookup by key",
                "wide-column": "Cassandra, HBase — time-series, write-heavy workloads",
                "graph": "Neo4j — relationship-heavy data",
                "BASE": "Basically Available, Soft state, Eventually consistent"
            },
            "interview_questions": ["When would you choose MongoDB over PostgreSQL?", "What is eventual consistency?"]
        }
    },
    {
        "slug": "caching-fundamentals",
        "topic_slug": "caching",
        "name": "Caching Fundamentals",
        "category": ConceptCategory.CACHING,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Cache strategies, Redis, cache invalidation, eviction policies.",
        "order_index": 32,
        "mastery_threshold": 77.0,
        "estimated_minutes": 25,
        "content": {
            "explanation": "Caching stores frequently accessed data in fast storage (memory) to reduce database load and latency. Redis is the most popular distributed cache.",
            "key_concepts": {
                "cache-aside": "App reads cache first; on miss, reads DB and populates cache",
                "write-through": "Write to cache and DB simultaneously",
                "write-back": "Write to cache only; async flush to DB (risk of data loss)",
                "eviction_policies": "LRU (Least Recently Used), LFU, TTL-based",
                "cache_invalidation": "How to keep cache consistent with DB (hardest problem in CS joke)"
            },
            "interview_questions": ["When should you NOT use caching?", "How do you handle cache invalidation in a distributed system?"]
        }
    },
    {
        "slug": "cap-theorem",
        "topic_slug": "distributed-systems",
        "name": "CAP Theorem & Distributed Consistency",
        "category": ConceptCategory.DISTRIBUTED_SYSTEMS,
        "difficulty": DifficultyLevel.ADVANCED,
        "description": "CAP theorem, consistency models, eventual consistency, distributed transactions.",
        "order_index": 33,
        "mastery_threshold": 77.0,
        "estimated_minutes": 30,
        "content": {
            "explanation": "CAP theorem states that a distributed system can only guarantee two of three: Consistency, Availability, Partition Tolerance. In practice, P is unavoidable, so you choose between C and A.",
            "key_concepts": {
                "consistency": "Every read returns the most recent write",
                "availability": "Every request gets a response (not necessarily most recent data)",
                "partition_tolerance": "System continues despite network partitions",
                "CP_systems": "HBase, Zookeeper, etcd — sacrifice availability for consistency",
                "AP_systems": "Cassandra, CouchDB — sacrifice consistency for availability"
            },
            "interview_questions": ["Where does DynamoDB sit in the CAP theorem?", "What is the PACELC extension to CAP?"]
        }
    },
    {
        "slug": "horizontal-scaling",
        "topic_slug": "distributed-systems",
        "name": "Scaling: Horizontal vs Vertical",
        "category": ConceptCategory.DISTRIBUTED_SYSTEMS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Vertical scaling, horizontal scaling, sharding, replication, partitioning.",
        "order_index": 34,
        "mastery_threshold": 75.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "Vertical scaling (scale up) means adding more resources to a single machine. Horizontal scaling (scale out) means adding more machines. Most large-scale systems scale horizontally.",
            "key_concepts": {
                "replication": "Copies of data on multiple nodes for read scaling and HA",
                "sharding": "Split data across nodes based on a shard key",
                "consistent_hashing": "Distribute data across nodes with minimal reshuffling when nodes are added/removed",
                "load_balancer": "Distribute traffic across multiple app server instances"
            },
            "interview_questions": ["What are the trade-offs of sharding?", "How does consistent hashing work?"]
        }
    },
    {
        "slug": "message-queues",
        "topic_slug": "hld-components",
        "name": "Message Queues & Kafka",
        "category": ConceptCategory.HLD_COMPONENTS,
        "difficulty": DifficultyLevel.ADVANCED,
        "description": "Async communication, Kafka, RabbitMQ, pub-sub, event streaming.",
        "order_index": 35,
        "mastery_threshold": 77.0,
        "estimated_minutes": 30,
        "content": {
            "explanation": "Message queues decouple producers from consumers and enable async processing. Kafka is a distributed event streaming platform used for high-throughput, fault-tolerant pipelines.",
            "key_concepts": {
                "producer_consumer": "Producers publish messages, consumers read at their own pace",
                "topics_partitions": "Kafka organises messages in topics, split into partitions for parallelism",
                "consumer_groups": "Multiple consumers in a group share partition workload",
                "at_least_once": "vs at-most-once vs exactly-once delivery semantics"
            },
            "interview_questions": ["When would you use Kafka vs RabbitMQ?", "How does Kafka guarantee ordering?"]
        }
    },
    {
        "slug": "load-balancing",
        "topic_slug": "hld-components",
        "name": "Load Balancing & API Gateway",
        "category": ConceptCategory.HLD_COMPONENTS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Layer 4/7 load balancers, algorithms, API gateway, rate limiting.",
        "order_index": 36,
        "mastery_threshold": 75.0,
        "estimated_minutes": 20,
        "content": {
            "explanation": "A load balancer distributes incoming requests across multiple servers to improve throughput and availability. An API gateway sits in front of microservices and handles auth, routing, rate limiting.",
            "key_concepts": {
                "L4_LB": "Routes based on IP/TCP (faster but less flexible)",
                "L7_LB": "Routes based on HTTP content (smarter, can inspect URLs/headers)",
                "algorithms": "Round-robin, least connections, IP hash, weighted",
                "api_gateway": "Single entry point: handles auth, routing, rate limiting, logging"
            },
            "interview_questions": ["What is the difference between a load balancer and an API gateway?"]
        }
    },

    # ── HLD PROBLEMS ──────────────────────────────────────────────────────
    {
        "slug": "hld-url-shortener",
        "topic_slug": "hld-problems",
        "name": "Design: URL Shortener",
        "category": ConceptCategory.HLD_PROBLEMS,
        "difficulty": DifficultyLevel.BEGINNER,
        "description": "Design a system like bit.ly that shortens URLs and redirects users.",
        "order_index": 37,
        "mastery_threshold": 75.0,
        "estimated_minutes": 60,
        "content": {
            "problem_statement": "Design a URL shortener service. 100M URLs created/day, 10B reads/day.",
            "functional_requirements": ["Create short URL", "Redirect to original URL", "Custom aliases", "Analytics (optional)"],
            "non_functional_requirements": ["Low latency redirects (< 10ms)", "High availability", "No single point of failure"],
            "architecture": {
                "flow": "Client → CDN → Load Balancer → App Servers → Cache (Redis) → DB",
                "short_code": "Base62 encoding of an auto-increment ID (6 chars = 56B URLs)",
                "database": "Write: relational (id, short_code, long_url, user_id, created_at); Read-heavy → cache aggressively"
            },
            "key_design_decisions": ["How to generate unique short codes?", "How to handle 301 vs 302 redirect?", "How to handle custom aliases?"]
        }
    },
    {
        "slug": "hld-instagram",
        "topic_slug": "hld-problems",
        "name": "Design: Instagram",
        "category": ConceptCategory.HLD_PROBLEMS,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "description": "Design a photo sharing social platform at scale.",
        "order_index": 38,
        "mastery_threshold": 77.0,
        "estimated_minutes": 90,
        "content": {
            "problem_statement": "Design Instagram — users can upload photos, follow others, and view a personalised feed.",
            "scale": "500M DAU, 100M photos/day, 4.2B likes/day",
            "architecture": {
                "upload_flow": "Client → API Gateway → Upload Service → Object Storage (S3) → CDN",
                "feed_generation": "Pull model (compute on read) vs Push model (fanout on write). For celebrities: hybrid.",
                "database": "User/Follow data: PostgreSQL; Photos metadata: Cassandra; Feed cache: Redis sorted sets"
            },
            "key_components": ["CDN for media", "Object Storage", "News Feed Service", "Notification Service"],
            "trade_offs": ["Push vs pull feed", "Consistency vs availability for likes", "Storage costs"]
        }
    },
    {
        "slug": "hld-rate-limiter",
        "topic_slug": "hld-problems",
        "name": "Design: Rate Limiter",
        "category": ConceptCategory.HLD_PROBLEMS,
        "difficulty": DifficultyLevel.ADVANCED,
        "description": "Design a distributed rate limiter.",
        "order_index": 39,
        "mastery_threshold": 77.0,
        "estimated_minutes": 60,
        "content": {
            "problem_statement": "Design a rate limiter that limits requests per user/IP. Must work in a distributed environment.",
            "algorithms": {
                "token_bucket": "Tokens added at fixed rate; request consumes a token. Allows bursts.",
                "leaky_bucket": "Queue processes at fixed rate. Smooths bursts.",
                "sliding_window_log": "Track request timestamps; count in last N seconds.",
                "sliding_window_counter": "Approximate sliding window using two fixed windows."
            },
            "distributed_implementation": "Redis + Lua script for atomic increment; Redis Sorted Sets for sliding window log.",
            "key_design_decisions": ["Which algorithm?", "Where to enforce (API Gateway vs middleware)?", "How to handle race conditions?"]
        }
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PREREQUISITE EDGES  (concept_slug → [prerequisite_slugs])
# ─────────────────────────────────────────────────────────────────────────────

PREREQUISITES: dict[str, list[str]] = {
    # OOP internal ordering
    "encapsulation":            ["classes-and-objects"],
    "inheritance":              ["classes-and-objects", "encapsulation"],
    "polymorphism":             ["inheritance"],
    "abstraction":              ["interfaces-and-composition"],
    "interfaces-and-composition": ["inheritance", "polymorphism"],

    # SOLID requires OOP
    "single-responsibility":    ["interfaces-and-composition"],
    "open-closed":              ["single-responsibility", "polymorphism"],
    "liskov-substitution":      ["inheritance", "polymorphism"],
    "interface-segregation":    ["abstraction"],
    "dependency-inversion":     ["interface-segregation", "open-closed"],

    # Design principles
    "dry-principle":            ["single-responsibility"],
    "kiss-yagni":               ["dry-principle"],
    "dependency-injection":     ["dependency-inversion"],

    # Creational patterns require SOLID
    "singleton-pattern":        ["dependency-inversion"],
    "factory-pattern":          ["open-closed", "single-responsibility"],
    "builder-pattern":          ["factory-pattern"],

    # Structural patterns
    "adapter-pattern":          ["interfaces-and-composition"],
    "decorator-pattern":        ["open-closed", "interfaces-and-composition"],
    "facade-pattern":           ["single-responsibility"],

    # Behavioral patterns
    "strategy-pattern":         ["open-closed", "dependency-inversion"],
    "observer-pattern":         ["interfaces-and-composition", "single-responsibility"],
    "command-pattern":          ["strategy-pattern"],
    "state-pattern":            ["strategy-pattern"],

    # LLD problems require patterns
    "lld-parking-lot":          ["factory-pattern", "strategy-pattern", "singleton-pattern"],
    "lld-elevator":             ["state-pattern", "strategy-pattern", "observer-pattern"],
    "lld-splitwise":            ["strategy-pattern", "observer-pattern"],

    # HLD requires LLD mastery
    "system-design-fundamentals": ["lld-parking-lot"],
    "networking-basics":        ["system-design-fundamentals"],
    "sql-databases":            ["system-design-fundamentals"],
    "nosql-databases":          ["sql-databases"],
    "caching-fundamentals":     ["sql-databases", "nosql-databases"],
    "cap-theorem":              ["nosql-databases"],
    "horizontal-scaling":       ["cap-theorem"],
    "message-queues":           ["horizontal-scaling"],
    "load-balancing":           ["networking-basics", "horizontal-scaling"],
    "hld-url-shortener":        ["caching-fundamentals", "sql-databases", "load-balancing"],
    "hld-instagram":            ["message-queues", "caching-fundamentals", "load-balancing"],
    "hld-rate-limiter":         ["caching-fundamentals", "message-queues", "load-balancing"],
}
