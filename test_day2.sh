#!/bin/bash

# SPARK Coach API - Day 2 Test Script
# Tests morning briefing agent and learning system

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8080"
API_KEY="${SPARK_COACH_API_KEY:-dev_test_key_12345}"

echo "=========================================="
echo "SPARK Coach API - Day 2 Test Suite"
echo "Testing: Learning Schema & Briefing Agent"
echo "=========================================="
echo ""

# Test 1: Quick Briefing (No LLM)
echo -e "${YELLOW}Test 1: Quick Briefing (Stats Only)${NC}"
echo "This tests vault connectivity without LLM calls..."
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: ${API_KEY}" ${API_URL}/api/v1/briefing/quick)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Quick briefing returned 200"
    echo "$BODY" | python3 -m json.tool

    # Parse and display key stats
    REVIEWS_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('quick_briefing', {}).get('reviews_due_count', 0))" 2>/dev/null || echo "N/A")
    AT_RISK=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('quick_briefing', {}).get('at_risk_count', 0))" 2>/dev/null || echo "N/A")
    PATH=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('quick_briefing', {}).get('learning_path', 'None'))" 2>/dev/null || echo "N/A")

    echo ""
    echo -e "${BLUE}Quick Stats:${NC}"
    echo "  Reviews Due: $REVIEWS_COUNT"
    echo "  At Risk: $AT_RISK"
    echo "  Learning Path: $PATH"
else
    echo -e "${RED}✗ FAIL${NC} - Quick briefing returned $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 2: Full Briefing (With LLM)
echo -e "${YELLOW}Test 2: Full Morning Briefing (With LLM)${NC}"
echo "This tests LLM integration and personalized coaching..."
echo "Note: This may take 2-3 seconds for LLM generation..."
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: ${API_KEY}" ${API_URL}/api/v1/briefing)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Full briefing returned 200"
    echo "$BODY" | python3 -m json.tool

    # Parse and display key fields
    GREETING=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('briefing', {}).get('greeting', 'N/A'))" 2>/dev/null || echo "N/A")
    REVIEWS_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('briefing', {}).get('reviews_count', 0))" 2>/dev/null || echo "0")
    NUDGES_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('briefing', {}).get('nudges', [])))" 2>/dev/null || echo "0")

    echo ""
    echo -e "${BLUE}Briefing Summary:${NC}"
    echo "  Greeting: $GREETING"
    echo "  Reviews Due: $REVIEWS_COUNT"
    echo "  Nudges: $NUDGES_COUNT"

elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "${YELLOW}⚠ WARNING${NC} - Briefing returned 500"
    echo "This could mean:"
    echo "  1. Vault not configured with learning schema"
    echo "  2. MCP server not reachable"
    echo "  3. Anthropic API key not set or invalid"
    echo ""
    echo "Error details:"
    echo "$BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ FAIL${NC} - Briefing returned $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 3: Vault Prerequisites Check
echo -e "${YELLOW}Test 3: Vault Prerequisites${NC}"
echo "Checking if vault has required structure..."

# Try to search for learning paths
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: ${API_KEY}" "${API_URL}/api/v1/mcp/search?query=type:%20learning_path&folder=02_projects")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    RESULTS_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('results', [])))" 2>/dev/null || echo "0")

    if [ "$RESULTS_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Found $RESULTS_COUNT learning path(s) in vault"
    else
        echo -e "${YELLOW}⚠ WARNING${NC} - No learning paths found in vault"
        echo "Follow the setup guide: templates/VAULT-SETUP-GUIDE.md"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Could not search vault (MCP server issue)"
fi

# Try to search for active resources
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: ${API_KEY}" "${API_URL}/api/v1/mcp/search?query=learning_status:%20active&folder=04_resources")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    RESULTS_COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('results', [])))" 2>/dev/null || echo "0")

    if [ "$RESULTS_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Found $RESULTS_COUNT active resource(s) in vault"
    else
        echo -e "${YELLOW}⚠ WARNING${NC} - No active resources found in vault"
        echo "Add learning metadata to resources: templates/VAULT-SETUP-GUIDE.md"
    fi
else
    echo -e "${RED}✗ FAIL${NC} - Could not search vault (MCP server issue)"
fi
echo ""

echo "=========================================="
echo "Day 2 Test Summary"
echo "=========================================="
echo ""
echo "Components Tested:"
echo "  ✓ Quick briefing endpoint (no LLM)"
echo "  ✓ Full briefing endpoint (with LLM)"
echo "  ✓ Vault prerequisites check"
echo ""
echo "Next Steps:"
echo ""
echo "1. If tests passed but briefing is empty:"
echo "   → Configure your vault using templates/VAULT-SETUP-GUIDE.md"
echo ""
echo "2. If MCP errors occurred:"
echo "   → Ensure MCP server is running"
echo "   → Check MCP_SERVER_URL in .env"
echo ""
echo "3. If LLM errors occurred:"
echo "   → Verify ANTHROPIC_API_KEY in .env"
echo "   → Check API key has sufficient credits"
echo ""
echo "4. To create learning path and resources:"
echo "   → See templates/obsidian/learning-path-template.md"
echo "   → See templates/obsidian/resource-with-learning-metadata.md"
echo ""
echo "=========================================="
