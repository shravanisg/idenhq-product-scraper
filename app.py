import json
import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class ProductScraper:
    def __init__(self, credentials_file="credentials.json"):
        try:
            with open(credentials_file, "r") as f:
                self.credentials = json.load(f)
            print("Credentials loaded from file.")
        except Exception as e:
            print(f"Error loading credentials: {e}")
            self.credentials = {
                "username": "",
                "password": ""
            }

        self.session_file = "session.json"
        self.output_file = "product_data.json"
        self.base_url = "https://hiring.idenhq.com"


    def run(self):
        with sync_playwright() as p:
            browser_type = p.chromium
            browser = browser_type.launch(headless=False) 
            
            try:
                context = self._get_browser_context(browser)
                page = context.new_page()
                
                page.goto(self.base_url)
                print("Navigated to the main page")
                
                if "Sign out" not in page.content():
                    print("Not logged in, performing login...")
                    self._login(page)
                else:
                    print("Already logged in")
                
                self._navigate_to_challenge(page)
                
                self._navigate_to_product_data(page)

                products = self._extract_product_data(page)
                
                self._save_to_json(products)
                
                print(f"Successfully exported {len(products)} products to {self.output_file}")
                
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                try:
                    page.screenshot(path="error_screenshot.png")
                    print("Error screenshot saved as error_screenshot.png")
                    print("Current URL:", page.url)
                    menu_content = page.query_selector(".dashboard-menu") or page.query_selector("div[role='menu']") or page.query_selector("nav")
                    if menu_content:
                        print("Menu content:", menu_content.inner_html())
                except Exception as inner_e:
                    print(f"Screenshot error: {str(inner_e)}")
            finally:
                browser.close()

    def _get_browser_context(self, browser):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    storage_state = json.load(f)
                print("Using existing session")
                return browser.new_context(storage_state=storage_state)
            except Exception as e:
                print(f"Error loading session: {str(e)}")
        
        print("Creating new browser context")
        return browser.new_context()

    def _save_session(self, context):
        try:
            storage_state = context.storage_state()
            with open(self.session_file, "w") as f:
                json.dump(storage_state, f)
            print("Session saved successfully")
        except Exception as e:
            print(f"Error saving session: {str(e)}")

    def _login(self, page):
        try:
            print("Starting login process...")
            
            page.wait_for_load_state("networkidle")
            
            sign_in_button = page.get_by_role("button", name="Sign in")

            if page.get_by_label("Email").is_visible():
                print("Login form is already visible")
            else:
                print("Clicking Sign in button to show login form")
                sign_in_button.click()
                page.wait_for_selector("input[type='email']", timeout=5000)

            print(f"Filling email: {self.credentials['username']}")
            page.get_by_label("Email").fill(self.credentials["username"])
            
            print("Filling password")
            page.get_by_label("Password").fill(self.credentials["password"])

            print("Clicking sign-in button")
            page.get_by_role("button", name="Sign in").click()

            print("Waiting for redirect after login...")
            page.wait_for_load_state("networkidle")

            if "/instructions" in page.url:
                print("Successfully logged in and redirected to instructions page")
                self._save_session(page.context)
            else:
                page.wait_for_timeout(3000) 
                if "/instructions" in page.url:
                    print("Successfully logged in and redirected to instructions page (delayed)")
                    self._save_session(page.context)
                else:
                    print(f"Login might have issues - current URL: {page.url}")
                    page.screenshot(path="login_redirect_issue.png")
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            page.screenshot(path="login_error.png")
            raise
            
    def _navigate_to_challenge(self, page):
        try:
            print("Checking current page...")

            if "/instructions" in page.url:
                print("On instructions page, looking for Launch Challenge button...")

                page.wait_for_load_state("networkidle")
                
                launch_button = page.get_by_role("button", name="Launch Challenge")
                if launch_button.is_visible():
                    print("Found Launch Challenge button, clicking...")
                    launch_button.click()
                    
                    page.wait_for_load_state("networkidle")
                    
                    if "/challenge" in page.url:
                        print("Successfully navigated to challenge page")
                    else:
                        print(f"Navigation issue - current URL: {page.url}")
                        page.screenshot(path="challenge_navigation_issue.png")
                else:
                    print("Launch Challenge button not found")
                    page.screenshot(path="launch_button_not_found.png")
                    
                    alternative_selectors = [
                        "text=Launch Challenge",
                        "button:has-text('Launch')",
                        "a:has-text('Launch Challenge')",
                        ".launch-button"
                    ]
                    
                    for selector in alternative_selectors:
                        try:
                            if page.query_selector(selector) is not None:
                                print(f"Found launch button with selector: {selector}")
                                page.click(selector)
                                
                                page.wait_for_load_state("networkidle")
                                
                                if "/challenge" in page.url:
                                    print("Successfully navigated to challenge page using alternative selector")
                                    break
                        except:
                            continue
            elif "/challenge" in page.url:
                print("Already on challenge page")
            else:
                print(f"Unexpected URL: {page.url}, trying to navigate to challenge page...")
                page.goto(f"{self.base_url}/challenge")
                page.wait_for_load_state("networkidle")
                
        except Exception as e:
            print(f"Error navigating to challenge: {str(e)}")
            page.screenshot(path="challenge_navigation_error.png")
    
    def _navigate_to_product_data(self, page):
        try:
            if "/challenge" not in page.url:
                print(f"Not on challenge page, current URL: {page.url}")
                print("Attempting to navigate to challenge page...")
                page.goto(f"{self.base_url}/challenge")
                page.wait_for_load_state("networkidle")

            print("Looking for Dashboard Menu button...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000) 

            try:
                open_dashboard_button = page.get_by_role("button", name="Open Dashboard Menu")
                if open_dashboard_button.is_visible(timeout=2000):
                    print("Found Dashboard Menu button, clicking...")
                    open_dashboard_button.click()
                    page.wait_for_timeout(1500)
                else:
                    print("Dashboard button not found by role, trying alternative methods...")
                    menu_buttons = page.query_selector_all("button, [role='button']")
                    for button in menu_buttons:
                        try:
                            if "menu" in button.inner_text().lower() or button.query_selector("svg"):
                                print("Found potential menu button, clicking...")
                                button.click()
                                page.wait_for_timeout(1500)
                                break
                        except:
                            continue
            except Exception as e:
                print(f"Error with dashboard menu button: {e}")

            print("Looking for Data Tools item...")
            for i in range(2):
                try:
                    data_tools = page.get_by_text("Data Tools", exact=True)
                    if data_tools.is_visible(timeout=2000):
                        print(f"Found Data Tools item, clicking... (attempt {i+1})")
                        data_tools.click()
                        page.wait_for_timeout(1500)
                    else:
                        print(f"Data Tools not found by text on attempt {i+1}, trying alternatives...")
                        selectors = [
                            "[data-testid='menu-item-data-tools']",
                            "div:has-text('Data Tools')",
                            "li:has-text('Data Tools')"
                        ]
                        for selector in selectors:
                            try:
                                element = page.query_selector(selector)
                                if element:
                                    print(f"Clicking Data Tools using selector: {selector} (attempt {i+1})")
                                    element.click()
                                    page.wait_for_timeout(1500)
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"Error with Data Tools click {i+1}: {e}")

            print("Looking for Inventory options...")
            try:
                inventory_selectors = [
                    "text=Inventory Options",
                    "[data-testid*='inventory options']",
                    "li:has-text('Inventory options')",
                    "div:has-text('Inventory options')",
                    "svg.lucide-database"
                ]
                for selector in inventory_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        if len(elements) > 0:
                            print(f"Found Inventory option with selector: {selector}, clicking once...")
                            elements[0].click()
                            page.wait_for_timeout(1500)
                            break
                    except Exception as e:
                        print(f"Error with Inventory selector {selector}: {e}")
                        continue
            except Exception as e:
                print(f"Error finding Inventory option: {e}")

            print("Looking for 'Open Products Drawer' inside Dashboard Menu...")
            try:
                page.wait_for_selector("text=Open Products Drawer", timeout=5000)
                drawer_buttons = page.query_selector_all("text=Open Products Drawer")
                print(f"Found {len(drawer_buttons)} 'Open Products Drawer' buttons")

                if len(drawer_buttons) >= 1:
                    for i in range(2):
                        print(f"Clicking 'Open Products Drawer' inside menu (attempt {i+1})")
                        drawer_buttons[0].click()
                        page.wait_for_timeout(1500)
                else:
                    print("No 'Open Products Drawer' buttons found in Dashboard Menu.")
                    page.screenshot(path="no_drawer_buttons_found.png")

                print("Waiting for product cards to load after drawer clicks...")
                product_selectors = [
                    "div:has(h3):has-text('ID:')",
                    "h3",
                    ".card",
                    "[class*='product']"
                ]
                for selector in product_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=7000)
                        print(f"Product cards visible with selector: {selector}")
                        return
                    except:
                        continue

                print("Product cards may not have loaded properly, taking screenshot...")
                page.screenshot(path="product_cards_not_found.png")

            except Exception as e:
                print(f"Error interacting with drawer: {e}")
                page.screenshot(path="drawer_interaction_failed.png")

        except Exception as e:
            print(f"Overall navigation error: {str(e)}")
            page.screenshot(path="navigation_error.png")
            raise


    def _extract_product_data(self, page):
            all_products = []

            try:
                print("Waiting for at least one product card to appear...")
                page.wait_for_selector("div.rounded-lg.border.bg-card", timeout=7000)

                max_scroll_attempts = 100
                scroll_attempts = 0
                last_count = 0

                while scroll_attempts < max_scroll_attempts:
                    product_cards = page.query_selector_all("div.rounded-lg.border.bg-card")
                    current_count = len(product_cards)
                    print(f"Loaded product cards: {current_count}")

                    if current_count > last_count:
                        last_count = current_count
                        print(f"Scrolling to bottom... (attempt {scroll_attempts + 1})")
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1000)
                    else:
                        print("No new cards loaded, assuming all are visible.")
                        break

                    scroll_attempts += 1

                print(f"Extracting data from {last_count} visible product cards...")
                product_cards = page.query_selector_all("div.rounded-lg.border.bg-card")

                for card in product_cards:
                    try:
                        product = {}
                        name_element = card.query_selector("h3")
                        if name_element:
                            product["name"] = name_element.inner_text().strip()

                        raw_text = card.inner_text()
                        lines = raw_text.split("\n")

                        for line in lines:
                            if line.lower().startswith("id:"):
                                product["id"] = line.replace("ID:", "").strip()
                            elif line.lower().startswith("dimensions:"):
                                product["dimensions"] = line.replace("Dimensions:", "").strip()
                            elif line.lower().startswith("cost:"):
                                product["cost"] = line.replace("Cost:", "").strip()
                            elif line.lower().startswith("composition:"):
                                product["composition"] = line.replace("Composition:", "").strip()
                            elif line.lower().startswith("manufacturer:"):
                                product["manufacturer"] = line.replace("Manufacturer:", "").strip()
                            elif line.lower().startswith("inventory:"):
                                product["inventory"] = line.replace("Inventory:", "").strip()
                            elif line.lower().startswith("updated:"):
                                product["updated"] = line.replace("Updated:", "").strip()
                            elif line.lower().startswith("details:"):
                                product["details"] = line.replace("Details:", "").strip()

                        all_products.append(product)

                    except Exception as e:
                        print(f"Error extracting product card: {e}")

                print(f"Total products extracted: {len(all_products)}")
                return all_products

            except Exception as e:
                print(f"Error extracting products: {e}")
                page.screenshot(path="extraction_error.png")
                return all_products


    def _save_to_json(self, products):
        try:
            with open(self.output_file, "w") as f:
                json.dump({"products": products}, f, indent=2)
            print(f"Data successfully saved to {self.output_file}")
        except Exception as e:
            print(f"Error saving data to JSON: {str(e)}")

if __name__ == "__main__":
    scraper = ProductScraper()
    scraper.run()
