from botasaurus.request import request, Request
from botasaurus.soupify import soupify
from botasaurus.browser import browser, Driver
from chrome_extension_python import Extension
import re

headless = True


def operate_jable_playwright(url, mode="browser_"):
    if mode == "browser":
        return run_browser(url)
    else:
        return run_request(url)


def jable_favourite_playwright(url):
    pass


def callback(url, soup, drive=None, response=None):
    print(url)
    title = soup.find("h4").get_text()
    av_id = url.split("?")[0].split("/")[4]
    count = soup.select(".count")[0].text
    view = soup.select("span.mr-3")[1].text.replace(" ", "")

    models = []
    _models = soup.select(".models .model")
    for i in _models:
        try:
            title = i.select("span")[0]["data-original-title"]
        except KeyError:
            title = i.select("span")[0]["title"]
        except IndexError:
            title = i.select("img")[0]["title"]
        models.append({"title": title, "href": i["href"]})

    tags = []
    _tags = soup.select(".tags a")
    for i in _tags:
        tags.append({"tag": i.text, "href": i["href"]})

    if drive:
        hsl = drive.run_js("return hlsUrl")
    else:
        script = soup.select("#site-content")[0].find_all("script")[1].contents[0]
        hsl = re.findall("hlsUrl = '(.*)';", script)[0]

    return {
        "title": title,
        "av_id": av_id,
        "url": url,
        "hsl": hsl,
        "count": count,
        "view": view,
        "models": models,
        "tags": tags,
    }


@request(output=None)
def run_request(request: Request, url):
    response = request.get(url)
    soup = soupify(response)
    return callback(url, soup)


@browser(
    extensions=[
        Extension(
            # "https://chromewebstore.google.com/detail/adblock-%E2%80%94-best-ad-blocker/gighmmpiobklfepjocnamgkkbiglidom"
            "https://chromewebstore.google.com/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm"
        )
    ],
    output=None,
    headless=True,
)
def run_browser(driver: Driver, url):
    driver.get(url)
    soup = soupify(driver)
    return callback(url, soup, drive=driver)


if __name__ == "__main__":
    url = "https://jable.tv/videos/cawd-240/"
    data = operate_jable_playwright(url, mode="browser_")
    print(data)
