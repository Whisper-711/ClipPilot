import sqlite3
import hashlib
import config


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config.DB_FILE, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                content     TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT (datetime('now','localtime')),
                is_favorite INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_history_hash ON clipboard_history(content_hash);
            CREATE INDEX IF NOT EXISTS idx_history_time ON clipboard_history(created_at DESC);

            CREATE TABLE IF NOT EXISTS translations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT NOT NULL UNIQUE,
                source_lang  TEXT,
                target_text  TEXT NOT NULL,
                created_at   TIMESTAMP DEFAULT (datetime('now','localtime'))
            );
        """)
        self.conn.commit()

    # ── 剪贴板历史 ──

    def add_history(self, content):
        """添加新记录，已存在则更新时间戳（移到顶部）。返回记录 id。"""
        h = hashlib.sha256(content.encode('utf-8')).hexdigest()
        cur = self.conn.execute(
            "SELECT id FROM clipboard_history WHERE content_hash = ?", (h,)
        )
        row = cur.fetchone()
        if row:
            self.conn.execute(
                "UPDATE clipboard_history SET created_at = datetime('now','localtime') WHERE id = ?",
                (row[0],)
            )
            self.conn.commit()
            return row[0]
        self.conn.execute(
            "INSERT INTO clipboard_history (content, content_hash) VALUES (?, ?)",
            (content, h)
        )
        self.conn.commit()
        self._trim()
        return self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_history(self, limit=50, offset=0, search=None):
        """获取历史记录，支持搜索。"""
        if search:
            cur = self.conn.execute(
                "SELECT id, content, created_at, is_favorite FROM clipboard_history "
                "WHERE content LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (f'%{search}%', limit, offset)
            )
        else:
            cur = self.conn.execute(
                "SELECT id, content, created_at, is_favorite FROM clipboard_history "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
        return cur.fetchall()

    def get_history_count(self, search=None):
        if search:
            cur = self.conn.execute(
                "SELECT COUNT(*) FROM clipboard_history WHERE content LIKE ?",
                (f'%{search}%',)
            )
        else:
            cur = self.conn.execute("SELECT COUNT(*) FROM clipboard_history")
        return cur.fetchone()[0]

    def get_by_id(self, record_id):
        cur = self.conn.execute(
            "SELECT id, content, created_at FROM clipboard_history WHERE id = ?",
            (record_id,),
        )
        return cur.fetchone()

    def delete_history(self, record_id):
        self.conn.execute("DELETE FROM clipboard_history WHERE id = ?", (record_id,))
        self.conn.commit()

    def clear_all(self):
        self.conn.execute("DELETE FROM clipboard_history")
        self.conn.commit()

    def _trim(self):
        cfg = config.load()
        max_records = cfg.get('max_history', 200)
        self.conn.execute(
            "DELETE FROM clipboard_history WHERE id NOT IN ("
            "SELECT id FROM clipboard_history ORDER BY created_at DESC LIMIT ?"
            ")", (max_records,)
        )
        self.conn.commit()

    # ── 翻译缓存 ──

    def get_cached_translation(self, content_hash):
        cur = self.conn.execute(
            "SELECT target_text, source_lang FROM translations WHERE content_hash = ?",
            (content_hash,)
        )
        return cur.fetchone()

    def cache_translation(self, content_hash, source_lang, target_text):
        self.conn.execute(
            "INSERT OR REPLACE INTO translations (content_hash, source_lang, target_text) "
            "VALUES (?, ?, ?)",
            (content_hash, source_lang, target_text)
        )
        self.conn.commit()
