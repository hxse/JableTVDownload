import os


def deleteChildTs(folderPath):
    files = os.listdir(folderPath)
    originFile = folderPath.split(os.path.sep)[-1] + ".ts"
    for file in files:
        if file == originFile:
            continue
        if file.endswith(".ts"):
            os.remove(os.path.join(folderPath, file))


def deleteParentTs(folderPath):
    originFile = folderPath.split(os.path.sep)[-1] + ".ts"
    os.remove(os.path.join(folderPath, originFile))


def deleteMp4(folderPath):
    files = os.listdir(folderPath)
    originFile = folderPath.split(os.path.sep)[-1] + ".mp4"
    for file in files:
        if file != originFile:
            os.remove(os.path.join(folderPath, file))


def deleteM3u8(folderPath):
    files = os.listdir(folderPath)
    for file in files:
        if file.endswith(".m3u8"):
            os.remove(os.path.join(folderPath, file))
