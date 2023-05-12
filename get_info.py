#!/usr/bin/env python3
# coding: utf-8
import grequests
from bs4 import BeautifulSoup
from config import headers, proxies
import re
from pathlib import Path
import fire
import json
from get_playwright import operate_jable_playwright, jable_favourite_playwright
from config import sort_list


def index_of(input_list, value):
    try:
        return input_list.index(value)
    except ValueError:
        return -1


def rm_tree(path):
    path = Path(path)
    for child in path.glob("*"):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    path.rmdir()


def operate_jable(r):
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        title = soup.find(class_="info-header").find("h4").text
        count = soup.find(class_="count").text
        view = soup.find_all(class_="mr-3")[1].text.replace(" ", "")
        models = soup.find(class_="models").find_all(class_="model")
        tags = soup.find(class_="tags").find_all("a")
        script_list = soup.find_all("script")
        hsl = ""
        for i in script_list:
            for i in i.contents:
                m = re.search(r"var hlsUrl = '(.*)';", str(i))
                if m:
                    hsl = m[1]
        obj = {
            "title": title,
            "av_id": r.url.split("/")[4],
            "url": r.url,
            "hsl": hsl,
            "count": count,
            "view": view,
            "models": [
                {
                    "href": i["href"],
                    "title": i.find("img")["title"]
                    if i.find("img")
                    else i.find("span")["title"],
                }
                for i in models
            ],
            "tags": [{"tag": i.text, "href": i["href"]} for i in tags],
        }
        return obj
    raise Exception(f"请求失败 {r.status_code} {r.url}")


async def get_jable_one(url, get_mode="playwright"):
    if get_mode == "playwright":
        return await operate_jable_playwright(url, headless=True)
    else:
        tasks = (grequests.get(u, proxies=proxies, headers=headers) for u in [url])
        for r in grequests.imap(tasks, size=6):
            if r.status_code == 200:
                data = operate_jable(r)
                return data
            else:
                print(f"请求失败 {r.status_code}")


def load_json_data(path):
    jsonData = None
    if path.is_file():
        with open(path, "r", encoding="utf-8") as file:
            jsonData = json.load(file)
    return jsonData


def get_info_path(i):
    return i / f"{i.name} info.json"


async def loop_download_info(
    dirPath=r"E:\jable download",
    mode="jable",
    refresh=False,
    playlist=True,
    message=False,
    playlsit_message=False,
    get_mode="playwright",
):
    allUrls = []
    urls = []
    for i in Path(dirPath).glob("*"):
        if i.is_dir():
            if mode == "jable":
                info_file = get_info_path(i)
                jsonData = load_json_data(info_file)
                allUrls.append(f"https://jable.tv/videos/{i.name}/")
                if not refresh and jsonData and mode in jsonData:
                    if message:
                        print(f"检测到存在,已跳过 {info_file}")
                    continue
                urls.append(f"https://jable.tv/videos/{i.name}/")

    def write_json(data):
        for i in Path(dirPath).glob(data["av_id"]):
            info_file = get_info_path(i)
            with open(info_file, "w", encoding="utf-8") as file:
                json.dump({"jable": data}, file, ensure_ascii=False, indent=4)
            if message:
                print("success:", info_file)
            break

    if len(urls) == 0:
        print("tag,未检测到需要下载,标签分类跳过")
    else:
        print("tag,待下载", len(urls), "已跳过", len(allUrls))
    if get_mode == "playwright":
        for i in urls:
            data = await operate_jable_playwright(i)
            write_json(data)
    else:
        tasks = (grequests.get(u, proxies=proxies, headers=headers) for u in urls)
        for resp in grequests.imap(tasks, size=6):
            data = operate_jable(resp)
            write_json(data)

    # if not message:
    #     print("update info_file...")
    if playlist == True:
        await create_playlist(message=playlsit_message, update=(len(urls) > 0))
        # if not playlsit_message:
        #     print("update playlist...")


