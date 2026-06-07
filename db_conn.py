import psycopg
from psycopg_pool import ConnectionPool
DB_URI = "postgres://postgres:postgres@localhost:5432/ds-star"

class ConnectionManager:
    def __init__(self):
        self.pool = ConnectionPool(DB_URI, min_size=1, max_size=10, open=True)

    def connection(self):
        """Returns the connection context manager from the pool."""
        return self.pool.connection()  
    
    def close_all(self):
        """Closes the entire pool when the application shuts down."""
        self.pool.close()