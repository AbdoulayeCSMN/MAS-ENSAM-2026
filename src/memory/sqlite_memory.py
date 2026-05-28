"""SQLite persistent memory - no Docker, just Python built-in."""

import sqlite3
import hashlib
import logging
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class SQLiteMemory:
    """Persistent memory using SQLite (no external dependencies)."""
    
    def __init__(self, db_file: str = ".memory_cache.db"):
        self.db_file = Path(db_file)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            # Table des patterns
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    code_snippet TEXT,
                    cwe_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_description ON patterns(description)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cwe ON patterns(cwe_id)")
            
            # Table des patches
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cwe_id TEXT NOT NULL,
                    patch_diff TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patches_cwe ON patches(cwe_id)")
            
            # Full-text search pour recherche avancée
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts 
                USING fts5(description, code_snippet, content=patterns)
            """)
            
            # Trigger pour synchroniser FTS
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS patterns_fts_insert AFTER INSERT ON patterns
                BEGIN
                    INSERT INTO patterns_fts(rowid, description, code_snippet)
                    VALUES (new.rowid, new.description, new.code_snippet);
                END
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_file))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def retrieve_similar_patterns(self, code_snippets: list[str], top_k: int = 5) -> list[str]:
        """Retrieve similar patterns using full-text search."""
        if not code_snippets:
            return []
        
        query = " ".join(code_snippets[:3])
        
        with self._get_connection() as conn:
            # Tentative avec FTS5
            try:
                cursor = conn.execute("""
                    SELECT description, rank 
                    FROM patterns_fts 
                    WHERE patterns_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, top_k))
                
                results = cursor.fetchall()
                if results:
                    return [row['description'] for row in results]
            except:
                pass
            
            # Fallback avec LIKE
            cursor = conn.execute("""
                SELECT description FROM patterns
                WHERE description LIKE ? OR code_snippet LIKE ?
                LIMIT ?
            """, (f'%{query[:50]}%', f'%{query[:50]}%', top_k))
            
            return [row['description'] for row in cursor.fetchall()]
    
    def retrieve_patches(self, cwe_id: str, top_k: int = 3) -> list[str]:
        """Retrieve patches for a CWE."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT patch_diff FROM patches
                WHERE cwe_id LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'%{cwe_id}%', top_k))
            
            return [row['patch_diff'] for row in cursor.fetchall()]
    
    def store_pattern(self, description: str, code_snippet: str = "", cwe_id: str = ""):
        """Store a vulnerability pattern."""
        pattern_id = hashlib.md5(description.encode()).hexdigest()[:16]
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO patterns (id, description, code_snippet, cwe_id)
                VALUES (?, ?, ?, ?)
            """, (pattern_id, description, code_snippet, cwe_id))
        
        logger.info(f"[memory] Stored pattern: {description[:50]}...")
    
    def store_patch(self, cwe_id: str, patch_diff: str):
        """Store a patch."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO patches (cwe_id, patch_diff)
                VALUES (?, ?)
            """, (cwe_id, patch_diff))
        
        logger.info(f"[memory] Stored patch for {cwe_id}")
    
    def get_stats(self) -> dict:
        """Get memory statistics."""
        with self._get_connection() as conn:
            patterns_count = conn.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
            patches_count = conn.execute("SELECT COUNT(*) FROM patches").fetchone()[0]
            db_size = self.db_file.stat().st_size if self.db_file.exists() else 0
            
            return {
                "status": "enabled",
                "backend": "SQLite",
                "patterns_count": patterns_count,
                "patches_count": patches_count,
                "db_size_bytes": db_size,
                "db_size_mb": round(db_size / 1024 / 1024, 2)
            }
    
    @property
    def enabled(self) -> bool:
        return True


# Alias pour compatibilité
PersistentMemory = SQLiteMemory