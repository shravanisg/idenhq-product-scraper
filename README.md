🛒 Product Inventory Scraper – IDEN HQ

This project is a **web scraper** built with [Playwright](https://playwright.dev/python/) to automate the process of logging into [IDEN HQ](https://hiring.idenhq.com), navigating to the product inventory section, and extracting all visible product data into a structured JSON file.

📦 Features

- Automates login using secure credentials
- Navigates through dashboard menus
- Handles UI drawer animations
- Scrolls and loads all product cards dynamically
- Extracts fields like `ID`, `Name`, `Dimensions`, `Manufacturer`, `Cost`, etc.
- Saves the extracted data into `product_data.json`

🚀 Setup Instructions

Clone the Repository
git clone https://github.com/yourusername/idenhq-product-scraper.git
cd idenhq-product-scraper

Install dependencies
pip install playwright
playwright install

Add credentials
Create a credentials.json file in the project folder:

{
  "username": "your-email@example.com",
  "password": "your-password"
}

Run the scraper
python app.py

Get results
Scraped data will be saved to:
product_data.json
