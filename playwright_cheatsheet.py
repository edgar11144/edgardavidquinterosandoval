Browser Start and Close
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        # do something with the browser

asyncio.run(main())
Start a Chromium browser instance

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(channel='chrome')
        # do something with the browser

asyncio.run(main())
Start a Chrome browser instance

from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(channel='msedge')
        # do something with the browser

asyncio.run(main())
Start a Microsoft Edge browser instance

from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch()
        # do something with the browser

asyncio.run(main())
Start a Firefox browser instance

from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.webkit.launch()
        # do something with the browser
        
asyncio.run(main())
Start a WebKit browser instance

await browser.close()
Close the browser instance

Context Management
context = await browser.new_context()
Create a new browser context

await context.close()
Close the browser context

Page / Tab Management
page = await context.new_page()
Open a new page / tab

# add wait before the action that opens the new page
async with context.expect_page() as new_page_info:
  # perform the action that opens the new page, 
  # e.g. clicking a link
  await page.locator('a[target="_blank"]').click()
new_page = await new_page_info.value
Wait for a new page / tab to be opened (e.g. from clicking a link with target="_blank")

pages = context.pages
List all pages

page.bring_to_front()
Make the page / tab the active one

page.close()
Close the current page / tab

is_closed = page.is_closed()
Check if the page / tab is closed

Page Information
url = page.url
Get the current page URL

title = page.title()
Get the current page title

Page Assertions
Requires from playwright.async_api import expect

await expect(page).to_have_url('https://example.com/dashboard')
Assert the url of a page equals a specific value

await expect(page).to_have_title('Dashboard')
Assert the title of a page equals a specific value

Navigation
await page.goto('https://example.com')
Navigate to a URL

await page.reload()
Reload the current page

await page.go_back()
Navigate back in history

await page.go_forward()
Navigate forward in history

Element Selection
element = page.locator('#element')
Select an element using a CSS selector

element = page.get_by_text('Submit')
Select an element containing specific text

element = page.get_by_label('Username')
Select a form element by its associated label text

element = page.get_by_role('button', name='Submit')
Select an element by its ARIA role and name

element = page.get_by_placeholder('Enter your email')
Select an input element by its placeholder text

element = page.get_by_alt_text('Company Logo')
Select an image element by its alt text

element = page.get_by_title('Close')
Select an element by its title attribute

element = page.get_by_test_id('submit-button')
Select an element by its data-testid attribute

Waiting for Element States
await page.locator('#menu').wait_for(state='attached')
Wait for an element to be present in the DOM

await page.locator('#menu').wait_for(state='visible')
Wait for an element to be visible on the page

await page.locator('#menu').wait_for(
    state='visible', 
    timeout=30 * 60 * 1000 # 30 minutes
  )
Wait for an element to be visible on the page with a custom timeout

await page.locator('#menu').wait_for(state='hidden')
Wait for an element to be hidden or removed from the page

await page.locator('#menu').wait_for(state='detached')
Wait for an element to be removed from the DOM

Element State
text = await page.locator('#element').text_content()
Get the text content of an element

text = await page.locator('#element').inner_text()
Get the inner text of an element

html = await page.locator('#element').inner_html()
Get the inner HTML of an element

html = await page.locator('#element').outer_html()
Get the outer HTML of an element

href = await page.locator('#element').get_attribute('href')
Get the value of a specific attribute of an element

value = await page.locator('#input').input_value()
Get the value of an input element

# box contains x, y, width, height
box = await page.locator('#element').bounding_box()
Get the bounding box of an element

is_visible = await page.locator('#element').is_visible()
Check if an element is visible on the page

is_hidden = await page.locator('#element').is_hidden()
Check if an element is hidden on the page

is_enabled = await page.locator('#element').is_enabled()
Check if an element is enabled

is_disabled = await page.locator('#element').is_disabled()
Check if an element is disabled

is_checked = await page.locator('#checkbox').is_checked()
Check if a checkbox or radio button is checked

is_editable = await page.locator('#input').is_editable()
Check if an element is editable

