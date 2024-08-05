import os
import time
import pyperclip
import asyncio
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from dotenv import load_dotenv
import math
import requests

# Load environment variables from .env file
load_dotenv()

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
CSV_FILE = os.getenv('CSV_FILE')

def save_cookies(driver, filename='cookies.pkl'):
    import pickle
    cookies = driver.get_cookies()
    with open(filename, 'wb') as file:
        pickle.dump(cookies, file)

def load_cookies(driver, filename='cookies.pkl'):
    import pickle
    driver.get('https://www.mercadolibre.com.mx')  # Load initial page
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)

# Function to initialize WebDriver with existing Firefox session
def init_driver():
    # Kill all Firefox processes to ensure no conflicts (Mac)
    os.system("pkill -f 'firefox'")

    # Configure Firefox options
    options = Options()
    
    # Set the Firefox profile path
    options.add_argument("-profile")
    options.add_argument("/Users/isaac/Library/Application Support/Firefox/Profiles/ae15a4ti.default-release")

    # Initialize WebDriver with geckodriver
    driver = webdriver.Firefox(service=Service('/usr/local/bin/geckodriver'), options=options)

    # Load cookies
    load_cookies(driver)

    return driver

# Function to scrape product data and save to CSV
def scrape_products(driver, pages=['https://www.mercadolibre.com.mx/ofertas', 'https://www.mercadolibre.com.mx/ofertas?container_id=MLM779363-20&page=2']):
    products = []
    for page in pages:
        driver.get(page)
        
        # Wait until promotion items are loaded
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.promotion-item'))
            )
        except TimeoutException:
            print(f"Timed out waiting for page {page} to load")
            continue

        elements = driver.find_elements(By.CSS_SELECTOR, '.promotion-item')

        for element in elements:
            try:
                title = element.find_element(By.CSS_SELECTOR, '.promotion-item__title').text
                discount = element.find_element(By.CSS_SELECTOR, '.promotion-item__discount-text').text
                
                # Extract and clean price
                price_element = element.find_element(By.CSS_SELECTOR, '.andes-money-amount--cents-superscript')
                price = price_element.text.split(' ')[-1]  # Get numeric part only

                # Extract and clean previous price
                previous_price_element = element.find_element(By.CSS_SELECTOR, '.andes-money-amount--previous')
                previous_price = previous_price_element.text.split(' ')[-1]  # Get numeric part only

                # Extract link
                link = element.find_element(By.CSS_SELECTOR, '.promotion-item__link-container').get_attribute('href')
                
                products.append([title, discount, price, previous_price, link])
            
            except NoSuchElementException:
                # If any of the elements are not found, skip to the next promotion item
                print(f"Element not found on page {page} for element {element.text}")
                continue

    df = pd.DataFrame(products, columns=['Title', 'Discount', 'Price', 'Previous Price', 'Link'])
    # Drop duplicates based on the `Title` column, keeping the first occurrence
    df.drop_duplicates(subset=['Title'], keep='first', inplace=True)
    df.to_csv('products.csv', index=False, encoding='utf-8-sig')

# Function to generate affiliate links
async def generate_affiliate_links(driver):
    driver.get('https://www.mercadolibre.com.mx/afiliados/linkbuilder')
    time.sleep(5)  # Wait for page to load

    # Accept cookie consent if present
    try:
        cookie_accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.cookie-consent-banner-opt-out__button'))
        )
        cookie_accept_button.click()
    except:
        pass  # If the banner does not appear, continue

    df = pd.read_csv(CSV_FILE)
    urls = df['Link'].tolist()

    batch_size = 30
    affiliate_links = []

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]

        # Clear the textarea and paste URLs
        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea#url-0'))
        )
        textarea.clear()
        textarea.send_keys('\n'.join(batch))

        # Click the 'Generar' button
        generate_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#\\:Rkrcq\\:'))
        )
        generate_button.click()

        # Wait for the clipboard to be populated
        await asyncio.sleep(10)

        # Extract affiliate links from the clipboard
        batch_affiliate_links = pyperclip.paste().split('\n')
        affiliate_links.extend(batch_affiliate_links)

        # Refresh the page to clear previous data
        driver.refresh()
        await asyncio.sleep(5)  # Wait for page to refresh

    df['Affiliate Link'] = pd.Series(affiliate_links[:len(df)])  # Ensure the number of affiliate links matches the number of rows
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# Function to send messages to Telegram
async def send_to_telegram():
    df = pd.read_csv(CSV_FILE)
    df = df[df['Affiliate Link'].str.startswith('https://mercadolibre.com')]  # Filter valid affiliate links
    df = df.sort_values(by='Discount', ascending=False)  # Sort by discount in descending order

    interval = math.floor((12 * 60 * 60) / len(df))  # Calculate the interval in seconds for a 12-hour period
    for _, row in df.iterrows():
        price = row['Price'].strip().replace('\n', '')
        previous_price = row['Previous Price'].strip().replace('\n', '')
        message = f"🌟 ¡Oferta del día! 🌟\n\n" \
                  f"🔥 {row['Title']}\n" \
                  f"💰 Descuento: {row['Discount']}\n" \
                  f"💸 De {previous_price} a solo {price} \n" \
                  f"🔗 {row['Affiliate Link']}\n" \
                  f"¡Aprovecha antes de que se acabe! 🎉🛍️"
        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'text': message
        }
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data=payload)
        await asyncio.sleep(interval)  # Rate limit to publish over 12 hours

# Main function to execute the tasks
async def main():
    driver = init_driver()
    scrape_products(driver)
    await generate_affiliate_links(driver)
    await send_to_telegram()
    driver.quit()  # Close the Firefox browser when finished

if __name__ == "__main__":
    asyncio.run(main())