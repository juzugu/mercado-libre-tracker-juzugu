# import the necessary libraries "tool box"
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
#i put the ur in a variable to make it easier to read
url = "https://www.mercadolibre.com.co/pepper-gel-sabre-aim-and-fire-w-trigger-45m-range/p/MCO2027801104#polycard_client=recommendations_home_navigation-recommendations&reco_backend=machinalis-homes-univb-equivalent-offer&wid=MCO2968521650&reco_client=home_navigation-recommendations&reco_item_pos=0&reco_backend_type=function&reco_id=6ac44063-52fb-4475-aecb-2e59d38f3279&sid=recos&c_id=/home/navigation-recommendations/element&c_uid=7e07e687-c8d4-4463-bed1-3639e7ad7722"
#i added headers to mimic a real browser request(this is important to avoid being blocked by some websites)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
#(i get this from the REQUESTS documentation)
response = requests.get(url, headers=headers)

if response.status_code == 200:
    html_text = response.text
    Bsoup = BeautifulSoup(html_text, 'html.parser')

    title_element = Bsoup.find('h1', class_='ui-pdp-title')
    if title_element:#check if it  find anything
        title = title_element.text.strip()
    else:
        title = "Title not found"


    price_selector = "div.ui-pdp-price__second-line span.andes-money-amount__fraction"
    price_element = Bsoup.select_one(price_selector)    #this is for check if the price element was found
    if price_element:
        price = price_element.text.strip()
    else:
        print("Price not found")
    # Formats the current time as: YYYY-MM-DD HH:MM:SS
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Timestamp: {timestamp}")
    print(f"Product: {title}")
    print(f"Price: {price}")

else:
    print(f"Error:  {response.status_code}")
