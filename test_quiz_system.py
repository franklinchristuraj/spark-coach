#!/usr/bin/env python3
"""
Test script for SPARK Coach Quiz System
Tests the complete quiz flow: start -> answer -> complete
"""
import requests
import json
import sys
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
API_KEY = os.getenv("SPARK_COACH_API_KEY", "dev_test_key_12345")

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_status(message: str, status: str = "info"):
    """Print colored status message"""
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    color = colors.get(status, RESET)
    print(f"{color}{message}{RESET}")


def make_request(method: str, endpoint: str, data: Dict = None, token: str = None) -> Dict[str, Any]:
    """Make API request with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print_status(f"Request failed: {str(e)}", "error")
        if hasattr(e, 'response') and e.response:
            print_status(f"Response: {e.response.text}", "error")
        raise


def test_health_check():
    """Test 1: Health check"""
    print_status("\n=== Test 1: Health Check ===", "info")
    try:
        result = make_request("GET", "/health")
        print_status(f"✓ Health check passed: {result.get('status')}", "success")
        return True
    except Exception as e:
        print_status(f"✗ Health check failed: {str(e)}", "error")
        return False


def test_login():
    """Test 2: Login and get token"""
    print_status("\n=== Test 2: Login ===", "info")
    try:
        # Try login endpoint
        result = make_request("POST", "/auth/login", {
            "username": "franklin",
            "password": API_KEY
        })
        
        token = result.get("access_token")
        if token:
            print_status(f"✓ Login successful, got token: {token[:20]}...", "success")
            return token
        else:
            print_status("✗ Login failed: No token returned", "error")
            return None
    except Exception as e:
        print_status(f"✗ Login failed: {str(e)}", "error")
        return None


def test_start_quiz(token: str, resource_path: str = "04_resources/test-resource.md"):
    """Test 3: Start a quiz session"""
    print_status("\n=== Test 3: Start Quiz ===", "info")
    try:
        result = make_request("POST", "/api/v1/quiz/start", {
            "resource_path": resource_path,
            "num_questions": 3,
            "difficulty": "medium"
        }, token)
        
        session_id = result.get("session_id")
        question = result.get("current_question")
        
        print_status(f"✓ Quiz started successfully", "success")
        print_status(f"  Session ID: {session_id}", "info")
        print_status(f"  Total questions: {result.get('total_questions')}", "info")
        print_status(f"  First question: {question.get('question')}", "info")
        print_status(f"  Question type: {question.get('type')}", "info")
        
        return result
    except Exception as e:
        print_status(f"✗ Start quiz failed: {str(e)}", "error")
        return None


def test_answer_question(token: str, session_id: str, question_index: int, answer: str):
    """Test 4: Submit an answer"""
    print_status(f"\n=== Test 4: Submit Answer (Q{question_index}) ===", "info")
    try:
        result = make_request("POST", "/api/v1/quiz/answer", {
            "session_id": session_id,
            "question_index": question_index,
            "answer": answer
        }, token)
        
        correct = result.get("correct")
        score = result.get("score")
        feedback = result.get("feedback")
        quiz_complete = result.get("quiz_complete")
        
        status_emoji = "✓" if correct else "✗"
        status_color = "success" if correct else "warning"
        
        print_status(f"{status_emoji} Answer submitted", status_color)
        print_status(f"  Correct: {correct}", status_color)
        print_status(f"  Score: {score}/100", status_color)
        print_status(f"  Feedback: {feedback[:100]}...", "info")
        print_status(f"  Quiz complete: {quiz_complete}", "info")
        
        if quiz_complete:
            final_score = result.get("final_score")
            retention_updated = result.get("retention_updated")
            print_status(f"  Final score: {final_score}/100", "success")
            print_status(f"  Retention updated: {retention_updated}", "success")
        else:
            next_q = result.get("next_question")
            if next_q:
                print_status(f"  Next question: {next_q.get('question')}", "info")
        
        return result
    except Exception as e:
        print_status(f"✗ Submit answer failed: {str(e)}", "error")
        return None


def test_get_session(token: str, session_id: str):
    """Test 5: Get quiz session status"""
    print_status(f"\n=== Test 5: Get Session Status ===", "info")
    try:
        result = make_request("GET", f"/api/v1/quiz/session/{session_id}", token=token)
        
        session = result.get("session")
        print_status(f"✓ Session retrieved", "success")
        print_status(f"  Status: {session.get('status')}", "info")
        print_status(f"  Correct answers: {session.get('correct_answers')}/{session.get('total_questions')}", "info")
        print_status(f"  Final score: {session.get('score')}", "info")
        
        return result
    except Exception as e:
        print_status(f"✗ Get session failed: {str(e)}", "error")
        return None


def run_full_quiz_flow(resource_path: str = "04_resources/test-resource.md"):
    """Run complete quiz flow"""
    print_status("\n" + "="*60, "info")
    print_status("SPARK COACH QUIZ SYSTEM - FULL TEST", "info")
    print_status("="*60, "info")
    
    # Test 1: Health check
    if not test_health_check():
        print_status("\n❌ Backend is not running. Start it with:", "error")
        print_status("  source venv/bin/activate && python backend/main.py", "info")
        return False
    
    # Test 2: Login
    token = test_login()
    if not token:
        print_status("\n❌ Authentication failed. Check your credentials.", "error")
        return False
    
    # Test 3: Start quiz
    quiz_start = test_start_quiz(token, resource_path)
    if not quiz_start:
        print_status(f"\n❌ Failed to start quiz for resource: {resource_path}", "error")
        print_status("Make sure the resource exists in your vault.", "warning")
        return False
    
    session_id = quiz_start.get("session_id")
    total_questions = quiz_start.get("total_questions")
    
    # Test 4: Answer all questions
    sample_answers = [
        "This is a test answer demonstrating understanding of the concept.",
        "The key principle here is to apply the knowledge in practical scenarios.",
        "This connects to other areas by showing how ideas interrelate."
    ]
    
    for i in range(1, total_questions + 1):
        answer = sample_answers[i - 1] if i <= len(sample_answers) else "Test answer"
        result = test_answer_question(token, session_id, i, answer)
        
        if not result:
            print_status(f"\n❌ Failed to submit answer {i}", "error")
            return False
    
    # Test 5: Get final session status
    test_get_session(token, session_id)
    
    print_status("\n" + "="*60, "info")
    print_status("✓ ALL TESTS PASSED", "success")
    print_status("="*60, "info")
    
    return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SPARK Coach Quiz System")
    parser.add_argument(
        "--resource",
        default="04_resources/test-resource.md",
        help="Resource path to test with"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8080",
        help="API base URL"
    )
    
    args = parser.parse_args()
    
    global API_BASE_URL
    API_BASE_URL = args.api_url
    
    try:
        success = run_full_quiz_flow(args.resource)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("\n\nTest interrupted by user", "warning")
        sys.exit(1)
    except Exception as e:
        print_status(f"\n\n❌ Unexpected error: {str(e)}", "error")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
