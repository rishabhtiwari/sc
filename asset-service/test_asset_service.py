"""
Asset Service Test Script
Quick test to verify the asset service is working
"""
import requests
import json
import os
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:8099"
# You'll need to get a real JWT token from your auth system
JWT_TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}"
}


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_root():
    """Test root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_upload_audio():
    """Test audio upload"""
    print("Testing audio upload...")
    
    # Create a dummy audio file
    audio_data = b"RIFF" + b"\x00" * 100  # Dummy WAV header
    
    files = {
        'file': ('test.wav', BytesIO(audio_data), 'audio/wav')
    }
    
    data = {
        'asset_type': 'audio',
        'name': 'Test Audio',
        'folder': 'Test',
        'title': 'Test Audio Title',
        'description': 'This is a test audio',
        'tags': 'test,audio,demo'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/assets/upload",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json().get('asset_id')
    
    print()
    return None


def test_list_assets():
    """Test listing assets"""
    print("Testing list assets...")
    response = requests.get(
        f"{BASE_URL}/api/assets/",
        headers=headers,
        params={'page': 1, 'page_size': 10}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_get_asset(asset_id):
    """Test getting asset metadata"""
    print(f"Testing get asset {asset_id}...")
    response = requests.get(
        f"{BASE_URL}/api/assets/{asset_id}",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_get_asset_url(asset_id):
    """Test getting pre-signed URL"""
    print(f"Testing get asset URL {asset_id}...")
    response = requests.get(
        f"{BASE_URL}/api/assets/{asset_id}/url",
        headers=headers,
        params={'expires_hours': 1}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_audio_library():
    """Test audio library endpoints"""
    print("Testing audio library save...")
    
    data = {
        "text": "This is a test audio",
        "audio_url": "http://example.com/test.wav",
        "duration": 5.5,
        "voice": "af_sky",
        "voice_name": "Sky",
        "language": "en",
        "speed": 1.0,
        "model": "kokoro-82m",
        "folder": "Test",
        "tags": ["test", "demo"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/audio-library/",
        headers=headers,
        json=data
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # List audio library
    print("Testing audio library list...")
    response = requests.get(
        f"{BASE_URL}/api/audio-library/",
        headers=headers,
        params={'page': 1, 'page_size': 10}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Asset Service Test Suite")
    print("=" * 60)
    print()
    
    # Test without authentication
    test_health()
    test_root()
    
    # Note: The following tests require a valid JWT token
    print("Note: The following tests require a valid JWT token")
    print("Update JWT_TOKEN variable with a real token to test authenticated endpoints")
    print()
    
    # Uncomment when you have a valid token
    # test_list_assets()
    # asset_id = test_upload_audio()
    # if asset_id:
    #     test_get_asset(asset_id)
    #     test_get_asset_url(asset_id)
    # test_audio_library()

