#!/bin/bash
# Monitor Content Understanding processing
echo "🔍 Monitoring Content Understanding pipeline..."
echo "📄 Processing can take 3-5 minutes for documents with figures"
echo ""

for i in {1..20}; do
    echo "📊 Check $i/20 ($(date +%H:%M:%S))"
    
    # Check if server is still running
    if ! pgrep -f "python api_server.py" > /dev/null; then
        echo "❌ API server stopped"
        break
    fi
    
    # Get last few log lines
    tail -2 api_server.log | grep -E "(INFO|ERROR|Processing|Analyzing|analyzing|completed|failed)" || echo "   🔄 Still processing..."
    
    echo ""
    sleep 15
done

echo "✅ Monitoring complete"