def jable_favourite(
    url,
    urlApi,
):
    pageCount = None
    tasks = (grequests.get(u, proxies=proxies, headers=headers) for u in [url] * 3)
    for resp in grequests.imap(tasks):
        soup = BeautifulSoup(resp.text, "html.parser")
        item = soup.select_one(
            "#list_videos_favourite_videos > section > ul > li:nth-last-child(1) > a"
        )
        pageCount = int(item["data-parameters"].split(";")[-1].split(":")[-1])
        break
    if pageCount != None:
        urls = [urlApi.format(i + 1) for i in range(0, pageCount)]
        tasks = (grequests.get(u, proxies=proxies, headers=headers) for u in urls)
        respArr = grequests.map(tasks, size=6)
        data = []
        for i in respArr:
            soup = BeautifulSoup(i.text, "html.parser").select(
                "#list_videos_favourite_videos  div.detail"
            )
            arr = [
                {
                    "title": i.find("a").text,
                    "url": i.find("a").attrs["href"],
                    "av_id": i.find("a").attrs["href"].split("/")[-2],
                    "view": i.find("p", class_="sub-title")
                    .text.replace(" ", "")
                    .strip()
                    .split("\n")[0],
                    "count": i.find("p", class_="sub-title")
                    .text.replace(" ", "")
                    .strip()
                    .split("\n")[1],
                }
                for i in soup
            ]
            assert len(arr) > 0, f"检测到当前页视频数量不足,请检查 {url}"
            for i in arr:
                data.append(i)
    return data


def find_av_id(dirPath, av_id):
    for i in Path(dirPath).rglob(f"*{av_id}.mp4"):
        return True
    return False


def filter_data(av_id_arr, dirPath):
    newData = []
    for av_id in av_id_arr:
        if not find_av_id(dirPath, av_id):
            newData.append(av_id)
    return newData


def check_m3u8_file(dirPath, playlistPath):
    # 检测m3u8文件是否存在
    fileArr = []
    for i in Path(playlistPath).rglob("*.m3u8"):
        with open(i, "r", encoding="utf8") as f:
            data = f.readlines()
            for i in data:
                av_id = i.strip().split("\\")[-2]
                if av_id not in fileArr:
                    fileArr.append(av_id)
    empty_file_arr = filter_data(fileArr, dirPath)  # 只是提示一下

    # 清理m3u8列表里的空文件
    for path in Path(playlistPath).rglob("*.m3u8"):
        new_arr = []
        with open(path, "r", encoding="utf8") as f:
            data = f.readlines()
            for i in data:
                av_id = i.strip().split("\\")[-2]
                if not av_id in empty_file_arr:
                    new_arr.append(i)

        with open(path, "w", encoding="utf8") as f:
            f.writelines(new_arr)

    return empty_file_arr


