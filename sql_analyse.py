import sqlite3


table_name = "BTCUSDT1631632130"

conn = sqlite3.connect("Logfile.db")
c = conn.cursor()

c.execute(f"SELECT * FROM {table_name}")
content = c.fetchall()
print(content)
