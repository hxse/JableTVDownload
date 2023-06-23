import asyncio
from playwright.async_api import async_playwright

timeout = 90 * 1000


async def click_button(el, n):
    for i in el:
        text = await i.text_content()
        try:
            pageNumber = int(text.strip())
            if pageNumber == n:
                await i.click()
                return True
        except ValueError as e:
            pass


async def callback(page):
    el = await page.query_selector_all("#list_videos_favourite_videos  div.detail")
    data = []
    for i in el:
        titleEl = await i.query_selector(".title a")
        subTitleEl = await i.query_selector(".sub-title")

        title = await titleEl.text_content()
        url = await titleEl.get_attribute("href")
        av_id = url.split("?")[0].split("/")[-2]
        text = await subTitleEl.text_content()
        view = text.strip().split("\n")[0].replace(" ", "")
        count = text.strip().split("\n")[1].replace(" ", "")
        data.append(
            {"title": title, "url": url, "av_id": av_id, view: view, count: count}
        )
    return data


async def recursion_find_button(page, n=1, sleep=3500, callback=callback, data=[]):
    data = [*data, *(await callback(page))]
    el = await page.query_selector_all(".page-item")
    flag = await click_button(el, n + 1)
    if not flag:
        return data
    await page.wait_for_timeout(sleep)
    return await recursion_find_button(page, n + 1, data=data)


async def jable_favourite_playwright(
    url="https://jable.tv/members/297827/", localCount=None, headless=True
):
    async with async_playwright() as p:
        for browser_type in [p.firefox]:  # p.chromium, 用chromium会被检测到, firefox不会
            browser = await browser_type.launch(headless=headless)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout)

            countEl = await page.wait_for_selector(".count", state="attached")
            count = int(await countEl.text_content())

            if localCount != None:
                if int(localCount) == int(count):
                    print(f"favourite,检测到数目一致,已跳过,{count}")
                    return

            data = await recursion_find_button(page)
            assert count == len(data), f"数目不对,请检查,预期数目:{count}, 实际数目:{len(data)}"
            return data


async def operate_jable_playwright(url, headless=True):
    async with async_playwright() as p:
        for browser_type in [p.firefox]:  # p.chromium, 用chromium会被检测到, firefox不会
            browser = await browser_type.launch(
                headless=headless,
                # executablePath="C:\\Users\\hxse\\AppData\\Local\\ms-playwright\\firefox-1335\\firefox\\firefox.exe",
            )
            page = await browser.new_page()
            await page.goto(url, timeout=timeout)
            el = await page.query_selector("div.info-header")
            titleEl = await el.query_selector(".header-left h4")
            countEl = await page.query_selector(".count")
            viewEl = await el.query_selector_all("span.mr-3")
            modelsEl = await el.query_selector_all(".models .model")
            tagsEl = await page.query_selector_all(".tags a")

            title = await titleEl.text_content()
            count = await countEl.text_content()
            view = await viewEl[1].text_content()
            title, count, view = (
                title.strip(),
                count.strip(),
                view.replace(" ", "").strip(),
            )
            models = []
            for i in modelsEl:
                href = await i.get_attribute("href")
                mEl = await i.query_selector("img")
                if mEl == None:  # 模特有两种格式, 一种是img格式, 一种是span格式
                    mEl = await i.query_selector("span")
                name = await mEl.get_attribute("data-original-title")
                models.append({"href": href, "title": name})

            tags = []
            for i in tagsEl:
                tag = await i.text_content()
                href = await i.get_attribute("href")
                tags.append({"tag": tag, "href": href})

            hsl = await page.evaluate("hlsUrl")

            obj = {
                "title": title,
                "av_id": url.split("?")[0].split("/")[4],
                "url": url,
                "hsl": hsl,
                "count": count,
                "view": view,
                "models": models,
                "tags": tags,
            }
            # await page.screenshot(path=f"example-{browser_type.name}.png")
            # await browser.close()
            return obj


if __name__ == "__main__":
    url = "https://jable.tv/videos/ipx-252-c/"
    obj = asyncio.run(operate_jable_playwright(url, headless=True))
    print(obj)
