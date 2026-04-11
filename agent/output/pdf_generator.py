"""Generate PDF from HTML report using Playwright."""

import asyncio
from pathlib import Path


async def _generate_pdf(html_path: str, pdf_path: str) -> str:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{Path(html_path).resolve()}", wait_until="networkidle")
        await page.pdf(
            path=pdf_path,
            format="Letter",
            margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
            print_background=True,
        )
        await browser.close()
    return pdf_path


def generate_pdf(html_path: str, pdf_path: str) -> str:
    return asyncio.run(_generate_pdf(html_path, pdf_path))
