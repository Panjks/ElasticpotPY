from bottle import route, run, template, request, error
import requests
import os.path
import configparser
import base64
import datetime
import codecs


#
# read config from eventually existing T-Pot installation (see dtag-dev-sec.github.io)
#
def getConfig():
    if os.path.isfile('/data/ews/conf/ews.cfg'):
        config2 = configparser.ConfigParser()
        config2.read('/data/ews/conf/ews.cfg')
        username = config2.get("EWS", "username")
        token = config2.get("EWS", "token")
        server = config2.get("EWS", "rhost_first")
        nodeid = config2.get("GLASTOPFV3", "nodeid")

        return (username, token, server, nodeid)
    else:
        return (None, None, None, None)

#
# log data for DTAG TPot
#
def logData(attackerIP, attackerRequest, host):

    if os.path.isfile('/data/ews/conf/ews.cfg'):

        curDate = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')

        dumpStr = "{\"timestamp\":\"" + curDate + "\",\"event_type\":\"alert\",\"src_ip\":\""+attackerIP+"\",\"src_port\":44927,\"dest_ip\":\"127.0.0.1\",\"dest_port\":9200,\"honeypot\":{\"name\":\"Elasticpot\",\"nodeid\":\"elasticsearch\"}}\r\n"

        with open("/data/elasticpot/log/elasticpot.log", "a") as myfile:
            myfile.write(dumpStr)


#
# send the data back to the defined server (e.g. DTAG T-Pot environment)
#
def postdata(url, content, ip):

    username, token, server, nodeid = getConfig()

    logData(ip, url, server)

    if (username == None):
        return

    nodeid = "elasticpot-" + nodeid

    txt = open("./templates/ews.txt")
    xml = txt.read()

    out = codecs.encode(url.encode("UTF-8"), 'base64_codec')

    xml = xml.replace("_IP_", ip)
    xml = xml.replace("_USERNAME_", username)
    xml = xml.replace("_TOKEN_", token)

    xml = xml.replace("_URL_", url)
    xml = xml.replace("_RAW_", out.decode("utf-8") )
    xml = xml.replace("_NODEID_", nodeid)

    curDate = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

    xml = xml.replace("_TIME_", curDate)

    headers = {'Content-Type': 'application/xml'}
    requests.post(server, data=xml, headers=headers)


@route('/_plugin/head')
def pluginhead():
    txt = open("./templates/pluginhead.txt")
    indexData = txt.read()
    return indexData

#@route('/<index:path>?pretty', method='PUT')
#def createindex(index):


@route('/', method='GET')
def index():

    txt = open("./templates/index.txt")
    indexData = txt.read()

    ip = request.environ.get('REMOTE_ADDR')
    username, token, server, nodeid = getConfig()

    logData(ip, request.url, server)

    return indexData

#
# handle not relevant sides
#
@error(404)
def error404(error):
    txt = open("./templates/404.txt")
    indexData = txt.read()
    postContent = ""

    for l in request.body:
        postContent += l.decode("utf-8")

    print("Access to not existing ressource: " + request.url + postContent)
    ip = request.environ.get('REMOTE_ADDR')
    username, token, server, nodeid = getConfig()

    logData(ip, request.url, server)

    return indexData


@route('/_cat/indices', method='GET')
def getindeces():
    txt = open("./templates/getindeces.txt")
    indexData = txt.read()

    ip = request.environ.get('REMOTE_ADDR')
    username, token, server, nodeid = getConfig()

    logData(ip, request.url, server)

    return indexData

@route('/_search', method='GET')
def handleSearchExploitGet():

    ip = request.environ.get('REMOTE_ADDR')

    postdata(request.url, request.url , ip)
    print ("Found attack: " + request.url)
    return ""

@route('/_search', method='POST')
def handleSearchExploit():

    postContent = ""
    ip = request.environ.get('REMOTE_ADDR')

    for l in request.body:
        postContent += l.decode("utf-8")

    print("Found possible attack (_search): " + request.url + postContent)

    postdata(request.url, request.url + "Body: " + postContent, ip)

    return ""


#
# listen to all ports to keep
#
run(host='0.0.0.0', port=9200)