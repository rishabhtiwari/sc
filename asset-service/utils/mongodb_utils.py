"""
MongoDB Utilities
Helper functions for MongoDB operations and serialization
"""
from typing import Any, Dict, List, Union
from bson import ObjectId
from datetime import datetime


def serialize_objectid(obj: Any) -> Any:
    """
    Recursively convert MongoDB ObjectId to string for JSON serialization
    
    Args:
        obj: Object to serialize (can be dict, list, or primitive)
        
    Returns:
        Serialized object with ObjectId converted to string
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_objectid(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


def remove_objectid_field(doc: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Remove _id field from MongoDB document(s)
    
    Args:
        doc: Single document or list of documents
        
    Returns:
        Document(s) without _id field
    """
    if isinstance(doc, list):
        return [{k: v for k, v in d.items() if k != '_id'} for d in doc]
    elif isinstance(doc, dict):
        return {k: v for k, v in doc.items() if k != '_id'}
    else:
        return doc


def convert_objectid_to_str(doc: Union[Dict, List[Dict]]) -> Union[Dict, List[Dict]]:
    """
    Convert _id ObjectId to string in MongoDB document(s)
    
    Args:
        doc: Single document or list of documents
        
    Returns:
        Document(s) with _id converted to string
    """
    if isinstance(doc, list):
        result = []
        for d in doc:
            if '_id' in d and isinstance(d['_id'], ObjectId):
                d['_id'] = str(d['_id'])
            result.append(d)
        return result
    elif isinstance(doc, dict):
        if '_id' in doc and isinstance(doc['_id'], ObjectId):
            doc['_id'] = str(doc['_id'])
        return doc
    else:
        return doc

