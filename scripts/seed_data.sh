set -e

echo "=========================================="
echo "Seeding Test Data"
echo "=========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Running producer to generate test events..."
echo "This will generate 7 demo events for identity stitching"
echo ""

# Run producer in demo mode (one iteration)
python run_producer.py --mode demo --interval 1

echo ""
echo "=========================================="
echo "✅ Test Data Seeded!"
echo "=========================================="
echo ""
echo "Check data:"
echo "  - MongoDB: Use Mongo Express at http://localhost:8082"
echo "  - Neo4j: Use Neo4j Browser at http://localhost:7474"
echo ""
echo "Run batch job to compute metrics:"
echo "  python run_batch.py"
echo ""
