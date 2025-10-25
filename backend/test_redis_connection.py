"""Test Redis connection."""
import redis
import sys

# Your Redis URL
REDIS_URL = "redis://default:MNI6xU3YrFLdSlkyngCHy9HYt3al7F3h@redis-13891.c270.us-east-1-3.ec2.redns.redis-cloud.com:13891"

def test_redis_connection():
    """Test Redis connection and basic operations."""
    try:
        print("🔄 Connecting to Redis...")
        print(f"URL: {REDIS_URL[:50]}...")
        
        # Create Redis client
        r = redis.StrictRedis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        print("✅ Pinging Redis...")
        response = r.ping()
        print(f"✅ Redis PING successful: {response}")
        
        # Test set/get
        print("\n🔄 Testing SET operation...")
        r.set("zyana:test", "Hello from Zyana!", ex=60)  # Expires in 60 seconds
        print("✅ SET successful")
        
        print("🔄 Testing GET operation...")
        value = r.get("zyana:test")
        print(f"✅ GET successful: {value}")
        
        # Test session-like data
        print("\n🔄 Testing session data (JSON)...")
        import json
        session_data = {
            "user_id": "test_user",
            "intent": "schedule_meeting",
            "pending_fields": ["datetime"],
            "conversation_history": ["User: Schedule meeting", "Assistant: When?"]
        }
        r.set("zyana:session:test", json.dumps(session_data), ex=600)
        retrieved = json.loads(r.get("zyana:session:test"))
        print(f"✅ Session data stored and retrieved: {retrieved['intent']}")
        
        # Get info
        print("\n📊 Redis Info:")
        info = r.info()
        print(f"  - Redis Version: {info.get('redis_version')}")
        print(f"  - Connected Clients: {info.get('connected_clients')}")
        print(f"  - Used Memory: {info.get('used_memory_human')}")
        print(f"  - Database Keys: {r.dbsize()}")
        
        # Cleanup
        print("\n🧹 Cleaning up test keys...")
        r.delete("zyana:test", "zyana:session:test")
        print("✅ Cleanup complete")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - Redis is working perfectly!")
        print("="*60)
        return True
        
    except redis.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if Redis URL is correct")
        print("  2. Verify network connectivity")
        print("  3. Check firewall settings")
        return False
        
    except redis.TimeoutError as e:
        print(f"\n❌ TIMEOUT ERROR: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Redis server might be slow or overloaded")
        print("  2. Check network latency")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)

