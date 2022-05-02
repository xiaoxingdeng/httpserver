import socket
import os
import sys
from time import strftime, gmtime
from datetime import datetime
from threading import Thread

MAX_SIZE = 5000000
SERVER_HOST = 'localhost'
BUFSIZE = 1024
text404 = "The file doesn't exist at the server"
text403 = "Can't access secret file"
mediatype = {"txt": "text/plain",
             "css": "text/css",
             "htm": "text/html",
             "html": "text/html",
             "gif": "image/gif",
             "jpg": "image/jpeg",
             "jpeg": "image/jpeg",
             "png": "image/png",
             "mp4": "video/mp4",
             "webm": "video/webm",
             "ogg": "video/webm",
             "js": "application/javascript",
             }


def openserver(Port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (SERVER_HOST, Port)
    s.bind(server_address)
    s.listen(100)
    while True:
        conn, addr = s.accept()
        server_thread = Thread(target=newconn, args=(conn,))
        server_thread.start()


def newconn(conn):
    liveness = True
    while liveness:
        try:
            data = conn.recv(1024).decode()
            if len(data) == 0:
                liveness = False
            else:
                response = formResponse(data)
                conn.send(response)
        except Exception as e:
            conn.send(Reponse404(False))
            print(e)
            liveness = False
    conn.close()


def formResponse(requestdata):
    fileposition = getfilename(requestdata)
    if not searchfile(fileposition):
        return Reponse404(True)
    if checkSecret(fileposition):
        return Reponse403(True)

    f = open(fileposition, 'rb')
    data = f.read()
    f.close()
    filetype = fileposition.split(".")[1]
    contentname = "application/octet-stream"
    if filetype in mediatype:
        contentname = mediatype.get(filetype)
    if len(data) <= MAX_SIZE:
        return Response200(fileposition, data, contentname, True)
    else:
        start = checkchunkstart(requestdata)
        return Response206(start, fileposition, data, contentname, True)

def checkchunkstart(requestdata):
    splitedrequest = requestdata.splitlines()
    start = 0
    for line in splitedrequest:
        linelist=line.split(": ")
        if linelist[0] == "Range":
            range = linelist[1].split("=")
            ranges = range[1].split("-")
            start = int(ranges[0])
            print(start)
    return start

def getfilename(requestdata):
    splitedrequest = requestdata.splitlines()
    fileposition = "content" + splitedrequest[0].split(" ")[1]
    return fileposition


def searchfile(fileposition):
    isExist = os.path.exists(fileposition)
    return isExist


def checkSecret(fileposition):
    if "confidential" in fileposition:
        return True
    return False


def Reponse403(liveness):
    statusline = "HTTP/1.1 403 Forbidden\r\n"
    AcceptRanges = "Accept-Ranges: bytes\r\n"
    if liveness == True:
        Connection = "Connection: Keep-Alive\r\n"
    else:
        Connection = "Connection: close\r\n"
    ContentLength = "Content-Length: " + str(len(text403)) + "\r\n"
    ContentRange = "Content-Range: bytes " + contentrange(0, len(text403) - 1, len(text403)) + "\r\n"
    ContentType = "Content-Type: " + "text/html\r\n"
    Date = "Date: " + httpdate() + "\r\n"
    header = statusline + AcceptRanges + Connection + ContentLength + ContentRange + ContentType + Date + "\r\n"
    response = header.encode() + text403.encode()
    return response


def Reponse404(liveness):
    statusline = "HTTP/1.1 404 Not Found\r\n"
    AcceptRanges = "Accept-Ranges: bytes\r\n"
    if liveness == True:
        Connection = "Connection: Keep-Alive\r\n"
    else:
        Connection = "Connection: close\r\n"
    ContentLength = "Content-Length: " + str(len(text404)) + "\r\n"
    ContentRange = "Content-Range: bytes " + contentrange(0, len(text404) - 1, len(text404)) + "\r\n"
    ContentType = "Content-Type: " + "text/html\r\n"
    Date = "Date: " + httpdate() + "\r\n"
    header = statusline + AcceptRanges + Connection + ContentLength + ContentRange + ContentType + Date + "\r\n"
    response = header.encode() + text404.encode()
    return response


def Response200(pathname, data, contentname ,liveness):
    statusline = "HTTP/1.1 200 OK\r\n"
    AcceptRanges = "Accept-Ranges: bytes\r\n"
    if liveness == True:
        Connection = "Connection: Keep-Alive\r\n"
    else:
        Connection = "Connection: close\r\n"
    ContentLength = "Content-Length: " + str(len(data)) + "\r\n"
    ContentRange = "Content-Range: bytes " + contentrange(0, len(data) - 1, len(data)) + "\r\n"
    ContentType = "Content-Type: " + contentname + "\r\n"
    Date = "Date: " + httpdate() + "\r\n"
    LastModified = "Last-Modified: " + modefieddate(pathname) + "\r\n"
    header = statusline + AcceptRanges + Connection + ContentLength + ContentRange + ContentType + Date + LastModified + "\r\n"
    response = header.encode() + data

    return response

def Response206(start, pathname, data, contentname ,liveness):
    statusline = "HTTP/1.1 206 Partial Content\r\n"
    AcceptRanges = "Accept-Ranges: bytes\r\n"
    if liveness == True:
        Connection = "Connection: Keep-Alive\r\n"
    else:
        Connection = "Connection: close\r\n"
    end = min(start+MAX_SIZE, len(data))
    senddata = data[start:end]
    ContentLength = "Content-Length: " + str(len(senddata)) + "\r\n"
    ContentRange = "Content-Range: bytes " + contentrange(start, end - 1, len(data)) + "\r\n"
    ContentType = "Content-Type: " + contentname + "\r\n"
    Date = "Date: " + httpdate() + "\r\n"
    LastModified = "Last-Modified: " + modefieddate(pathname) + "\r\n"
    header = statusline + AcceptRanges + Connection + ContentLength + ContentRange + ContentType + Date + LastModified + "\r\n"
    response = header.encode() + senddata
    print(header)
    return response


def httpdate():
    return strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())


def contentrange(start, end, length):
    return "{}-{}/{}".format(str(start), str(end), str(length))


def modefieddate(pathname):
    t = os.path.getmtime(pathname)
    return datetime.utcfromtimestamp(t).strftime("%a, %d %b %Y")


if __name__ == '__main__':
    Port = sys.argv[1]
    openserver(int(Port))
