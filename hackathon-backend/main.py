import os
import mysql.connector

def main():
    # DB接続のための準備（Go例と同じ発想）
    mysql_user = os.getenv("MYSQL_USER")
    mysql_pwd = os.getenv("MYSQL_PWD")
    mysql_host = os.getenv("MYSQL_HOST")
    mysql_database = os.getenv("MYSQL_DATABASE")

    # 接続（まだクエリは打たない）
    conn = mysql.connector.connect(
        user=mysql_user,
        password=mysql_pwd,
        host=mysql_host,
        database=mysql_database,
    )

    print("DB connected")
    conn.close()

if __name__ == "__main__":
    main()