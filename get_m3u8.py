import cloudscraper
from config import headers, proxies
import re
import os
import requests
import m3u8
from Crypto.Cipher import AES
from delete import deleteM3u8
from pathlib import Path


def url_retrieve(url: str, outfile: str):
    R = requests.get(url, proxies=proxies, headers=headers)
    if R.status_code != 200:
        raise ConnectionError(
            "could not download {}\nerror code: {}".format(url, R.status_code)
        )
    Path(outfile).write_bytes(R.content)


def get_m3u8(url, folderPath, dirName, m3u8url):
    # 得到 m3u8 網址
    """
    htmlfile = cloudscraper.create_scraper(   browser={
                    'browser': 'firefox',
                    'platform': 'windows',
                    'mobile': False
                } , delay=10).get(url, headers= headers, proxies=proxies)
    result = re.search("https://.+m3u8", htmlfile.text)
    m3u8url = result[0]
    """

    m3u8urlList = m3u8url.split("/")
    m3u8urlList.pop(-1)
    downloadurl = "/".join(m3u8urlList)

    # 儲存 m3u8 file 至資料夾
    m3u8file = os.path.join(folderPath, dirName + ".m3u8")
    url_retrieve(m3u8url, m3u8file)

    # 得到 m3u8 file裡的 URI和 IV
    m3u8obj = m3u8.load(m3u8file)
    m3u8uri = ""
    m3u8iv = ""

    for key in m3u8obj.keys:
        if key:
            m3u8uri = key.uri
            m3u8iv = key.iv

    # 儲存 ts網址 in tsList
    tsList = []
    for seg in m3u8obj.segments:
        tsUrl = downloadurl + "/" + seg.uri
        tsList.append(tsUrl)

    # 有加密
    if m3u8uri:
        m3u8keyurl = downloadurl + "/" + m3u8uri  # 得到 key 的網址

        # 得到 key的內容
        response = requests.get(
            m3u8keyurl, headers=headers, proxies=proxies, timeout=10
        )
        contentKey = response.content

        vt = m3u8iv.replace("0x", "")[:16].encode()  # IV取前16位

        ci = AES.new(contentKey, AES.MODE_CBC, vt)  # 建構解碼器
    else:
        ci = ""

    # 刪除m3u8 file
    deleteM3u8(folderPath)

    return ci, tsList
