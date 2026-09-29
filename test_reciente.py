#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from playwright.async_api import async_playwright, expect


URL = "https://public.tableau.com/app/profile/wansikmyung/viz/HumanAnatomy3DModeling/HumanAnatomy3D-English"


async def filter_options_selector(frame, field_to_filter, items):

    filter_box = frame.locator(".CategoricalFilterBox").filter(
        has=frame.locator(f'h3[title="{field_to_filter}"]')
    )

    combo = filter_box.locator('span[role="combobox"]')

    label_id = await combo.get_attribute("aria-labelledby")

    await combo.click()

    menu = frame.locator(
        f'div[role="dialog"][aria-labelledby="{label_id}"]'
    )

    await expect(menu).to_be_visible()

    checkboxes = menu.locator('div[role="checkbox"]')

    names = await checkboxes.all_inner_texts()

    # Desmarcar todo
    for name in names:
        name = name.strip()

        if name == "(All)":
            continue

        option = checkboxes.filter(has_text=name)

        if await option.get_attribute("aria-checked") == "true":
            await option.click(
                position={"x": 15, "y": 10}
            )

    # Marcar únicamente lo solicitado
    for item in items:

        option = checkboxes.filter(has_text=item)

        if await option.get_attribute("aria-checked") == "false":
            await option.click(
                position={"x": 15, "y": 10}
            )

    # Apply
    apply_button = menu.locator('button[title="Apply"]')

    await expect(apply_button).to_be_enabled()
    await apply_button.click()

    print(f"{field_to_filter}: {items}")






async def main():

    p = await async_playwright().start()

    browser = await p.chromium.launch(
        headless=False
    )

    context = await browser.new_context(
        viewport={
            "width": 1800,
            "height": 1200
        }
    )

    page = await context.new_page()

    await page.goto(URL)

    print("Página cargada")

    # Click directo en cookies
    await page.get_by_role(
        "button",
        name="Accept All Cookies"
    ).click()

    frame = page.frame_locator(
        'iframe[title="Data Visualization"]'
    )

    await filter_options_selector(
        frame,
        "System",
        ["Muscular", "Skeletal", "Nervous"]
    )

    await filter_options_selector(
        frame,
        "Group",
        ["Abdomen", "Foot"]
    )

    print("Filtros terminados")

    input("Enter para cerrar")

    await context.close()
    await browser.close()
    await p.stop()

# asyncio.run(main())




# p, browser, context, page = await main()
