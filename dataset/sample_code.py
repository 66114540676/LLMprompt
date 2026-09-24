"""Sample code dataset for the Local Coding Assistant (RAG knowledge base).

Topics covered:
  1. Math and number utilities
  2. String utilities
  3. List and collection utilities
  4. Searching and sorting algorithms
  5. Data structures (Stack, Queue, Linked List)
  6. Object-oriented programming (Calculator, BankAccount, Shape classes)
  7. Design patterns (Singleton, Factory, Observer, Strategy)
  8. File handling (JSON, CSV)
  9. Decorators and generators
 10. Error handling
 11. Dates

Every function and class is self-contained and has a short docstring so that
each one can be retrieved as a separate chunk.
"""

import csv
import functools
import json
import math
import re
import time
from abc import ABC, abstractmethod
from collections import Counter, deque
from datetime import date


# ---------------------------------------------------------------------------
# 1. Math and number utilities
# ---------------------------------------------------------------------------
def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def multiply(a, b):
    """Return the product of two numbers."""
    return a * b


def factorial(n):
    """Return n! (n factorial) using recursion. Raises ValueError for negative n."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return 1 if n <= 1 else n * factorial(n - 1)


def fibonacci(n):
    """Return the n-th Fibonacci number (0-indexed) using iteration."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def gcd(a, b):
    """Return the greatest common divisor of two integers (Euclid's algorithm)."""
    while b:
        a, b = b, a % b
    return abs(a)


def is_prime(n):
    """Check whether an integer is a prime number."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


def circle_area(radius):
    """Calculate the area of a circle from its radius."""
    return math.pi * radius ** 2


# ---------------------------------------------------------------------------
# 2. String utilities
# ---------------------------------------------------------------------------
def reverse_string(text):
    """Reverse a string."""
    return text[::-1]


def is_palindrome(text):
    """Check if a string reads the same forwards and backwards, ignoring case and punctuation."""
    cleaned = re.sub(r"[^a-z0-9]", "", text.lower())
    return cleaned == cleaned[::-1]


def count_words(text):
    """Count the number of words in a string."""
    return len(text.split())


def validate_email(email):
    """Return True if the string looks like a valid email address (regex check)."""
    pattern = r"^[\w.+-]+@[\w-]+\.[\w.-]+$"
    return re.match(pattern, email) is not None


def slugify(title):
    """Convert a title into a URL-friendly slug, e.g. 'Hello World!' becomes 'hello-world'."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return slug.strip("-")


# ---------------------------------------------------------------------------
# 3. List and collection utilities
# ---------------------------------------------------------------------------
def remove_duplicates(items):
    """Remove duplicates from a list while keeping the original order."""
    return list(dict.fromkeys(items))


def flatten_list(nested):
    """Flatten a nested list (any depth) into a single flat list."""
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(flatten_list(item))
        else:
            flat.append(item)
    return flat


def chunk_list(items, size):
    """Split a list into consecutive chunks of the given size."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def word_frequency(text):
    """Count how often each word appears in a text (case-insensitive), most common first."""
    words = re.findall(r"\w+", text.lower())
    return Counter(words).most_common()


# ---------------------------------------------------------------------------
# 4. Searching and sorting algorithms
# ---------------------------------------------------------------------------
def binary_search(sorted_items, target):
    """Return the index of target in a sorted list, or -1 if it is not found."""
    low, high = 0, len(sorted_items) - 1
    while low <= high:
        mid = (low + high) // 2
        if sorted_items[mid] == target:
            return mid
        if sorted_items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def bubble_sort(items):
    """Sort a list in ascending order using bubble sort, O(n^2). Returns a new list."""
    items = list(items)
    for i in range(len(items)):
        for j in range(len(items) - i - 1):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items


def quick_sort(items):
    """Sort a list using quick sort, average O(n log n). Returns a new list."""
    if len(items) <= 1:
        return list(items)
    pivot = items[len(items) // 2]
    left = [x for x in items if x < pivot]
    middle = [x for x in items if x == pivot]
    right = [x for x in items if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def merge_sort(items):
    """Sort a list using merge sort (stable), O(n log n). Returns a new list."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid])
    right = merge_sort(items[mid:])
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    return merged + left[i:] + right[j:]


# ---------------------------------------------------------------------------
# 5. Data structures
# ---------------------------------------------------------------------------
class Stack:
    """A LIFO (last in, first out) stack."""

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self.items.pop()

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


class Queue:
    """A FIFO (first in, first out) queue backed by collections.deque."""

    def __init__(self):
        self.items = deque()

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self.items.popleft()

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


class Node:
    """A single node of a singly linked list."""

    def __init__(self, value):
        self.value = value
        self.next = None


