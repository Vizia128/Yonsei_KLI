from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv


def get_word_meanings(driver, word_element):
    """
    Click on a word and extract all its meanings with star counts

    Args:
        driver: Selenium WebDriver instance
        word_element: The word element to click

    Returns:
        list: List of dictionaries containing meaning data
    """
    meanings = []

    try:
        # Click the word to open details
        word_element.click()

        # Wait for the popup/details panel to appear and be fully loaded
        wait = WebDriverWait(driver, 10)

        # Wait for the meaning container to be present and visible
        meaning_container = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[3]/div[1]/div/div[4]/div[2]/div[1]/div/div[2]",
                )
            )
        )

        # Additional wait to ensure all content is loaded
        time.sleep(1.5)

        # Wait for at least one meaning row to be present
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.\\[display\\:contents\\]")
            )
        )

        # Get all meaning rows
        meaning_rows = meaning_container.find_elements(
            By.CSS_SELECTOR, "div.\\[display\\:contents\\]"
        )

        print(f"    Found {len(meaning_rows)} meanings")

        for idx, row in enumerate(meaning_rows, 1):
            try:
                meaning_data = {}

                # Get meaning number
                meaning_num = row.find_element(
                    By.CSS_SELECTOR, "div[pr-2]"
                ).text.strip()
                meaning_data["number"] = meaning_num

                # Get short meaning (the orange text)
                try:
                    short_meaning = row.find_element(
                        By.CSS_SELECTOR, "div[c-orange]"
                    ).text.strip()
                    meaning_data["short"] = short_meaning
                except NoSuchElementException:
                    meaning_data["short"] = ""

                # Get long meaning (the description)
                divs = row.find_elements(By.TAG_NAME, "div")
                # The long meaning is typically the last div without special attributes
                long_meaning = ""
                for div in divs:
                    if (
                        not div.get_attribute("pr-2")
                        and not div.get_attribute("c-orange")
                        and not div.get_attribute("flex")
                    ):
                        text = div.text.strip()
                        if text and text != meaning_num and text != short_meaning:
                            long_meaning = text
                            break
                meaning_data["long"] = long_meaning

                # Get star count - need to find the corresponding star div
                # The star divs are siblings that come before the meaning rows
                try:
                    # Get the parent container
                    parent = meaning_container

                    # Find all star containers
                    star_containers = parent.find_elements(
                        By.CSS_SELECTOR, "div[flex][flex-row][justify-end]"
                    )

                    # The star container index should match the meaning index
                    if idx <= len(star_containers):
                        stars = star_containers[idx - 1].find_elements(
                            By.CSS_SELECTOR, "div.i-mingcute-star-fill"
                        )
                        meaning_data["stars"] = len(stars)
                    else:
                        meaning_data["stars"] = 0

                except Exception as e:
                    print(f"      Error getting stars: {e}")
                    meaning_data["stars"] = 0

                meanings.append(meaning_data)
                print(
                    f"      Meaning {idx}: {meaning_data['short']} ({meaning_data['stars']} stars)"
                )

            except Exception as e:
                print(f"    Error extracting meaning {idx}: {e}")
                continue

        # Close the popup - try clicking outside or on a close button
        # Wait a moment before closing
        time.sleep(0.5)

        # Try to click outside the popup to close it
        try:
            # Click on the main container area outside the popup
            body = driver.find_element(By.TAG_NAME, "body")
            # Use JavaScript to click to avoid interception issues
            driver.execute_script("arguments[0].click();", body)
        except:
            pass

        # Wait for popup to close
        time.sleep(0.5)

    except TimeoutException:
        print(f"  Timeout waiting for meanings popup to load")
    except Exception as e:
        print(f"  Error getting meanings: {e}")

    return meanings


