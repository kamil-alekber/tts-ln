import redis
import json
import hashlib
from typing import Optional, List, Dict, Any, Type, TypeVar
from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum

T = TypeVar('T')

class RedisDB:
    """Redis database manager for TTS models."""
    
    def __init__(self, host: str = 'redis', port: int = 6379, db: int = 0, password: Optional[str] = None):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        
    def _generate_key(self, model_type: str, identifier: str) -> str:
        """Generate Redis key for a model instance."""
        return f"{model_type}:{identifier}"
    
    def _generate_list_key(self, model_type: str) -> str:
        """Generate Redis key for listing all instances of a model type."""
        return f"{model_type}:all"
    
    def _serialize(self, obj: Any) -> str:
        """Serialize object to JSON string."""
        if hasattr(obj, '__dict__'):
            # check if field is enum
            data = asdict(obj)
            for k, v in data.items():
                if isinstance(v, Enum):
                    data[k] = v.value
            return json.dumps(data)
        return json.dumps(obj)
    
    def _deserialize(self, data: str, model_class: Type[T]) -> T:
        """Deserialize JSON string to model instance."""
        obj_dict = json.loads(data)
        return model_class(**obj_dict)
    
    def save(self, obj: Any, identifier: str) -> bool:
        """Save an object to Redis."""
        try:
            model_type = obj.__class__.__name__.lower()
            key = self._generate_key(model_type, identifier)
            list_key = self._generate_list_key(model_type)
            
            # Serialize and save the object
            serialized_data = self._serialize(obj)
            self.redis_client.set(key, serialized_data)
            
            # Add identifier to the list of all objects of this type
            self.redis_client.sadd(list_key, identifier)
            
            return True
        except Exception as e:
            print(f"Error saving object: {e}")
            return False
    
    def get(self, model_class: Type[T], identifier: str) -> Optional[T]:
        """Get an object from Redis by identifier."""
        try:
            model_type = model_class.__name__.lower()
            key = self._generate_key(model_type, identifier)
            
            data = self.redis_client.get(key)
            if data is None:
                return None
                
            return self._deserialize(data, model_class)
        except Exception as e:
            print(f"Error getting object: {e}")
            return None
    
    def update(self, obj: Any, identifier: str) -> bool:
        """Update an existing object in Redis."""
        try:
            model_type = obj.__class__.__name__.lower()
            key = self._generate_key(model_type, identifier)
            
            # Check if object exists
            if not self.redis_client.exists(key):
                return False
            
            # Update the object
            serialized_data = self._serialize(obj)
            self.redis_client.set(key, serialized_data)
            
            return True
        except Exception as e:
            print(f"Error updating object: {e}")
            return False
    
    def delete(self, model_class: Type[T], identifier: str) -> bool:
        """Delete an object from Redis by identifier."""
        try:
            model_type = model_class.__name__.lower()
            key = self._generate_key(model_type, identifier)
            list_key = self._generate_list_key(model_type)
            
            # Delete the object
            deleted = self.redis_client.delete(key)
            
            # Remove identifier from the list
            self.redis_client.srem(list_key, identifier)
            
            return deleted > 0
        except Exception as e:
            print(f"Error deleting object: {e}")
            return False
    
    def list_all(self, model_class: Type[T]) -> List[T]:
        """List all objects of a given model type."""
        try:
            model_type = model_class.__name__.lower()
            list_key = self._generate_list_key(model_type)
            
            # Get all identifiers for this model type
            identifiers = self.redis_client.smembers(list_key)
            
            objects = []
            for identifier in identifiers:
                obj = self.get(model_class, identifier)
                if obj:
                    objects.append(obj)
            
            return objects
        except Exception as e:
            print(f"Error listing objects: {e}")
            return []
    
    def list_by_field(self, model_class: Type[T], field_name: str, field_value: str) -> List[T]:
        """List all objects that match a specific field value."""
        try:
            all_objects = self.list_all(model_class)
            
            return [obj for obj in all_objects if hasattr(obj, field_name) and getattr(obj, field_name) == field_value]
        except Exception as e:
            print(f"Error filtering objects by field: {e}")
            return []
    
    def exists(self, model_class: Type[T], identifier: str) -> bool:
        """Check if an object exists in Redis."""
        model_type = model_class.__name__.lower()
        key = self._generate_key(model_type, identifier)
        return self.redis_client.exists(key) > 0
    
    def count(self, model_class: Type[T]) -> int:
        """Count the number of objects of a given model type."""
        model_type = model_class.__name__.lower()
        list_key = self._generate_list_key(model_type)
        return self.redis_client.scard(list_key)

# Global database instance
db = RedisDB()