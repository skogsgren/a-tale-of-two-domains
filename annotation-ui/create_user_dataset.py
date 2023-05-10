import pandas as pd
import sqlite3
import sys
import re
import random
import json


def main(database, export_db, n_posts):
    """Creates a new SQLITE3 DB from n-random threads from existing SQLITE DB"""
    conn = sqlite3.connect(database)
    new_conn = sqlite3.connect(export_db)
    with new_conn:
        new_cur = new_conn.cursor()
        if new_cur.execute("SELECT * FROM sqlite_master;").fetchall() == []:
            new_cur.execute(
                "CREATE TABLE posts("
                "id INTEGER UNIQUE PRIMARY KEY,"
                "forum TEXT,"
                "url TEXT,"
                "text TEXT);"
            )
            new_conn.commit()

    post_per_thread = 13
    n_threads = int(n_posts) // post_per_thread
    print(
        f"A total of {n_threads} threads will be extracted"
        f"({post_per_thread} posts/thread)."
    )

    with conn, new_conn:
        cur = conn.cursor()
        new_cur = new_conn.cursor()

        # get list of desired forums in database
        with open("config.json", "r") as f:
            forum_list = json.load(f)["forums"]

        # calculate how many threads to extract from each forum
        n_threads_per_forum = n_threads // len(forum_list)
        print(f"{n_threads_per_forum} threads will be extracted from each forum")

        for forum in forum_list:
            print(f"Processing {forum}")
            # extract unique thread urls
            thread_urls = set()
            url_list = cur.execute(
                f'SELECT DISTINCT url FROM posts WHERE forum LIKE "{forum}";'
            )

            for original_url in url_list:
                url = re.search(
                    r"https:\/\/www\.familjeliv\.se\/forum\/thread\/\d+.+(?=/)",
                    original_url[0],
                )

                if url is None:
                    url = re.search(
                        r"https:\/\/www\.familjeliv\.se\/forum\/thread\/\d+.+",
                        original_url[0],
                    )

                thread_urls.add(url.group())

            thread_urls = list(thread_urls)
            random.shuffle(thread_urls)

            # extract set amount of posts from randomly chosen threads
            for i in range(n_threads_per_forum):
                thread_over_threshold = False

                while thread_over_threshold is False:
                    current_thread = thread_urls.pop()
                    list_of_posts = [
                        x
                        for x in cur.execute(
                            f'SELECT * FROM posts WHERE url LIKE "{current_thread}";'
                        )
                    ]

                    if len(list_of_posts) > 15:
                        thread_over_threshold = True

                list_of_posts = list_of_posts[:10] + list_of_posts[-3:]

                for post in list_of_posts:
                    new_cur.execute("INSERT INTO posts VALUES (?, ?, ?, ?)", post)
                    new_conn.commit()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
