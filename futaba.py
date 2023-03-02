from bs4 import BeautifulSoup
from waybackpy import WaybackMachineSaveAPI
from rich.prompt import Prompt
from rich.console import Console
from rich.table import Table
import urllib.request
import math
import threading

lastThreadURL = None


def get_boards(console, boards):
    l = len(boards)
    third = math.ceil(l / 3)
    table = Table()
    table.add_column("1~" + str(third), no_wrap=True, min_width=30)
    table.add_column(str(third) + "~" + str(third * 2), no_wrap=True, min_width=30)
    table.add_column(str(2 * third) + "~" + str(l), no_wrap=True, min_width=30)

    for i in range(0, third):
        if i + third * 2 < l:
            table.add_row(str(i + 1) + "\t" + boards[i][1], str(i + third) + "\t" + boards[i + third][1],
                          str(i + third * 2) + "\t" + boards[i + third * 2][1])
        elif i + third < l:
            table.add_row(str(i + 1) + "\t" + boards[i][1], str(i + third) + "\t" + boards[i + third][1], "")
        else:
            table.add_row(str(i + 1) + "\t" + boards[i][1], "", "")

    console.print(table)
    # console.clear()


def board(console, boards):
    boardID = int(Prompt.ask("board id: "))
    console.clear()
    # Browsing Board

    table = Table()
    table.add_column("Thread No", no_wrap=True, min_width=5)
    table.add_column("title", no_wrap=True, min_width=15)
    table.add_column("replies", no_wrap=True, min_width=5)
    while boardID:

        b = boards[boardID - 1][0]
        cat = 'https:' + b[0:len(b) - 3] + "php?mode=cat"

        url = urllib.request.urlopen(cat)
        soup = BeautifulSoup(url, 'html.parser')
        threads = []
        threadPreviews = []
        for i, td in enumerate(soup.find_all('td')):
            if td is not None:
                threadTitle = ""
                if td.find('small'):
                    threadTitle = td.find('small').text
                replies = ""
                if td.find('font'):
                    replies = td.find('font').text
                table.add_row(str(i + 1), threadTitle, replies)
                threads.append(td.find('a').get('href'))
        console.print(table)

        def printThreads(threadPreview):
            for thread in threadPreview:
                console.print(thread)

        # Browsing Thread
        threadID = int(Prompt.ask("(zero to break) thread no "))
        console.clear()
        consoleTable = Table(show_lines=True)
        consoleTable.add_column("Thread No", no_wrap=False, min_width=40)
        consoleTable.add_column("Text", no_wrap=False, min_width=60)
        while threadID:
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
                    threadInfo = table.find('span', {"class": "csb"}).text + " " + table.find('span', {"class": "cnm"}).text + " " + table.find('span', {"class": "cnw"}).text + " " + table.find('span', {"class": "cno"}).text
                    for j, tag in enumerate(blockquote):
                        paragraph = paragraph + tag.text
                    consoleTable.add_row(threadInfo, paragraph)
                    if i % 10 == 9:
                        console.clear()
                        console.print(consoleTable)
                        cont = Prompt.ask("Next ten: y/n ")
                        if cont == "n" or cont == "N":
                            breakThread = True
                            console.clear()

                    if breakThread:
                        break

            console.print(consoleTable)
            printThreads(threadPreviews)
            threadID = int(Prompt.ask("(zero to break) thread no "))

        boardID = int(Prompt.ask("board id: "))
        console.clear()


def archive(console):
    global lastThreadURL
    if lastThreadURL is not None:
        console.print("archiving last thread, this may take up to 30 seconds")
        user_agent = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        save_api = WaybackMachineSaveAPI(lastThreadURL, user_agent)
        archivedURL = save_api.save()
        console.print("\n successfully archived " + archivedURL)
        f = open("URLS.txt", "a")
        f.write(archivedURL + "\n")
        f.close()
    else:
        console.print("no threads visited")


def main():
    console = Console()
    # INITIAL SCAN THROUGH BOARDS CREATE A LIST OF TUPLES
    url = urllib.request.urlopen('https://www.2chan.net/index2.html')
    soup = BeautifulSoup(url, 'html.parser')

    boards = []
    for i, td in enumerate(soup.find_all('td')):
        for j, a in enumerate(td.find_all('a')):
            boards.append((a.get('href'), a.text))

    get_boards(console, boards)
    run = True
    while run:

        console.print("l: list boards, b: go to board, a: archive last thread, e: exit")
        command = Prompt.ask("Enter Command: ")
        match command:
            case "list_boards" | "l" | "list" | "list boards":
                get_boards(console, boards)
            case "board" | "b":
                board(console, boards)
            case "archive" | "a":
                a = threading.Thread(target=archive, args=console)
                a.start()
            case "exit" | "e" | "quit" | "q":
                run = False
            case _:
                console.print("invalid command")
                console.clear()


main()
