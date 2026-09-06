# SOLID Principles — Complete Reference

## Overview

SOLID is an acronym for five design principles that make software more maintainable, extensible, and testable. Coined by Robert C. Martin (Uncle Bob).

---

## S — Single Responsibility Principle

**Definition:** A class should have only one reason to change.

Every module or class should have responsibility over a single part of the program's functionality. If a class handles both business logic AND persistence AND logging, any of those three concerns changing forces you to touch the same class — increasing risk of regression.

**Indicators of violation:**
- Class name contains "And" (e.g., `UserManagerAndEmailSender`)
- Method count > 15
- Class imports from many unrelated packages

**Fix:** Extract into separate focused classes. Use services layer.

```java
// Violation
class UserService {
    void registerUser(User u) { ... }
    void sendWelcomeEmail(User u) { ... }
    void saveToDatabase(User u) { ... }
    void generateReport(User u) { ... }
}

// Fixed
class UserRegistrationService { void register(User u) { ... } }
class EmailService            { void sendWelcome(User u) { ... } }
class UserRepository          { void save(User u) { ... } }
class ReportingService        { void generateReport(User u) { ... } }
```

---

## O — Open/Closed Principle

**Definition:** Software entities should be open for extension, closed for modification.

You should be able to add new behaviour without touching existing, tested code. This is achieved through abstraction — adding new implementations of existing interfaces rather than modifying existing code.

```java
// Violation — every new discount type requires editing this class
class PriceCalculator {
    double calculate(String userType, double price) {
        if (userType.equals("STUDENT")) return price * 0.8;
        if (userType.equals("EMPLOYEE")) return price * 0.7;
        return price;
    }
}

// Fixed
interface DiscountStrategy {
    double apply(double price);
}
class StudentDiscount  implements DiscountStrategy { ... }
class EmployeeDiscount implements DiscountStrategy { ... }
// Adding VIPDiscount requires zero changes to PriceCalculator
```

---

## L — Liskov Substitution Principle

**Definition:** Objects of a superclass should be replaceable with objects of a subclass without breaking the program.

If `S` is a subtype of `T`, then objects of type `T` may be replaced with objects of type `S` without altering any of the desirable properties of the program.

**Classic violation — Square extends Rectangle:**
```java
class Rectangle {
    void setWidth(int w)  { this.width  = w; }
    void setHeight(int h) { this.height = h; }
    int area() { return width * height; }
}
class Square extends Rectangle {
    // Forces both dimensions equal — violates Rectangle contract
    void setWidth(int w)  { this.width = this.height = w; }
    void setHeight(int h) { this.width = this.height = h; }
}
// This breaks:
Rectangle r = new Square();
r.setWidth(5); r.setHeight(10);
assert r.area() == 50; // FAILS — returns 100
```

**Fix:** Use separate `Shape` interface instead of inheritance hierarchy.

---

## I — Interface Segregation Principle

**Definition:** Clients should not be forced to depend on interfaces they do not use.

Keep interfaces small and focused on a single role. "Fat" interfaces that bundle unrelated operations force implementing classes to provide no-op or throw-not-supported implementations.

```java
// Violation
interface Worker {
    void work();
    void eat();
    void sleep();
}
// RobotWorker must implement eat() and sleep() which makes no sense

// Fixed
interface Workable { void work(); }
interface Eatable  { void eat();  }
interface Sleepable { void sleep(); }

class HumanWorker  implements Workable, Eatable, Sleepable { ... }
class RobotWorker  implements Workable { ... }
```

---

## D — Dependency Inversion Principle

**Definition:**
1. High-level modules should not depend on low-level modules. Both should depend on abstractions.
2. Abstractions should not depend on details. Details should depend on abstractions.

DIP is what makes your code testable and loosely coupled. High-level business logic should not import concrete database, HTTP, or file system classes.

```java
// Violation — OrderService is coupled to MySQL
class OrderService {
    private MySQLOrderRepository repo = new MySQLOrderRepository();
    void placeOrder(Order o) {
        repo.save(o);
    }
}

// Fixed — depends on abstraction
interface OrderRepository {
    void save(Order o);
    Optional<Order> findById(UUID id);
}

class OrderService {
    private final OrderRepository repo;  // injected
    OrderService(OrderRepository repo) { this.repo = repo; }
    void placeOrder(Order o) { repo.save(o); }
}

// Swap implementations without touching OrderService:
class MySQLOrderRepository  implements OrderRepository { ... }
class InMemoryOrderRepository implements OrderRepository { ... }  // for tests
```

---

## Relationships between SOLID principles

```
SRP → Focused classes
 ↓
OCP → Extend via new classes
 ↓
LSP → Safe polymorphism
 ↓
ISP → Role interfaces
 ↓
DIP → Depend on interfaces (glues everything)
```

DIP is the culmination — it pulls all five principles together by requiring that every dependency be expressed as an abstraction.

---

## Common Interview Questions

1. Which SOLID principle does the Strategy pattern implement?  → OCP
2. What is cohesion? → Degree to which elements of a class belong together (high cohesion = SRP)
3. Can SOLID principles conflict? → Yes, over-applying DIP leads to too many abstractions (over-engineering)
4. How do you identify SRP violations? → Multiple reasons to change, large class, many unrelated imports
