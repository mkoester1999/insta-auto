#!/usr/bin/env python3
"""Open Firefox, let the user log in to Instagram, then save the HttpOnly cookies
and the exact request headers needed to replay an authenticated request to JSON."""

import sys
import time
import json

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

LOGIN_URL = "https://www.instagram.com/accounts/login/"
HOME_URL = "https://www.instagram.com/"
OUTPUT_FILE = "instagram_auth.json"
POLL_INTERVAL = 2
TIMEOUT_SECONDS = 10 * 60  # 10 minutes
SESSION_COOKIE = "sessionid"


def wait_for_session_cookie(driver, timeout):
    """Poll until the sessionid HttpOnly cookie appears (indicates logged in)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for cookie in driver.get_cookies():
            if cookie.get("name") == SESSION_COOKIE:
                return True
        time.sleep(POLL_INTERVAL)
    return False


def _headers_to_dict(headers):
    """Convert a BiDi header list to a name -> value mapping."""
    result = {}
    for header in headers or []:
        if isinstance(header, dict):
            value = header.get("value")
            if isinstance(value, dict) and value.get("type") == "string":
                value = value.get("value")
            result[header.get("name")] = value
    return result


def capture_request_headers(driver, url):
    """Use WebDriver BiDi to capture the exact request headers fired for the
    main document request to `url`. Returns (url, method, headers) or
    (None, None, {}).

    Uses a passive event listener (no intercept), so requests are observed
    without being paused/blocked.
    """
    seen = {}

    def on_before_request(params):
        if isinstance(params, dict):
            req = params.get("request", {}) or {}
        else:
            req = getattr(params, "request", {}) or {}
        if not isinstance(req, dict):
            req = req.__dict__ if hasattr(req, "__dict__") else {}
        seen[req.get("url", "")] = {
            "method": req.get("method"),
            "headers": _headers_to_dict(req.get("headers")),
        }

    cb_id = driver.network.add_event_handler("before_request_sent", on_before_request)

    try:
        driver.get(url)
        time.sleep(3)  # let the page/request settle
    finally:
        driver.network.remove_event_handler("before_request_sent", cb_id)

    if url in seen:
        return url, seen[url]["method"], seen[url]["headers"]
    if seen:
        last_url = next(reversed(seen))
        last = seen[last_url]
        return last_url, last["method"], last["headers"]
    return None, None, {}


def main():
    options = Options()
    options.enable_bidi = True  # required for WebDriver BiDi network capture in Firefox
    # options.add_argument("--headless")  # NOT recommended for interactive login

    driver = Firefox(options=options)
    try:
        driver.get(LOGIN_URL)
        print(
            f"Log in to Instagram in the opened Firefox window.\n"
            f"Waiting (up to {TIMEOUT_SECONDS // 60} min) for the session cookie..."
        )

        if not wait_for_session_cookie(driver, TIMEOUT_SECONDS):
            print("Timed out waiting for login. No session cookie found.", file=sys.stderr)
            sys.exit(1)

        print("Login detected. Capturing request headers...")
        req_url, req_method, req_headers = capture_request_headers(driver, HOME_URL)

        cookies = [c for c in driver.get_cookies() if c.get("httpOnly") is True]

        data = {
            "url": req_url,
            "method": req_method,
            "headers": req_headers,
            "cookies": cookies,
        }

        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved to {OUTPUT_FILE}")
        print(f"  url:    {data['url']}")
        print(f"  method: {data['method']}")
        print(f"  headers: {len(data['headers'])} key(s)")
        print(f"  httpOnly cookies: {len(data['cookies'])}")
        for c in cookies:
            print(f"    - {c['name']}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