async def create_playlist_favourite(
    dirPath,
    playlistPath,
    mode,
    message,
    url="https://jable.tv/members/297827/",
    urlApi="https://jable.tv/members/297827/?mode=async&function=get_block&block_id=list_videos_favourite_videos&fav_type=0&playlist_id=0&sort_by=&from_fav_videos={}",
    get_mode="playwright",
):
    pathJson = rf"{playlistPath}\favourite.json"
    pathText = rf"{playlistPath}\favourite.m3u8"

    localCount = None
    if Path(pathJson).is_file():
        with open(pathText, "r", encoding="utf-8") as file:
            d = file.readlines()
            localCount = len(d)

    if get_mode == "playwright":
        data = await jable_favourite_playwright(url, localCount=localCount)
        if data == None:
            return
        print("favourite页面,成功获取,数量为:", len(data))
    else:
        data = jable_favourite(
            url=url,
            urlApi=urlApi,
        )
    print("downloading favourite")

    with open(pathJson, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    with open(pathText, "w", encoding="utf-8") as file:
        for i in data:
            file.write(f'..\jable download\{i["av_id"]}\{i["av_id"]}.mp4\n')


def create_playlist_tag(
    dirPath,
    playlistPath,
    mode,
    message,
    update,
):
    data = []
    for i in Path(dirPath).glob("*"):
        if i.is_dir():
            info_file = get_info_path(i)
            json_data = load_json_data(info_file)
            data.append(json_data)

    if mode == "jable":
        data.sort(key=lambda x: int(x["jable"]["count"]), reverse=True)

        obj = {}
        for i in data:
            i = i["jable"]
            if "models" not in obj:
                obj["models"] = {}
            for model in i["models"]:
                m = model["title"]
                if m not in obj["models"]:
                    obj["models"][m] = []
                obj["models"][m].append(i["av_id"])
            if "tags" not in obj:
                obj["tags"] = {}
            for tag in i["tags"]:
                t = tag["tag"]
                if t not in obj["tags"]:
                    obj["tags"][t] = []
                obj["tags"][t].append(i["av_id"])

        for name in ["models", "tags", "count"]:
            if name == "count":
                playlist_file = Path(playlistPath) / ("count" + ".m3u8")
                with open(playlist_file, "w", encoding="utf8") as f:
                    f.writelines(
                        [
                            f"..\{Path(dirPath).name}\{i['jable']['av_id']}\{i['jable']['av_id']}.mp4\n"
                            for i in data
                        ]
                    )
                continue
            for k, v in obj[name].items():
                k = k.replace("/", "_")
                playlist_file = Path(playlistPath) / name / (k + ".m3u8")
                playlist_file.parent.mkdir(parents=True, exist_ok=True)
                with open(playlist_file, "w", encoding="utf8") as f:
                    f.writelines(
                        [f"..\..\{Path(dirPath).name}\{i}\{i}.mp4\n" for i in v]
                    )
                    if message:
                        print(f"success create file: {playlist_file}")

        # sort models
        playlist_dir = Path(playlistPath) / "models"
        playlist_dir_sort = Path(playlistPath) / "models_sort"
        if playlist_dir_sort.is_dir():
            rm_tree(playlist_dir_sort)
        playlist_dir_sort.mkdir(exist_ok=True)

        d = list(Path(playlist_dir).glob("*"))
        new_list = []
        for i in d:
            idx = index_of(sort_list, i.stem)
            if idx == -1:
                new_list.append(i)
            else:
                sort_list[idx] = i
        new_list = [*sort_list, *new_list]

        number_fill = lambda x, y: str(x).zfill(len(str(len(y) - 1)))  # 数字补零
        new_list2 = [
            playlist_dir_sort / f"{number_fill(k,new_list)}_{v.name}"
            for k, v in enumerate(new_list)
        ]
        for in_file, out_file in zip(new_list, new_list2):
            out_file.write_bytes(in_file.read_bytes())


async def create_playlist(
    dirPath=r"E:\jable download",
    playlistPath=r"E:\jable playlist",
    mode="jable",
    message=True,
    update=True,
):
    if update:
        create_playlist_tag(
            dirPath=dirPath,
            playlistPath=playlistPath,
            mode=mode,
            message=message,
            update=update,
        )

    empty_file_arr = check_m3u8_file(dirPath, playlistPath)

    await create_playlist_favourite(
        dirPath=dirPath,
        playlistPath=playlistPath,
        mode=mode,
        message=message,
    )

    empty_file_arr = [*empty_file_arr, *check_m3u8_file(dirPath, playlistPath)]

    for i in empty_file_arr:
        print(f"没有检测到文件, https://jable.tv/videos/{i}/")


if __name__ == "__main__":
    # url = "https://jable.tv/videos/sdde-686/"
    # data = operate_jable(url)
    # print(data)
    fire.Fire({"ld": loop_download_info, "gb": get_jable_one, "cp": create_playlist})
