# -*- coding: utf-8 -*-
"""
login_screen.py
شاشة تسجيل الدخول المطورة - Premium Login Screen
- مدمج بها ميزة استعادة كلمة المرور عبر أسئلة الأمان بأسلوب الويب الذكي.
"""
import time
import os
import binascii
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QLabel, QMessageBox, QDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from config import APP_NAME, SECURITY_QUESTIONS
from assets import get_pixmap, get_icon


class ResetPasswordDialog(QDialog):
    """نافذة منبثقة ذكية وفخمة تتيح للمستخدم استعادة حسابه بنفسه عبر سؤال الأمان"""
    def __init__(self, parent, auth_service):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setWindowTitle("استعادة كلمة المرور")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(380, 260)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info_label = QLabel("يرجى إدخال اسم حسابك والإجابة على سؤال الأمان لتوليد كلمة مرور مؤقتة:")
        info_label.setStyleSheet("color: #f5f6fa; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        form = QFormLayout()
        form.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم المعطل...")
        self.username_input.setMinimumHeight(35)

        self.question_input = QComboBox()
        self.question_input.setMinimumHeight(35)
        for q_id, q_text in SECURITY_QUESTIONS.items():
            self.question_input.addItem(q_text, q_id)

        self.answer_input = QLineEdit()
        self.answer_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.answer_input.setPlaceholderText("أدخل إجابة سؤال الأمان الخاص بك...")
        self.answer_input.setMinimumHeight(35)

        # إضافة ميزة العين لرؤية الإجابة أثناء كتابتها
        self.show_answer_action = QAction(self)
        self.show_answer_action.setIcon(get_icon("eye_icon") if get_icon("eye_icon") else QIcon())
        self.show_answer_action.setCheckable(True)
        self.show_answer_action.toggled.connect(self._toggle_answer_visibility)
        self.answer_input.addAction(self.show_answer_action, QLineEdit.ActionPosition.TrailingPosition)

        form.addRow("اسم المستخدم:", self.username_input)
        form.addRow("سؤال الأمان:", self.question_input)
        form.addRow("الإجابة السرية:", self.answer_input)
        layout.addLayout(form)

        # أزرار الإجراءات
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        verify_btn = QPushButton("تحقق وإعادة تعيين")
        verify_btn.setMinimumHeight(38)
        verify_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; border: none; border-radius: 4px;")
        verify_btn.clicked.connect(self._verify_and_reset)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setStyleSheet("background-color: #7f8c8d; color: white; border: none; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(verify_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _toggle_answer_visibility(self, checked):
        self.answer_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _verify_and_reset(self):
        username = self.username_input.text().strip()
        question_id = self.question_input.currentData()
        answer = self.answer_input.text().strip()

        if not username or not answer:
            QMessageBox.warning(self, "تنبيه", "الرجاء كتابة اسم المستخدم والإجابة أولاً.")
            return

        try:
            # استدعاء دالة التحقق وإعادة التعيين من الـ AuthService الخاص بك
            temp_password = self.auth_service.reset_password_via_security_question(username, question_id, answer)
            
            # في حال النجاح، يتم عرض كلمة المرور الجديدة في صندوق رسائل فخم قابل للنسخ
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("نجاح العملية")
            msg_box.setText("تم التحقق من هويتك بنجاح! 🎉")
            msg_box.setInformativeText(f"كلمة المرور المؤقتة الخاصة بك هي:\n\n 👉  {temp_password}  👈\n\nيرجى نسخها واستخدامها لتسجيل الدخول، وتغييرها فوراً من شاشة المستخدمين.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            
            self.accept()
        except Exception as e:
            # لو الإجابة غلط أو الحساب مش موجود تظهر رسالة خطأ آمنة ومحددة
            QMessageBox.critical(self, "فشل التحقق", str(e))


class LoginScreen(QWidget):
    login_successful = pyqtSignal(dict)

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.setWindowTitle("تسجيل الدخول")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # أبعاد فخمة ومتناسقة
        self.resize(420, 450) # تم تعديل الارتفاع قليلاً ليتناسب مع الرابط الجديد
        self.setWindowIcon(get_icon("appicon"))
        
        # عداد محاولات الدخول للأمان
        self.failed_attempts = 0
        self.lockout_time = 0

        self._build_ui()
        
        # وضع التركيز تلقائياً على اسم المستخدم فور فتح الشاشة
        self.username_input.setFocus()

    def _build_ui(self):
        # Layout عمودي رئيسي مع هوامش مريحة للعين
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)

        # ---------- 1. الشعار / الأيقونة ----------
        image_container = QHBoxLayout()
        image_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = QLabel()
        pixmap = get_pixmap("appiconpng")
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                90, 90,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("🏛️")
            self.image_label.setStyleSheet("font-size: 64px;")
        
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_container.addWidget(self.image_label)
        layout.addLayout(image_container)

        # ---------- 2. عنوان البرنامج ----------
        title = QLabel(APP_NAME)
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #00a8ff; /* اللون المميز المضيء */
            margin-bottom: 5px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        # ---------- 3. نموذج الدخول (Form Layout) ----------
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # حقل اسم المستخدم
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم...")
        self.username_input.setMinimumHeight(35)
        self.username_input.returnPressed.connect(self.password_input_focus)

        # حقل كلمة المرور
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.returnPressed.connect(self._attempt_login)

        # --- إضافة ميزة إظهار/إخفاء كلمة المرور ---
        self.show_password_action = QAction(self)
        self.show_password_action.setIcon(get_icon("eye_icon") if get_icon("eye_icon") else QIcon())
        self.show_password_action.setCheckable(True)
        self.show_password_action.toggled.connect(self._toggle_password_visibility)
        self.password_input.addAction(self.show_password_action, QLineEdit.ActionPosition.TrailingPosition)

        form.addRow("اسم المستخدم:", self.username_input)
        form.addRow("كلمة المرور:", self.password_input)
        layout.addLayout(form)

        # ---------- 🔄 4. زر "نسيت كلمة المرور؟" بأسلوب الويب المطور ----------
        forgot_layout = QHBoxLayout()
        forgot_layout.setAlignment(Qt.AlignmentFlag.AlignLeft) # محاذاة لليمين حسب الـ RTL

        self.forgot_btn = QPushButton("نسيت كلمة المرور؟")
        self.forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor) # تحويل الماوس ليد كأنه رابط ويب
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #718093;
                font-size: 12px;
                text-decoration: underline; /* وضع خط تحت الكلمة مثل الروابط */
                padding: 0px;
            }
            QPushButton:hover {
                color: #00a8ff; /* يتحول للأزرق المضيء عند تمرير الماوس */
            }
        """)
        self.forgot_btn.clicked.connect(self._open_forgot_password_dialog)
        forgot_layout.addWidget(self.forgot_btn)
        layout.addLayout(forgot_layout)

        # ---------- 5. زر تسجيل الدخول ----------
        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 15px;
            }
        """)
        self.login_btn.clicked.connect(self._attempt_login)
        layout.addWidget(self.login_btn)

        # ---------- 6. تلميح بالأسفل ----------
        hint = QLabel("بيانات الدخول الافتراضية: admin / admin123")
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        layout.addStretch()

    def password_input_focus(self):
        """توجيه المؤشر لكلمة المرور عند الضغط على Enter في حقل الاسم"""
        self.password_input.setFocus()

    def _toggle_password_visibility(self, checked):
        """دالة للتبديل بين إظهار وإخفاء كلمة المرور"""
        self.password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _open_forgot_password_dialog(self):
        """فتح نافذة استعادة الحساب المنبثقة"""
        dialog = ResetPasswordDialog(self, self.auth_service)
        dialog.exec()

    def _attempt_login(self):
        # التحقق من قفل الأمان Brute-force
        current_time = time.time()
        if current_time < self.lockout_time:
            remaining = int(self.lockout_time - current_time)
            QMessageBox.warning(
                self, "حظر مؤقت", 
                f"تم قفل محاولات الدخول مؤقتاً بسبب كثرة الأخطاء.\nيرجى الانتظار {remaining} ثانية."
            )
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم المستخدم وكلمة المرور أولاً.")
            return

        # عملية المصادقة
        user = self.auth_service.authenticate(username, password)
        
        if user:
            self.failed_attempts = 0 # تصفير العداد عند النجاح
            self.login_successful.emit(user)
        else:
            self.failed_attempts += 1
            self.password_input.clear()
            
            # تطبيق الحظر المؤقت بعد 3 محاولات فاشلة متتالية
            if self.failed_attempts >= 3:
                self.lockout_time = time.time() + 30 # قفل لمدة 30 ثانية
                self.failed_attempts = 0 # تصفير المحاولات للبدء مجدداً بعد الحظر
                QMessageBox.critical(
                    self, "حظر مؤقت للأمان", 
                    "أدخلت بيانات خاطئة 3 مرات متتالية!\nتم حظر محاولات تسجيل الدخول لمدة 30 ثانية حمايةً لبياناتك."
                )
            else:
                QMessageBox.critical(
                    self, "خطأ في الدخول", 
                    f"اسم المستخدم أو كلمة المرور غير صحيحة.\nالمحاولات المتبقية قبل القفل المؤقت: {3 - self.failed_attempts}"
                )
                #Reset@e6fecc