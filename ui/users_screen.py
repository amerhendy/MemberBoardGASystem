# -*- coding: utf-8 -*-
"""
users_screen.py
شاشة إدارة المستخدمين الاحترافية بمفهوم UX الحديث
- تحكم صارم بالصلاحيات: Admin يرى ويعدل الكل، User يرى ويعدل نفسه فقط.
- فورم منبثق ذكي يتكيف ديناميكياً مع دور المستخدم المسجل.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QCheckBox,
    QLabel, QDialog, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QAction, QIcon
from assets import get_icon
from config import SECURITY_QUESTIONS


class UserFormDialog(QDialog):
    """نافذة منبثقة ذكية تتكيف حسب صلاحيات المستخدم لطلب التعديل أو الإضافة"""
    def __init__(self, parent, auth_service, current_user, user_data=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = current_user  # المستخدم الحالي المسجل دخوله بالنظام
        self.user_data = user_data  # بيانات المستخدم المستهدف بالتعديل
        
        self.setWindowTitle("بيانات حساب المستخدم" if user_data else "مستخدم جديد")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(420, 460)
        
        self._build_ui()
        if self.user_data:
            self._load_user_data()
            self._apply_role_restrictions() # تطبيق قيود الخصوصية فور التحميل

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم...")
        self.username_input.setMinimumHeight(35)

        self.role_input = QComboBox()
        self.role_input.setMinimumHeight(35)
        self.role_input.addItem("مستخدم عادي", "User")
        self.role_input.addItem("مدير (Admin)", "Admin")

        self.active_checkbox = QCheckBox("الحساب نشط ويُسمح له بالدخول")
        self.active_checkbox.setChecked(True)
        self.active_checkbox.setStyleSheet("font-size: 13px;")

        # حقل كلمة المرور
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("إلزامي للجديد - اتركه فارغاً عند التعديل")
        self.password_input.setMinimumHeight(35)
        
        self.show_pass_action = QAction(self)
        self.show_pass_action.setIcon(get_icon("eye_icon") if get_icon("eye_icon") else QIcon())
        self.show_pass_action.setCheckable(True)
        self.show_pass_action.toggled.connect(self._toggle_password_visibility)
        self.password_input.addAction(self.show_pass_action, QLineEdit.ActionPosition.TrailingPosition)

        # حقل تأكيد كلمة المرور
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("أعد كتابة كلمة المرور للتأكيد...")
        self.confirm_password_input.setMinimumHeight(35)
        
        self.show_confirm_pass_action = QAction(self)
        self.show_confirm_pass_action.setIcon(get_icon("eye_icon") if get_icon("eye_icon") else QIcon())
        self.show_confirm_pass_action.setCheckable(True)
        self.show_confirm_pass_action.toggled.connect(self._toggle_confirm_password_visibility)
        self.confirm_password_input.addAction(self.show_confirm_pass_action, QLineEdit.ActionPosition.TrailingPosition)
        self.confirm_password_input.textChanged.connect(self._check_passwords_match)

        # حقول أسئلة الأمان
        self.question_input = QComboBox()
        self.question_input.setMinimumHeight(35)
        for q_id, q_text in SECURITY_QUESTIONS.items():
            self.question_input.addItem(q_text, q_id)

        self.answer_input = QLineEdit()
        self.answer_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.answer_input.setPlaceholderText("أدخل إجابة السؤال السري (احفظها جيداً)...")
        self.answer_input.setMinimumHeight(35)

        self.show_answer_action = QAction(self)
        self.show_answer_action.setIcon(get_icon("eye_icon") if get_icon("eye_icon") else QIcon())
        self.show_answer_action.setCheckable(True)
        self.show_answer_action.toggled.connect(self._toggle_answer_visibility)
        self.answer_input.addAction(self.show_answer_action, QLineEdit.ActionPosition.TrailingPosition)

        form.addRow("اسم المستخدم:", self.username_input)
        form.addRow("الصلاحية:", self.role_input)
        form.addRow("", self.active_checkbox)
        form.addRow("كلمة المرور:", self.password_input)
        form.addRow("تأكيد كلمة المرور:", self.confirm_password_input)
        form.addRow("", QLabel("⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"))
        form.addRow("سؤال الأمان:", self.question_input)
        form.addRow("إجابة السؤال:", self.answer_input)
        layout.addLayout(form)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        save_btn = QPushButton("حفظ")
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border: none; border-radius: 4px;")
        save_btn.clicked.connect(self._validate_and_accept)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setStyleSheet("background-color: #7f8c8d; color: white; border: none; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def _toggle_password_visibility(self, checked):
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _toggle_confirm_password_visibility(self, checked):
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _toggle_answer_visibility(self, checked):
        self.answer_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _check_passwords_match(self):
        p1 = self.password_input.text()
        p2 = self.confirm_password_input.text()
        if not p2:
            self.confirm_password_input.setStyleSheet("")
            return
        if p1 == p2:
            self.confirm_password_input.setStyleSheet("border: 1.5px solid #2ecc71;")
        else:
            self.confirm_password_input.setStyleSheet("border: 1.5px solid #e74c3c;")

    def _load_user_data(self):
        self.username_input.setText(self.user_data["username"])
        idx = self.role_input.findData(self.user_data["role"])
        self.role_input.setCurrentIndex(max(idx, 0))
        self.active_checkbox.setChecked(bool(self.user_data["is_active"]))
        
        if "question_id" in self.user_data and self.user_data["question_id"]:
            q_idx = self.question_input.findData(self.user_data["question_id"])
            self.question_input.setCurrentIndex(max(q_idx, 0))

    def _apply_role_restrictions(self):
        """حظر الحقول التي لا يُسمح للمستخدم العادي (User) بتعديلها في حسابه الشخصي"""
        if self.current_user.get("role") != "Admin":
            # العضو العادي لا يغير صلاحيته ولا يعطل حسابه بنفسه حماية للسيستم
            self.role_input.setEnabled(False)
            self.active_checkbox.setEnabled(False)
            self.username_input.setToolTip("اسم المستخدم ثابت، تواصل مع الإدارة لتغييره")

    def _validate_and_accept(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        answer = self.answer_input.text().strip()

        if not username:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم المستخدم.")
            return

        if not self.user_data:
            if not password:
                QMessageBox.warning(self, "تنبيه", "الرجاء إدخال كلمة المرور للمستخدم الجديد.")
                return
            if not answer:
                QMessageBox.warning(self, "تنبيه", "الرجاء تعبئة إجابة سؤال الأمان لاستخدامها عند الطوارئ.")
                return

        if password or confirm_password:
            if password != confirm_password:
                QMessageBox.warning(self, "تنبيه", "كلمة المرور وتأكيدها غير متطابقين.")
                return
            if len(password) < 4:
                QMessageBox.warning(self, "تنبيه", "كلمة المرور قصيرة جدًا (4 أحرف على الأقل).")
                return

        exclude_id = self.user_data["id"] if self.user_data else None
        if self.auth_service.username_exists(username, exclude_user_id=exclude_id):
            QMessageBox.warning(self, "تنبيه", "اسم المستخدم ده مسجّل بالفعل.")
            return

        self.accept()


class UsersScreen(QWidget):
    """الشاشة الأساسية لإدارة المستخدمين بجدول فخم متكامل متوافق مع الصلاحيات"""
    def __init__(self, auth_service, current_user: dict):
        super().__init__()
        self.auth_service = auth_service
        self.current_user = current_user

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh_users_list()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        header_layout = QHBoxLayout()
        
        # تكييف اسم العنوان حسب الرول لمزيد من الاحترافية
        title_text = "إدارة مستخدمي النظام" if self.current_user.get("role") == "Admin" else "إعدادات حسابي الشخصي"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f5f6fa;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # زر إضافة مستخدم يظهر فقط للـ Admin، ويختفي تماماً للمستخدم العادي!
        self.add_user_btn = QPushButton("+ إضافة مستخدم جديد")
        self.add_user_btn.setMinimumHeight(38)
        self.add_user_btn.setStyleSheet("""
            QPushButton { background-color: #00a8ff; color: white; font-weight: bold; border: none; border-radius: 6px; padding: 0 15px; }
            QPushButton:hover { background-color: #0097e6; }
        """)
        self.add_user_btn.clicked.connect(self._open_add_user_dialog)
        
        if self.current_user.get("role") == "Admin":
            header_layout.addWidget(self.add_user_btn)
        
        main_layout.addLayout(header_layout)

        # جدول المستخدمين
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["اسم المستخدم", "الصلاحية", "الحالة", "الإجراءات"])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: #2f3640; alternate-background-color: #1e272e; color: #f5f6fa; gridline-color: #718093; border: 1px solid #718093; border-radius: 8px; }
            QTableWidget::item { background-color: transparent; color: #f5f6fa; padding: 10px; }
            QTableWidget::item:selected { background-color: #00a8ff; color: white; }
            QHeaderView::section { background-color: #1e272e; color: #f5f6fa; font-weight: bold; padding: 8px; border: 1px solid #718093; }
        """)
        main_layout.addWidget(self.table)

    def refresh_users_list(self):
        self.table.setRowCount(0)
        # نمرر الـ current_user لخدمة الفلترة المحدثة بقاعدة البيانات
        users = self.auth_service.list_users(self.current_user)

        for row_idx, u in enumerate(users):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 45)

            self.table.setItem(row_idx, 0, QTableWidgetItem(u["username"]))

            role_text = "مدير" if u["role"] == "Admin" else "مستخدم عادي"
            self.table.setItem(row_idx, 1, QTableWidgetItem(role_text))

            status_item = QTableWidgetItem("مفعّل" if u["is_active"] else "معطّل")
            if u["is_active"]:
                status_item.setForeground(QColor("#2ecc71"))
            else:
                status_item.setForeground(QColor("#7f8c8d"))
            self.table.setItem(row_idx, 2, status_item)

            # أزرار الإجراءات داخل الصف
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(10, 2, 10, 2)
            actions_layout.setSpacing(15)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setToolTip("تعديل البيانات")
            edit_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #f39c12 !important; font-size: 15px; }\nQPushButton:hover { color: #e67e22 !important; font-size: 17px; }")
            edit_btn.clicked.connect(lambda checked, user=u: self._open_edit_user_dialog(user))
            actions_layout.addWidget(edit_btn)

            # زر الحذف يظهر فقط إذا كان المستخدم أدمن وحساب الصف ليس حسابه الحالي
            if self.current_user.get("role") == "Admin":
                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(32, 28)
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.setToolTip("حذف حساب المستخدم")
                delete_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #e74c3c !important; font-size: 15px; }\nQPushButton:hover { color: #c0392b !important; font-size: 17px; }")
                delete_btn.clicked.connect(lambda checked, user_id=u["id"]: self._delete_user(user_id))
                actions_layout.addWidget(delete_btn)

            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            actions_widget.setStyleSheet("background-color: transparent;") 
            self.table.setCellWidget(row_idx, 3, actions_widget)

    def _open_add_user_dialog(self):
        dialog = UserFormDialog(self, self.auth_service, self.current_user)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username_input.text().strip()
            role = dialog.role_input.currentData()
            is_active = dialog.active_checkbox.isChecked()
            password = dialog.password_input.text()
            
            question_id = dialog.question_input.currentData()
            answer = dialog.answer_input.text().strip()

            new_id = self.auth_service.create_user(username, password, role=role)
            if not is_active:
                self.auth_service.update_user(new_id, is_active=False)
                
            if answer:
                self.auth_service.save_security_answers(new_id, question_id, answer)

            QMessageBox.information(self, "تم", "تم إنشاء المستخدم الجديد مدمجاً به سؤال الأمان بنجاح.")
            self.refresh_users_list()

    def _open_edit_user_dialog(self, user_data):
        dialog = UserFormDialog(self, self.auth_service, self.current_user, user_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username_input.text().strip()
            role = dialog.role_input.currentData()
            is_active = dialog.active_checkbox.isChecked()
            password = dialog.password_input.text()
            
            question_id = dialog.question_input.currentData()
            answer = dialog.answer_input.text().strip()

            # حماية السيستم لآخر أدمن نشط
            was_active_admin = user_data["role"] == "Admin" and user_data["is_active"]
            will_stay_active_admin = role == "Admin" and is_active
            if was_active_admin and not will_stay_active_admin and self.auth_service.count_active_admins() <= 1:
                QMessageBox.warning(self, "غير مسموح", "لا يمكن تعطيل أو تغيير صلاحية آخر مدير (Admin) نشط في النظام.")
                return

            self.auth_service.update_user(user_data["id"], username=username, role=role, is_active=is_active)
            if password:
                self.auth_service.change_password(user_data["id"], password)
                
            if answer:
                self.auth_service.db.execute("DELETE FROM user_security_answers WHERE user_id = ?", (user_data["id"],), commit=True)
                self.auth_service.save_security_answers(user_data["id"], question_id, answer)

            QMessageBox.information(self, "تم", "تم تحديث البيانات بنجاح.")
            self.refresh_users_list()

    def _delete_user(self, user_id):
        if user_id == self.current_user["id"]:
            QMessageBox.warning(self, "غير مسموح", "لا يمكنك حذف حسابك الحالي وأنت مسجّل دخول به.")
            return

        target = self.auth_service.get_user(user_id)
        if target and target["role"] == "Admin" and target["is_active"] and self.auth_service.count_active_admins() <= 1:
            QMessageBox.warning(self, "غير مسموح", "لا يمكن حذف آخر مدير (Admin) نشط في النظام.")
            return

        confirm = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا المستخدم؟ لا يمكن التراجع.")
        if confirm == QMessageBox.StandardButton.Yes:
            self.auth_service.delete_user(user_id)
            self.refresh_users_list()