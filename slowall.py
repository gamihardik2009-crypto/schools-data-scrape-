import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def get_schools(driver):

    url = "https://www.fultonschools.org/our-district/schools-admin-locations/all-fcs-schools"
    driver.get(url)

    time.sleep(5)

    buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "section > div > section header h2 a"
    )

    schools = []

    for btn in buttons:

        name = btn.text.strip()
        panel_id = btn.get_attribute("aria-controls")

        try:
            panel = driver.find_element(By.ID, panel_id)

            link = panel.find_element(
                By.XPATH,
                ".//a[normalize-space()='School Website']"
            ).get_attribute("href")

            schools.append([name, link])

        except:
            continue

    return schools


def scrape_staff(driver, staff_url, school_name):

    driver.get(staff_url)
    time.sleep(4)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.fsConstituentItem")

    staff_data = []

    for card in cards:

        try:
            name = card.find_element(By.CSS_SELECTOR, "h3.fsFullName").text.strip()
        except:
            name = ""

        try:
            role = card.find_element(By.CSS_SELECTOR, "div.fsTitles").text.replace("Title:", "").strip()
        except:
            role = ""

        try:
            email = card.find_element(By.CSS_SELECTOR, "div.fsEmail a").text.strip()
        except:
            email = ""

        staff_data.append([
            name,
            role,
            email,
            school_name
        ])

    return staff_data


def main():

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    print("Getting school list...")
    schools = get_schools(driver)

    print("Total schools:", len(schools))

    all_data = []

    for name, site in schools:

        staff_url = site.rstrip("/") + "/staff"

        print("Scraping:", name)

        try:
            staff = scrape_staff(driver, staff_url, name)
            all_data.extend(staff)

        except:
            print("Failed:", name)

    driver.quit()

    # Save to Excel
    df = pd.DataFrame(
        all_data,
        columns=["Name", "Role", "Email", "School"]
    )

    df.to_excel("fulton_staff_database.xlsx", index=False)

    print("\nSaved to fulton_staff_database.xlsx")


if __name__ == "__main__":
    main()