class LinkedList:
    """A singly linked list with append, reverse and conversion to a Python list."""

    def __init__(self):
        self.head = None

    def append(self, value):
        node = Node(value)
        if self.head is None:
            self.head = node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = node

    def reverse(self):
        previous = None
        current = self.head
        while current:
            following = current.next
            current.next = previous
            previous = current
            current = following
        self.head = previous

    def to_list(self):
        values = []
        current = self.head
        while current:
            values.append(current.value)
            current = current.next
        return values


# ---------------------------------------------------------------------------
# 6. Object-oriented programming
# ---------------------------------------------------------------------------
class Calculator:
    """A simple calculator class that remembers its calculation history."""

    def __init__(self):
        self.history = []

    def _record(self, expression, result):
        self.history.append(f"{expression} = {result}")
        return result

    def add(self, a, b):
        return self._record(f"{a} + {b}", a + b)

    def subtract(self, a, b):
        return self._record(f"{a} - {b}", a - b)

    def multiply(self, a, b):
        return self._record(f"{a} * {b}", a * b)

    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return self._record(f"{a} / {b}", a / b)


class InsufficientFundsError(Exception):
    """Custom exception raised when a withdrawal is larger than the account balance."""


class BankAccount:
    """A bank account that demonstrates encapsulation and custom exceptions."""

    def __init__(self, owner, balance=0):
        self.owner = owner
        self._balance = balance

    @property
    def balance(self):
        return self._balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self._balance += amount

    def withdraw(self, amount):
        if amount > self._balance:
            raise InsufficientFundsError(f"Balance {self._balance} is less than {amount}")
        self._balance -= amount


class Shape(ABC):
    """Abstract base class for shapes (abstraction and polymorphism)."""

    @abstractmethod
    def area(self):
        """Return the area of the shape."""

    @abstractmethod
    def perimeter(self):
        """Return the perimeter of the shape."""


class Circle(Shape):
    """A circle. Inherits from Shape and implements area and perimeter."""

    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return math.pi * self.radius ** 2

    def perimeter(self):
        return 2 * math.pi * self.radius


class Rectangle(Shape):
    """A rectangle. Inherits from Shape and implements area and perimeter."""

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)


# ---------------------------------------------------------------------------
# 7. Design patterns
# ---------------------------------------------------------------------------
class Config:
    """Singleton pattern: only one instance of this class is ever created."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = {}
        return cls._instance


class EmailNotifier:
    """Notifier that sends messages by email."""

    def send(self, message):
        return f"Email sent: {message}"


class SMSNotifier:
    """Notifier that sends messages by SMS."""

    def send(self, message):
        return f"SMS sent: {message}"


def create_notifier(kind):
    """Factory pattern: create a notifier object from a string, either 'email' or 'sms'."""
    notifiers = {"email": EmailNotifier, "sms": SMSNotifier}
    if kind not in notifiers:
        raise ValueError(f"Unknown notifier type: {kind}")
    return notifiers[kind]()


class EventEmitter:
    """Observer pattern: listeners subscribe to an event and are notified when it is emitted."""

    def __init__(self):
        self._listeners = {}

    def subscribe(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args):
        for callback in self._listeners.get(event, []):
            callback(*args)


def percentage_discount(percent):
    """Return a discount strategy function that takes the given percentage off a price."""
    return lambda price: price * (1 - percent / 100)


class Checkout:
    """Strategy pattern: the discount rule is a function passed in, so it can be swapped at runtime."""

    def __init__(self, discount_strategy=None):
        self.discount_strategy = discount_strategy or (lambda price: price)

    def total(self, prices):
        return self.discount_strategy(sum(prices))


# ---------------------------------------------------------------------------
# 8. File handling
# ---------------------------------------------------------------------------
def read_json_file(path):
    """Read a JSON file and return its contents as a Python object."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path, data):
    """Write a Python object to a JSON file with indentation, keeping non-ASCII characters."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_csv_rows(path):
    """Read a CSV file that has a header row and return a list of dictionaries."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# 9. Decorators and generators
# ---------------------------------------------------------------------------
def timer(func):
    """Decorator that prints how long a function takes to run."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.4f}s")
        return result

    return wrapper


def retry(times=3, delay=1.0):
    """Decorator factory: retry a function up to `times` times when it raises an exception."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times:
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator


def memoize(func):
    """Decorator that caches results so repeated calls with the same arguments are fast."""
    cache = {}

    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrapper


def fibonacci_generator(limit):
    """Generator that yields Fibonacci numbers below the given limit."""
    a, b = 0, 1
    while a < limit:
        yield a
        a, b = b, a + b


# ---------------------------------------------------------------------------
# 10. Error handling
# ---------------------------------------------------------------------------
def safe_divide(a, b):
    """Divide a by b and return None instead of raising ZeroDivisionError."""
    try:
        return a / b
    except ZeroDivisionError:
        return None


# ---------------------------------------------------------------------------
# 11. Dates
# ---------------------------------------------------------------------------
def days_between(start, end):
    """Return the number of days between two dates given as 'YYYY-MM-DD' strings."""
    return (date.fromisoformat(end) - date.fromisoformat(start)).days