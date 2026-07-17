# -*- coding: utf-8 -*-
"""
auth_service.py
خدمة المصادقة المطورة - Premium Authentication Service
- يدعم التوافق الرجعي التلقائي (Backward Compatibility) لحسابات المستخدمين القديمة والجديدة معاً.
- تلافي مشكلة خطأ تسجيل الدخول بعد زيادة جولات التشفير.
"""
import hashlib
import os
import binascii

# الجولات الجديدة للأمان العالي
PBKDF2_ITERATIONS = 600_000
# الجولات القديمة للتوافق الرجعي وحل مشكلة الحسابات الحالية
OLD_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """يُنتج hash بصيغة 'salt_hex:hash_hex'."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(pwd_hash).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        
        # 1. المحاولة أولاً بالمعيار الجديد (600,000 دورة)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        if pwd_hash == expected:
            return True
            
        # 2. التوافق الرجعي: إذا لم يتطابق، نجرب المعيار القديم (100,000 دورة) لمنع حدوث أخطاء للمستخدمين الحاليين
        pwd_hash_old = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, OLD_PBKDF2_ITERATIONS)
        return pwd_hash_old == expected

    except Exception:
        return False


class AuthService:
    def __init__(self, db):
        self.db = db
        self.current_user = None

    def authenticate(self, username: str, password: str):
        """يتحقق من بيانات الدخول، ويُرجع dict للمستخدم عند النجاح أو None عند الفشل."""
        row = self.db.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,), fetchone=True,
        )
        if row and verify_password(password, row["password_hash"]):
            # إذا دخل المستخدم بنجاح وكان حسابه بالهاش القديم، يفضل تحديثه تلقائياً للهاش الجديد مستقبلاً
            # لتسهيل الأمر سنقوم فقط بتحديث وقت تسجيل الدخول حالياً
            self.db.execute(
                "UPDATE users SET last_login_at = datetime('now') WHERE id = ?",
                (row["id"],), commit=True,
            )
            self.current_user = dict(row)
            return self.current_user
        return None

    def create_user(self, username: str, password: str, role: str = "User", is_active: bool = True) -> int:
        """ينشئ مستخدمًا جديدًا مع تشفير كلمة المرور وتحديد الحالة النشطة صراحةً."""
        pwd_hash = hash_password(password)
        return self.db.execute(
            "INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, ?)",
            (username, pwd_hash, role, int(is_active)), commit=True,
        )

    def change_password(self, user_id: int, new_password: str):
        """تغيير كلمة مرور مستخدم بشكل مباشر."""
        self.db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id), commit=True,
        )

    # ---------- إدارة المستخدمين (شاشة Users) ----------
    def list_users(self, current_user: dict):
        """
        جلب المستخدمين بناءً على الصلاحية:
        - الـ Admin يرى كافة مستخدمي النظام مرتبين أبجدياً.
        - المستخدم العادي (User) يرى حسابه الشخصي فقط.
        """
        if current_user.get("role") == "Admin":
            rows = self.db.execute(
                "SELECT id, username, role, is_active, created_at, last_login_at FROM users ORDER BY username",
                fetchall=True,
            )
        else:
            rows = self.db.execute(
                "SELECT id, username, role, is_active, created_at, last_login_at FROM users WHERE id = ?",
                (current_user.get("id"),),
                fetchall=True,
            )
        return [dict(r) for r in rows]

    def get_user(self, user_id: int):
        row = self.db.execute("SELECT * FROM users WHERE id = ?", (user_id,), fetchone=True)
        return dict(row) if row else None

    def username_exists(self, username: str, exclude_user_id: int = None) -> bool:
        if exclude_user_id:
            row = self.db.execute(
                "SELECT id FROM users WHERE username = ? AND id != ?",
                (username, exclude_user_id), fetchone=True,
            )
        else:
            row = self.db.execute(
                "SELECT id FROM users WHERE username = ?", (username,), fetchone=True
            )
        return row is not None

    def count_active_admins(self) -> int:
        row = self.db.execute(
            "SELECT COUNT(*) as c FROM users WHERE role = 'Admin' AND is_active = 1",
            fetchone=True,
        )
        return row["c"]

    def update_user(self, user_id: int, username: str = None, role: str = None, is_active: bool = None, password: str = None):
        """
        تحديث مرن لبيانات المستخدم.
        يدعم إمكانية تحديث كلمة المرور مدمجاً في نفس طلب التحديث عند تمريرها.
        """
        fields = {}
        if username is not None:
            fields["username"] = username
        if role is not None:
            fields["role"] = role
        if is_active is not None:
            if is_active is False:
                target_user = self.get_user(user_id)
                if target_user and target_user["role"] == "Admin" and self.count_active_admins() <= 1:
                    raise ValueError("لا يمكن تعطيل آخر مدير نشط في النظام.")
            fields["is_active"] = int(is_active)
        if password is not None and password.strip() != "":
            fields["password_hash"] = hash_password(password)

        if not fields:
            return

        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id]
        self.db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values, commit=True)

    def delete_user(self, user_id: int):
        """حذف مستخدم مع تطبيق خط الدفاع الخلفي لمنع حذف آخر مدير نشط."""
        target_user = self.get_user(user_id)
        if target_user and target_user["role"] == "Admin" and self.count_active_admins() <= 1:
            raise ValueError("لا يمكن حذف آخر مدير نشط في النظام.")
            
        self.db.execute("DELETE FROM users WHERE id = ?", (user_id,), commit=True)

    def ensure_default_admin(self):
        """ينشئ مستخدم admin افتراضي (admin/admin123) عند تشغيل التطبيق لأول مرة فقط."""
        row = self.db.execute("SELECT COUNT(*) as c FROM users", fetchone=True)
        if row["c"] == 0:
            self.create_user("admin", "admin123", role="Admin")

    def save_security_answers(self, user_id: int, question_id: int, raw_answer: str):
        """تشفير وحفظ إجابة سؤال الأمان للمستخدم"""
        # تنظيف النص وتحويله لأحرف صغيرة (لو إنجليزي) لضمان دقة التحقق لاحقاً
        cleaned_answer = " ".join(raw_answer.strip().lower().split())
        answer_hash = hash_password(cleaned_answer)  # نستخدم دالتك الأصلية للتشفير
        
        self.db.execute(
            """INSERT INTO user_security_answers (user_id, question_id, answer_hash) 
               VALUES (?, ?, ?)""",
            (user_id, question_id, answer_hash), commit=True
        )

    def reset_password_via_security_question(self, username: str, question_id: int, raw_answer: str) -> str:
        """
        التحقق من الإجابة، وإذا كانت صحيحة، يتم توليد كلمة سر افتراضية 
        وإرجاعها ليتم عرضها للمستخدم في الواجهة.
        """
        # 1. جلب بيانات المستخدم وإجابته المخزنة
        row = self.db.execute(
            """SELECT u.id, sa.answer_hash FROM users u
               JOIN user_security_answers sa ON u.id = sa.user_id
               WHERE u.username = ? AND sa.question_id = ? AND u.is_active = 1""",
            (username.strip(), question_id), fetchone=True
        )
        
        if not row:
            raise ValueError("اسم المستخدم أو سؤال الأمان غير صحيح.")
            
        # 2. التحقق من تطابق الإجابة المدخلة مع الهاش المخزن
        cleaned_answer = " ".join(raw_answer.strip().lower().split())
        if not verify_password(cleaned_answer, row["answer_hash"]):
            raise ValueError("إجابة سؤال الأمان غير صحيحة، حاول مجدداً.")
            
        # 3. الإجابة صحيحة! نولد كلمة سر افتراضية عشوائية أو ثابتة آمنة
        default_password = "Reset@" + binascii.hexlify(os.urandom(3)).decode() # مثال: Reset@a1b2c3
        
        # 4. تحديث كلمة المرور في قاعدة البيانات
        self.change_password(row["id"], default_password)
        
        return default_password