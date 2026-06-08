import psycopg
from db_conn import ConnectionManager
from datetime import datetime, timezone
import uuid
from typing import Union, List, Dict, Any
import hashlib

class DatabaseSetup:
    def __init__(self, db_manager: ConnectionManager):
        self.db = db_manager

    def create_history(self):        
        with self.db.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    
                    # custom ENUM type if it doesn't exist
                    cur.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'query_class_type') THEN
                                CREATE TYPE query_class_type AS ENUM ('follow_up', 'standalone');
                            END IF;
                        END
                        $$;
                    """)
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS chat_history (
                            id SERIAL PRIMARY KEY,
                            data_paths TEXT[],
                            conversation_id UUID NOT NULL, 
                            run_id UUID NOT NULL,
                            query_class query_class_type NOT NULL,
                            user_query TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            created_at TIMESTAMP 
                        );
                    """)
                    
        print("Chat history table created  successfully")


    def insert_chat_record(
        self,
        db: ConnectionManager,
        conversation_id: str,
        run_id: uuid.UUID,
        query_class: str, 
        user_query: str,
        answer: str,
        data_paths: List[str]
        ):
        """
        Inserts a new chat record into the chat_history table.
        Returns the newly generated record ID if successful, or None if it fails.
        """
        if query_class not in ('standalone', 'follow_up'):
            raise ValueError("query_class must be either 'standalone' or 'follow_up'")
        query = """
            INSERT INTO chat_history (
                conversation_id, data_paths, run_id, query_class, user_query, answer, created_at
            ) VALUES (%s, %s,  %s, %s, %s, %s, %s)
            RETURNING id;
        """
        now = datetime.now(timezone.utc)
        try:
            with db.connection() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(query, (
                            conversation_id,
                            data_paths,
                            run_id,
                            query_class,
                            user_query,
                            answer,
                            now
                        ))
                        new_id = cur.fetchone()[0]
                        return new_id

        except Exception as e:
            print(f"Failed to insert chat history record: {e}")
            return None
        
    def get_latest_chat_history(
        self,
        db: ConnectionManager, 
        conversation_id: uuid.UUID, 
        limit: int = 4
        ) -> List[Dict[str, Any]]:
        """
        Fetches the latest 'limit' (default 4) records for a specific conversation_id,
        ordered from newest to oldest. Returns a list of dictionaries.
        """
        query = """
            SELECT id, data_paths, run_id, conversation_id, query_class, user_query, answer, created_at
            FROM chat_history
            WHERE conversation_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
        """
        records = []
        try:
            with db.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (conversation_id, limit))
                    colnames = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    for row in rows:
                        records.append(dict(zip(colnames, row)))
                        
            return records
        except Exception as e:
            print(f"Failed to fetch chat history: {e}")
            return []
        
    def generate_conversation_id(self, paths: Union[str, List[str]]) -> uuid.UUID:
        """
        Generates a deterministic UUID based on the provided path or paths.
        The resulting ID is order-independent and immune to trailing slash mismatches.
        """
        # list of strings
        if isinstance(paths, str):
            path_list = [paths]
        else:
            path_list = list(paths)
        # normalize paths (remove trailing slashes, strip spaces) and sort them
        normalized_paths = sorted([p.strip().rstrip('/') for p in path_list])
        # join them into a single unique string structure
        combined_string = "||".join(normalized_paths)
        # generate a SHA-256 hash of the string
        hasher = hashlib.sha256(combined_string.encode('utf-8'))
        hash_bytes = hasher.digest()
        #convert the first 16 bytes of the hash into a valid  UUID
        conversation_id = uuid.UUID(bytes=hash_bytes[:16])
        return conversation_id
    