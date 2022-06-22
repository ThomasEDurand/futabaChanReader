from bs4 import BeautifulSoup
import urllib.request
import requests
from waybackpy import WaybackMachineSaveAPI


lastThreadURL = None

def get_boards(boards):
    for i, t in enumerate(boards):
        print("id: ", i+1, "board: ",  t[1])

        if(i%10 == 9):
            cont = input("Next ten: y/n ")
            if(cont == "n" or cont == "N"):
                return


def board(boards): 
    
    boardID = int(input("board id: "))
    #Browsing Board    
    while boardID:

        b = boards[boardID-1][0]
        cat = 'https:' + b[0:len(b)-3] + "php?mode=cat"
        
        url = urllib.request.urlopen(cat)
        soup = BeautifulSoup(url, 'html.parser')
        threads = []
        threadPreviews = []
        for i, td in enumerate(soup.find_all('td')):
            if td is not None:
                preview = str(i+1)+') ' + td.find('small').text + ' id ' + td.find('a').get('href') + ' replies: ' + td.find('font').text
                print(preview)
                threads.append(td.find('a').get('href'))
                threadPreviews.append(preview)

        def printThreads(threadPreviews):
            for thread in threadPreviews:
                print(thread)

       
        
        #Browsing Thread
        threadID = int(input("(zero to break) thread no: "))
        while threadID:

            cat = 'https:' + b[0:len(b)-10] + threads[threadID-1]    
            url = urllib.request.urlopen(cat)
            global lastThreadURL
            lastThreadURL = cat
            soup = BeautifulSoup(url, 'html.parser')
            breakThread = False

            #Print OP's POST
            print(soup.find('span', {"class": "csb"}).text)
            print(soup.find('span', {"class": "cnw"}).text)  
            print(soup.find('span', {"class": "cno"}).text)
            print(soup.find('blockquote').text)


            #Print Replies
            for i, table in enumerate(soup.find_all('table')):
                print("\n")
    
                if table.find('blockquote') is not None:
                    for tag in table:
                        print(tag.text)
                    if(i%10 == 9):
                        cont = input("Next ten: y/n ")
                        if(cont == "n" or cont == "N"):
                            breakThread = True

                    if breakThread:
                        break
                    
                
            printThreads(threadPreviews)
            threadID = int(input("(zero to break) thread no: "))


        boardID = int(input("board id: "))




def archive():
    global lastThreadURL
    if lastThreadURL is not None:
        print("arhciving last thread")
        user_agent = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"
        save_api = WaybackMachineSaveAPI(lastThreadURL, user_agent)
        archivedURL = save_api.save()
        print(archivedURL)
        f = open("URLS.txt", "a")
        f.write(archivedURL)
        f.write("\n")
        f.close()
    else:
        print("no thread visited")



def main():
    #INITIAL SCAN THROUGH BOARDS CREATE A LIST OF TUPPLES
    url = urllib.request.urlopen('https://www.2chan.net/index2.html')
    soup = BeautifulSoup(url, 'html.parser')
        

    boards = []
    for i, td in enumerate(soup.find_all('td')):
        for j, a in enumerate(td.find_all('a')):
            boards.append((a.get('href'), a.text))
    


    run = True
    while(run):

        print("l: list boards, b: go to board, a: archive last thread, e: exit")
        print("list_boards")
        print("board: go to board")
        print("archive: archive last thread visited")
        print("exit")
        command = input("Enter Command: ")

        match command:
            case "list_boards":
                get_boards(boards)
            case "board":
                board(boards)
            case "archive":
                archive()
            case "exit":
                run = False
            case _:
                print("invalid command")




main()
