from bs4 import BeautifulSoup
from waybackpy import WaybackMachineSaveAPI
import urllib.request
from rich.prompt import Prompt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.console import Group
import urllib.request
import math
import io
import threading
import numpy as np
import climage

lastThreadURL = None
header = Panel("ふたばちゃんは、生まれたばかりの掲示板です。")
console = Console()


def getBoardsTable(boards):
    l = len(boards)
    third = math.ceil(l/3)
    table = Table()
    table.add_column("1~" + str(third), no_wrap=True, min_width=30)
    table.add_column(str(third) + "~" + str(third * 2), no_wrap=True, min_width=30)
    table.add_column(str(2 * third) + "~" + str(l), no_wrap=True, min_width=30)

    for i in range(1, third+1):
        if i+third*2 <= l:
            table.add_row(str(i) + "\t" + boards[i-1][1], str(i+third) + "\t" + boards[i-1+third][1],
                          str(i+third*2) + "\t" + boards[i-1+third*2][1])
        elif i+third < l:
            table.add_row(str(i) + "\t" + boards[i-1][1], str(i+third) + "\t" + boards[i-1+third][1], "")
        else:
            table.add_row(str(i) + "\t" + boards[i-1][1], "", "")

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
        if threadID == 0:
            return

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
        console.clear()

        consoleTable = Table(show_lines=True)
        consoleTable.add_column("Thread No", no_wrap=False, min_width=40)
        consoleTable.add_column("Text", no_wrap=False, min_width=60)
        consoleTable.add_column("Img", no_wrap=True, min_width=10)

        viewThread(threads, threadID, b, consoleTable)
        threadID = int(renderDisp(threadTable, "(zero to break) thread no "))
    console.clear()


def viewThread(threads, threadID, b, consoleTable):
    global console
    cat = 'https:' + b[0:len(b) - 10] + threads[threadID - 1]
    url = urllib.request.urlopen(cat)
    global lastThreadURL
    lastThreadURL = cat
    soup = BeautifulSoup(url, 'html.parser')
    breakThread = False

    # Print OP's POST
    opID = soup.find('span', {"class": "csb"}).text + "\n" + soup.find('span', {
        "class": "cnw"}).text + "\n" + soup.find('span', {"class": "cno"}).text
    opText = soup.find('blockquote').text
    consoleTable.add_row(opID, opText)

    # Print Replies
    for i, table in enumerate(soup.find_all('table')):
        blockquote = table.find('blockquote')
        if blockquote is not None:
            paragraph = ""
            threadInfo = table.find('span', {"class": "csb"}).text + " " + table.find('span', {
                "class": "cnm"}).text + " " + table.find('span', {"class": "cnw"}).text + " " + table.find('span', {
                "class": "cno"}).text
            for j, tag in enumerate(blockquote):
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
            consoleTable.add_row(threadInfo, paragraph, imageURL)
            if i % 10 == 9:
                cont = renderDisp(consoleTable, "Next ten: y/n")
                if cont == "n" or cont == "N":
                    breakThread = True
            if breakThread:
                break

    if renderDisp(consoleTable, "press a to archive thread") == "a":
        archiveThread = threading.Thread(target=archive)
        archiveThread.start()
    console.clear()


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
