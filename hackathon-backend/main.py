import os
import mysql.connector
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def health():
    conn = mysql.connector.connect(
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PWD"],
        host=os.environ["MYSQL_HOST"],
        database=os.environ["MYSQL_DATABASE"],
        ssl_ca="/app/server-ca.pem",
        ssl_cert="/app/client-cert.pem",
        ssl_key="/app/client-key.pem",
    )

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return {"status": "ok", "users": count}