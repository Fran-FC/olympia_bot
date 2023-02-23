from requests_html import HTMLSession
from bs4 import BeautifulSoup
import logging
import argparse
import json

# globals
clases_url = "https://www.olympialcoy.com/reservas/clases"

# opt parse
parser = argparse.ArgumentParser()
parser.add_argument("--hour", default="18:30", help="Pass hour to book")
parser.add_argument("--activity", default="CROSS OLYMPIA", help="Pass hour to book")
parser.add_argument("--email", required=True, help="Pass hour to book")
parser.add_argument("--password", required=True, help="Pass hour to book")
opts = parser.parse_args() 

# logging config
logging.basicConfig(filename=opts.email+"_bot.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 
# same session through program run
session = HTMLSession()

# functions
def login(email, password):
    # login loop
    while True:
        login_resp = session.post(
            "https://www.olympialcoy.com/wp-login.php", 
            data= {
                "log": email,
                "pwd":	password,
                "rememberme": "forever",
                "wp-submit":	"Acceder",
                "redirect_to":	clases_url,
                "testcookie":	"1"
            }
        )
        if not login_resp.ok:
            logging.info("Failed login")
            logout()
            continue
        break
    logging.info("login")


def logout():
    resp = session.get("https://www.olympialcoy.com/wp-login.php?action=logout")

    soup = BeautifulSoup(resp.content, "html.parser")
    for link in soup.find_all("a"):
        r = session.get(link.get("href"))
        break

    logging.info("logout")


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
    logging.info("retrieved booking codes")
    return {
        "postid" : int(code), # scrap from reservas_url response
        "userid" : int(uid) # fixed id 
    }

    
def book_session(activity, hour):
    resp = session.get(clases_url)
    codes = get_reserva_codes(resp.content, activity, hour)

    resp = session.post(
        "https://www.olympialcoy.com/reservas/clases/crearnuevareserva",
        headers={
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
    
    return resp_json


def main():
    logging.info("Starting bot")

    login(opts.email, opts.password)

    resp_json = book_session(opts.activity, opts.hour)
    
    if resp_json["res"]  == "ok":
        logging.info("SUCCESS BOOKING. msg: {}".format(resp_json["msg"]))
    else:
        logging.info("FAILED BOOKING. msg: {}".format(resp_json["msg"]))

    # exit 
    logout()
    session.close()


if __name__=="__main__":
    main()
