#!/usr/bin/env python3
"""
CDP Batch Job
Main entry point for batch processing (simulates nightly Spark job).
"""
from config import settings
from config.logging_config import setup_logging, get_logger
from src.python.common.database import get_mongodb_client
from .profile_processor import ProfileProcessor

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)


def print_summary(processor: ProfileProcessor) -> None:
    """
    Print batch job summary.
    
    Args:
        processor: Profile processor instance
    """
    logger.info("=" * 60)
    logger.info("BATCH JOB SUMMARY")
    logger.info("=" * 60)
    
    stats = processor.get_summary_stats()
    
    if stats:
        logger.info(f"\n📊 Profiles Processed: {stats.get('total_profiles', 0)}")
        logger.info(f"💰 Total LTV: ${stats.get('total_ltv', 0):,.2f}")
        logger.info(f"📈 Avg Engagement Score: {stats.get('avg_engagement', 0):.1f}/100")
        logger.info(f"📝 Total Events: {stats.get('total_events', 0)}")
    
    logger.info("\n🏆 Top Profiles by Lifetime Value:")
    logger.info("-" * 60)
    
    top_profiles = processor.get_top_profiles(limit=5)
    
    for idx, profile in enumerate(top_profiles, 1):
        email = profile.get("identities", {}).get("email", "N/A")
        ltv = profile.get("computed_attributes", {}).get("lifetime_value", 0)
        engagement = profile.get("computed_attributes", {}).get("engagement_score", 0)
        logger.info(f"{idx}. {email:30} | LTV: ${ltv:8,.2f} | Engagement: {engagement:3}/100")
    
    logger.info("\n" + "=" * 60)


def main() -> None:
    """Main entry point for batch processing."""
    logger.info("=" * 60)
    logger.info("CDP BATCH JOB - Mock Spark Processing")
    logger.info("=" * 60)
    logger.info("\nThis simulates a nightly Spark job that:")
    logger.info("  1. Reads profiles from MongoDB")
    logger.info("  2. Computes aggregate metrics")
    logger.info("  3. Writes computed attributes back")
    logger.info("")
    
    try:
        # Connect to MongoDB
        client = get_mongodb_client()
        logger.info(f"Connected to database: {settings.MONGO_DB}")
        
        # Create processor
        processor = ProfileProcessor(client, settings.MONGO_DB)
        
        # Process profiles
        total_processed = processor.process_all_profiles(limit=settings.BATCH_PROFILE_LIMIT)
        
        if total_processed > 0:
            # Print summary
            print_summary(processor)
            
            logger.info("\n💡 View results in MongoDB Compass:")
            logger.info("   Database: cdp")
            logger.info("   Collection: profiles")
            logger.info("   Look for: computed_attributes field")
        
    except Exception as e:
        logger.error(f"Batch job failed: {e}", exc_info=True)
        raise
    finally:
        client.close()
        logger.info("\n👋 Batch job finished.\n")


if __name__ == "__main__":
    main()
