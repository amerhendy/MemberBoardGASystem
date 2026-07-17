# -*- coding: utf-8 -*-
"""
dynamic_fields_service.py
خدمة الحقول الديناميكية - Dynamic Fields Service (EAV)
تسمح بإضافة/تعطيل حقول مخصصة (National ID, IBAN, ...) من شاشة الإعدادات
دون تعديل بنية قاعدة البيانات، وتخزين/قراءة قيمها لكل عضو.
"""
import json


class DynamicFieldsService:
    def __init__(self, db):
        self.db = db

    # ---------- تعريف الحقول ----------
    def create_field(self, field_key, label_ar, field_type, applies_to="Both",
                      label_en=None, choices=None, is_required=False, display_order=0):
        choices_json = json.dumps(choices, ensure_ascii=False) if choices else None
        return self.db.execute(
            """INSERT INTO dynamic_field_definitions
               (field_key, label_ar, label_en, field_type, choices_json,
                applies_to, is_required, display_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (field_key, label_ar, label_en, field_type, choices_json,
             applies_to, int(is_required), display_order),
            commit=True,
        )

    def list_fields(self, applies_to=None, active_only=True):
        query = "SELECT * FROM dynamic_field_definitions WHERE 1=1"
        params = []
        if active_only:
            query += " AND is_active = 1"
        if applies_to:
            query += " AND (applies_to = ? OR applies_to = 'Both')"
            params.append(applies_to)
        query += " ORDER BY display_order, id"
        rows = self.db.execute(query, params, fetchall=True)
        result = []
        for r in rows:
            d = dict(r)
            d["choices"] = json.loads(d["choices_json"]) if d.get("choices_json") else None
            result.append(d)
        return result

    def deactivate_field(self, field_id):
        self.db.execute(
            "UPDATE dynamic_field_definitions SET is_active = 0 WHERE id = ?",
            (field_id,), commit=True,
        )

    # ---------- قيم الحقول لكل عضو ----------
    def set_member_value(self, member_id, field_definition_id, value):
        self.db.execute(
            """INSERT INTO member_field_values (member_id, field_definition_id, value)
               VALUES (?, ?, ?)
               ON CONFLICT(member_id, field_definition_id) DO UPDATE SET value = excluded.value""",
            (member_id, field_definition_id, value), commit=True,
        )

    def get_member_values(self, member_id, applies_to=None):
        query = """SELECT d.id as field_id, d.field_key, d.label_ar, d.label_en,
                          d.field_type, d.choices_json, d.is_required, v.value
                   FROM dynamic_field_definitions d
                   LEFT JOIN member_field_values v
                     ON v.field_definition_id = d.id AND v.member_id = ?
                   WHERE d.is_active = 1"""
        params = [member_id]
        if applies_to:
            query += " AND (d.applies_to = ? OR d.applies_to = 'Both')"
            params.append(applies_to)
        query += " ORDER BY d.display_order"
        rows = self.db.execute(query, params, fetchall=True)
        result = []
        for r in rows:
            d = dict(r)
            d["choices"] = json.loads(d["choices_json"]) if d.get("choices_json") else None
            result.append(d)
        return result
