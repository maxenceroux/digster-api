import psycopg2


class DigsterDB:
    def __init__(self, host: str, db: str, user: str, password: str) -> None:
        self.conn = psycopg2.connect(
            host=host, database=db, user=user, password=password
        )
        self.cur = self.conn.cursor()
