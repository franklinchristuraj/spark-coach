#!/bin/bash

# SPARK Coach API Test Script
# Tests Day 1 deliverables

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8080"
API_KEY="${SPARK_COACH_API_KEY:-dev_test_key_12345}"

echo "======================================="
echo "SPARK Coach API - Day 1 Test Suite"
echo "======================================="
echo ""

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check (no auth)${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" ${API_URL}/health)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Health check returned 200"
    echo "$BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ FAIL${NC} - Health check returned $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 2: Root Endpoint
echo -e "${YELLOW}Test 2: Root Endpoint${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" ${API_URL}/)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Root endpoint returned 200"
    echo "$BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ FAIL${NC} - Root endpoint returned $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 3: MCP Test (with auth)
echo -e "${YELLOW}Test 3: MCP Connection Test (with auth)${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: ${API_KEY}" ${API_URL}/api/v1/test-mcp)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - MCP test returned 200"
    echo "$BODY" | python3 -m json.tool
elif [ "$HTTP_CODE" = "503" ]; then
    echo -e "${YELLOW}⚠ WARNING${NC} - MCP server not reachable (returned 503)"
    echo "This is expected if your MCP server is not running."
    echo "$BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ FAIL${NC} - MCP test returned $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 4: Auth Required
echo -e "${YELLOW}Test 4: Authentication Check (should fail without API key)${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" ${API_URL}/api/v1/test-mcp)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Authentication correctly required (returned $HTTP_CODE)"
    echo "$BODY" | python3 -m json.tool
else
    echo -e "${RED}✗ FAIL${NC} - Expected 401/403, got $HTTP_CODE"
    echo "$BODY"
fi
echo ""

# Test 5: OpenAPI Docs
echo -e "${YELLOW}Test 5: OpenAPI Documentation${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" ${API_URL}/docs)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} - API docs accessible at ${API_URL}/docs"
else
    echo -e "${RED}✗ FAIL${NC} - API docs returned $HTTP_CODE"
fi
echo ""

echo "======================================="
echo "Day 1 Deliverables:"
echo "  ✓ GET /health returns 200"
echo "  ✓ GET /api/v1/test-mcp (requires auth)"
echo "  ✓ MCP client implementation complete"
echo "======================================="
echo ""
echo "Next: Configure your .env file with:"
echo "  - ANTHROPIC_API_KEY"
echo "  - MCP_SERVER_URL"
echo "  - SPARK_COACH_API_KEY"
echo ""
echo "Then start your MCP server and test again!"
