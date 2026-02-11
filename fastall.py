import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from rich.console import Console
from rich.table import Table

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


console = Console()

SCRAPED_STAFF_URLS = set()
url_lock = Lock()


def make_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def get_schools():
    driver = make_driver()
    driver.get("https://www.fultonschools.org/our-district/schools-admin-locations/all-fcs-schools")

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section header h2 a"))
    )

    schools = []

    buttons = driver.find_elements(By.CSS_SELECTOR, "section > div > section header h2 a")

    for btn in buttons:
        try:
            name = btn.text.strip()
            panel_id = btn.get_attribute("aria-controls")
            panel = driver.find_element(By.ID, panel_id)

            link = panel.find_element(
                By.XPATH, ".//a[normalize-space()='School Website']"
            ).get_attribute("href")

            schools.append([name, link])
        except:
            continue

    driver.quit()
    return schools


def scrape_staff(args):
    school, site = args
    driver = make_driver()
    staff_url = site.rstrip("/") + "/staff"
    data = []

    try:
        driver.get(staff_url)
        final_url = driver.current_url

        with url_lock:
            if final_url in SCRAPED_STAFF_URLS:
                driver.quit()
                return []
            SCRAPED_STAFF_URLS.add(final_url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.fsConstituentItem"))
        )

        cards = driver.find_elements(By.CSS_SELECTOR, "div.fsConstituentItem")

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

            data.append([name, role, email, school])

    except:
        pass

    driver.quit()
    return data


def main():
    console.print("\n[bold green]Getting school list...[/bold green]")
    schools = get_schools()

    console.print(f"\nFound {len(schools)} schools\n")

    for i, (name, url) in enumerate(schools, start=1):
        console.print(f"{i}. {name} -> {url}")

    limit = int(input("\nHow many schools do you want to scrape? : "))
    schools = schools[:limit]

    all_rows = []
    MAX_WORKERS = 5

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(scrape_staff, s) for s in schools]

        for future in as_completed(futures):
            rows = future.result()
            all_rows.extend(rows)

    # Build table ONCE
    table = Table(title="Final Staff Data")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Email", style="green")
    table.add_column("School", style="magenta")

    for row in all_rows:
        table.add_row(
            row[0][:25],
            row[1][:25],
            row[2][:30],
            row[3][:25]
        )

    console.print(table)

    df = pd.DataFrame(all_rows, columns=["Name", "Role", "Email", "School"])
    df.drop_duplicates(subset=["Email"], inplace=True)

    df.to_excel("fulton_staff_fast.xlsx", index=False)
    console.print("\n[bold green]Saved: fulton_staff_fast.xlsx[/bold green]")


if __name__ == "__main__":
    main()