Element Assertions
Requires from playwright.async_api import expect

await expect(page.locator('#element')).to_be_attached()
Assert that an element is attached to the DOM

await expect(page.locator('#element')).to_be_visible()
Assert that an element is visible on the page

await expect(page.locator('#element')).to_be_hidden()
Assert that an element is hidden on the page

await expect(page.locator('#element')).to_contain_text('Welcome Master Bruce')
Assert that an element contains specific text (case insensitive)

await expect(page.locator('#element')).to_contain_text(
    'wElComE mAster bRuCe', 
    ignore_case=True
  )
Assert that an element contains specific text (case insensitive)

await expect(page.locator('#element')).not_to_contain_text('Error')
Assert that an element does not contain specific text

await expect(page.locator('#input')).to_have_value('Hello World')
Assert that an input element has a specific value

await expect(page.locator('#multi-select')).to_have_values([
    'red', 'green'
  ])
Assert that a multi-select element has specific selected values

await expect(page.locator('#element')).to_have_class("error")
Assert that an element contains a specific CSS class

await expect(page.locator('#element')).not_to_have_class("error")
Assert that an element does not contain a specific CSS class

await expect(page.locator('#element')).to_have_css(
    'display', 'block'
  )
Assert that an element has a specific CSS style

await expect(page.locator('#element')).to_have_attribute('alt-text')
Assert that an element has a specific attribute with a specific value

await expect(page.locator('#element')).to_have_attribute(
    'alt-text', 'Company Logo'
  )
Assert that an element has a specific attribute with a specific value

await expect(page.locator('#checkbox')).to_be_checked()
Assert that a checkbox or radio button is checked

await expect(page.locator('#checkbox')).not_to_be_checked()
Assert that a checkbox or radio button is not checked

await expect(page.locator('#element')).to_be_enabled()
Assert that an element is enabled

await expect(page.locator('#element')).to_be_disabled()
Assert that an element is disabled

await expect(page.locator('#element')).to_be_focused()
Assert that an element is focused

Element Click / Hover / Drag and Drop
await page.locator('#button').click()
Click on an element

await page.locator('#button').click(button='right')
Right click on an element

await page.locator('#button').dblclick()
Double click on an element

await page.locator('#button').click(modifiers=['Control'])
Click on an element with keyboard modifiers (e.g. Ctrl, Shift)

await page.locator('#button').click(position={'x': 10, 'y': 5})
Click on an element at specific coordinates

await page.locator('#button').hover()
Hover over an element

await page.locator('#button').hover(position={'x': 10, 'y': 5})
Hover over an element at specific coordinates relative to top-left of the element

await page.locator('#source').drag_to(page.locator('#target'))
Drag an element and drop it onto another element

await page.locator('#source').drag_to(page.locator('#target'), 
    source_position={'x': 10, 'y': 5},
    target_position={'x': 10, 'y': 5}
  )
Drag an element and drop it onto another element with an offset

Mouse
await page.mouse.move(100, 200)
Move the mouse to specific coordinates relative to viewport

await page.mouse.down()
await page.mouse.up()
Click the mouse at the current position

await page.mouse.click(100, 200)
Click the mouse at specific coordinates relative to viewport

await page.mouse.click(100, 200, button='right')
Click the mouse with a specific button (e.g. right button) at specific coordinates relative to viewport

await page.mouse.dblclick(100, 200)
Double-click the mouse at specific coordinates relative to viewport

await page.mouse.down()
Press the mouse button down

await page.mouse.down(button='right')
Press the mouse button down with options

await page.mouse.up()
Release the mouse button

await page.mouse.up(button='right')
Release the mouse button with options

await page.mouse.wheel(0, 100)
Scroll the mouse wheel by deltaX and deltaY

Form Input Element Interactions
await page.locator('#input').fill('Hello World')
Fill a text input

await page.locator('#input').press('Enter')
Use press to type text input

await page.locator('#input').press('Control+A')
Use press to send a key chord (e.g. Control+A to select all text)

await page.locator('#input').pressSequentially('Hello', delay=100)
Use pressSequentially to type text input with a delay between each key

