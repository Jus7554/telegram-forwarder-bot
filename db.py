import sqlite3
from config import DB_NAME, CUSTOM_FOOTER, DEFAULT_DELAY

class Database:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        # جدول قنوات المصدر
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS SourceChannels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id BIGINT UNIQUE NOT NULL,
                channel_name TEXT,
                last_message_id INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # جدول الإعدادات العامة
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # إعدادات افتراضية
        self.set_setting('bot_status', 'Stopped', default=True) # تغيير الحالة الافتراضية إلى Stopped
        self.set_setting('default_delay', str(DEFAULT_DELAY), default=True)
        self.set_setting('custom_footer', CUSTOM_FOOTER, default=True)
        self.set_setting('target_channel_id', '', default=True) # إضافة معرف قناة الهدف
        self.conn.commit()

    def get_setting(self, key):
        self.cursor.execute("SELECT value FROM Settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def set_setting(self, key, value, default=False):
        if default:
            # تحقق مما إذا كان الإعداد موجوداً بالفعل
            if self.get_setting(key) is not None:
                return
        
        self.cursor.execute("INSERT OR REPLACE INTO Settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_active_channels(self):
        self.cursor.execute("SELECT channel_id, last_message_id FROM SourceChannels WHERE is_active = 1")
        return self.cursor.fetchall()

    def get_all_channels(self):
        self.cursor.execute("SELECT channel_id, channel_name, is_active FROM SourceChannels")
        return self.cursor.fetchall()

    def add_channel(self, channel_id, channel_name):
        try:
            self.cursor.execute("INSERT INTO SourceChannels (channel_id, channel_name) VALUES (?, ?)", (channel_id, channel_name))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # القناة موجودة بالفعل

    def remove_channel(self, channel_id):
        self.cursor.execute("DELETE FROM SourceChannels WHERE channel_id = ?", (channel_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def update_last_message_id(self, channel_id, message_id):
        self.cursor.execute("UPDATE SourceChannels SET last_message_id = ? WHERE channel_id = ?", (message_id, channel_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == '__main__':
    # مثال للاستخدام
    db = Database()
    print("Database setup complete.")
    db.add_channel(-100123456789, "Test Channel 1")
    db.add_channel(-100987654321, "Test Channel 2")
    print(db.get_all_channels())
    db.update_last_message_id(-100123456789, 50)
    db.set_setting('target_channel_id', '-100111222333')
    print(db.get_setting('custom_footer'))
    print(db.get_setting('target_channel_id'))
    db.close()