def scrape_frequency_words(max_pages=100):
    """
    Scrapes frequency words from kimchi-reader.app with multiple meanings

    Args:
        max_pages (int): Maximum number of pages to scrape (default: 100)

    Returns:
        list: List of dictionaries containing word data with meanings
    """

    # Setup Chrome driver
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Commented out for debugging
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)  # Set implicit wait

    url = "https://kimchi-reader.app/explore/freq/words"
    words_data = []

    try:
        driver.get(url)
        print(f"Navigating to {url}")

        # Wait for page to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[kr-lemma-item]")))

        # Extra wait for initial page load
        time.sleep(3)

        current_page = 1

        while current_page <= max_pages:
            print(f"\nScraping page {current_page}...")

            # Wait a bit for content to load
            time.sleep(2)

            # Find all word elements on current page
            try:
                # Find the container with all words
                word_container = driver.find_element(
                    By.XPATH,
                    "/html/body/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/div/div[4]",
                )

                # Get all child divs (each contains index + word)
                word_divs = word_container.find_elements(By.XPATH, "./div")

                print(f"Found {len(word_divs)} words on page {current_page}")

                for div_idx, div in enumerate(word_divs, 1):
                    try:
                        # Get index (the text node) and remove the period
                        index_text = div.text.split("\n")[0].strip().rstrip(".")
                        # Extract just the number part
                        rank = index_text.split(".")[0].strip()

                        # Get word element
                        word_element = div.find_element(
                            By.CSS_SELECTOR, "[kr-lemma-item]"
                        )
                        word = word_element.text.strip()

                        if rank and word:
                            print(
                                f"  Processing word {div_idx}/{len(word_divs)}: {rank}|{word}"
                            )

                            # Get meanings for this word
                            meanings = get_word_meanings(driver, word_element)

                            if meanings:
                                # Create a row for each meaning
                                for i, meaning in enumerate(meanings, 1):
                                    word_data = {
                                        "rank": f"{rank}.{i}",
                                        "word": word,
                                        "meaning_num": meaning.get("number", ""),
                                        "short_meaning": meaning.get("short", ""),
                                        "long_meaning": meaning.get("long", ""),
                                        "stars": meaning.get("stars", 0),
                                    }
                                    words_data.append(word_data)
                            else:
                                # If no meanings found, add basic entry
                                print(f"    No meanings found, adding basic entry")
                                word_data = {
                                    "rank": f"{rank}.1",
                                    "word": word,
                                    "meaning_num": "1",
                                    "short_meaning": "",
                                    "long_meaning": "",
                                    "stars": 0,
                                }
                                words_data.append(word_data)

                            # Small delay between words
                            time.sleep(0.5)

                    except Exception as e:
                        print(f"  Error extracting word: {e}")
                        continue

            except NoSuchElementException as e:
                print(f"Could not find word container: {e}")
                break

            # Try to go to next page
            try:
                next_button = driver.find_element(
                    By.XPATH,
                    "/html/body/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[2]/div/div[5]/div[3]/button[3]",
                )

                # Check if button is disabled
                if next_button.get_attribute("disabled"):
                    print("Reached last page")
                    break

                # Scroll to button
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)

                # Click next button
                next_button.click()
                current_page += 1

                # Wait for new content to load
                time.sleep(3)

            except NoSuchElementException:
                print("Next button not found, ending scrape")
                break
            except Exception as e:
                print(f"Error navigating to next page: {e}")
                break

    finally:
        driver.quit()

    return words_data


def save_to_csv(words_data, filename="korean_frequency_words.csv"):
    """
    Save scraped words to CSV file

    Args:
        words_data (list): List of dictionaries with word data
        filename (str): Output filename
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(
            ["Rank", "Word", "Meaning_Num", "Short_Meaning", "Long_Meaning", "Stars"]
        )

        for word_data in words_data:
            writer.writerow(
                [
                    word_data["rank"],
                    word_data["word"],
                    word_data["meaning_num"],
                    word_data["short_meaning"],
                    word_data["long_meaning"],
                    word_data["stars"],
                ]
            )

    print(f"\nSaved {len(words_data)} word meanings to {filename}")


if __name__ == "__main__":
    print("Starting web scraper...")

    # Scrape pages (start with fewer for testing)
    words = scrape_frequency_words(max_pages=2)

    print(f"\nTotal word meanings scraped: {len(words)}")

    # Save to CSV
    save_to_csv(words)

    # Print first 10 entries as sample
    print("\nFirst 10 entries:")
    for word_data in words[:10]:
        print(
            f"{word_data['rank']}|{word_data['word']}|{word_data['short_meaning']}|{word_data['stars']} stars"
        )
