from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv


def scrape_frequency_words(max_pages=100):
    """
    Scrapes frequency words from kimchi-reader.app

    Args:
        max_pages (int): Maximum number of pages to scrape (default: 100)

    Returns:
        list: List of tuples containing (rank, word)
    """

    # Setup Chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    url = "https://kimchi-reader.app/explore/freq/words"
    words_data = []

    try:
        driver.get(url)
        print(f"Navigating to {url}")

        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[kr-lemma-item]")))

        current_page = 1

        while current_page <= max_pages:
            print(f"Scraping page {current_page}...")

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

                for div in word_divs:
                    try:
                        # Get index (the text node) and remove the period and word
                        index_text = div.text.split("\n")[0].strip().rstrip(".")
                        # Extract just the number part
                        index_text = index_text.split(".")[0].strip()

                        # Get word element
                        word_element = div.find_element(
                            By.CSS_SELECTOR, "[kr-lemma-item]"
                        )
                        word = word_element.text.strip()

                        if index_text and word:
                            words_data.append((index_text, word))
                            # Only print every 100th word
                            if len(words_data) % 100 == 0:
                                print(f"  {index_text}|{word}")

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

                # Click next button
                next_button.click()
                current_page += 1

                # Wait for new content to load
                time.sleep(2)

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
        words_data (list): List of tuples (rank, word)
        filename (str): Output filename
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerow(["Rank", "Word"])
        writer.writerows(words_data)

    print(f"\nSaved {len(words_data)} words to {filename}")


if __name__ == "__main__":
    print("Starting web scraper...")

    # Scrape all 100 pages (or however many you want)
    words = scrape_frequency_words(max_pages=100)

    print(f"\nTotal words scraped: {len(words)}")

    # Save to CSV
    save_to_csv(words)

    # Print first 10 words as sample
    print("\nFirst 10 words:")
    for rank, word in words[:10]:
        print(f"{rank}|{word}")
