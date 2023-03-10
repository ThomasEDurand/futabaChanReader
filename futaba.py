import math
import threading
import urllib.request
import urllib.request

from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from waybackpy import WaybackMachineSaveAPI

lastThreadURL = None
header = Panel("ふたばちゃんは、生まれたばかりの掲示板です。")
console = Console()
replyTables = list()
stopThread = False


def getBoardsTable(boards):
    length = len(boards)
    third = math.ceil(length / 3)
    table = Table()
    table.add_column("1~" + str(third), no_wrap=True, min_width=30)
    table.add_column(str(third) + "~" + str(third * 2), no_wrap=True, min_width=30)
    table.add_column(str(2 * third) + "~" + str(length), no_wrap=True, min_width=30)

    for i in range(1, third + 1):
        if i + third * 2 <= length:
            table.add_row(str(i) + "\t" + boards[i - 1][1], str(i + third) + "\t" + boards[i - 1 + third][1],
                          str(i + third * 2) + "\t" + boards[i - 1 + third * 2][1])
        elif i + third < length:
            table.add_row(str(i) + "\t" + boards[i - 1][1], str(i + third) + "\t" + boards[i - 1 + third][1], "")
        else:
            table.add_row(str(i) + "\t" + boards[i - 1][1], "", "")

    return table


def getBoards():
    url = urllib.request.urlopen('https://www.2chan.net/index2.html')
    soup = BeautifulSoup(url, 'html.parser')
    boards = []
    for i, td in enumerate(soup.find_all('td')):
        for j, a in enumerate(td.find_all('a')):
            boards.append((a.get('href'), a.text))
    return boards


def board(boardID, boards):
    global console
    console.clear()
    threadID = 1
    # Browsing Board
    while threadID:

        b = boards[boardID - 1][0]
        cat = 'https:' + b[0:len(b) - 3] + "php?mode=cat"

        url = urllib.request.urlopen(cat)
        soup = BeautifulSoup(url, 'html.parser')

        tit = soup.find("span", {"id": "tit"}).text
        threadTable = Table(title=tit)
        threadTable.add_column("Thread No", no_wrap=True, min_width=5)
        threadTable.add_column("title", no_wrap=True, min_width=15)
        threadTable.add_column("replies", no_wrap=True, min_width=5)

        threads = []
        for i, td in enumerate(soup.find_all('td')):
            if td is not None:
                threadTitle = ""
                if td.find('small'):
                    threadTitle = td.find('small').text
                replies = ""
                if td.find('font'):
                    replies = td.find('font').text
                threadTable.add_row(str(i + 1), threadTitle, replies)
                threads.append(td.find('a').get('href'))

        threadID = int(renderDisp(threadTable, "(zero to break) thread no "))
        if 0 < threadID < len(threads):
            console.clear()

            viewThread(threads, threadID, b)
            threadID = int(renderDisp(threadTable, "(zero to break) thread no "))
        else:
            return
    console.clear()


def viewThread(threads, threadID, b):
    global console
    global lastThreadURL
    global replyTables
    global stopThread

    concatURL = 'https:' + b[0:len(b) - 10] + threads[threadID - 1]
    lastThreadURL = concatURL
    url = urllib.request.urlopen(concatURL)

    soup = BeautifulSoup(url, 'html.parser')
    breakThread = False

    # Print OP's POST
    opTable = Table(show_lines=True)
    opTable.add_column("Thread No", no_wrap=False, min_width=40)
    opTable.add_column("Text", no_wrap=False, min_width=60)
    opTable.add_column("Img", no_wrap=True, min_width=10)

    opID = soup.find('span', {"class": "csb"}).text + "\n"
    opID += soup.find('span', {"class": "cnw"}).text + "\n"
    opID += soup.find('span', {"class": "cno"}).text
    opText = soup.find('blockquote').text
    opTable.add_row(opID, opText)
    replyTables.append(opTable)

    fetch = threading.Thread(target=fetchReplies, args=(url,))
    fetch.start()
    k = 0
    while True:
        r = renderDisp(replyTables[k],
                       "j: prev 10, k: next 10, a: archive thread, tables " + str(len(replyTables)) + " threads " + str(
                           threading.active_count()))
        if r == "a":
            archiveThread = threading.Thread(target=archive)
            archiveThread.start()
        elif r == "j" and 0 < k:
            k -= 1
        elif r == "k" and k < len(replyTables) - 1:
            k += 1
        elif r == "q":
            stopThread = True
            fetch.join()
            replyTables = list()
            stopThread = False
            return
        else:
            console.print("invalid char")
    # Print Replies


def fetchReplies(url):
    global replyTables
    global stopThread
    soup = BeautifulSoup(url, 'html.parser')

    s = soup.find_all('table')
    numReplies = len(s)

    k = 1
    replyTables.append(Table(show_lines=True))
    replyTables[k].add_column("Thread No", no_wrap=False, min_width=40)
    replyTables[k].add_column("Text", no_wrap=False, min_width=60)
    replyTables[k].add_column("Img", no_wrap=True, min_width=10)
    for i, table in enumerate(s):
        bq = table.find('blockquote')
        if bq is not None:
            paragraph = ""
            threadInfo = table.find('span', {"class": "csb"}).text + " "
            threadInfo += table.find('span', {"class": "cnm"}).text + " "
            threadInfo += table.find('span', {"class": "cnw"}).text + " "
            threadInfo += table.find('span', {"class": "cno"}).text
            for j, tag in enumerate(bq):
                paragraph = paragraph + tag.text

            image = table.find('img')
            imageURL = ""
            if image is not None:
                imageURL = "https://nov.2chan.net" + image['src']  # thumbnail
                # with urllib.request.urlopen(imageURL) as url:
                #    f = io.BytesIO(url.read())
                # img = climage.convert(f, is_unicode=True)
                # console.print(img)
                # imageURL = "https://nov.2chan.net" + image['src'].replace("thumb", "src")[0:-5] + ".jpg"  # source

            replyTables[k].add_row(threadInfo, paragraph, imageURL)
            if (i-1) % 10 == 0 or i == numReplies - 1:
                if stopThread:
                    return

                replyTables.append(Table(show_lines=True))
                k += 1
                replyTables[k].add_column("Thread No", no_wrap=False, min_width=40)
                replyTables[k].add_column("Text", no_wrap=False, min_width=60)
                replyTables[k].add_column("Img", no_wrap=True, min_width=10)


def archive():
    global lastThreadURL
    global header
    global console
    if lastThreadURL is not None:
        header = Panel("archiving", style="blink")
        user_agent = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        save_api = WaybackMachineSaveAPI(lastThreadURL, user_agent)
        archivedURL = save_api.save()
        header = Panel(" successfully archived " + archivedURL)
        f = open("URLS.txt", "a")
        f.write(archivedURL + "\n")
        f.close()
    else:
        header = Panel("no threads visited")


def renderDisp(table, prompt):
    global console
    global header
    console.clear()
    console.print(header)
    console.print(table)
    if prompt is not None or prompt != "":
        return Prompt.ask(prompt)
    return -1


def main():
    boards = getBoards()  # array of tuples
    boardsTable = getBoardsTable(boards)  # table, object that only needs to be generated once
    while True:
        bID = renderDisp(boardsTable, "Go to board")
        if bID == "0" or bID == "e" or bID == "exit" or bID == "q" or bID == "quit":
            return 0
        board(int(bID), boards)


main()
