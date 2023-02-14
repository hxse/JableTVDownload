#!/usr/bin/env python3
# coding: utf-8
import grequests
from bs4 import BeautifulSoup
from config import headers, proxies
import re
from pathlib import Path
import fire
import json


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
    print(f"请求失败 {r.status_code}")
    return r.text


def get_jable_one(url):
    tasks = (grequests.get(u, proxies=proxies, headers=headers) for u in [url])
    for r in grequests.imap(tasks, size=6):
        if r.status_code == 200:
            data = operate_jable(r)
            print(data)
        else:
            print(f"请求失败 {r.status_code}")


def load_json_data(path):
    jsonData = None
    if path.is_file():
        with open(path, "r", encoding="utf-8") as file:
            jsonData = json.load(file)
    return jsonData


def get_info_path(i):
    return i / "info.json"


def loop_download_info(
    dirPath=r"E:\jable download",
    mode="jable",
    refresh=False,
    playlist=True,
    message=True,
    playlsit_message=False,
):
    urls = []
    for i in Path(dirPath).glob("*"):
        if i.is_dir():
            if mode == "jable":
                info_file = get_info_path(i)
                jsonData = load_json_data(info_file)
                if not refresh and jsonData and mode in jsonData:
                    if message:
                        print(f"检测到存在,已跳过 {info_file}")
                    continue
                urls.append(f"https://jable.tv/videos/{i.name}/")
    tasks = (grequests.get(u, proxies=proxies, headers=headers) for u in urls)
    for resp in grequests.imap(tasks, size=6):
        data = operate_jable(resp)
        for i in Path(dirPath).glob(data["av_id"]):
            info_file = get_info_path(i)
            with open(info_file, "w", encoding="utf-8") as file:
                json.dump({"jable": data}, file, ensure_ascii=False, indent=4)
            if message:
                print("success:", info_file)
            break
    if playlist == True:
        create_playlist(message=playlsit_message)
        if not playlsit_message:
            print("update playlist...")


def create_playlist(
    dirPath=r"E:\jable download",
    playlistPath=r"E:\jable playlist",
    mode="jable",
    message=True,
):
    data = []
    for i in Path(dirPath).glob("*"):
        if i.is_dir():
            info_file = get_info_path(i)
            json_data = load_json_data(info_file)
            data.append(json_data)
    obj = {}
    if mode == "jable":
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

    for name in ["models", "tags"]:
        for k, v in obj[name].items():
            k = k.replace("/", "_")
            playlist_file = Path(playlistPath) / name / (k + ".m3u8")
            playlist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(playlist_file, "w", encoding="utf8") as f:
                f.writelines([f"..\..\{Path(dirPath).name}\{i}\{i}.mp4\n" for i in v])
                if message:
                    print(f"success create file: {playlist_file}")


if __name__ == "__main__":
    # url = "https://jable.tv/videos/sdde-686/"
    # data = operate_jable(url)
    # print(data)
    fire.Fire({"ld": loop_download_info, "gb": get_jable_one, "cp": create_playlist})
