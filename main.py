# author: hcjohn463
#!/usr/bin/env python
# coding: utf-8
from get_m3u8 import get_m3u8
import os
from merge import mergeMp4
from delete import deleteM3u8, deleteMp4, deleteChildTs, deleteParentTs
from crawler import prepareCrawl
import subprocess
import fire


def covert(folderPath):
    path = folderPath + os.path.sep + folderPath.split(os.path.sep)[-1]
    command = f'ffmpeg -i "{path+".ts"}" -acodec copy -vcodec copy "{path+".mp4"}"'
    subprocess.call(command, shell=True)


def main(url, m3u8url, outPath="./"):
    urlSplit = url.split("/")
    dirName = urlSplit[-2] if url[-1] == "/" else urlSplit[-1]
    folderPath = os.path.join(outPath, dirName)
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    video_name = folderPath.split(os.path.sep)[-1]
    tsPath = os.path.join(folderPath, video_name + ".ts")
    mp4Path = os.path.join(folderPath, video_name + ".mp4")

    if os.path.exists(mp4Path):
        print("mp4文件已存在,已跳过")
    elif os.path.exists(tsPath):
        print("ts父文件已存在,进行合并")
        # 转换ts to mp4
        covert(folderPath)
        # 删除父ts
        deleteParentTs(folderPath)
    else:
        # 获取m3u8
        ci, tsList = get_m3u8(url, folderPath, dirName, m3u8url)
        # 開始爬蟲並下載ts片段至資料夾
        prepareCrawl(ci, folderPath, tsList)
        # 合成父ts
        mergeMp4(folderPath, tsList)
        # 刪除子ts
        deleteChildTs(folderPath)
        # 转换ts to mp4
        covert(folderPath)
        # 删除父ts
        deleteParentTs(folderPath)


if __name__ == "__main__":
    fire.Fire(main)
