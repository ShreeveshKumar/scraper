import time
import csv # Not strictly used by the current scrapers, but kept from your template
import re # For cleaning text
import json # For JSON output
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback 


def runscraper():
    DRIVER_PATH = None
    USE_WEBDRIVER_MANAGER = False
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        DRIVER_PATH = ChromeDriverManager().install()
        print(f"Using ChromeDriver installed by webdriver-manager at: {DRIVER_PATH}")
        USE_WEBDRIVER_MANAGER = True
    except ImportError:
        print("webdriver-manager not found. Install with `pip install webdriver-manager` or set DRIVER_PATH manually.")
        DRIVER_PATH = '/path/to/your/chromedriver'
        if DRIVER_PATH == '/path/to/your/chromedriver':
             print("WARNING: DRIVER_PATH is using the default placeholder. Please update it if webdriver-manager is not used.")
        USE_WEBDRIVER_MANAGER = False
    except Exception as e:
        print(f"Error during WebDriver manager setup: {e}")
        print("Scraping cannot proceed without a valid ChromeDriver path.")
        return {"error": "WebDriver setup failed", "details": str(e), "events": []}

    SELENIUM_TIMEOUT = 30
    SCROLL_PAUSE_TIME = 3.0
    MAX_SCROLL_ATTEMPTS = 8

    def clean_text(text):
        if text:
            return ' '.join(text.split()).strip()
        return None

    def get_driver():
        if not DRIVER_PATH or (DRIVER_PATH == '/path/to/your/chromedriver' and not USE_WEBDRIVER_MANAGER):
            raise Exception("ChromeDriver path is not configured correctly. Please install webdriver-manager or set DRIVER_PATH.")
        
        service = Service(executable_path=DRIVER_PATH)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        )
        options.add_argument("--start-maximized") 
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def scrape_devfolio(driver_instance, base_url="https://devfolio.co/"):
        print("\n--- Starting Devfolio Scrape ---")
        target_url = urljoin(base_url, "/hackathons")
        all_hackathons = []
        processed_urls = set()

        try:
            print(f"Navigating to {target_url}...")
            driver_instance.get(target_url)

            wait_selector_css = "a.bnxtME"
            print(f"Waiting for Devfolio listings ({wait_selector_css})...")
            try:
                WebDriverWait(driver_instance, SELENIUM_TIMEOUT).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, wait_selector_css))
                )
                print("Devfolio listings detected.")
                time.sleep(3) # Stability pause
            except TimeoutException:
                print("Timeout waiting for Devfolio listings. Structure might have changed or page blocked.")
                print(f"Page title: {driver_instance.title}")
                return []

            print("Scrolling Devfolio page...")
            last_height = driver_instance.execute_script("return document.body.scrollHeight")
            no_change_count = 0
            for i in range(MAX_SCROLL_ATTEMPTS // 2):
                driver_instance.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = driver_instance.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count +=1
                    if no_change_count >= 2: break
                else: no_change_count = 0
                last_height = new_height
            print("Finished Devfolio scrolling.")

            html_content = driver_instance.page_source
            soup = BeautifulSoup(html_content, 'lxml')
            hackathon_links = soup.find_all('a', class_='bnxtME')
            print(f"Found {len(hackathon_links)} potential Devfolio listings.")

            for link_tag in hackathon_links:
                card = link_tag.find_parent('div', class_=lambda x: x and x.startswith('CompactHackathonCard__Card-sc-'))
                if not card:
                     card = link_tag.find_parent('div', class_=lambda x: x and x.startswith('sc-'))
                if not card: continue

                event_data = {'source': 'Devfolio'}

                try:
                    raw_url = link_tag.get('href')
                    if not raw_url: continue
                    event_data['url'] = urljoin(base_url, raw_url)
                    if event_data['url'] in processed_urls: continue
                    processed_urls.add(event_data['url'])

                    title_tag = link_tag.find('h3')
                    event_data['title'] = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                    if event_data['title'] == 'N/A': continue

                    status_tags = card.find_all('p', class_='ifkmYk')
                    statuses = [clean_text(tag.get_text()) for tag in status_tags if clean_text(tag.get_text())]
                    event_data['status_mode'] = ', '.join(statuses) if statuses else 'N/A'
                    
                    event_data['prize_info'] = 'N/A (Details on event page)'
                    event_data['participants_count'] = 'N/A (Details on event page)'
                    event_data['host_name'] = 'N/A (Details on event page)'
                    event_data['dates'] = 'N/A (Details on event page)'
                    event_data['themes_tags'] = 'N/A (Details on event page)'
                    event_data['location_mode'] = 'Online/Offline (Check Status/Mode)'

                    all_hackathons.append(event_data)
                except Exception as e:
                    print(f"  Error processing one Devfolio card (URL: {event_data.get('url', 'Unknown')}): {e}")
        except Exception as e:
            print(f"Critical error during Devfolio scrape: {e}")
            traceback.print_exc()
        finally:
            print(f"--- Finished Devfolio Scrape ({len(all_hackathons)} events found) ---")
            return all_hackathons

    def scrape_devpost(driver_instance, base_url="https://devpost.com/"):
        print("\n--- Starting Devpost Scrape ---")
        target_url = urljoin(base_url, "/hackathons")
        all_hackathons = []
        processed_urls = set()

        try:
            print(f"Navigating to {target_url}...")
            driver_instance.get(target_url)

            wait_selector_css = "div.hackathon-tile"
            print(f"Waiting for Devpost listings ({wait_selector_css})...")
            try:
                WebDriverWait(driver_instance, SELENIUM_TIMEOUT).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, wait_selector_css))
                )
                print("Devpost listings detected.")
                time.sleep(3)
            except TimeoutException:
                print("Timeout waiting for Devpost listings.")
                print(f"Page title: {driver_instance.title}")
                return []

            print("Scrolling Devpost page...")
            last_height = driver_instance.execute_script("return document.body.scrollHeight")
            no_change_count = 0
            for i in range(MAX_SCROLL_ATTEMPTS):
                driver_instance.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                try:
                     load_more_button = driver_instance.find_element(By.CSS_SELECTOR, "a.load-more-challenges")
                     if load_more_button.is_displayed() and load_more_button.is_enabled():
                         print("Clicking Devpost 'Load More' button...")
                         driver_instance.execute_script("arguments[0].click();", load_more_button)
                         time.sleep(SCROLL_PAUSE_TIME + 1)
                except Exception: pass

                new_height = driver_instance.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count +=1
                    if no_change_count >= 2: break
                else: no_change_count = 0
                last_height = new_height
            print("Finished Devpost scrolling.")

            html_content = driver_instance.page_source
            soup = BeautifulSoup(html_content, 'lxml')
            hackathon_tiles = soup.select('div.hackathon-tile')
            print(f"Found {len(hackathon_tiles)} potential Devpost tiles.")

            for tile in hackathon_tiles:
                event_data = {'source': 'Devpost'}

                try:
                    anchor = tile.find('a', class_='tile-anchor')
                    if not anchor or not anchor.has_attr('href'): continue

                    relative_url = anchor['href']
                    event_data['url'] = urljoin(base_url, relative_url.split('?')[0])
                    if event_data['url'] in processed_urls: continue
                    processed_urls.add(event_data['url'])

                    # Initialize fields
                    event_data['title'] = 'N/A'
                    event_data['status_label'] = 'N/A'
                    event_data['location_mode'] = 'N/A'
                    event_data['prize_info'] = 'N/A'
                    event_data['participants_count'] = 'N/A'
                    event_data['host_name'] = 'N/A'
                    event_data['dates'] = 'N/A'
                    event_data['themes_tags'] = 'N/A'

                    main_content = anchor.find('div', class_='main-content')
                    if main_content:
                        content_div = main_content.find('div', class_='content')
                        if content_div:
                             title_tag = content_div.find('h3', class_='mb-4')
                             event_data['title'] = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                             if event_data['title'] == 'N/A': continue

                             info_row = content_div.find('div', class_='flex-row') # Simplified
                             if info_row:
                                 status_tag = info_row.find('div', class_='status-label')
                                 event_data['status_label'] = clean_text(status_tag.get_text()) if status_tag else 'N/A'
                                 
                                 location_text = 'N/A'
                                 mode_text = 'N/A'
                                 location_icon_div = info_row.find('div', class_='info-with-icon')
                                 if location_icon_div:
                                     icon = location_icon_div.find('i')
                                     info_span = location_icon_div.find('span')
                                     if icon and info_span:
                                         location_text = clean_text(info_span.get_text())
                                         mode_text = 'Online' if 'fa-globe' in icon.get('class', []) else \
                                                     ('In-Person' if 'fa-map-marker-alt' in icon.get('class', []) else 'Hybrid/Unknown')
                                 event_data['location_mode'] = f"{mode_text} - {location_text}" if location_text != 'N/A' else mode_text

                             pnp_div = content_div.find('div', class_='prizes-and-participants')
                             if pnp_div:
                                 prize_tag = pnp_div.find('span', class_='prize-amount')
                                 event_data['prize_info'] = clean_text(prize_tag.get_text()) if prize_tag else 'N/A'
                                 partic_tag = pnp_div.find('div', class_='participants')
                                 strong_tag = partic_tag.find('strong') if partic_tag else None
                                 event_data['participants_count'] = clean_text(strong_tag.get_text()) if strong_tag else 'N/A'
                    
                    side_info = anchor.find('div', class_='side-info')
                    if side_info:
                         host_tag = side_info.find('span', class_='host-label')
                         event_data['host_name'] = clean_text(host_tag['title']) if host_tag and host_tag.has_attr('title') else (clean_text(host_tag.get_text()) if host_tag else 'N/A')
                         sub_period_tag = side_info.find('div', class_='submission-period')
                         event_data['dates'] = clean_text(sub_period_tag.get_text()) if sub_period_tag else 'N/A'
                         theme_tags_elements = side_info.select('span.theme-label')
                         themes_list = [clean_text(tag['title']) for tag in theme_tags_elements if tag.has_attr('title')]
                         event_data['themes_tags'] = ', '.join(themes_list) if themes_list else 'N/A'
                    
                    event_data['status_mode'] = f"{event_data.get('status_label', 'N/A')} ({event_data.get('location_mode', 'N/A')})"
                    all_hackathons.append(event_data)
                except Exception as e:
                    print(f"  Error processing one Devpost tile (URL: {event_data.get('url', 'Unknown')}): {e}")
        except Exception as e:
            print(f"Critical error during Devpost scrape: {e}")
            traceback.print_exc()
        finally:
            print(f"--- Finished Devpost Scrape ({len(all_hackathons)} events found) ---")
            return all_hackathons

    def scrape_unstop(driver_instance, base_url="https://unstop.com/"):
        print("\n--- Starting Unstop Scrape ---")
        target_url = urljoin(base_url, "/hackathons")
        all_hackathons = []
        processed_ids = set()

        try:
            print(f"Navigating to {target_url}...")
            driver_instance.get(target_url)

            list_container_selector = "div.user_list"
            listing_item_selector = "app-competition-listing div.single_profile"
            print(f"Waiting for Unstop listings ({listing_item_selector})...")
            try:
                WebDriverWait(driver_instance, SELENIUM_TIMEOUT).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, list_container_selector))
                )
                WebDriverWait(driver_instance, SELENIUM_TIMEOUT).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, listing_item_selector))
                )
                print("Unstop listings detected.")
                time.sleep(3)
            except TimeoutException:
                print("Timeout waiting for Unstop listings.")
                if "Just a moment..." in driver_instance.page_source or "Cloudflare" in driver_instance.title:
                     print("Cloudflare detected on Unstop. Scraping will likely fail.")
                print(f"Page title: {driver_instance.title}")
                return []

            print("Scrolling Unstop page...")
            last_height = driver_instance.execute_script("return document.body.scrollHeight")
            no_change_count = 0
            for i in range(MAX_SCROLL_ATTEMPTS):
                driver_instance.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = driver_instance.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count +=1
                    if no_change_count >= 3: break
                else: no_change_count = 0
                last_height = new_height
            print("Finished Unstop scrolling.")

            html_content = driver_instance.page_source
            soup = BeautifulSoup(html_content, 'lxml')
            listings = soup.select('app-competition-listing div.single_profile')
            print(f"Found {len(listings)} potential Unstop listings.")

            for profile_div in listings:
                event_data = {'source': 'Unstop'}

                try:
                     comp_id = None
                     comp_id_match = re.search(r'i_(\d+)_', profile_div.get('id', ''))
                     if comp_id_match: comp_id = comp_id_match.group(1)
                     else:
                        class_list = profile_div.get('class', [])
                        for cls in class_list:
                            if cls.startswith('opp_') and cls.split('_')[-1].isdigit():
                                comp_id = cls.split('_')[-1]; break
                     if not comp_id or comp_id in processed_ids: continue
                     processed_ids.add(comp_id)
                     event_data['url'] = urljoin(base_url, f"o/{comp_id}")

                     content_div = profile_div.find('div', class_='content')
                     if not content_div: continue

                     title_tag = content_div.find('h2', class_='double-wrap')
                     event_data['title'] = clean_text(title_tag.get_text()) if title_tag else 'N/A'
                     if event_data['title'] == 'N/A': continue

                     org_tag = content_div.find('p')
                     event_data['host_name'] = clean_text(org_tag.get_text()) if org_tag else 'N/A'
                     
                     event_data['prize_info'] = 'N/A'
                     event_data['participants_count'] = 'N/A'
                     event_data['dates'] = 'N/A'
                     event_data['themes_tags'] = 'N/A'
                     event_data['status_mode'] = 'Online (typically)' # Unstop is mostly online
                     event_data['location_mode'] = 'Online (typically)'

                     other_fields_div = content_div.find('div', class_='other_fields')
                     if other_fields_div:
                         seperate_boxes = other_fields_div.find_all('div', class_='seperate_box', recursive=False)
                         for box in seperate_boxes:
                             box_text = clean_text(box.get_text())
                             if not box_text: continue
                             
                             img_alt = box.find('img')['alt'] if box.find('img') and box.find('img').has_attr('alt') else ''

                             if 'prize' in box.get('class', []) or 'Prize money' in img_alt:
                                 prize_text_cleaned = re.sub(r'^\s*🏆\s*', '', box_text).strip()
                                 event_data['prize_info'] = prize_text_cleaned if prize_text_cleaned else box_text
                             elif img_alt == 'group' or 'Registered' in box_text:
                                 match = re.search(r'([\d,]+)\s+Registered', box_text)
                                 event_data['participants_count'] = match.group(1).replace(',', '') if match else box_text
                             elif img_alt == 'schedule' or any(k in box_text for k in ['ago', 'left', 'day']):
                                 event_data['dates'] = box_text # This is "time left" or similar
                     
                     skills_div = content_div.find('div', class_='skills')
                     if skills_div:
                         tag_elements = skills_div.select('un-chip-items span.chip_text')
                         tags_list = [clean_text(tag.get_text()) for tag in tag_elements]
                         if tags_list: event_data['themes_tags'] = ', '.join(tags_list)

                     all_hackathons.append(event_data)
                except Exception as e:
                    print(f"  Error processing one Unstop listing (ID: {event_data.get('url', 'Unknown').split('/')[-1]}): {e}")
        except Exception as e:
            print(f"Critical error during Unstop scrape: {e}")
            traceback.print_exc()
        finally:
            print(f"--- Finished Unstop Scrape ({len(all_hackathons)} events found) ---")
            return all_hackathons

    print("Starting event aggregation scrape...")
    master_event_list = []
    
    current_driver = None
    try:
        print("\nInitializing WebDriver for Devfolio...")
        current_driver = get_driver()
        devfolio_events = scrape_devfolio(current_driver)
        master_event_list.extend(devfolio_events)
        print(f"Devfolio events added: {len(devfolio_events)}")
    except Exception as e:
        print(f"Failed to initialize driver or scrape Devfolio: {e}")
        traceback.print_exc()
    finally:
         if current_driver:
            try:
                print("Quitting Devfolio WebDriver...")
                current_driver.quit()
            except Exception as e:
                print(f"Error quitting Devfolio driver: {e}")

    current_driver = None
    try:
        print("\nInitializing WebDriver for Devpost...")
        current_driver = get_driver()
        devpost_events = scrape_devpost(current_driver)
        master_event_list.extend(devpost_events)
        print(f"Devpost events added: {len(devpost_events)}")
    except Exception as e:
        print(f"Failed to initialize driver or scrape Devpost: {e}")
        traceback.print_exc()
    finally:
         if current_driver:
            try:
                print("Quitting Devpost WebDriver...")
                current_driver.quit()
            except Exception as e:
                print(f"Error quitting Devpost driver: {e}")

    current_driver = None
    try:
        print("\nInitializing WebDriver for Unstop...")
        current_driver = get_driver()
        unstop_events = scrape_unstop(current_driver)
        master_event_list.extend(unstop_events)
        print(f"Unstop events added: {len(unstop_events)}")
    except Exception as e:
        print(f"Failed to initialize driver or scrape Unstop: {e}")
        traceback.print_exc()
    finally:
         if current_driver:
            try:
                print("Quitting Unstop WebDriver...")
                current_driver.quit()
            except Exception as e:
                print(f"Error quitting Unstop driver: {e}")

    total_events = len(master_event_list)
    print(f"\nTotal events scraped from all sources: {total_events}")
    
    if total_events == 0:
        print("\nNo events were scraped from any source. Check individual scraper outputs and website structures.")

    print("--- Aggregation Script Finished ---")
    
    return {
        "message": f"Scraping completed. Found {total_events} events.",
        "total_events": total_events,
        "events": master_event_list
    }


if __name__ == "__main__":
    print("Running scraper directly...")
    
    results = runscraper()

    print(f"\n--- Direct Execution Results ---")
    print(f"Message: {results.get('message', 'N/A')}")
    print(f"Total Events Scraped: {results.get('total_events', 0)}")

    if results.get('events'):
        print(f"First 2 events (if available):")
        for i, event in enumerate(results['events'][:2]):
            print(f"Event {i+1}: {event.get('title', 'N/A')} from {event.get('source', 'N/A')}")
        
        OUTPUT_JSON_FILE = 'aggregated_events_direct_run.json'
        print(f"\nSaving all events to {OUTPUT_JSON_FILE}...")
        try:
            with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(results['events'], f, indent=4, ensure_ascii=False)
            print(f"Data saved successfully to {OUTPUT_JSON_FILE}.")
        except IOError as e:
            print(f"Error writing to JSON file {OUTPUT_JSON_FILE}: {e}")
    elif results.get("error"):
        print(f"Error during scraping: {results.get('error')}")
        print(f"Details: {results.get('details')}")
    else:
        print("No events were scraped or an unknown issue occurred.")
    
    print("--- Direct Execution Finished ---")