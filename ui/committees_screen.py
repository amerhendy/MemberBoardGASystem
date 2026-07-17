# -*- coding: utf-8 -*-
"""
committees_screen.py
شاشة إدارة اللجان المطورة - Premium Committees Screen
- تدعم تعديل اللجان وحالتها والتواريخ بالكامل.
- فحص أوتوماتيكي للتواريخ المنتهية.
- تعديل وإضافة الأعضاء مع البدلات والمكافآت والدور التنظيمي.
"""
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QPushButton, QLabel, QMessageBox, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config import MEMBER_TYPES, MEMBER_TYPE_LABELS_AR


# ==============================================================================
# 1. نافذة منبثقة ذكية لإضافة أو تعديل لجنة
# ==============================================================================
class CommitteeFormDialog(QDialog):
    def __init__(self, parent, committee_data=None):
        super().__init__(parent)
        self.committee_data = committee_data
        self.setWindowTitle("تعديل بيانات اللجنة" if committee_data else "إنشاء لجنة جديدة")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(450, 420)
        self._build_ui()
        if self.committee_data:
            self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: لجنة الرقابة والمطابقة")
        self.name_input.setMinimumHeight(35)

        self.category_input = QComboBox()
        self.category_input.setMinimumHeight(35)
        for t in MEMBER_TYPES:
            self.category_input.addItem(MEMBER_TYPE_LABELS_AR[t], t)

        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setMinimumHeight(35)
        self.start_date_input.setDate(QDate.currentDate())

        self.has_end_date_cb = QCheckBox("تحديد تاريخ نهاية عمل اللجنة")
        self.has_end_date_cb.toggled.connect(lambda checked: self.end_date_input.setEnabled(checked))

        self.end_date_input = QDateEdit(calendarPopup=True)
        self.end_date_input.setMinimumHeight(35)
        self.end_date_input.setDate(QDate.currentDate().addYears(1))
        self.end_date_input.setEnabled(False)

        self.active_cb = QCheckBox("اللجنة نشطة حالياً")
        self.active_cb.setChecked(True)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("اكتب وصفاً أو صلاحيات اللجنة هنا...")
        self.description_input.setMaximumHeight(70)

        form.addRow("اسم اللجنة:", self.name_input)
        form.addRow("تابعة لـ:", self.category_input)
        form.addRow("تاريخ البداية:", self.start_date_input)
        form.addRow("", self.has_end_date_cb)
        form.addRow("تاريخ النهاية:", self.end_date_input)
        form.addRow("الحالة:", self.active_cb)
        form.addRow("وصف اللجنة:", self.description_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px;")
        save_btn.clicked.connect(self._validate)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setStyleSheet("background-color: #7f8c8d; color: white; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _load_data(self):
        self.name_input.setText(self.committee_data["name"])
        idx = self.category_input.findData(self.committee_data["category"])
        self.category_input.setCurrentIndex(max(idx, 0))
        
        if self.committee_data.get("start_date"):
            self.start_date_input.setDate(QDate.fromString(self.committee_data["start_date"], "yyyy-MM-dd"))
        
        if self.committee_data.get("end_date"):
            self.has_end_date_cb.setChecked(True)
            self.end_date_input.setEnabled(True)
            self.end_date_input.setDate(QDate.fromString(self.committee_data["end_date"], "yyyy-MM-dd"))
            
        self.active_cb.setChecked(bool(self.committee_data["is_active"]))
        self.description_input.setText(self.committee_data["description"] or "")

    def _validate(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم اللجنة.")
            return
        self.accept()


# ==============================================================================
# 2. نافذة منبثقة ذكية لإضافة أو تعديل عضوية داخل لجنة مع المكافآت والبدل
# ==============================================================================
class CommitteeMemberFormDialog(QDialog):
    def __init__(self, parent, members_list, member_data=None):
        super().__init__(parent)
        self.members_list = members_list
        self.member_data = member_data
        self.setWindowTitle("تعديل بيانات العضو باللجنة" if member_data else "إضافة عضو جديد للجنة")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(450, 420)
        self._build_ui()
        if self.member_data:
            self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.member_combo = QComboBox()
        self.member_combo.setMinimumHeight(35)
        if self.member_data:
            # في حال التعديل، نعرض اسم العضو الحالي فقط ولا نسمح بتغييره
            self.member_combo.addItem(self.member_data["full_name"], self.member_data["member_real_id"])
            self.member_combo.setEnabled(False)
        else:
            for m in self.members_list:
                self.member_combo.addItem(m["full_name"], m["id"])

        self.role_input = QComboBox()
        self.role_input.setMinimumHeight(35)
        self.role_input.addItems(["عضو لجنة", "رئيس اللجنة", "نائب رئيس اللجنة", "أمين السر"])

        self.allowance_input = QDoubleSpinBox()
        self.allowance_input.setMinimumHeight(35)
        self.allowance_input.setRange(0, 1000000)
        self.allowance_input.setSuffix(" ج.م")

        self.bonus_input = QDoubleSpinBox()
        self.bonus_input.setMinimumHeight(35)
        self.bonus_input.setRange(0, 1000000)
        self.bonus_input.setSuffix(" ج.م")

        self.start_date_input = QDateEdit(calendarPopup=True)
        self.start_date_input.setMinimumHeight(35)
        self.start_date_input.setDate(QDate.currentDate())

        self.has_end_date_cb = QCheckBox("تحديد تاريخ نهاية العضوية")
        self.has_end_date_cb.toggled.connect(lambda checked: self.end_date_input.setEnabled(checked))

        self.end_date_input = QDateEdit(calendarPopup=True)
        self.end_date_input.setMinimumHeight(35)
        self.end_date_input.setDate(QDate.currentDate().addYears(1))
        self.end_date_input.setEnabled(False)

        form.addRow("العضو:", self.member_combo)
        form.addRow("الدور باللجنة:", self.role_input)
        form.addRow("بدل الحضور للجلسة:", self.allowance_input)
        form.addRow("المكافأة المخصصة للجنة:", self.bonus_input)
        form.addRow("تاريخ بداية العضوية:", self.start_date_input)
        form.addRow("", self.has_end_date_cb)
        form.addRow("تاريخ نهاية العضوية:", self.end_date_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        save_btn = QPushButton("حفظ البيانات")
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; border-radius: 4px;")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setStyleSheet("background-color: #7f8c8d; color: white; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _load_data(self):
        self.role_input.setCurrentText(self.member_data.get("role") or "عضو لجنة")
        self.allowance_input.setValue(float(self.member_data.get("attendance_allowance") or 0.0))
        self.bonus_input.setValue(float(self.member_data.get("bonus_amount") or 0.0))
        
        if self.member_data.get("start_date"):
            self.start_date_input.setDate(QDate.fromString(self.member_data["start_date"], "yyyy-MM-dd"))
            
        if self.member_data.get("end_date"):
            self.has_end_date_cb.setChecked(True)
            self.end_date_input.setEnabled(True)
            self.end_date_input.setDate(QDate.fromString(self.member_data["end_date"], "yyyy-MM-dd"))


# ==============================================================================
# 3. الشاشة الرئيسية الكبرى لإدارة اللجان
# ==============================================================================
class CommitteesScreen(QWidget):
    def __init__(self, committee_service, member_service):
        super().__init__()
        self.committee_service = committee_service
        self.member_service = member_service
        self.current_committee_id = None
        self.current_committee_category = None

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # الهيدر العلوي
        header = QHBoxLayout()
        title = QLabel("منظومة إدارة اللجان والمجالس الذكية")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f5f6fa;")
        header.addWidget(title)
        header.addStretch()

        self.category_filter = QComboBox()
        self.category_filter.setMinimumHeight(38)
        self.category_filter.setMinimumWidth(150)
        self.category_filter.addItem("جميع فئات المجالس", None)
        for t in MEMBER_TYPES:
            self.category_filter.addItem(MEMBER_TYPE_LABELS_AR[t], t)
        self.category_filter.currentIndexChanged.connect(self.refresh_committees_list)
        header.addWidget(self.category_filter)

        add_committee_btn = QPushButton("+ إنشاء لجنة جديدة")
        add_committee_btn.setMinimumHeight(38)
        add_committee_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 6px; padding: 0 15px;")
        add_committee_btn.clicked.connect(self._open_create_committee_dialog)
        header.addWidget(add_committee_btn)
        main_layout.addLayout(header)

        # جدول اللجان الرئيسي
        self.committees_table = QTableWidget()
        self.committees_table.setColumnCount(6)
        self.committees_table.setHorizontalHeaderLabels(["اسم اللجنة", "الفئة", "البداية", "النهاية", "الحالة", "الإجراءات"])
        self.committees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.committees_table.setAlternatingRowColors(True)
        self.committees_table.setStyleSheet(self._get_table_stylesheet())
        self.committees_table.itemSelectionChanged.connect(self._on_committee_selection_changed)
        main_layout.addWidget(self.committees_table, 3)

        # قسم أعضاء اللجنة المحددة
        member_header = QHBoxLayout()
        self.committee_title_label = QLabel("أعضاء اللجنة المحددة (اختر لجنة من الجدول للتحكم)")
        self.committee_title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00a8ff; margin-top: 10px;")
        member_header.addWidget(self.committee_title_label)
        member_header.addStretch()

        self.add_member_btn = QPushButton("+ إضافة عضو للجنة")
        self.add_member_btn.setMinimumHeight(35)
        self.add_member_btn.setEnabled(False)
        self.add_member_btn.setStyleSheet("background-color: #00a8ff; color: white; font-weight: bold; border-radius: 6px; padding: 0 15px;")
        self.add_member_btn.clicked.connect(self._open_add_member_dialog)
        member_header.addWidget(self.add_member_btn)
        main_layout.addLayout(member_header)

        # جدول أعضاء اللجنة المطور ماليًا وتفصيليًا
        self.members_table = QTableWidget()
        self.members_table.setColumnCount(6)
        self.members_table.setHorizontalHeaderLabels(["اسم العضو الكامل", "الدور باللجنة", "البدل المالي", "المكافأة", "الفترة", "التحكم"])
        self.members_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.members_table.setAlternatingRowColors(True)
        self.members_table.setStyleSheet(self._get_table_stylesheet())
        main_layout.addWidget(self.members_table, 2)

    def _get_table_stylesheet(self):
        return """
            QTableWidget { background-color: #2f3640; alternate-background-color: #1e272e; color: #f5f6fa; gridline-color: #718093; border: 1px solid #718093; border-radius: 8px; }
            QTableWidget::item { color: #f5f6fa; padding: 6px; }
            QTableWidget::item:selected { background-color: #353b48; color: #00a8ff; font-weight: bold; }
            QHeaderView::section { background-color: #1e272e; color: #f5f6fa; font-weight: bold; padding: 6px; border: 1px solid #718093; }
        """

    def refresh(self):
        self.refresh_committees_list()
        self.members_table.setRowCount(0)
        self.add_member_btn.setEnabled(False)
        self.committee_title_label.setText("أعضاء اللجنة المحددة (اختر لجنة من الجدول للتحكم)")
        self.current_committee_id = None

    def refresh_committees_list(self):
        self.committees_table.setRowCount(0)
        category = self.category_filter.currentData()
        committees = self.committee_service.list_committees(category=category)

        for row, c in enumerate(committees):
            self.committees_table.insertRow(row)
            self.committees_table.setRowHeight(row, 45)

            name_item = QTableWidgetItem(c["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, c) 
            self.committees_table.setItem(row, 0, name_item)
            
            self.committees_table.setItem(row, 1, QTableWidgetItem(MEMBER_TYPE_LABELS_AR[c["category"]]))
            self.committees_table.setItem(row, 2, QTableWidgetItem(c["start_date"]))
            self.committees_table.setItem(row, 3, QTableWidgetItem(c["end_date"] or "مفتوح"))

            # حقل الحالة الملونة
            status_text = "نشطة" if c["is_active"] == 1 else "معطلة"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#2ecc71" if c["is_active"] == 1 else "#e74c3c"))
            self.committees_table.setItem(row, 4, status_item)

            # أزرار الإجراءات
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(10)

            edit_btn = QPushButton("تعديل ✏️")
            edit_btn.setStyleSheet("color: #f39c12; font-weight: bold; background: transparent; border: 1px solid #f39c12; border-radius: 4px; padding: 2px 6px;")
            edit_btn.clicked.connect(lambda checked, comm=c: self._open_edit_committee_dialog(comm))
            actions_layout.addWidget(edit_btn)

            toggle_btn = QPushButton("تعطيل ❌" if c["is_active"] == 1 else "تنشيط  ")
            toggle_btn.setStyleSheet(f"color: {'#e74c3c' if c['is_active'] == 1 else '#2ecc71'}; font-weight: bold; background: transparent; border: 1px solid {'#e74c3c' if c['is_active'] == 1 else '#2ecc71'}; border-radius: 4px; padding: 2px 6px;")
            toggle_btn.clicked.connect(lambda checked, c_id=c["id"], curr=c["is_active"]: self._toggle_status(c_id, curr))
            actions_layout.addWidget(toggle_btn)

            widget = QWidget()
            widget.setLayout(actions_layout)
            self.committees_table.setCellWidget(row, 5, widget)

    def _on_committee_selection_changed(self):
        selected = self.committees_table.selectedRanges()
        if not selected: return
        row = selected[0].topRow()
        name_item = self.committees_table.item(row, 0)
        if name_item:
            c_data = name_item.data(Qt.ItemDataRole.UserRole)
            self.current_committee_id = c_data["id"]
            self.current_committee_category = c_data["category"]
            self.committee_title_label.setText(f"أعضاء لجنة: {c_data['name']}")
            self.add_member_btn.setEnabled(True)
            self._load_committee_members()

    def _load_committee_members(self):
        self.members_table.setRowCount(0)
        if not self.current_committee_id: return

        members = self.committee_service.list_committee_members(self.current_committee_id)
        for row, m in enumerate(members):
            self.members_table.insertRow(row)
            self.members_table.setRowHeight(row, 45)

            self.members_table.setItem(row, 0, QTableWidgetItem(m["full_name"]))
            self.members_table.setItem(row, 1, QTableWidgetItem(m["role"] or "عضو لجنة"))
            self.members_table.setItem(row, 2, QTableWidgetItem(f"{m['attendance_allowance']} [ج.م]"))
            self.members_table.setItem(row, 3, QTableWidgetItem(f"{m['bonus_amount']} ج.م"))
            
            period = f"من {m['start_date']} إلى {m['end_date'] or 'الآن'}"
            self.members_table.setItem(row, 4, QTableWidgetItem(period))

            # لوحة التحكم في العضوية
            act_layout = QHBoxLayout()
            act_layout.setContentsMargins(2, 2, 2, 2)
            
            m_edit_btn = QPushButton("✏️")
            m_edit_btn.setToolTip("تعديل العضوية والماليات")
            m_edit_btn.setStyleSheet("color: #f39c12; background: transparent; font-size: 14px; border: none;")
            m_edit_btn.clicked.connect(lambda checked, member=m: self._open_edit_member_dialog(member))
            act_layout.addWidget(m_edit_btn)

            m_del_btn = QPushButton("🗑️")
            m_del_btn.setToolTip("إزالة العضو من اللجنة")
            m_del_btn.setStyleSheet("color: #e74c3c; background: transparent; font-size: 14px; border: none;")
            m_del_btn.clicked.connect(lambda checked, cm_id=m["committee_member_id"]: self._remove_member(cm_id))
            act_layout.addWidget(m_del_btn)

            w = QWidget()
            w.setLayout(act_layout)
            self.members_table.setCellWidget(row, 5, w)

    def _open_create_committee_dialog(self):
        dialog = CommitteeFormDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.committee_service.create_committee(
                name=dialog.name_input.text().strip(),
                category=dialog.category_input.currentData(),
                start_date=dialog.start_date_input.date().toString("yyyy-MM-dd"),
                end_date=dialog.end_date_input.date().toString("yyyy-MM-dd") if dialog.has_end_date_cb.isChecked() else None,
                description=dialog.description_input.toPlainText().strip(),
                is_active=1 if dialog.active_cb.isChecked() else 0
            )
            self.refresh()
            QMessageBox.information(self, "تم", "تم إنشاء اللجنة بنجاح.")

    def _open_edit_committee_dialog(self, comm_data):
        dialog = CommitteeFormDialog(self, comm_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.committee_service.update_committee(
                committee_id=comm_data["id"],
                name=dialog.name_input.text().strip(),
                category=dialog.category_input.currentData(),
                start_date=dialog.start_date_input.date().toString("yyyy-MM-dd"),
                end_date=dialog.end_date_input.date().toString("yyyy-MM-dd") if dialog.has_end_date_cb.isChecked() else None,
                description=dialog.description_input.toPlainText().strip(),
                is_active=1 if dialog.active_cb.isChecked() else 0
            )
            self.refresh()
            QMessageBox.information(self, "تم", "تم تحديث بيانات اللجنة وحالتها أوتوماتيكياً بنجاح.")

    def _toggle_status(self, committee_id, current_status):
        self.committee_service.toggle_committee_status(committee_id, current_status)
        self.refresh()

    def _open_add_member_dialog(self):
        if not self.current_committee_id: return
        available_members = self.member_service.list_members(member_type=self.current_committee_category, status="Active")
        if not available_members:
            QMessageBox.warning(self, "تنبيه", "لا يوجد أعضاء نشطون متاحون للإضافة لهذه الفئة.")
            return

        dialog = CommitteeMemberFormDialog(self, available_members)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.committee_service.add_member_to_committee(
                committee_id=self.current_committee_id,
                member_id=dialog.member_combo.currentData(),
                start_date=dialog.start_date_input.date().toString("yyyy-MM-dd"),
                end_date=dialog.end_date_input.date().toString("yyyy-MM-dd") if dialog.has_end_date_cb.isChecked() else None,
                role=dialog.role_input.currentText(),
                allowance=dialog.allowance_input.value(),
                bonus=dialog.bonus_input.value()
            )
            self._load_committee_members()
            QMessageBox.information(self, "تم", "تم إضافة العضو وتحديد البدلات والمكافآت الخاصة به.")

    def _open_edit_member_dialog(self, member_data):
        dialog = CommitteeMemberFormDialog(self, [], member_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.committee_service.update_committee_membership(
                cm_id=member_data["committee_member_id"],
                start_date=dialog.start_date_input.date().toString("yyyy-MM-dd"),
                end_date=dialog.end_date_input.date().toString("yyyy-MM-dd") if dialog.has_end_date_cb.isChecked() else None,
                role=dialog.role_input.currentText(),
                allowance=dialog.allowance_input.value(),
                bonus=dialog.bonus_input.value()
            )
            self._load_committee_members()
            QMessageBox.information(self, "تم", "تم تحديث البدلات والتواريخ بنجاح.")

    def _remove_member(self, cm_id):
        confirm = QMessageBox.question(self, "تأكيد الإزالة", "هل أنت متأكد من إزالة هذا العضو من اللجنة؟")
        if confirm == QMessageBox.StandardButton.Yes:
            self.committee_service.remove_member_from_committee(cm_id)
            self._load_committee_members()