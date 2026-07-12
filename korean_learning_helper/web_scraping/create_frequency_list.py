"""
Scrapes frequency words from kimchi-reader.app and extracts their meanings.
"""

import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- Constants ---
URL = "https://kimchi-reader.app/explore/freq/words"
POPUP_MEANING_CONTAINER_XPATH = "/html/body/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[3]/div[1]/div/div[4]/div[2]/div[1]/div/div[2]"
MEANING_ROW_CSS = "div.\\[display\\:contents\\]"
WORD_CONTAINER_XPATH = "/html/body/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/div/div[4]"
NEXT_BUTTON_XPATH = "/html/body/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/div/div[5]/div[3]/button[3]"


def _extract_star_count(meaning_container, idx: int) -> int:
    """Extracts the star count from the corresponding star div."""
    try:
        star_containers = meaning_container.find_elements(
            By.CSS_SELECTOR, "div[flex][flex-row][justify-end]"
        )
        if idx <= len(star_containers):
            stars = star_containers[idx - 1].find_elements(
                By.CSS_SELECTOR, "div.i-mingcute-star-fill"
            )
            return len(stars)
        return 0
    except Exception as e:
        print(f"      Error getting stars: {e}")
        return 0


def _extract_long_meaning(row, meaning_num: str, short_meaning: str) -> str:
    """Extracts the detailed, long meaning from the meaning row."""
    divs = row.find_elements(By.TAG_NAME, "div")
    for div in divs:
        if (
            not div.get_attribute("pr-2")
            and not div.get_attribute("c-orange")
            and not div.get_attribute("flex")
        ):
            text = div.text.strip()
            if text and text != meaning_num and text != short_meaning:
                return text
    return ""


def get_word_meanings(driver, word_element) -> list:
    """Click on a word and extract all its meanings with star counts.

    Args:
        driver: Selenium WebDriver instance.
        word_element: The word element to click.

    Returns:
        list: List of dictionaries containing meaning data.
    """
    meanings = []
    try:
        word_element.click()
        wait = WebDriverWait(driver, 10)
        meaning_container = wait.until(
            EC.presence_of_element_located((By.XPATH, POPUP_MEANING_CONTAINER_XPATH))
        )
        time.sleep(1.5)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, MEANING_ROW_CSS)))
        meaning_rows = meaning_container.find_elements(By.CSS_SELECTOR, MEANING_ROW_CSS)

        print(f"    Found {len(meaning_rows)} meanings")

        for idx, row in enumerate(meaning_rows, 1):
            try:
                meaning_num = row.find_element(By.CSS_SELECTOR, "div[pr-2]").text.strip()

                try:
                    short_meaning = row.find_element(By.CSS_SELECTOR, "div[c-orange]").text.strip()
                except NoSuchElementException:
                    short_meaning = ""

                long_meaning = _extract_long_meaning(row, meaning_num, short_meaning)
                stars = _extract_star_count(meaning_container, idx)

                meaning_data = {
                    "number": meaning_num,
                    "short": short_meaning,
                    "long": long_meaning,
                    "stars": stars,
                }
                meanings.append(meaning_data)
                print(f"      Meaning {idx}: {short_meaning} ({stars} stars)")

            except Exception as e:
                print(f"    Error extracting meaning {idx}: {e}")
                continue

        time.sleep(0.5)

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            driver.execute_script("arguments[0].click();", body)
        except Exception:
            pass

        time.sleep(0.5)

    except TimeoutException:
        print("  Timeout waiting for meanings popup to load")
    except Exception as e:
        print(f"  Error getting meanings: {e}")

    return meanings


def _process_word_element(driver, div, div_idx: int, total_words: int, words_data: list):
    """Processes a single word element from the list."""
    try:
        index_text = div.text.split("\n")[0].strip().rstrip(".")
        rank = index_text.split(".")[0].strip()

        word_element = div.find_element(By.CSS_SELECTOR, "[kr-lemma-item]")
        word = word_element.text.strip()

        if rank and word:
            print(f"  Processing word {div_idx}/{total_words}: {rank}|{word}")
            meanings = get_word_meanings(driver, word_element)

            if meanings:
                for i, meaning in enumerate(meanings, 1):
                    words_data.append({
                        "rank": f"{rank}.{i}",
                        "word": word,
                        "meaning_num": meaning.get("number", ""),
                        "short_meaning": meaning.get("short", ""),
                        "long_meaning": meaning.get("long", ""),
                        "stars": meaning.get("stars", 0),
                    })
            else:
                print("    No meanings found, adding basic entry")
                words_data.append({
                    "rank": f"{rank}.1",
                    "word": word,
                    "meaning_num": "1",
                    "short_meaning": "",
                    "long_meaning": "",
                    "stars": 0,
                })
            time.sleep(0.5)
    except Exception as e:
        print(f"  Error extracting word: {e}")


def _navigate_to_next_page(driver) -> bool:
    """Attempts to click the next page button. Returns True if successful."""
    try:
        next_button = driver.find_element(By.XPATH, NEXT_BUTTON_XPATH)
        if next_button.get_attribute("disabled"):
            print("Reached last page")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(1)
        next_button.click()
        time.sleep(3)
        return True
    except NoSuchElementException:
        print("Next button not found, ending scrape")
        return False
    except Exception as e:
        print(f"Error navigating to next page: {e}")
        return False


def scrape_frequency_words(max_pages: int = 100) -> list:
    """Scrapes frequency words from kimchi-reader.app with multiple meanings.

    Args:
        max_pages (int): Maximum number of pages to scrape (default: 100).

    Returns:
        list: List of dictionaries containing word data with meanings.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    words_data = []

    try:
        driver.get(URL)
        print(f"Navigating to {URL}")

        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[kr-lemma-item]")))
        time.sleep(3)

        current_page = 1
        while current_page <= max_pages:
            print(f"\nScraping page {current_page}...")
            time.sleep(2)

            try:
                word_container = driver.find_element(By.XPATH, WORD_CONTAINER_XPATH)
                word_divs = word_container.find_elements(By.XPATH, "./div")
                print(f"Found {len(word_divs)} words on page {current_page}")

                for div_idx, div in enumerate(word_divs, 1):
                    _process_word_element(driver, div, div_idx, len(word_divs), words_data)

            except NoSuchElementException as e:
                print(f"Could not find word container: {e}")
                break

            if not _navigate_to_next_page(driver):
                break
            current_page += 1

    finally:
        driver.quit()

    return words_data


def save_to_csv(words_data: list, filename: str = "korean_frequency_words.csv"):
    """Saves scraped words to a CSV file.

    Args:
        words_data (list): List of dictionaries with word data.
        filename (str): Output filename.
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(["Rank", "Word", "Meaning_Num", "Short_Meaning", "Long_Meaning", "Stars"])

        for word_data in words_data:
            writer.writerow([
                word_data["rank"],
                word_data["word"],
                word_data["meaning_num"],
                word_data["short_meaning"],
                word_data["long_meaning"],
                word_data["stars"],
            ])

    print(f"\nSaved {len(words_data)} word meanings to {filename}")


if __name__ == "__main__":
    print("Starting web scraper...")
    words = scrape_frequency_words(max_pages=2)
    print(f"\nTotal word meanings scraped: {len(words)}")
    save_to_csv(words)

    print("\nFirst 10 entries:")
    for data in words[:10]:
        print(f"{data['rank']}|{data['word']}|{data['short_meaning']}|{data['stars']} stars")
