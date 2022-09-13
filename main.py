# author: hcjohn463
#!/usr/bin/env python
# coding: utf-8
from inspect import istraceback
from get_m3u8 import get_m3u8
import os
from merge import mergeMp4
from delete import deleteM3u8, deleteMp4, deleteChildTs, deleteParentTs
from crawler import prepareCrawl
import subprocess
import fire
from pathlib import Path
import shutil


def covert(folderPath):
    # path = folderPath + os.path.sep + folderPath.split(os.path.sep)[-1]
    originPath = Path(folderPath) / (Path(folderPath).name + ".ts")
    targetPath = Path(folderPath) / (Path(folderPath).name + ".mp4")
    command = f'ffmpeg -i "{originPath.as_posix()}" -acodec copy -vcodec copy "{targetPath.as_posix()}"'
    print(command)
    subprocess.call(command, shell=True)


def main(url, m3u8url, outPath="./", tempDir=""):
    urlSplit = url.split("/")
    dirName = urlSplit[-2] if url[-1] == "/" else urlSplit[-1]
    folderPath = os.path.join(outPath, dirName)
    isTempDir = True if tempDir else False
    tempDir = os.path.join(tempDir, dirName)
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    if isTempDir and not os.path.exists(tempDir):
        os.makedirs(tempDir)

    tempObj = {
        "path": tempDir,
        "tsPath": os.path.join(tempDir, dirName + ".ts"),
        "mp4Path": os.path.join(tempDir, dirName + ".mp4"),
    }
    targetObj = {
        "path": folderPath,
        "tsPath": os.path.join(folderPath, dirName + ".ts"),
        "mp4Path": os.path.join(folderPath, dirName + ".mp4"),
    }

    if os.path.exists(targetObj["mp4Path"]):
        print("目标文件夹,mp4已存在")
        return
    if os.path.exists(tempObj["mp4Path"]):
        print("临时文件夹,mp4已存在")
        print("开始复制...")
        shutil.copy(tempObj["mp4Path"], targetObj["mp4Path"])
        shutil.rmtree(tempObj["path"], ignore_errors=True)
        print("复制完毕")
        return

    _Obj = tempObj if isTempDir else targetObj

    if not os.path.exists(_Obj["tsPath"]):
        # 获取m3u8
        ci, tsList = get_m3u8(url, _Obj["path"], dirName, m3u8url)
        # 開始爬蟲並下載ts片段至資料夾
        prepareCrawl(ci, _Obj["path"], tsList)
        # 合成父ts
        mergeMp4(_Obj["path"], tsList)
    # 刪除子ts
    deleteChildTs(_Obj["path"])
    # 转换ts to mp4
    covert(_Obj["path"])
    # 删除父ts
    deleteParentTs(_Obj["path"])

    if isTempDir:
        # 把mp4从临时文件夹复制到目标文件夹
        print("开始复制...")
        shutil.copy(tempObj["mp4Path"], targetObj["mp4Path"])
        shutil.rmtree(tempObj["path"], ignore_errors=True)
        print("复制完毕")
        return


if __name__ == "__main__":
    fire.Fire(main)