await page.locator('#input').clear()
Clear a text input

await page.locator('#checkbox').check()
Check a checkbox

await page.locator('#checkbox').uncheck()
Uncheck a checkbox

await page.locator('.select-color').select_option('Red')
Select an option in a dropdown by label or value

await page.locator('.select-color').select_option(['Red', 'Green'])
Select multiple options in a multi-select dropdown

Keyboard
await page.keyboard.press('Enter')
Press a key

await page.keyboard.press('Control+A')
Press a key chord (e.g. Control+A to select all text)

await page.keyboard.type('Hello World')
Type text with delay between each key

await page.keyboard.type('Hello World', delay=100)
Type text with delay between each key

await page.keyboard.down('Shift')
Hold a key down (without releasing it)

await page.keyboard.up('Shift')
Release a key that is being held down

Element Interactions
await page.locator('#input').focus()
Focus an element

await page.locator('#input').blur()
Remove focus from an element

await page.locator('#element').scroll_into_view_if_needed()
Scroll an element into view if it is not already visible

await page.locator('#element').select_text()
Focuses on an element and selects all its text content

File Upload and Download
el = page.locator('input[type="file"]')
await el.set_input_files('photos/mountain.png')
Upload a single file to a file input element

el = page.locator('input[type="file"]')
await el.set_input_files([
    'photos/mountain.png', 'photos/river.png'
  ])
Upload multiple files to a file input element

import io
el = page.locator('input[type="file"]')
await el.set_input_files([
    {
      'name': 'file1.txt',
      'mime_type': 'text/plain',
      'buffer': b"Hello World"
    }
  ])
Upload multiple files from memory to a file input element

el = page.locator('input[type="file"]')
await el.set_input_files([])
Clear a file input element

# set up a download listener before clicking
async with page.expect_download() as download_info:
  # trigger download
  await page.locator('#download-link').click()

# wait for the download to complete and save it
download = await download_info.value
await download.save_as('report.pdf')
Download a file and save it to disk

Evaluate javascript
sum = await page.evaluate('1 + 2')
Evaluate JavaScript in the page context as a string

await page.evaluate("() => alert('Hello World')")
Evaluate JavaScript in the page context as a function

sum = await page.evaluate("""([a, b]) => {
  return a + b;
}""", [1, 2])
Evaluate JavaScript in the page context with arguments

Alert / Prompt / Confirmation Dialogs
page.on('dialog', lambda dialog: dialog.accept())
Listen for an alert dialog and accept it

page.on('dialog', lambda dialog: dialog.accept('Hello World'))
Listen for a prompt dialog and enter text before accepting it

page.on('dialog', lambda dialog: dialog.dismiss())
Listen for a confirmation dialog and dismiss it

page.on('dialog', lambda dialog: (
  if dialog.message() == 'Are you sure?':
    dialog.accept()
  else:
    dialog.dismiss()
))
Listen for an alert dialog and get its message

Cookies
cookies = await context.cookies()
Get all cookies for the current context

await context.add_cookies([{
  name: 'session-id', 
  value: 'abc123', 
  domain: 'example.com', 
  path: '/', 
  expires: 24 * 60 * 60, // 1 day from now
  httpOnly: true, 
  secure: true, 
  sameSite: 'Lax'
}]);
Add cookies to the current context

await context.clear_cookies()
Clear all cookies in the current context

await context.clear_cookies(name='session-id')
Clear a cookie with a specific name

await context.clear_cookies(domain='example.com')
Clear cookies for a specific domain

Viewport / Window Size
# returns { 'width': int, 'height': int }
viewport_size = page.viewport_size
Get the current viewport size

await page.set_viewport_size({ 'width': 1280, 'height': 720 })
Set the viewport size

Screenshots
element = page.locator('#element')
await element.screenshot(path='element.png')
Take a screenshot of a specific element

await page.screenshot(path='viewport.png') 
Take a screenshot of the current viewport

await page.screenshot(path='fullpage.png', full_page=True)
Take a screenshot of the entire page

