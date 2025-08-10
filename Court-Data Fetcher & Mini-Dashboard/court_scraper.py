"""
Court scraper for Delhi High Court website
Enhanced with improved CAPTCHA bypass strategies
"""
import re
import os
import time
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class CourtScraper:
    """
    Enhanced scraper for the Delhi High Court website.
    Includes improved CAPTCHA solving and PDF extraction strategies.
    """

    def __init__(self):
        """Initializes the scraper with configuration."""
        self.base_url = "https://delhihighcourt.nic.in"
        self.case_search_url = "https://delhihighcourt.nic.in/app/get-case-type-status"
        self.timeout = int(os.getenv('SELENIUM_TIMEOUT', 30))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.request_delay = int(os.getenv('REQUEST_DELAY', 5))
        self.driver = None

    def _setup_driver(self):
        """Configures and initializes the Selenium WebDriver with enhanced options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Enhanced WebDriver setup successful.")
            return True
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def _close_driver(self):
        """Closes the WebDriver session if it's active."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            logger.info("WebDriver closed.")

    def scrape_case_data(self, case_type, case_number, filing_year):
        """
        Enhanced main method to scrape case data with improved CAPTCHA handling.
        """
        for attempt in range(self.max_retries):
            logger.info(f"Scraping attempt {attempt + 1} of {self.max_retries}")
            
            if not self._setup_driver():
                continue

            try:
                logger.info(f"Navigating to case search page: {self.case_search_url}")
                self.driver.get(self.case_search_url)
                
                # Wait for page to load completely
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(3)  # Additional wait for dynamic content

                # Fill search form
                if not self._fill_search_form_enhanced(case_type, case_number, filing_year):
                    logger.error("Failed to fill search form")
                    continue

                # Handle CAPTCHA with enhanced strategy
                if not self._handle_captcha_enhanced():
                    logger.error("CAPTCHA solving failed")
                    continue

                # Submit form
                if not self._submit_form():
                    logger.error("Form submission failed")
                    continue

                # Wait for results
                time.sleep(self.request_delay)

                # Parse results with enhanced extraction
                result = self._parse_case_results_enhanced(self.driver.page_source)
                
                if result.get('success'):
                    logger.info("Successfully scraped case data")
                    return result
                else:
                    logger.warning(f"No results found: {result.get('error')}")
                    if attempt == self.max_retries - 1:
                        return result
                    continue

            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"Element not found (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {'success': False, 'error': 'Failed to find required elements on the page'}
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    return {'success': False, 'error': str(e)}
            finally:
                self._close_driver()
                
            # Wait before retry
            if attempt < self.max_retries - 1:
                time.sleep(5)
        
        return {'success': False, 'error': 'All scraping attempts failed'}

    def _fill_search_form_enhanced(self, case_type, case_number, filing_year):
        """Enhanced form filling with multiple XPath strategies."""
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            logger.info("Filling search form with enhanced strategy...")

            # Strategy 1: Fill case type with multiple XPath attempts
            case_type_selectors = [
                "//select[contains(@id,'case_type')]",
                "//select[contains(@name,'case_type')]",
                "//select[contains(@class,'case_type')]",
                "//select[1]"  # Fallback to first select
            ]
            
            case_type_filled = False
            for selector in case_type_selectors:
                try:
                    case_type_element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    Select(case_type_element).select_by_visible_text(case_type)
                    logger.info(f"Case type filled using selector: {selector}")
                    case_type_filled = True
                    break
                except Exception as e:
                    logger.debug(f"Case type selector {selector} failed: {e}")
                    continue
            
            if not case_type_filled:
                logger.error("Failed to fill case type")
                return False

            # Strategy 2: Fill case number with multiple attempts
            case_number_selectors = [
                "//input[contains(@id,'case_number')]",
                "//input[contains(@name,'case_number')]",
                "//input[contains(@placeholder,'case')]",
                "//input[@type='text'][1]"  # Fallback
            ]
            
            case_number_filled = False
            for selector in case_number_selectors:
                try:
                    case_number_element = self.driver.find_element(By.XPATH, selector)
                    case_number_element.clear()
                    case_number_element.send_keys(str(case_number))
                    logger.info(f"Case number filled using selector: {selector}")
                    case_number_filled = True
                    break
                except Exception as e:
                    logger.debug(f"Case number selector {selector} failed: {e}")
                    continue
            
            if not case_number_filled:
                logger.error("Failed to fill case number")
                return False

            # Strategy 3: Fill filing year
            year_selectors = [
                "//select[contains(@id,'case_year')]",
                "//select[contains(@name,'year')]",
                "//select[contains(@class,'year')]",
                "//select[last()]"  # Fallback to last select
            ]
            
            year_filled = False
            for selector in year_selectors:
                try:
                    year_element = self.driver.find_element(By.XPATH, selector)
                    Select(year_element).select_by_value(str(filing_year))
                    logger.info(f"Filing year filled using selector: {selector}")
                    year_filled = True
                    break
                except Exception as e:
                    logger.debug(f"Year selector {selector} failed: {e}")
                    continue
            
            if not year_filled:
                logger.error("Failed to fill filing year")
                return False

            logger.info("Search form filled successfully with enhanced strategy.")
            return True
            
        except Exception as e:
            logger.error(f"Error filling search form: {e}")
            return False

    def _handle_captcha_enhanced(self):
        """
        Enhanced CAPTCHA handling with multiple detection strategies.
        """
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # Multiple XPath strategies for CAPTCHA detection
            captcha_selectors = [
                "//span[contains(@class,'captcha')]",
                "//span[contains(@id,'captcha')]",
                "//div[contains(@class,'captcha')]//span",
                "//div[contains(@id,'captcha')]//span",
                "//span[contains(text(),'')]",  # Look for spans with numeric content
                "//*[contains(@class,'captcha')]",
                "//*[contains(@id,'captcha')]"
            ]
            
            captcha_element = None
            captcha_text = None
            
            # Try each selector strategy
            for selector in captcha_selectors:
                try:
                    potential_elements = self.driver.find_elements(By.XPATH, selector)
                    for element in potential_elements:
                        text = element.text.strip()
                        if text and text.isdigit() and len(text) >= 3:  # Reasonable CAPTCHA length
                            captcha_element = element
                            captcha_text = text
                            logger.info(f"CAPTCHA found using selector '{selector}' with value: '{captcha_text}'")
                            break
                    if captcha_text:
                        break
                except Exception as e:
                    logger.debug(f"CAPTCHA selector {selector} failed: {e}")
                    continue
            
            # If no CAPTCHA found with above methods, try text extraction from page
            if not captcha_text:
                try:
                    # Look for numeric patterns in page source
                    page_text = self.driver.page_source
                    numeric_patterns = re.findall(r'<span[^>]*>(\d{3,6})</span>', page_text)
                    if numeric_patterns:
                        captcha_text = numeric_patterns[0]
                        logger.info(f"CAPTCHA extracted from page source: '{captcha_text}'")
                except Exception as e:
                    logger.debug(f"Page source CAPTCHA extraction failed: {e}")

            if not captcha_text:
                logger.warning("No CAPTCHA found. Attempting to proceed without it.")
                return True  # Some pages might not have CAPTCHA

            # Fill CAPTCHA input with multiple strategies
            captcha_input_selectors = [
                "//input[contains(@id,'captcha')]",
                "//input[contains(@name,'captcha')]",
                "//input[contains(@placeholder,'captcha')]",
                "//input[@type='text'][last()]"  # Often the last text input
            ]
            
            captcha_filled = False
            for selector in captcha_input_selectors:
                try:
                    captcha_input = self.driver.find_element(By.XPATH, selector)
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)
                    logger.info(f"CAPTCHA filled using selector: {selector}")
                    captcha_filled = True
                    break
                except Exception as e:
                    logger.debug(f"CAPTCHA input selector {selector} failed: {e}")
                    continue
            
            if not captcha_filled:
                logger.error("Failed to fill CAPTCHA input")
                return False
                
            logger.info(f"CAPTCHA handled successfully with value: {captcha_text}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {e}")
            return False

    def _submit_form(self):
        """Enhanced form submission with multiple button detection strategies."""
        try:
            submit_selectors = [
                "//button[contains(text(),'Submit')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//button[contains(@class,'submit')]",
                "//input[contains(@value,'Submit')]"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.XPATH, selector)
                    # Scroll to button and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", submit_button)
                    logger.info(f"Form submitted using selector: {selector}")
                    return True
                except Exception as e:
                    logger.debug(f"Submit selector {selector} failed: {e}")
                    continue
            
            logger.error("Failed to find submit button")
            return False
            
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False

    def _parse_case_results_enhanced(self, html_content):
        """Enhanced parsing with better data extraction and PDF finding."""
        logger.info("Parsing case results with enhanced strategy...")
        soup = BeautifulSoup(html_content, 'html.parser')

        # Check for "No record found" message
        if any(phrase in html_content.lower() for phrase in ["no record found", "no data found", "record not found"]):
            logger.warning("No records found for the given case details.")
            return {'success': False, 'error': 'No record found for the specified case.'}
            
        # Find results table with multiple strategies
        table_selectors = [
            "table",
            ".table",
            "#results-table",
            "[class*='table']"
        ]
        
        case_table = None
        for selector in table_selectors:
            case_table = soup.select_one(selector)
            if case_table:
                logger.info(f"Results table found using selector: {selector}")
                break
        
        if not case_table:
            logger.error("Could not find the results table.")
            return {'success': False, 'error': 'Results table not found on the page.'}

        data_rows = case_table.find_all('tr')
        if len(data_rows) < 2:
            return {'success': False, 'error': 'No data rows found in the results table.'}

        try:
            # Enhanced data extraction from the first data row
            cols = data_rows[1].find_all('td')
            
            # Extract parties information with better parsing
            parties_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            if "VS." in parties_text.upper():
                parts = parties_text.upper().split("VS.")
                parties_plaintiff = parts[0].strip()
                parties_defendant = parts[1].strip()
            else:
                parties_plaintiff = parties_text
                parties_defendant = "N/A"

            # Enhanced date extraction
            listing_text = cols[3].get_text(strip=True) if len(cols) > 3 else ""
            dates_found = re.findall(r'\d{2}/\d{2}/\d{4}', listing_text)
            
            # Convert date format from DD/MM/YYYY to YYYY-MM-DD
            filing_date = None
            next_hearing_date = None
            
            if dates_found:
                try:
                    # First date is usually filing date
                    filing_parts = dates_found[0].split('/')
                    filing_date = f"{filing_parts[2]}-{filing_parts[1]}-{filing_parts[0]}"
                    
                    # Second date is usually next hearing
                    if len(dates_found) > 1:
                        hearing_parts = dates_found[1].split('/')
                        next_hearing_date = f"{hearing_parts[2]}-{hearing_parts[1]}-{hearing_parts[0]}"
                except Exception as e:
                    logger.warning(f"Date parsing error: {e}")

            # Enhanced PDF extraction with multiple strategies
            pdf_urls = self._extract_pdfs_enhanced(soup, cols)
            
            # Prepare orders list
            orders = []
            for pdf_url in pdf_urls:
                orders.append({
                    'date': filing_date,  # Use filing date as default
                    'type': 'Order',
                    'pdf_url': pdf_url
                })

            result_data = {
                'success': True,
                'parties': {
                    'plaintiff': parties_plaintiff,
                    'defendant': parties_defendant
                },
                'filing_date': filing_date,
                'next_hearing': next_hearing_date,
                'status': 'Active',  # Default status
                'orders': orders,
                'raw_html': html_content  # For debugging
            }
            
            logger.info("Case data parsed successfully")
            return result_data

        except Exception as e:
            logger.error(f"Error parsing case results: {e}")
            return {'success': False, 'error': f'Error parsing results: {str(e)}'}

    def _extract_pdfs_enhanced(self, soup, cols):
        """Enhanced PDF extraction with multiple fallback methods."""
        pdf_urls = []
        
        try:
            # Method 1: Check main table columns for PDF links
            for col in cols:
                links = col.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '.pdf' in href.lower():
                        full_url = urljoin(self.base_url, href)
                        pdf_urls.append(full_url)
                        logger.info(f"PDF found in main table: {full_url}")

            # Method 2: Check for orders page link and navigate
            if not pdf_urls:
                pdf_urls.extend(self._check_orders_page())

            # Method 3: Search entire page for PDF links
            if not pdf_urls:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if '.pdf' in href.lower():
                        full_url = urljoin(self.base_url, href)
                        pdf_urls.append(full_url)
                        logger.info(f"PDF found in page scan: {full_url}")

            # Remove duplicates while preserving order
            unique_pdfs = []
            for url in pdf_urls:
                if url not in unique_pdfs:
                    unique_pdfs.append(url)
                    
            return unique_pdfs

        except Exception as e:
            logger.error(f"Error extracting PDFs: {e}")
            return []

    def _check_orders_page(self):
        """Check orders page for additional PDFs."""
        pdf_urls = []
        try:
            # Look for orders link
            orders_selectors = [
                "//a[contains(text(),'Orders')]",
                "//a[contains(text(),'Order')]",
                "//a[contains(@href,'order')]"
            ]
            
            for selector in orders_selectors:
                try:
                    orders_link = self.driver.find_element(By.XPATH, selector)
                    self.driver.execute_script("arguments[0].click();", orders_link)
                    time.sleep(3)
                    
                    # Wait for orders table
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//table"))
                    )
                    
                    # Extract PDFs from orders table
                    pdf_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
                    for element in pdf_elements:
                        href = element.get_attribute("href")
                        if href:
                            full_url = href if href.startswith("http") else urljoin(self.base_url, href)
                            pdf_urls.append(full_url)
                            logger.info(f"PDF found in orders page: {full_url}")
                    
                    break  # Exit loop if orders page accessed successfully
                    
                except Exception as e:
                    logger.debug(f"Orders selector {selector} failed: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error checking orders page: {e}")
        
        return pdf_urls

    def download_pdf(self, pdf_url):
        """Download PDF from URL with enhanced error handling."""
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').lower().startswith('application/pdf'):
                logger.info(f"PDF downloaded successfully from: {pdf_url}")
                return response.content
            else:
                logger.warning(f"URL did not return a PDF: {pdf_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None

    def test_captcha_detection(self):
        """Test method to debug CAPTCHA detection."""
        if not self._setup_driver():
            return False

        try:
            self.driver.get(self.case_search_url)
            time.sleep(3)
            
            # Take screenshot for debugging
            screenshot_path = "debug_captcha.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            # Try to find CAPTCHA elements
            captcha_selectors = [
                "//span[contains(@class,'captcha')]",
                "//span[contains(@id,'captcha')]",
                "//div[contains(@class,'captcha')]",
                "//*[contains(text(), '')]"
            ]
            
            for selector in captcha_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            logger.info(f"Found element with selector '{selector}': '{text}'")
                            if text.isdigit():
                                logger.info(f"NUMERIC CAPTCHA FOUND: '{text}'")
                except Exception as e:
                    logger.debug(f"Debug selector {selector} failed: {e}")
            
            # Print page source snippet for manual inspection
            logger.info("Page source snippet (first 2000 chars):")
            logger.info(self.driver.page_source[:2000])
            
            return True
            
        except Exception as e:
            logger.error(f"Error in CAPTCHA test: {e}")
            return False
        finally:
            self._close_driver()