from bs4 import BeautifulSoup
from waybackpy import WaybackMachineSaveAPI
from rich.prompt import Prompt
from rich.console import Console
import urllib.request
import threading


lastThreadURL = None


def get_boards(console, boards):
    console.print("id \t board:")
    for i, t in enumerate(boards):
        console.print(i + 1, "\t", t[1])

        if i % 10 == 9:
            cont = input("Next ten: y/n ")
            if cont == "n" or cont == "N":
                console.clear()
                return
    console.clear()


def board(console, boards):
    boardID = int(Prompt.ask("board id: "))
    # Browsing Board
    while boardID:

        b = boards[boardID - 1][0]
        cat = 'https:' + b[0:len(b) - 3] + "php?mode=cat"

        url = urllib.request.urlopen(cat)
        soup = BeautifulSoup(url, 'html.parser')
        threads = []
        threadPreviews = []
        console.print("Thread No \t replies")
        for i, td in enumerate(soup.find_all('td')):
            if td is not None:
                preview = str(i + 1) + ') ' + td.find('small').text + '\t replies: ' + td.find('font').text
                console.print(preview)
                threads.append(td.find('a').get('href'))
                threadPreviews.append(preview)

        def printThreads(threadPreview):
            for thread in threadPreview:
                console.print(thread)

        # Browsing Thread
        threadID = int(Prompt.ask("(zero to break) thread no "))
        console.clear()
        while threadID:

            cat = 'https:' + b[0:len(b) - 10] + threads[threadID - 1]
            url = urllib.request.urlopen(cat)
            global lastThreadURL
            lastThreadURL = cat
            soup = BeautifulSoup(url, 'html.parser')
            breakThread = False

            # Print OP's POST
            console.print(soup.find('span', {"class": "csb"}).text)
            console.print(soup.find('span', {"class": "cnw"}).text)
            console.print(soup.find('span', {"class": "cno"}).text)
            console.print(soup.find('blockquote').text)

            # Print Replies
            for i, table in enumerate(soup.find_all('table')):
                console.print("\n")

                if table.find('blockquote') is not None:
                    for tag in table:
                        console.print(tag.text)
                    if i % 10 == 9:
                        cont = Prompt.ask("Next ten: y/n ")
                        if cont == "n" or cont == "N":
                            breakThread = True
                            console.clear()

                    if breakThread:
                        break

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
