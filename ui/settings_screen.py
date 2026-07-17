# -*- coding: utf-8 -*-
"""
settings_screen.py
شاشة الإعدادات المطورة - Premium Settings Screen
إدارة الحقول الديناميكية بمفهوم UX الحديث عبر جدول فخم وفورم منبثق ذكي.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QCheckBox,
    QLabel, QDialog, QHeaderView, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from config import MEMBER_TYPES, MEMBER_TYPE_LABELS_AR

# أنواع الحقول وترجمتها العربية
FIELD_TYPES = ["text", "number", "date", "boolean", "choice"]
FIELD_TYPE_LABELS_AR = {
    "text": "نص", "number": "رقم", "date": "تاريخ", "boolean": "نعم/لا", "choice": "قائمة اختيار",
}


class FieldFormDialog(QDialog):
    """نافذة منبثقة ذكية لإضافة حقل ديناميكي جديد"""
    def __init__(self, parent, dynamic_fields_service):
        super().__init__(parent)
        self.dynamic_fields_service = dynamic_fields_service
        
        self.setWindowTitle("إضافة حقل جديد")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(380, 340)
        
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # فورم الإدخال
        form = QFormLayout()
        form.setSpacing(10)

        self.field_key_input = QLineEdit()
        self.field_key_input.setPlaceholderText("مثال: national_id")
        self.field_key_input.setMinimumHeight(35)

        self.label_ar_input = QLineEdit()
        self.label_ar_input.setPlaceholderText("مثال: الرقم القومي")
        self.label_ar_input.setMinimumHeight(35)

        self.label_en_input = QLineEdit()
        self.label_en_input.setPlaceholderText("National ID (اختياري)")
        self.label_en_input.setMinimumHeight(35)

        self.field_type_input = QComboBox()
        self.field_type_input.setMinimumHeight(35)
        for ft in FIELD_TYPES:
            self.field_type_input.addItem(FIELD_TYPE_LABELS_AR[ft], ft)

        self.applies_to_input = QComboBox()
        self.applies_to_input.setMinimumHeight(35)
        self.applies_to_input.addItem("كلاهما", "Both")
        for t in MEMBER_TYPES:
            self.applies_to_input.addItem(MEMBER_TYPE_LABELS_AR[t], t)

        self.required_checkbox = QCheckBox("حقل إلزامي")
        self.required_checkbox.setStyleSheet("font-size: 13px;")

        form.addRow("المفتاح (بالإنجليزية):", self.field_key_input)
        form.addRow("العنوان بالعربية:", self.label_ar_input)
        form.addRow("العنوان بالإنجليزية:", self.label_en_input)
        form.addRow("نوع الحقل:", self.field_type_input)
        form.addRow("ينطبق على:", self.applies_to_input)
        form.addRow("", self.required_checkbox)
        layout.addLayout(form)

        # أزرار الحفظ والإلغاء
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        save_btn = QPushButton("إضافة الحقل")
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #219653; }
        """)
        save_btn.clicked.connect(self._validate_and_accept)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #95a5a6; }
        """)
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def _validate_and_accept(self):
        field_key = self.field_key_input.text().strip()
        label_ar = self.label_ar_input.text().strip()

        if not field_key or not label_ar:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال المفتاح والعنوان بالعربية على الأقل.")
            return

        self.accept()


class SettingsScreen(QWidget):
    """شاشة الإعدادات الأساسية التي تعرض الحقول في جدول فخم وتحتوي على زر الإضافة"""
    def __init__(self, dynamic_fields_service):
        super().__init__()
        self.dynamic_fields_service = dynamic_fields_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh_fields_list()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # ---------- الهيدر العلوي مع زر إضافة حقل جديد ----------
        header_layout = QHBoxLayout()

        title_label = QLabel("إعدادات الحقول الديناميكية للأعضاء")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f5f6fa;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        add_field_btn = QPushButton("+ إضافة حقل جديد")
        add_field_btn.setMinimumHeight(38)
        add_field_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #0097e6;
            }
        """)
        add_field_btn.clicked.connect(self._open_add_field_dialog)
        header_layout.addWidget(add_field_btn)
        main_layout.addLayout(header_layout)

        # ---------- جدول الحقول الفخم ----------
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["العنوان بالعربية", "المفتاح (البرمجي)", "النوع", "ينطبق على", "إلزامي", "الإجراءات"])
        # حل مشكلة PyQt6 بخصوص الـ SectionResizeMode
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2f3640;
                alternate-background-color: #1e272e;
                color: #f5f6fa;
                gridline-color: #718093;
                border: 1px solid #718093;
                border-radius: 8px;
            }
            QTableWidget::item {
                background-color: transparent;
                color: #f5f6fa;
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #00a8ff;
                color: white;
            }
            QHeaderView::section {
                background-color: #1e272e;
                color: #f5f6fa;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #718093;
            }
        """)
        main_layout.addWidget(self.table)

    def refresh_fields_list(self):
        self.table.setRowCount(0)
        fields = self.dynamic_fields_service.list_fields(active_only=True)

        for row_idx, field in enumerate(fields):
            self.table.insertRow(row_idx)

            # ضبط ارتفاع الصف لمنع قص الأزرار عمودياً (تم الحفاظ عليه بمقاس 45 بكسل مريح وفخم)
            self.table.setRowHeight(row_idx, 45)

            # 1. العنوان بالعربية
            self.table.setItem(row_idx, 0, QTableWidgetItem(field["label_ar"]))

            # 2. المفتاح البرمجي
            self.table.setItem(row_idx, 1, QTableWidgetItem(field["field_key"]))

            # 3. نوع الحقل (مترجم)
            type_label = FIELD_TYPE_LABELS_AR.get(field["field_type"], field["field_type"])
            self.table.setItem(row_idx, 2, QTableWidgetItem(type_label))

            # 4. ينطبق على
            applies_label = (
                "كلاهما" if field["applies_to"] == "Both" else MEMBER_TYPE_LABELS_AR.get(field["applies_to"], field["applies_to"])
            )
            self.table.setItem(row_idx, 3, QTableWidgetItem(applies_label))

            # 5. هل الحقل إلزامي (ملون لمزيد من الفخامة البصرية)
            is_req_item = QTableWidgetItem("نعم" if field["is_required"] else "لا")
            if field["is_required"]:
                is_req_item.setForeground(QColor("#2ecc71"))  # لون أخضر للحقول الهامة
            else:
                is_req_item.setForeground(QColor("#7f8c8d"))  # لون رمادي للحقول الاختيارية
            self.table.setItem(row_idx, 4, is_req_item)

            # 6. زر "تعطيل الحقل" متناسق ومنظم جداً ومحمي من الاختفاء
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(10, 2, 10, 2)
            actions_layout.setSpacing(8)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            deactivate_btn = QPushButton("تعطيل الحقل")
            deactivate_btn.setFixedSize(100, 28)  # حجم ثابت لمنع المطه والإنضغاط
            deactivate_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #e74c3c !important;
                    font-weight: bold;
                    font-size: 11px;
                    border: 1px solid #e74c3c;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e74c3c;
                    color: #ffffff !important;
                }
            """)
            # ربط الحدث البرمجي بتعطيل الحقل
            deactivate_btn.clicked.connect(lambda checked, f_id=field["id"]: self._deactivate_field(f_id))
            actions_layout.addWidget(deactivate_btn)

            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            actions_widget.setStyleSheet("background-color: transparent;")
            
            self.table.setCellWidget(row_idx, 5, actions_widget)

    # ------------------------------------------------------------- العمليات المنطقية
    def _open_add_field_dialog(self):
        dialog = FieldFormDialog(self, self.dynamic_fields_service)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.dynamic_fields_service.create_field(
                    field_key=dialog.field_key_input.text().strip(),
                    label_ar=dialog.label_ar_input.text().strip(),
                    label_en=dialog.label_en_input.text().strip() or None,
                    field_type=dialog.field_type_input.currentData(),
                    applies_to=dialog.applies_to_input.currentData(),
                    is_required=dialog.required_checkbox.isChecked(),
                )
                QMessageBox.information(self, "تم", "تمت إضافة الحقل بنجاح.")
                self.refresh_fields_list()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذّر إضافة الحقل (قد يكون المفتاح مكررًا): {e}")

    def _deactivate_field(self, field_id):
        confirm = QMessageBox.question(self, "تأكيد التعطيل", "هل أنت متأكد من تعطيل هذا الحقل؟")
        if confirm == QMessageBox.StandardButton.Yes:
            self.dynamic_fields_service.deactivate_field(field_id)
            self.refresh_fields_list()