import os
import time
import pyperclip
import asyncio
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Bot

from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
CSV_FILE = os.getenv('CSV_FILE')

# Function to initialize WebDriver with existing Chrome session
def init_driver():
    # Kill all Chrome processes to ensure no conflicts (Mac)
    os.system("pkill -f 'Google Chrome'")

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--user-data-dir=/Users/YourUsername/Library/Application Support/Google/Chrome")
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument("--start-maximized")

    # Initialize WebDriver with ChromeDriver manager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Function to scrape product data and save to CSV
def scrape_products(driver):
    driver.get('https://www.mercadolibre.com.mx/ofertas')
    time.sleep(5)  # Wait for page to load

    products = []
    elements = driver.find_elements(By.CSS_SELECTOR, '.promotion-item')

    for element in elements:
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

    df = pd.DataFrame(products, columns=['Title', 'Discount', 'Price', 'Previous Price', 'Link'])
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# Function to generate affiliate links
async def generate_affiliate_links(driver):
    driver.get('https://www.mercadolibre.com.mx/afiliados/linkbuilder')
    time.sleep(5)  # Wait for page to load

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

    df = pd.read_csv(CSV_FILE)
    df['Affiliate Link'] = pd.Series(affiliate_links[:len(df)])  # Ensure the number of affiliate links matches the number of rows

    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')

# Function to send messages to Telegram
async def send_to_telegram():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    df = pd.read_csv(CSV_FILE)
    df = df[df['Affiliate Link'].str.startswith('https://mercadolibre.com')]  # Filter valid affiliate links
    df = df.sort_values(by='Discount', ascending=False)  # Sort by discount in descending order

    for _, row in df.iterrows():
        message = f"🌟 ¡Oferta del día! 🌟\n\n" \
                  f"🛒 {row['Title']}\n" \
                  f"💰 Descuento: {row['Discount']}\n" \
                  f"🔗 {row['Affiliate Link']}\n" \
                  f"¡Aprovecha antes de que se acabe! 🎉🛍️"
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
        await asyncio.sleep(3600)  # Rate limit to avoid spamming

# Main function to execute the tasks
async def main():
    driver = init_driver()
    scrape_products(driver)
    await generate_affiliate_links(driver)
    # await send_to_telegram()
    driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
