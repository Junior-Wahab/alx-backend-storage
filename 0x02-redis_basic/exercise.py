#!/usr/bin/env python3
"""
exercise.py
A simple Cache class that uses Redis for storage.
"""

import redis
import uuid
from typing import Callable, Any, Optional

class Cache:
    """Cache class that stores data in Redis."""

    def __init__(self) -> None:
        """Initialize the Cache class and flush the Redis database."""
        self._redis = redis.Redis()
        self._redis.flushdb()

    def store(self, data: Any) -> str:
        """
        Store data in Redis with a random key.
        
        Args:
            data: The data to store (str, bytes, int, or float).
        
        Returns:
            str: The key under which the data is stored.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable[[bytes], Any]] = None) -> Any:
        """
        Retrieve data from Redis by key, with optional conversion.

        Args:
            key: The key to retrieve data from.
            fn: Optional callable to convert the data.

        Returns:
            The retrieved and optionally converted data.
        """
        value = self._redis.get(key)
        if value is None:
            return None
        if fn:
            return fn(value)
        return value

    def get_str(self, key: str) -> str:
        """Retrieve a string from Redis."""
        return self.get(key, lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> int:
        """Retrieve an integer from Redis."""
        return self.get(key, int)

    def count_calls(method: Callable) -> Callable:
        """
        Decorator that counts how many times a method is called.

        Args:
            method: The method to wrap.

        Returns:
            Callable: Wrapped method that increments the call count.
        """
        def wrapper(self, *args, **kwargs):
            key = method.__qualname__
            self._redis.incr(key)
            return method(self, *args, **kwargs)
        return wrapper

    @count_calls
    def store(self, data: Any) -> str:
        """Override store method to include call counting."""
        return self.store(data)

    def call_history(method: Callable) -> Callable:
        """
        Decorator that stores the history of calls to a method.

        Args:
            method: The method to wrap.

        Returns:
            Callable: Wrapped method that stores input and output history.
        """
        def wrapper(self, *args, **kwargs):
            inputs_key = f"{method.__qualname__}:inputs"
            outputs_key = f"{method.__qualname__}:outputs"
            self._redis.rpush(inputs_key, str(args).encode())
            output = method(self, *args, **kwargs)
            self._redis.rpush(outputs_key, output)
            return output
        return wrapper

    @call_history
    def store(self, data: Any) -> str:
        """Override store method to include call history."""
        return self.store(data)

def replay(method: Callable) -> None:
    """
    Display the history of calls to a method.

    Args:
        method: The method to replay history for.
    """
    key = method.__qualname__
    count = method._redis.get(key).decode("utf-8")
    inputs = method._redis.lrange(f"{key}:inputs", 0, -1)
    outputs = method._redis.lrange(f"{key}:outputs", 0, -1)

    print(f"{key} was called {count} times:")
    for input, output in zip(inputs, outputs):
        print(f"{key}(*{input.decode()}) -> {output.decode()}")


