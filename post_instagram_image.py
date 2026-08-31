#!/usr/bin/env python3
"""Restore the saved Instagram session (via restore_instagram_session) and post
a PNG image from the current directory to the user's feed.

Usage:
    python3 post_instagram_image.py [path/to/image.png]
"""

import argparse
import glob
import os
import sys

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from restore_instagram_session import restore_session

HOME_URL = "https://www.instagram.com/"


def find_image():
    """Return the full path of the PNG in the current directory, or None."""
    pngs = glob.glob(os.path.join(os.getcwd(), "*.png"))
    if pngs:
        return pngs[0]
    return None


def dismiss_notifications_popup(driver, timeout=5):
    """Dismiss the 'Turn on Notifications' overlay by clicking 'Not Now'."""
    wait = WebDriverWait(driver, timeout)
    candidates = [
        "//*[contains(text(), 'Not Now')]",
        "//div[contains(text(), 'Not Now')]",
        "//button[contains(., 'Not Now')]",
        "[aria-label='Not now']",
    ]
    for selector in candidates:
        try:
            by = By.XPATH if selector.startswith("//") else By.CSS_SELECTOR
            elem = wait.until(EC.element_to_be_clickable((by, selector)))
            elem.click()
            print("Dismissed 'Turn on Notifications' popup.")
            return True
        except TimeoutException:
            continue
    return False


def post_image(driver, image_path, caption="", timeout=15):
    wait = WebDriverWait(driver, timeout)
    file_wait = WebDriverWait(driver, 30)  # file picker may legitimately lag

    # Open the "create" flow from the sidebar.
    try:
        create_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='New post']"))
        )
        create_button.click()
    except Exception:
        # Fallback: the creation flow may appear as a different control.
        print("Falling back for create button...")
        new_post = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'New post')]"))
        )
        new_post.click()

    # Locate the hidden file input and feed it the image path.
    file_input = file_wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    file_input.send_keys(image_path)

    # Step through the creation modal: Next -> Next -> caption -> Share.
    next_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Next')]"))
    )
    next_button.click()

    # On some versions a final "Next" appears before the caption editor.
    try:
        next_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Next')]"))
        )
        next_button.click()
    except Exception:
        pass

    caption_box = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Write a caption...']"))
    )
    caption_box.send_keys(caption)

    share_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Share')]"))
    )
    share_button.click()

    # Wait for confirmation that the post was shared.
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Close']"))
    )
    print("Post published.")


def main():
    parser = argparse.ArgumentParser(description="Post a PNG to Instagram.")
    parser.add_argument("image", nargs="?", default=find_image(),
                        help="path to the PNG (default: first .png in cwd)")
    parser.add_argument("caption", nargs="?", default="",
                        help="optional caption text")
    parser.add_argument("--headless", action="store_true",
                        help="run Firefox with a hidden window")
    args = parser.parse_args()

    image_path = args.image
    if not image_path or not os.path.exists(image_path):
        print(
            "No PNG found in the current directory and none was provided as an "
            "argument.",
            file=sys.stderr,
        )
        sys.exit(1)

    driver = None
    try:
        driver = restore_session(headless=args.headless)
        dismiss_notifications_popup(driver)
        post_image(driver, os.path.abspath(image_path), caption=args.caption)
        if not args.headless:
            input("Press Enter to close the browser window...")
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    main()
