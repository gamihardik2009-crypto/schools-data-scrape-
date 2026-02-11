import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# ---------------- Browser Setup ----------------
def make_driver():

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# ---------------- Get School List ----------------
def get_schools():

    driver = make_driver()

    url = "https://www.fultonschools.org/our-district/schools-admin-locations/all-fcs-schools"
    driver.get(url)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section header h2 a"))
    )

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

    driver.quit()

    return schools


# ---------------- Scrape Staff ----------------
def scrape_staff(args):

    school, site = args

    driver = make_driver()

    staff_url = site.rstrip("/") + "/staff"

    data = []

    try:
        driver.get(staff_url)

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

            row = [name, role, email, school]
            data.append(row)

    except:
        pass

    driver.quit()

    return data


# ---------------- Main ----------------
def main():

    console.print("\n[bold green]Getting school list...[/bold green]")

    schools = get_schools()

    console.print(f"Found {len(schools)} schools\n")

    table = Table(title="Live Staff Data")

    table.add_column("Name", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Email", style="green")
    table.add_column("School", style="magenta")

    all_rows = []

    # Parallel workers (adjust if PC is weak: 3-5)
    MAX_WORKERS = 5

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = []

        for s in schools:
            futures.append(executor.submit(scrape_staff, s))

        for future in as_completed(futures):

            rows = future.result()

            for row in rows:

                all_rows.append(row)

                table.add_row(
                    row[0][:25],
                    row[1][:25],
                    row[2][:30],
                    row[3][:25]
                )

                console.clear()
                console.print(table)

    # Save Excel
    df = pd.DataFrame(
        all_rows,
        columns=["Name", "Role", "Email", "School"]
    )

    df.drop_duplicates(subset=["Email"], inplace=True)

    df.to_excel("fulton_staff_fast.xlsx", index=False)

    console.print("\n[bold green]Saved: fulton_staff_fast.xlsx[/bold green]")


if __name__ == "__main__":
    main()
