# -*- coding: utf-8 -*-
"""
meetings_screen.py
شاشة الاجتماعات والحضور المطورة - Premium Meetings & Attendance Screen
تم التخلص من التقسيم الثنائي واستخدام النوافذ المنبثقة (Dialogs) لإنشاء الجلسات الجديدة
للحصول على واجهة مستخدم فائقة النقاء والتركيز البصري.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QDateEdit,
    QLineEdit, QDoubleSpinBox, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QCheckBox, QMessageBox, QDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config import MEMBER_TYPES, MEMBER_TYPE_LABELS_AR, SESSION_TYPES


# ==============================================================================
# 1. نافذة منبثقة ذكية لإنشاء جلسة جديدة
# ==============================================================================
class CreateMeetingDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("إنشاء جلسة جديدة")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(400, 320)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # فورم البيانات
        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: اجتماع مجلس الإدارة الأول لعام 2026")
        self.name_input.setMinimumHeight(35)

        self.category_input = QComboBox()
        self.category_input.setMinimumHeight(35)
        for t in MEMBER_TYPES:
            self.category_input.addItem(MEMBER_TYPE_LABELS_AR[t], t)

        self.session_type_input = QComboBox()
        self.session_type_input.setMinimumHeight(35)
        self.session_type_input.addItems(SESSION_TYPES)

        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setMinimumHeight(35)
        self.date_input.setDate(QDate.currentDate())

        self.allowance_input = QDoubleSpinBox()
        self.allowance_input.setMinimumHeight(35)
        self.allowance_input.setMaximum(1_000_000)
        self.allowance_input.setDecimals(2)
        self.allowance_input.setValue(0.0)

        form.addRow("اسم الجلسة:", self.name_input)
        form.addRow("الفئة:", self.category_input)
        form.addRow("نوع الجلسة:", self.session_type_input)
        form.addRow("التاريخ:", self.date_input)
        form.addRow("البدل الافتراضي:", self.allowance_input)
        layout.addLayout(form)

        # أزرار الحفظ والإلغاء
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        save_btn = QPushButton("إنشاء الجلسة")
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
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم الجلسة.")
            return
        self.accept()


# ==============================================================================
# 2. الشاشة الرئيسية للاجتماعات والحضور
# ==============================================================================
class MeetingsScreen(QWidget):
    def __init__(self, meeting_service, committee_service):
        super().__init__()
        self.meeting_service = meeting_service
        self.committee_service = committee_service
        self.current_meeting_id = None
        self._row_member_ids = []

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh_meetings_list()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # ---------- الهيدر العلوي ----------
        header_layout = QHBoxLayout()

        title_label = QLabel("سجل الجلسات والاجتماعات")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f5f6fa;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # زر إنشاء جلسة جديدة بداخل نافذة منبثقة
        add_meeting_btn = QPushButton("+ إنشاء جلسة جديدة")
        add_meeting_btn.setMinimumHeight(38)
        add_meeting_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
            }
            QPushButton:hover { background-color: #219653; }
        """)
        add_meeting_btn.clicked.connect(self._open_create_meeting_dialog)
        header_layout.addWidget(add_meeting_btn)

        main_layout.addLayout(header_layout)

        # ---------- جدول الجلسات الرئيسي (كامل المساحة) ----------
        self.meetings_table = QTableWidget()
        self.meetings_table.setColumnCount(5)
        self.meetings_table.setHorizontalHeaderLabels(["تاريخ الجلسة", "اسم الجلسة", "الفئة", "نوع الجلسة", "البدل الافتراضي"])
        self.meetings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.meetings_table.setAlternatingRowColors(True)
        self.meetings_table.setStyleSheet(self._get_table_stylesheet())
        self.meetings_table.itemSelectionChanged.connect(self._on_meeting_selection_changed)
        main_layout.addWidget(self.meetings_table, 3)

        # ---------- هيدر الحضور السفلي ----------
        attendance_header_layout = QHBoxLayout()

        self.attendance_title_label = QLabel("تشيك ليست الحضور (اختر جلسة من الجدول أعلاه)")
        self.attendance_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00a8ff; margin-top: 10px;")
        attendance_header_layout.addWidget(self.attendance_title_label)

        attendance_header_layout.addStretch()

        # زر حفظ الحضور والمبالغ
        self.save_attendance_btn = QPushButton("حفظ الحضور والمبالغ")
        self.save_attendance_btn.setMinimumHeight(35)
        self.save_attendance_btn.setEnabled(False) # لا ينشط إلا عند تحديد جلسة
        self.save_attendance_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
            }
            QPushButton:hover { background-color: #0097e6; }
            QPushButton:disabled { background-color: #718093; color: #dcdde1; }
        """)
        self.save_attendance_btn.clicked.connect(self._save_attendance)
        attendance_header_layout.addWidget(self.save_attendance_btn)

        main_layout.addLayout(attendance_header_layout)

        # ---------- جدول تفاصيل وتحضير الحضور ----------
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["العضو الكريـم", "حضور / غياب", "المبلغ المستحق (البدل)", "ملاحظات"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.attendance_table.setAlternatingRowColors(True)
        self.attendance_table.setStyleSheet(self._get_table_stylesheet())
        main_layout.addWidget(self.attendance_table, 3)

    # ------------------------------------------------------------- تنسيقات مخصصة للجداول
    def _get_table_stylesheet(self):
        return """
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
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #353b48;
                color: #00a8ff;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #1e272e;
                color: #f5f6fa;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #718093;
            }
        """

    # ------------------------------------------------------------- منطق العمليات
    def refresh(self):
        self.refresh_meetings_list()
        self.attendance_table.setRowCount(0)
        self.save_attendance_btn.setEnabled(False)
        self.attendance_title_label.setText("تشيك ليست الحضور (اختر جلسة من الجدول أعلاه)")
        self.current_meeting_id = None

    def refresh_meetings_list(self):
        self.meetings_table.setRowCount(0)
        meetings = self.meeting_service.list_meetings()

        for row_idx, m in enumerate(meetings):
            self.meetings_table.insertRow(row_idx)
            self.meetings_table.setRowHeight(row_idx, 45)

            # 1. التاريخ
            date_item = QTableWidgetItem(m["meeting_date"])
            date_item.setData(Qt.ItemDataRole.UserRole, m["id"]) # تخزين آيدي الجلسة في الحقل الأول
            self.meetings_table.setItem(row_idx, 0, date_item)

            # 2. الاسم
            self.meetings_table.setItem(row_idx, 1, QTableWidgetItem(m["name"]))

            # 3. الفئة
            self.meetings_table.setItem(row_idx, 2, QTableWidgetItem(MEMBER_TYPE_LABELS_AR[m["category"]]))

            # 4. نوع الجلسة
            self.meetings_table.setItem(row_idx, 3, QTableWidgetItem(m["session_type"]))

            # 5. البدل الافتراضي
            self.meetings_table.setItem(row_idx, 4, QTableWidgetItem(f"{float(m['default_allowance'] or 0):,.2f}"))

    def _on_meeting_selection_changed(self):
        selected_ranges = self.meetings_table.selectedRanges()
        if not selected_ranges:
            return

        row = selected_ranges[0].topRow()
        date_item = self.meetings_table.item(row, 0)
        name_item = self.meetings_table.item(row, 1)
        if date_item and name_item:
            self.current_meeting_id = date_item.data(Qt.ItemDataRole.UserRole)
            self.attendance_title_label.setText(f"تحضير جلسة: {name_item.text()} ({date_item.text()})")
            self.save_attendance_btn.setEnabled(True)
            self._load_attendance_checklist()

    def _load_attendance_checklist(self):
        self.attendance_table.setRowCount(0)
        if not self.current_meeting_id:
            return

        eligible = self.meeting_service.get_eligible_members_for_meeting(self.current_meeting_id)
        self.attendance_table.setRowCount(len(eligible))
        self._row_member_ids = []

        for row, member in enumerate(eligible):
            self.attendance_table.setRowHeight(row, 45)
            self._row_member_ids.append(member["id"])

            # العضو
            name_item = QTableWidgetItem(member["full_name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.attendance_table.setItem(row, 0, name_item)

            # تشيك بوكس الحضور
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(0, 0, 0, 0)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            attended_checkbox = QCheckBox()
            attended_checkbox.setChecked(bool(member.get("attended", 0)))
            check_layout.addWidget(attended_checkbox)
            check_widget.setLayout(check_layout)
            self.attendance_table.setCellWidget(row, 1, check_widget)

            # البدل المستحق
            amount_spin = QDoubleSpinBox()
            amount_spin.setMinimumHeight(32)
            amount_spin.setMaximum(1_000_000)
            amount_spin.setDecimals(2)
            amount_spin.setValue(float(member.get("amount_paid", 0) or 0))
            self.attendance_table.setCellWidget(row, 2, amount_spin)

            # ملاحظات
            notes_item = QTableWidgetItem(member.get("notes") or "")
            self.attendance_table.setItem(row, 3, notes_item)

    # ------------------------------------------------------------- الإجراءات والربط
    def _open_create_meeting_dialog(self):
        dialog = CreateMeetingDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_input.text().strip()
            category = dialog.category_input.currentData()
            session_type = dialog.session_type_input.currentText()
            meeting_date = dialog.date_input.date().toString("yyyy-MM-dd")
            allowance = dialog.allowance_input.value()

            self.meeting_service.create_meeting(
                name=name, category=category, session_type=session_type,
                meeting_date=meeting_date, default_allowance=allowance,
            )
            self.refresh()
            QMessageBox.information(self, "تم", "تم إنشاء الجلسة بنجاح.")

    def _save_attendance(self):
        if not self.current_meeting_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار جلسة أولاً.")
            return

        rows = []
        for row, member_id in enumerate(self._row_member_ids):
            # استخراج حالة التشيك بوكس من الحاوية الخاصة به
            check_widget = self.attendance_table.cellWidget(row, 1)
            attended = False
            if check_widget:
                checkbox = check_widget.findChild(QCheckBox)
                if checkbox:
                    attended = checkbox.isChecked()

            amount_spin = self.attendance_table.cellWidget(row, 2)
            notes_item = self.attendance_table.item(row, 3)

            rows.append({
                "member_id": member_id,
                "attended": attended,
                "amount_paid": amount_spin.value() if amount_spin else 0.0,
                "notes": notes_item.text() if notes_item else "",
            })

        try:
            self.meeting_service.bulk_save_attendance(self.current_meeting_id, rows)
            QMessageBox.information(self, "تم", "تم حفظ بيانات الحضور والمبالغ بنجاح.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدثت مشكلة أثناء الحفظ: {e}")