-- schema.sql
-- مخطط قاعدة البيانات الكامل لنظام إدارة الأعضاء (مجلس الإدارة + الجمعية العمومية)

PRAGMA foreign_keys = ON;

-- ============================
-- 1) المستخدمون والصلاحيات
-- ============================
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('Admin','User')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at   TEXT
);
-- جدول إجابات أسئلة الأمان للمستخدمين
CREATE TABLE IF NOT EXISTS user_security_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,          -- رقم السؤال من المصفوفة الثابتة
    answer_hash TEXT NOT NULL,             -- إجابة المستخدم (مشفرة لحمايتها)
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
-- ============================
-- 2) الأعضاء (Board / Assembly)
-- ============================
CREATE TABLE IF NOT EXISTS members (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name       TEXT NOT NULL,
    member_type     TEXT NOT NULL CHECK (member_type IN ('Board','Assembly')),
    organization    TEXT,
    start_date      TEXT NOT NULL,
    end_date        TEXT,
    status          TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active','Ended','Suspended')),
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_members_type_status ON members(member_type, status);
CREATE INDEX IF NOT EXISTS idx_members_dates ON members(start_date, end_date);

-- ============================
-- 3) الحقول الديناميكية (EAV)
-- ============================
CREATE TABLE IF NOT EXISTS dynamic_field_definitions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    field_key       TEXT NOT NULL UNIQUE,
    label_ar        TEXT NOT NULL,
    label_en        TEXT,
    field_type      TEXT NOT NULL CHECK (field_type IN ('text','number','date','boolean','choice')),
    choices_json    TEXT,
    applies_to      TEXT NOT NULL DEFAULT 'Both'
                    CHECK (applies_to IN ('Board','Assembly','Both')),
    is_required     INTEGER NOT NULL DEFAULT 0,
    display_order   INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS member_field_values (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id           INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    field_definition_id INTEGER NOT NULL REFERENCES dynamic_field_definitions(id) ON DELETE CASCADE,
    value               TEXT,
    UNIQUE(member_id, field_definition_id)
);

-- ============================
-- 4) مستندات الأعضاء
-- ============================
CREATE TABLE IF NOT EXISTS member_documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id       INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    doc_type        TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    original_name   TEXT,
    uploaded_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ============================
-- 5) اللجان
-- ============================
-- 1. جدول اللجان (تم إضافة تاريخ بداية ونهاية اللجنة نفسها)
CREATE TABLE IF NOT EXISTS committees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL CHECK (category IN ('Board','Assembly')),
    description     TEXT,
    start_date      TEXT NOT NULL,  -- تاريخ بداية الدورة أو اللجنة (صيغة YYYY-MM-DD)
    end_date        TEXT,           -- تاريخ نهاية الدورة أو اللجنة
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- 2. جدول أعضاء اللجان (تم إضافة البدل والمكافأة لكل عضو داخل اللجنة)
CREATE TABLE IF NOT EXISTS committee_members (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    committee_id    INTEGER NOT NULL REFERENCES committees(id) ON DELETE CASCADE,
    member_id       INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    role            TEXT,           -- دور العضو (رئيس، نائب، عضو...) "إضافة تنظيمية مفيدة"
    start_date      TEXT NOT NULL,  -- تاريخ انضمام العضو للجنة
    end_date        TEXT,           -- تاريخ خروج العضو أو انتهاء فترته
    
    -- الحقول المالية الخاصة بكل عضو في هذه اللجنة
    attendance_allowance REAL NOT NULL DEFAULT 0.0, -- بدل حضور الجلسة الواحدة للعضو
    bonus_amount         REAL NOT NULL DEFAULT 0.0, -- المكافأة المقطوعة أو السنوية للعضو في اللجنة
    
    UNIQUE(committee_id, member_id, start_date)
);

-- ============================
-- 6) الاجتماعات (Meetings / Committee Sessions)
-- ============================
CREATE TABLE IF NOT EXISTS meetings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    category            TEXT NOT NULL CHECK (category IN ('Board','Assembly')),
    session_type        TEXT NOT NULL CHECK (session_type IN ('Meeting','Committee')),
    committee_id        INTEGER REFERENCES committees(id),
    meeting_date        TEXT NOT NULL,
    default_allowance   REAL NOT NULL DEFAULT 0,
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_meetings_cat_date ON meetings(category, meeting_date);

-- ============================
-- 7) الحضور والصرف المالي
-- ============================
CREATE TABLE IF NOT EXISTS attendance_financials (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    member_id       INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    attended        INTEGER NOT NULL DEFAULT 0,
    amount_paid     REAL NOT NULL DEFAULT 0,
    paid_date       TEXT,
    notes           TEXT,
    UNIQUE(meeting_id, member_id)
);

-- ============================
-- 8) سجل التدقيق
-- ============================
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    action          TEXT NOT NULL,
    entity          TEXT NOT NULL,
    entity_id       INTEGER,
    details_json    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
