"""
Integration Tests for Neo4j
Tests graph database operations with actual Neo4j instance.
"""
import pytest


@pytest.mark.integration
class TestNeo4jIntegration:
    """Integration tests for Neo4j operations."""
    
    def test_neo4j_connection(self, neo4j_driver):
        """Test Neo4j connection."""
        assert neo4j_driver is not None
        
        # Test simple query
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 as num")
            record = result.single()
            assert record["num"] == 1
    
    def test_create_profile_node(self, neo4j_driver):
        """Test creating a profile node."""
        with neo4j_driver.session() as session:
            result = session.run(
                """
                CREATE (p:Profile {profileId: $profileId, email: $email})
                RETURN p
                """,
                profileId="test_profile_001",
                email="neo4j@test.com"
            )
            
            record = result.single()
            assert record is not None
            assert record["p"]["profileId"] == "test_profile_001"
    
    def test_create_identity_relationship(self, neo4j_driver):
        """Test creating profile-identity relationships."""
        with neo4j_driver.session() as session:
            # Create profile and identities
            session.run(
                """
                CREATE (p:Profile {profileId: 'test_002'})
                CREATE (e:Identity {type: 'email', value: 'test@example.com'})
                CREATE (d:Identity {type: 'deviceID', value: 'device_123'})
                CREATE (p)-[:HAS_IDENTITY]->(e)
                CREATE (p)-[:HAS_IDENTITY]->(d)
                """
            )
            
            # Query relationships
            result = session.run(
                """
                MATCH (p:Profile {profileId: 'test_002'})-[:HAS_IDENTITY]->(i:Identity)
                RETURN count(i) as identityCount
                """
            )
            
            record = result.single()
            assert record["identityCount"] == 2
    
    def test_identity_stitching_scenario(self, neo4j_driver):
        """Test identity stitching (profile merge scenario)."""
        with neo4j_driver.session() as session:
            # Create two profiles with shared email
            session.run(
                """
                CREATE (p1:Profile {profileId: 'profile_A'})
                CREATE (p2:Profile {profileId: 'profile_B'})
                CREATE (email:Identity {type: 'email', value: 'shared@example.com'})
                CREATE (d1:Identity {type: 'deviceID', value: 'device_A'})
                CREATE (d2:Identity {type: 'deviceID', value: 'device_B'})
                CREATE (p1)-[:HAS_IDENTITY]->(d1)
                CREATE (p2)-[:HAS_IDENTITY]->(d2)
                CREATE (p1)-[:HAS_IDENTITY]->(email)
                CREATE (p2)-[:HAS_IDENTITY]->(email)
                """
            )
            
            # Find profiles sharing same email
            result = session.run(
                """
                MATCH (email:Identity {type: 'email', value: 'shared@example.com'})
                <-[:HAS_IDENTITY]-(p:Profile)
                RETURN collect(p.profileId) as profiles
                """
            )
            
            record = result.single()
            profiles = record["profiles"]
            assert len(profiles) == 2
            assert 'profile_A' in profiles
            assert 'profile_B' in profiles
