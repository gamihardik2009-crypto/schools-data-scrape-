import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def main():

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    url = "https://www.fultonschools.org/our-district/schools-admin-locations/all-fcs-schools"
    driver.get(url)

    # only wait once
    time.sleep(5)

    buttons = driver.find_elements(
        By.CSS_SELECTOR,
        "section > div > section header h2 a"
    )

    results = []

    for btn in buttons:

        name = btn.text.strip()

        panel_id = btn.get_attribute("aria-controls")

        try:
            panel = driver.find_element(By.ID, panel_id)

            link = panel.find_element(
                By.XPATH,
                ".//a[normalize-space()='School Website']"
            ).get_attribute("href")

            results.append([name, link])
            print(name, "=>", link)

        except:
            print("No link:", name)

    print("\nTotal schools:", len(results))

    driver.quit()


if __name__ == "__main__":
    main()
