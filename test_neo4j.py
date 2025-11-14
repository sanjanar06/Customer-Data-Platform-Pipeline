"""
Day 2: Neo4j Connectivity Test
This script verifies that Python can connect to the Neo4j Docker container.
"""

from neo4j import GraphDatabase
from datetime import datetime

def test_neo4j_connection():
    print("=" * 50)
    print("Testing Neo4j Connection...")
    print("=" * 50)
    
    try:
        # Connection details from docker-compose.yml
        uri = "bolt://localhost:7687"
        username = "neo4j"
        password = "password123"
        
        # Create driver
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Test the connection
        driver.verify_connectivity()
        print("✅ Connected to Neo4j successfully!")
        
        # Create a test node
        with driver.session() as session:
            # Create a test Person node
            result = session.run("""
                CREATE (p:TestPerson {
                    name: $name,
                    test_id: $test_id,
                    timestamp: datetime()
                })
                RETURN p.name AS name, p.test_id AS test_id
            """, name="Day 2 Test User", test_id="test_001")
            
            record = result.single()
            print(f"✅ Created test node: {record['name']} (ID: {record['test_id']})")
            
            # Count test nodes
            count_result = session.run("""
                MATCH (p:TestPerson)
                RETURN count(p) AS count
            """)
            count = count_result.single()["count"]
            print(f"✅ Total TestPerson nodes in database: {count}")
            
            # Clean up (optional - comment out if you want to see it in Neo4j Browser)
            # session.run("MATCH (p:TestPerson) DELETE p")
            # print("✅ Cleaned up test nodes")
        
        driver.close()
        print("\n" + "=" * 50)
        print("Neo4j connectivity test PASSED! ✅")
        print("=" * 50)
        print("\nTip: Go to http://localhost:7474 and run:")
        print("MATCH (p:TestPerson) RETURN p")
        print("to see your test node in the Neo4j Browser!")
        
    except Exception as e:
        print(f"\n❌ Neo4j connection FAILED!")
        print(f"Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure docker-compose is running: docker-compose ps")
        print("2. Check Neo4j logs: docker-compose logs neo4j")
        print("3. Verify credentials: neo4j / password123")
        print("4. Make sure port 7687 is not blocked")

if __name__ == "__main__":
    test_neo4j_connection()