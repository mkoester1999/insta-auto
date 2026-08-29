#!/usr/bin/env python3
"""Use Selenium to restore an Instagram session from the saved auth JSON
(instagram_auth.json) produced by save_instagram_auth.py."""

import argparse
import json
import os

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

DEFAULT_AUTH_FILE = "instagram_auth.json"
HOME_URL = "https://www.instagram.com/"


def load_auth(path):
    with open(path, "r") as f:
        return json.load(f)


def restore_session(auth_file=DEFAULT_AUTH_FILE, headless=False):
    """Create a Firefox driver, restore the saved Instagram session cookies onto
    it, and return the ready-to-use driver. The caller owns calling driver.quit().

    If headless is True, Firefox runs with a hidden window.
    """
    if not os.path.exists(auth_file):
        raise FileNotFoundError(f"Auth file not found: {auth_file}")

    auth = load_auth(auth_file)
    cookies = auth.get("cookies", [])
    saved_ua = (auth.get("headers") or {}).get("User-Agent")

    options = Options()
    options.enable_bidi = True  # keep parity with the save script
    if headless:
        options.add_argument("--headless")
    if saved_ua:
        options.set_preference("general.useragent.override", saved_ua)

    driver = Firefox(options=options)

    # Selenium requires being on the domain before adding cookies.
    driver.get(HOME_URL)

    added = 0
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if name is None or value is None:
            continue
        payload = {
            "name": name,
            "value": str(value),
            "domain": cookie.get("domain", ".instagram.com"),
            "path": cookie.get("path", "/"),
        }
        if cookie.get("secure"):
            payload["secure"] = True
        if cookie.get("sameSite") in ("Strict", "Lax", "None"):
            payload["sameSite"] = cookie["sameSite"]
        if cookie.get("expiry") is not None:
            payload["expiry"] = int(cookie["expiry"])
        driver.add_cookie(payload)
        added += 1

    print(f"Added {added}/{len(cookies)} cookie(s). Refreshing...")

    driver.get(HOME_URL)

    sessionid = None
    for cookie in driver.get_cookies():
        if cookie.get("name") == "sessionid":
            sessionid = cookie.get("value")
            break

    if sessionid:
        print("Session restored successfully (sessionid present).")
    else:
        print(
            "No 'sessionid' cookie after restore. The session may have expired "
            "or been invalidated.",
            file=sys.stderr,
        )

    return driver


def main():
    parser = argparse.ArgumentParser(description="Restore an Instagram session.")
    parser.add_argument("auth_file", nargs="?", default=DEFAULT_AUTH_FILE,
                        help="auth JSON file (default: instagram_auth.json)")
    parser.add_argument("--headless", action="store_true",
                        help="run Firefox with a hidden window")
    args = parser.parse_args()

    driver = None
    try:
        driver = restore_session(args.auth_file, headless=args.headless)
        if not args.headless:
            input("Press Enter to close the browser window...")
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()
