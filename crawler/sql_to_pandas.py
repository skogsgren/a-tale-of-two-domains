import pandas as pd
import sys
import sqlite3


def main(database):
    conn = sqlite3.connect(database)
    with conn:
        df = pd.read_sql_query("SELECT * FROM posts;", conn)
    print([x for x in df["text"]][-2:])


if __name__ == "__main__":
    main(sys.argv[1])
