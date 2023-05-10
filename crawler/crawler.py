from bs4 import BeautifulSoup
import requests
import logging
import sys
import json
import re
import os
import pandas as pd
import urllib.parse
import pickle
import sqlite3


# Basic logging configuration
logging.basicConfig(format="%(asctime)s %(message)s")
logging.getLogger().setLevel(logging.INFO)


def main(url):
    # Read config
    with open("config.json", "r") as f:
        config = json.load(f)

    # Read desired CSS classes
    css_classes = config["css_classes"]

    # Open DB if it exists, otherwise create it
    logging.info("Initializing SQLITE database.")
    conn = sqlite3.connect(config["database"])
    cur = conn.cursor()
    if cur.execute("SELECT * FROM sqlite_master;").fetchall() == []:
        cur.execute(
            "CREATE TABLE posts("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "forum TEXT,"
            "url TEXT,"
            "text TEXT);"
        )

    forum_title = BeautifulSoup(request(url), "html.parser").title.string
    url_base = re.match(r".+\.\w+", url).group(0)
    if os.path.exists("visited.pkl") and os.path.exists("to_visit.pkl"):
        logging.info("Importing previous state")
        with open("visited.pkl", "rb") as f, open("to_visit.pkl", "rb") as g:
            visited = pickle.load(f)
            to_visit = pickle.load(g)
    else:
        visited = set()
        to_visit = [url]
    try:
        while to_visit:
            url_to_visit = to_visit.pop()
            if "allmant" in url_to_visit:
                visited.add(url_to_visit)
                continue
            # since these pages are identical in content for familjeliv
            elif (url_to_visit[-1] == "1" and url_to_visit[:-1] in visited) or (
                url_to_visit[-1] == "/" and f"{url_to_visit}1" in visited
            ):
                continue
            elif url_to_visit not in visited:
                logging.info(f"{len(visited)} Visiting {url_to_visit}")
                soup = BeautifulSoup(request(url_to_visit), "html.parser")
                visited.add(url_to_visit)
            else:
                continue

            # for links to threads
            links = soup.find_all("td", class_=css_classes["thread"])
            for i in links:
                try:
                    new_link = urllib.parse.urljoin(url_base, i.find("a").get("href"))
                    if new_link not in visited:
                        to_visit.append(new_link)
                except AttributeError:
                    pass

            # for nav links
            try:
                nav_div = soup.find("div", class_=css_classes["nav_forum"]).find("ul")
                for i in nav_div.find_all("li"):
                    try:
                        new_link = urllib.parse.urljoin(
                            url_base, i.find("a").get("href")
                        )
                        if new_link not in visited:
                            to_visit.append(new_link)
                    except AttributeError:
                        pass
            except AttributeError:
                pass

            # for posts
            posts = soup.find_all("div", class_=css_classes["text"])
            if len(posts) == 0:
                continue
            for i in posts:
                text = ""
                for child in i.contents:
                    try:
                        try:
                            if css_classes["thread_header"] in child.attrs["class"]:
                                break
                        except AttributeError:
                            pass
                        except KeyError:
                            pass
                        if child.name != "div":
                            text += child.text.replace("\xa0", " ")
                    except AttributeError:
                        pass
                    except KeyError:
                        pass
                text = text.lstrip().rstrip()
                if text != "":
                    try:
                        cur.execute(
                            "INSERT INTO posts (forum, url, text) VALUES (?, ?, ?);",
                            (forum_title, url_to_visit, text),
                        )
                        conn.commit()
                    except sqlite3.IntegrityError:
                        logging.info("ERROR: Can't add duplicate post. Continuing...")

            # periodical backup of visited list
            if len(visited) % 10 == 0:
                with open("visited.pkl", "wb") as f, open("to_visit.pkl", "wb") as g:
                    pickle.dump(visited, f)
                    pickle.dump(to_visit, g)
    except KeyboardInterrupt:
        pass
    conn.close()


def request(url):
    html_request = requests.get(url)
    try:
        if html_request.status_code == 200:
            html = html_request.text
        else:
            html = "<!-- -->"
            print("404 error, but keepin' on keepin' on...")
    except (
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ConnectionError,
        requests.exceptions.InvalidSchema,
    ):
        html = "<!-- -->"
        print("404 error, but keepin' on keepin' on...")
    return html


if __name__ == "__main__":
    main(sys.argv[1])
