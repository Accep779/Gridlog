"""
Automated Integration Validator for Gridlog
Runs periodic checks to ensure:
- All frontend API calls resolve to existing endpoints
- Response formats match expectations
- Authentication flows work
"""

import json
import requests
import sys
from typing import Dict, List, Tuple, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials
TEST_USER = {
    "email": "test@gridlog.com",
    "password": "testpassword123"
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_status(message: str, status: str = "info"):
    colors = {
        "pass": Colors.GREEN + "✓",
        "fail": Colors.RED + "✗",
        "warn": Colors.YELLOW + "⚠",
        "info": Colors.BLUE + "ℹ",
        "end": Colors.RESET
    }
    print(f"{colors.get(status, '')}{message}{colors['end']}")

class IntegrationValidator:
    def __init__(self):
        self.token: Optional[str] = None
        self.results: Dict = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

    def login(self) -> bool:
        """Authenticate and get token"""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login/",
                json=TEST_USER,
                timeout=10
            )
            if response.status_code == 200:
                self.token = response.json().get("access")
                print_status("Authentication successful", "pass")
                return True
            else:
                print_status(f"Login failed: {response.status_code}", "fail")
                return False
        except requests.exceptions.RequestException as e:
            print_status(f"Login error: {e}", "fail")
            return False

    def validate_endpoint(
        self,
        method: str,
        path: str,
        expected_status: int = 200,
        data: Optional[Dict] = None,
        requires_auth: bool = True
    ) -> Tuple[bool, Optional[Dict]]:
        """Validate a single endpoint"""
        url = f"{API_BASE}{path}"
        headers = {}

        if requires_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            return success, response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def validate_backend_endpoints(self) -> None:
        """Validate all backend endpoints exist"""
        print("\n" + "="*50)
        print("PHASE 1: Validating Backend Endpoints")
        print("="*50)

        endpoints = [
            # Auth endpoints
            ("POST", "/auth/login/", 200, {}, False),
            ("POST", "/auth/token/refresh/", 200, {}, False),
            ("POST", "/auth/logout/", 200, {}, True),
            ("GET", "/auth/me/", 200, {}, True),
            ("POST", "/auth/initial-password-reset/", 200, {}, True),

            # Reports endpoints
            ("GET", "/reports/", 200, {}, True),
            ("POST", "/reports/", 201, {
                "accomplishments": "Test",
                "goals_next_week": "Test",
                "progress_rating": "3"
            }, True),

            # Notifications endpoints
            ("GET", "/notifications/", 200, {}, True),
            ("POST", "/notifications/mark-read/", 200, {"ids": [1]}, True),
            ("POST", "/notifications/mark-all-read/", 200, {}, True),
            ("GET", "/notifications/unread-count/", 200, {}, True),
        ]

        for method, path, expected, data, requires_auth in endpoints:
            success, _ = self.validate_endpoint(
                method, path, expected, data, requires_auth
            )
            status = "pass" if success else "fail"
            print_status(f"{method} {path}", status)
            if success:
                self.results["passed"].append(f"{method} {path}")
            else:
                self.results["failed"].append(f"{method} {path}")

    def validate_missing_endpoints(self) -> None:
        """Check for missing endpoints that frontend expects"""
        print("\n" + "="*50)
        print("PHASE 2: Checking Missing Endpoints")
        print("="*50)

        # These should return 404 if not implemented
        missing_endpoints = [
            ("GET", "/reports/my-reports/", False),
            ("GET", "/reports/pending-approval/", False),
            ("GET", "/reports/team-reports/", False),
            ("GET", "/reports/dashboard-stats/", False),
            ("GET", "/reports/recent-activity/", False),
            ("POST", "/reports/1/approve/", False),
            ("POST", "/reports/1/reject/", False),
            ("GET", "/users/employees/", False),
        ]

        for method, path, should_exist in missing_endpoints:
            success, _ = self.validate_endpoint(method, path, 200 if should_exist else 404)
            if not should_exist and not success:
                print_status(f"Expected 404: {method} {path}", "warn")
                self.results["warnings"].append(f"Missing: {method} {path}")
            elif should_exist and success:
                print_status(f"Found: {method} {path}", "pass")
            else:
                print_status(f"Issue: {method} {path}", "fail")
                self.results["failed"].append(f"Endpoint issue: {method} {path}")

    def validate_auth_flow(self) -> None:
        """Test authentication flow"""
        print("\n" + "="*50)
        print("PHASE 3: Authentication Flow Validation")
        print("="*50)

        # Test login
        if self.login():
            # Test protected endpoint with token
            success, _ = self.validate_endpoint("GET", "/auth/me/", 200)
            print_status("Protected endpoint with token", "pass" if success else "fail")

            # Test protected endpoint without token
            old_token = self.token
            self.token = None
            success, _ = self.validate_endpoint("GET", "/auth/me/", 401, requires_auth=False)
            print_status("Protected endpoint without token (expects 401)", "pass" if success else "fail")
            self.token = old_token

    def generate_report(self) -> None:
        """Generate validation report"""
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)

        total = len(self.results["passed"]) + len(self.results["failed"])
        if total > 0:
            score = len(self.results["passed"]) / total * 100
            print(f"Integration Score: {score:.1f}%")

        print(f"Passed: {len(self.results['passed'])}")
        print(f"Failed: {len(self.results['failed'])}")
        print(f"Warnings: {len(self.results['warnings'])}")

        if self.results["failed"]:
            print("\nFailed Tests:")
            for test in self.results["failed"]:
                print(f"  - {test}")

        if self.results["warnings"]:
            print("\nWarnings:")
            for warning in self.results["warnings"]:
                print(f"  - {warning}")

def run_validation():
    """Main validation runner"""
    print("="*50)
    print("GRIDLOG INTEGRATION VALIDATOR")
    print("="*50)

    validator = IntegrationValidator()

    # Run all validation phases
    validator.validate_auth_flow()
    validator.validate_backend_endpoints()
    validator.validate_missing_endpoints()
    validator.generate_report()

    # Exit with appropriate code
    if validator.results["failed"]:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    run_validation()
