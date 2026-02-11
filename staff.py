import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def scrape_staff(staff_url, school_name):

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(staff_url)

    time.sleep(5)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.fsConstituentItem")

    results = []

    for card in cards:

        try:
            name = card.find_element(By.CSS_SELECTOR, "h3.fsFullName").text.strip()
        except:
            name = ""

        try:
            title = card.find_element(By.CSS_SELECTOR, "div.fsTitles").text.replace("Title:", "").strip()
        except:
            title = ""

        try:
            email = card.find_element(By.CSS_SELECTOR, "div.fsEmail a").text.strip()
        except:
            email = ""

        results.append([
            name,
            title,
            email,
            school_name
        ])

        print(name, "|", title, "|", email)

    print("\nTotal staff:", len(results))

    driver.quit()

    return results


if __name__ == "__main__":

    url = "https://langstonhughes.fultonschools.org/staff"
    school = "Langston Hughes High School"

    scrape_staff(url, school)
