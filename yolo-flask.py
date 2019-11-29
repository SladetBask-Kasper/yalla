from flask import Flask, render_template, request, jsonify
import threading, random, string, socket, requests, json
from time import sleep
from os import system

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Constants
STD_ERROR = "__ERROR__"
CONST_DELAY = 1
HARD_LIMIT = 500
DDOS_TIMEOUT = 50 # Every 50 seconds you are allowed to make MAX_PACKETS requests
MAX_PACKETS = 25
MAX_THREADS = 100
MAX_THREADS_ERROR_TXT = "SERVER OVERLOADED. TOO MANY THREADS...\t:'("
BLOCKABLE = "~/flask_webserver/blockable.txt"
USERAGENT = "Mozilla/5.0 (X11; Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0"
__TITLE__ = "Yolo Spammer"

# Global variables
counter = 0
shift = 0
ip_tabel = []
ip_attempts = []
request_tabel = []
request_attempts = []

@app.route('/')
def index():
    #ip_adress = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    #del ip_adress
    ip_adress = str(request.remote_addr)

    if ip_adress not in ip_tabel:
        if check_threads(): return render_template("error.html", error_txt=MAX_THREADS_ERROR_TXT)
        t = threading.Thread(target=spy, args=(ip_adress,))
        t.daemon = True
        t.start()
    else:
        ip_attempts[ip_tabel.index(ip_adress)] += 1

    return render_template("index.html", MAIN_TITLE=__TITLE__)

@app.route("/get_my_ip", methods=["GET"])
def get_ip():
    return jsonify({'ip': request.remote_addr, "ip2": request.environ.get('HTTP_X_REAL_IP', request.remote_addr)}), 200

@app.route('/', methods=["POST"])
def getValue():
    ip_adress = str(request.remote_addr)
    if ip_adress in ip_tabel: ip_attempts[ip_tabel.index(ip_adress)] += 1
    url = request.form["url"].strip()
    msg = request.form["message"]
    limit = -1
    try:
        limit = int(request.form["limit"].strip())
    except:
        return render_template("error.html", error_txt="Limit is not an int")
    if limit < 1:
        return render_template("error.html", error_txt="Limit is too small")
    if limit > HARD_LIMIT:
        return render_template("error.html", error_txt="Limit is too high")
    target, url = convert(url)
    print(f"TARGET: {target} URL: {url}")
    if target == STD_ERROR or url == STD_ERROR:
        return render_template("error.html", error_txt="URL Converting error")

    if check_threads(): return render_template("error.html", error_txt=MAX_THREADS_ERROR_TXT)
    t = threading.Thread(target=spammer, args=(target, url, msg, limit))
    t.daemon = True
    t.start()
    #adapt_uagent()

    print("Started thread on : URL: {}, Message: {}".format(target, msg))
    return render_template("success.html", desc="Started service on : URL: {} with message: {}, {} times".format(url, msg, limit))

def convert(link):
    where = link.find('?')
    url = ""
    correctDomainCheck = url.find("onyolo.com")
    if correctDomainCheck > 14 or correctDomainCheck < 0:
        return (STD_ERROR, STD_ERROR)
    del correctDomainCheck
    if where < 0:
        if link.find("/message") > 0:
            url = link[:link.find("/message")] + "?w=x"
            return (link, url)
        else:
            return (STD_ERROR, STD_ERROR)
    url = link[:where] + "?w=x"
    link = link[:where] + "/message"
    return (link, url)

def newCookie():
    ### Generates a new cookie.
    cookie = ''.join(random.choices(string.ascii_letters + string.digits, k=22))
    return cookie

def refresh_header(url, cookie, size):
    header = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Content-Length": str(57 + int(size) + 1),
        "Content-Type": "application/json;charset=utf-8",
        "Cookie": f"popshow-temp-id={cookie}",
        "DNT":"1",
        "Host": "onyolo.com",
        "id=": str(cookie),
        "Cache-Control": "no-cache",
        "Referer": url,
        "User-Agent": USERAGENT
    }
    return header

def spammer(target, url, message, amount):
    global counter
    local_counter = 0

    while local_counter < amount:
        cookie = newCookie()
        send_msg = message
        if "%random%" in send_msg:
            send_msg = send_msg.replace("%random%", str(random.randint(0, 999999)))
        if "%nr%" in send_msg:
            send_msg = send_msg.replace("%nr%", str(local_counter+1))
        payload = {"text":f"{send_msg}","cookie":f"{cookie}", "wording":"x"}
        header = refresh_header(url, cookie, len(send_msg))
        r = requests.post(target, data=json.dumps(payload), headers=header)
        if not r.text == "ok":
            print(f"\t ! ERROR SENDING PACKET {local_counter+1} ON {url}! Dying...")
            system(f"echo 'ERROR SENDING PACKET {local_counter+1} ON {url} TARGET {target}!\nHEADER:{header} PAYLOAD:{payload}\n\n\n\n' > send_errors.log")
            return
        local_counter += 1
        sleep(CONST_DELAY)

    counter += local_counter
    print("\t * Total Counter: {}\n\t * Local Counter: {}, Dying...".format(counter, local_counter))
    return

def adapt_uagent():
    global USERAGENT
    global shift

    if shift < 1:
        USERAGENT = "Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.503l3; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; MSOffice 12)"
        shift += 1
    elif shift == 1:
        USERAGENT = "Mozilla/5.0 (Linux; Tizen 2.3) AppleWebKit/538.1 (KHTML, like Gecko)Version/2.3 TV Safari/538.1"
        shift += 1
    elif shift > 1:
        USERAGENT = "Mozilla/5.0 (X11; Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0"
        shift = 0

###
### DDoS Protection Area
###

def check_threads():
    return threading.active_count() >= MAX_THREADS

def spy(ip):
    global ip_tabel
    global ip_attempts

    ip_tabel += [ip]
    ip_attempts += [1]
    index = ip_tabel.index(ip)

    for i in range(DDOS_TIMEOUT):
        sleep(1) # Sleep before checking for first time.
                 #If it's the first connection in fifthy seconds then it's prolly got some time to wait.
        if ip_attempts[index] > MAX_PACKETS:
            system("echo '{}' >> {}".format(ip, BLOCKABLE))
            sleep(2)# give firewall time to update.
            break
        #print("IP: {} WITH ATTEMPTS: {} AT SECOND: {}".format(ip_tabel[index], ip_attempts[index], i+1))
    del ip_attempts[index]
    del ip_tabel[index]
    return
app.run(debug=True, host= '0.0.0.0')
