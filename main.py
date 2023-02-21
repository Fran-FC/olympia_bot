from requests_html import HTMLSession
from bs4 import BeautifulSoup
import logging
import argparse
import json

def logout(session):
    resp = session.get("https://www.olympialcoy.com/wp-login.php?action=logout")

    soup = BeautifulSoup(resp.content, "html.parser")
    for link in soup.find_all("a"):
        r = session.get(link.get("href"))
    if r.ok:
        return True 
    return False

def get_reserva_codes(content, book_activity, book_hour):
    code = None
    uid = None

    soup = BeautifulSoup(content, "html.parser")
    for hour in soup.find_all("li", class_="list-group-item disabled text-center"):
        if hour.next.string == book_hour:
            item = hour.next.next.next
            while True:
                if item.string == book_activity:
                    link = item.parent.parent.parent.parent # a tag parent with code
                    code = link.get("data-post-id")
                    uid = link.get("data-user-id")
                    break
                else:
                    item = item.next
                    continue
    return {
        "postid" : int(code), # scrap from reservas_url response
        "userid" : int(uid) # fixed id 
    }

# opt parse
parser = argparse.ArgumentParser()
parser.add_argument("--hour", default="18:30", help="Pass hour to book")
parser.add_argument("--activity", default="CROSS OLYMPIA", help="Pass hour to book")
parser.add_argument("--email", required=True, help="Pass hour to book")
parser.add_argument("--password", required=True, help="Pass hour to book")
opts = parser.parse_args() 

# logging config
logging.basicConfig(filename="bot.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

# globals
clases_url = "https://www.olympialcoy.com/reservas/clases"
session = HTMLSession()

# login loop
while True:
    login_resp = session.post(
        "https://www.olympialcoy.com/wp-login.php", 
        data= {
            "log": opts.email,
            "pwd":	opts.password,
            "rememberme": "forever",
            "wp-submit":	"Acceder",
            "redirect_to":	clases_url,
            "testcookie":	"1"
        }
    )
    if not login_resp.ok:
        logout(session)
        continue
    break

resp = session.get(clases_url)
codes = get_reserva_codes(resp.content, opts.activity, opts.hour)

resp = session.post(
    "https://www.olympialcoy.com/reservas/clases/crearnuevareserva",
    headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Content-Type': 'application/json;charset=utf-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.olympialcoy.com',
        'Connection': 'keep-alive',
        'Referer': 'https://www.olympialcoy.com/reservas/clases',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    },
    json=codes
)
resp_json = json.loads(resp.content)

if resp_json == "ok":
    logging.info("SUCCESS BOOKING. msg: {}".format(resp_json["msg"]))
else:
    logging.info("FAILED BOOKING. msg: {}".format(resp_json["msg"]))

# exit 
logout(session)
session.close()