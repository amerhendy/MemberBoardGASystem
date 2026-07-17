# -*- coding: utf-8 -*-
"""
config.py
إعدادات عامة للتطبيق - General application configuration

ملاحظة عن التحويل إلى exe واحد (PyInstaller --onefile):
عند تشغيل التطبيق كملف exe واحد، يقوم PyInstaller بفك ضغط الملفات المرفقة
(مثل schema.sql) في مجلد مؤقت (sys._MEIPASS) يُحذف بعد إغلاق البرنامج.
لذلك:
  - resource_path()  تُستخدم لقراءة ملفات ثابتة مرفقة مع البرنامج (schema.sql).
  - app_data_dir()    تُستخدم لتخزين البيانات الدائمة (قاعدة البيانات والمستندات)
                       في مجلد ثابت على جهاز المستخدم (لا يُحذف أبدًا)، حتى لو
                       اتنقل الملف التنفيذي أو اتشغّل من مكان تاني.
"""
import os
import sys


def resource_path(relative_path: str) -> str:
    """مسار ملف مرفق (read-only) سواء بنشغّل من الكود مباشرة أو من exe واحد."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def app_data_dir() -> str:
    """
    مجلد دائم لتخزين البيانات (قاعدة البيانات + المستندات) في فولدر باسم
    "AppData" يكون **جنب ملف الـ exe مباشرة** (وليس في %APPDATA% النظامي)،
    عشان تقدر تنقل مجلد البرنامج كامل (exe + الفولدر ده) لأي جهاز تاني
    وتلاقي بياناتك اتنقلت معاه.

    - لو البرنامج شغال كملف exe (PyInstaller onefile): بناخد مكان ملف الـ exe
      نفسه بـ sys.executable (مش المجلد المؤقت sys._MEIPASS).
    - لو شغال من الكود مباشرة (python main.py): بناخد مجلد المشروع.
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "AppData")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(app_data_dir(), "app_data.db")
DOCUMENTS_DIR = os.path.join(app_data_dir(), "member_documents")

APP_NAME = "نظام إدارة الأعضاء - مجلس الإدارة والجمعية العمومية"
APP_VERSION = "1.0.0"

# أنواع الأعضاء / Member types
MEMBER_TYPES = ["Board", "Assembly"]
MEMBER_TYPE_LABELS_AR = {"Board": "مجلس الإدارة", "Assembly": "الجمعية العمومية"}

# حالات العضو / Member statuses
MEMBER_STATUSES = ["Active", "Ended", "Suspended"]
MEMBER_STATUS_LABELS_AR = {"Active": "نشط", "Ended": "منتهي", "Suspended": "موقوف"}

# أنواع المستندات الافتراضية / Default document types
DOC_TYPES = ["ID Card", "Appointing Decree", "CV", "Other"]

# أنواع الجلسات / Session types
SESSION_TYPES = ["Meeting", "Committee"]

# تأكد من وجود المجلدات المطلوبة عند تشغيل التطبيق
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

SECURITY_QUESTIONS = {
    1: "ما هو اسم أول مدرسة التحقت بها؟",
    2: "في أي مدينة ولد والدك؟",
    3: "ما هو اسم حيوانك الأليف الأول؟",
    4: "ما هي الأكلة المفضلة لديك في طفولتك؟"
}