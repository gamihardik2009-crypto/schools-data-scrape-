import asyncio
import pandas as pd

from rich.console import Console
from rich.table import Table

from playwright.async_api import async_playwright, TimeoutError

console = Console()


# ---------------- Get School List ----------------
async def get_schools(page):
    await page.goto(
        "https://www.fultonschools.org/our-district/schools-admin-locations/all-fcs-schools",
        timeout=60000
    )

    await page.wait_for_selector("section header h2 a")

    schools = []
    buttons = await page.query_selector_all("section > div > section header h2 a")

    for btn in buttons:
        try:
            name = (await btn.inner_text()).strip()
            panel_id = await btn.get_attribute("aria-controls")

            panel = await page.query_selector(f"#{panel_id}")
            link = await panel.query_selector("a:text('School Website')")
            link = await link.get_attribute("href")

            schools.append([name, link])
        except:
            continue

    return schools


# ---------------- Scrape Staff ----------------
async def scrape_staff(browser, school, site, seen_urls):
    page = await browser.new_page()
    staff_url = site.rstrip("/") + "/staff"
    data = []

    try:
        await page.goto(staff_url, timeout=60000)
        final_url = page.url

        if final_url in seen_urls:
            await page.close()
            return []

        seen_urls.add(final_url)

        await page.wait_for_selector("div.fsConstituentItem", timeout=15000)
        cards = await page.query_selector_all("div.fsConstituentItem")

        for card in cards:
            async def safe_text(sel):
                el = await card.query_selector(sel)
                return (await el.inner_text()).strip() if el else ""

            name = await safe_text("h3.fsFullName")
            role = (await safe_text("div.fsTitles")).replace("Title:", "").strip()
            email = await safe_text("div.fsEmail a")

            data.append([name, role, email, school])

    except TimeoutError:
        pass

    await page.close()
    return data


# ---------------- Main ----------------
async def main():
    console.print("[bold green]Starting FAST async Playwright scraper...[/bold green]")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox"
            ]
        )

        page = await browser.new_page()
        schools = await get_schools(page)

        console.print(f"\nFound {len(schools)} schools\n")
        for i, (name, url) in enumerate(schools, start=1):
            console.print(f"{i}. {name} -> {url}")

        limit = int(input("\nHow many schools do you want to scrape? : "))
        schools = schools[:limit]

        seen_urls = set()

        tasks = [
            scrape_staff(browser, school, site, seen_urls)
            for school, site in schools
        ]

        results = await asyncio.gather(*tasks)
        await browser.close()

    # Flatten results
    all_rows = [row for group in results for row in group]

    table = Table(title="Final Staff Data")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="yellow")
    table.add_column("Email", style="green")
    table.add_column("School", style="magenta")

    for r in all_rows:
        table.add_row(r[0][:25], r[1][:25], r[2][:30], r[3][:25])

    console.print(table)

    df = pd.DataFrame(all_rows, columns=["Name", "Role", "Email", "School"])
    df.drop_duplicates(subset=["Email"], inplace=True)
    df.to_excel("fulton_staff_fast_async.xlsx", index=False)

    console.print("\n[bold green]Saved: fulton_staff_fast_async.xlsx[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())


