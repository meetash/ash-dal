from sqlalchemy import URL

SYNC_DB_URL = URL.create(
    drivername="mysql+pymysql",
    username="my_db_user",
    password="S3cret",
    host="127.0.0.1",
    port=3306,
    database="my_db",
)


ASYNC_DB_URL = URL.create(
    drivername="mysql+aiomysql",
    username="my_db_user",
    password="S3cret",
    host="127.0.0.1",
    port=3306,
    database="my_db",
)
