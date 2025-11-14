"""
MongoDB Connectivity Test
This script verifies that Python can connect to the MongoDB Docker container.
"""

from pymongo import MongoClient
from datetime import datetime

def test_mongodb_connection():
    print("=" * 50)
    print("Testing MongoDB Connection...")
    print("=" * 50)
    
    try:
        # Connection string from docker-compose.yml
        client = MongoClient(
            "mongodb://admin:password123@localhost:27017/",
            serverSelectionTimeoutMS=5000
        )
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        
        # Create a test database and collection
        db = client['cdp_test']
        collection = db['test_collection']
        
        # Insert a test document
        test_doc = {
            "test_id": "test_001",
            "message": "Hello from Python!",
            "timestamp": datetime.utcnow(),
            "source": "Day 2 connectivity test"
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Inserted test document with ID: {result.inserted_id}")
        
        # Read it back
        retrieved = collection.find_one({"test_id": "test_001"})
        print(f"✅ Retrieved document: {retrieved['message']}")
        
        # Count documents
        count = collection.count_documents({})
        print(f"✅ Total documents in test_collection: {count}")
        
        # Clean up (optional - comment out if you want to see it in Compass)
        # collection.delete_many({})
        # print("✅ Cleaned up test documents")
        
        client.close()
        print("\n" + "=" * 50)
        print("MongoDB connectivity test PASSED! ✅")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ MongoDB connection FAILED!")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure docker-compose is running: docker-compose ps")
        print("2. Check MongoDB logs: docker-compose logs mongodb")
        print("3. Verify port 27017 is not blocked")

if __name__ == "__main__":
    test_mongodb_connection()