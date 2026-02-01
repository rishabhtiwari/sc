# MongoDB ObjectId Serialization Fix

## Problem
FastAPI was throwing a `ValueError` when trying to serialize MongoDB documents containing `ObjectId` fields:

```
ValueError: [TypeError("'ObjectId' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]
```

This error occurred because:
1. MongoDB's `_id` field is an `ObjectId` type
2. FastAPI's `jsonable_encoder` cannot serialize `ObjectId` objects by default
3. Some database queries were not excluding the `_id` field

## Solution

### 1. Fixed Database Queries
Updated `database_service.py` to ensure all MongoDB queries exclude the `_id` field:

**Before:**
```python
audio = self.audio_library.find_one(query)
if audio:
    audio['_id'] = str(audio['_id'])  # Manual conversion
```

**After:**
```python
audio = self.audio_library.find_one(query, {"_id": 0})  # Exclude _id from query
```

### 2. Added Global ObjectId Serialization
Patched FastAPI's `jsonable_encoder` in `app.py` to handle `ObjectId` and `datetime` objects globally:

```python
import fastapi.encoders
from bson import ObjectId
from datetime import datetime

original_jsonable_encoder = fastapi.encoders.jsonable_encoder

def patched_jsonable_encoder(obj, **kwargs):
    """Patched jsonable_encoder that handles ObjectId"""
    custom_encoder = kwargs.get('custom_encoder', {})
    custom_encoder[ObjectId] = str
    if datetime not in custom_encoder:
        custom_encoder[datetime] = lambda dt: dt.isoformat()
    kwargs['custom_encoder'] = custom_encoder
    return original_jsonable_encoder(obj, **kwargs)

fastapi.encoders.jsonable_encoder = patched_jsonable_encoder
```

### 3. Created Utility Functions
Added `utils/mongodb_utils.py` with helper functions for MongoDB serialization:
- `serialize_objectid()` - Recursively convert ObjectId to string
- `remove_objectid_field()` - Remove _id field from documents
- `convert_objectid_to_str()` - Convert _id ObjectId to string

## Files Modified
1. `asset-service/app.py` - Added global ObjectId serialization
2. `asset-service/services/database_service.py` - Fixed `get_audio_by_id()` method
3. `asset-service/utils/mongodb_utils.py` - Created utility functions (new file)

## Testing
To verify the fix works:

1. Start the asset-service:
   ```bash
   cd asset-service
   uvicorn app:app --reload --port 8099
   ```

2. Test an endpoint that returns MongoDB documents:
   ```bash
   curl -X GET "http://localhost:8099/api/audio-studio/library" \
     -H "x-customer-id: customer_system" \
     -H "x-user-id: user_123"
   ```

3. The response should now serialize correctly without ObjectId errors.

## Best Practices Going Forward
1. Always use `{"_id": 0}` projection in MongoDB queries to exclude the `_id` field
2. If `_id` is needed, convert it to string immediately: `str(doc['_id'])`
3. The global patch will handle any ObjectId that slips through
4. Use the utility functions in `mongodb_utils.py` for complex serialization needs

