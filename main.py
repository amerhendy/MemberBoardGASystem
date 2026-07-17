# -*- coding: utf-8 -*-
"""
main.py
نقطة تشغيل التطبيق - Application Entry Point
يعرض شاشة تسجيل الدخول أولًا، وبعد النجاح يفتح النافذة الرئيسية بتبويبات:
لوحة التحكم / الأعضاء / الاجتماعات / الإعدادات / التقارير.
"""
import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon  # <--- أضف هذا السطر لاستخدام الأيقونات

from config import DB_PATH, APP_NAME
from database.db_manager import DatabaseManager
from auth.auth_service import AuthService
from services.member_service import MemberService
from services.dynamic_fields_service import DynamicFieldsService
from services.document_service import DocumentService
from services.committee_service import CommitteeService
from services.meeting_service import MeetingService
from services.evaluation_service import EvaluationService
from services.export_service import ExportService

from ui.login_screen import LoginScreen
from ui.dashboard_screen import DashboardScreen
from ui.members_screen import MembersScreen
from ui.meetings_screen import MeetingsScreen
from ui.committees_screen import CommitteesScreen
from ui.settings_screen import SettingsScreen
from ui.reports_screen import ReportsScreen
from ui.users_screen import UsersScreen

from assets import get_pixmap, get_icon
from style_assets import QSS_STYLE
class MainWindow(QMainWindow):
    def __init__(self, user, services):
        super().__init__()
        self.user = user
        self.services = services
        self.setWindowTitle(f"{APP_NAME} - مرحبًا {user['username']}")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(1100, 700)
        # ----- إضافة أيقونة النافذة الرئيسية -----
        self.setWindowIcon(get_icon("appicon"))
        # ----------------------------------------
        
        self._build_ui()

    def _build_ui(self):
        tabs = QTabWidget()

        # إنشاء الشاشات
        dashboard = DashboardScreen(
            self.services["member_service"],
            self.services["meeting_service"],
            self.services["evaluation_service"],
        )
        members = MembersScreen(
            self.services["member_service"],
            self.services["dynamic_fields_service"],
            self.services["document_service"],
            self.services["export_service"],
        )
        meetings = MeetingsScreen(
            self.services["meeting_service"],
            self.services["committee_service"],
        )
        committees = CommitteesScreen(
            self.services["committee_service"],
            self.services["member_service"],
        )
        settings = SettingsScreen(self.services["dynamic_fields_service"])
        reports = ReportsScreen(
            self.services["evaluation_service"],
            self.services["export_service"],
        )

        # إضافة التبويبات مع أيقونات
        # نضيف التبويبات أولاً، ثم نضبط الأيقونات
        tabs.addTab(dashboard, "لوحة التحكم")
        tabs.addTab(members, "الأعضاء")
        tabs.addTab(committees, "اللجان")
        tabs.addTab(meetings, "الاجتماعات والحضور")
        tabs.addTab(settings, "الإعدادات")
        tabs.addTab(reports, "التقارير")

        # ----- إضافة أيقونات للتبويبات -----
        # نحدد أيقونة لكل تبويب (حسب الترتيب)
        tab_icons = [
            get_icon("dashboard_icon"),
            get_icon("memberimg"),       # الأعضاء
            get_icon("ethics"),    # اللجان
            get_icon("conferance"),      # الاجتماعات
            get_icon("cogwheel"),      # الإعدادات
            get_icon("analytics"),       # التقارير
        ]
        for idx, icon_path in enumerate(tab_icons):
            icon = QIcon(icon_path)
            if not icon.isNull():
                tabs.setTabIcon(idx, icon)
            else:
                # بديل: استخدم إيموجي كأيقونة نصية (اختياري)
                # نستطيع أيضاً وضع نص صغير أو رمز تعبيري
                pass
        # ------------------------------------

        # تبويب إدارة المستخدمين يظهر فقط لمن صلاحيته Admin
        users_screen = UsersScreen(self.services["auth_service"], self.user)
        tabs.addTab(users_screen, "المستخدمون")
        # أيقونة المستخدمين (اختياري)
        icon = QIcon(get_icon("user"))
        if not icon.isNull():
            tabs.setTabIcon(tabs.count() - 1, icon)

        # تحديث الداشبورد والأعضاء واللجان عند الرجوع لتبويباتهم
        def on_tab_changed(idx):
            current_widget = tabs.widget(idx)
            if current_widget is dashboard:
                dashboard.refresh()
            elif current_widget is members:
                members.refresh()
            elif current_widget is committees:
                committees.refresh()

        tabs.currentChanged.connect(on_tab_changed)

        self.setCentralWidget(tabs)


def build_services():
    db = DatabaseManager(DB_PATH)
    auth_service = AuthService(db)
    auth_service.ensure_default_admin()

    member_service = MemberService(db)
    dynamic_fields_service = DynamicFieldsService(db)
    document_service = DocumentService(db)
    committee_service = CommitteeService(db)
    meeting_service = MeetingService(db, member_service)
    evaluation_service = EvaluationService(db, member_service)
    export_service = ExportService()

    return auth_service, {
        "auth_service": auth_service,
        "member_service": member_service,
        "dynamic_fields_service": dynamic_fields_service,
        "document_service": document_service,
        "committee_service": committee_service,
        "meeting_service": meeting_service,
        "evaluation_service": evaluation_service,
        "export_service": export_service,
    }


def main():
    app = QApplication(sys.argv)
    
    # ----- تعيين أيقونة التطبيق الأساسية (تظهر في شريط المهام) -----
    app_icon = QIcon(get_icon("appicon"))
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    # ----------------------------------------------------------------

    auth_service, services = build_services()

    login_screen = LoginScreen(auth_service)
    # أيضاً تعيين أيقونة نافذة تسجيل الدخول (اختياري)
    login_icon = QIcon(get_icon("appiconpng"))
    if not login_icon.isNull():
        login_screen.setWindowIcon(login_icon)

    main_window_holder = {}

    def on_login_success(user):
        main_window = MainWindow(user, services)
        main_window.show()
        main_window_holder["window"] = main_window
        login_screen.close()

    login_screen.login_successful.connect(on_login_success)
    login_screen.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # --- السحر هنا: تطبيق الستايل الموحد على التطبيق بأكمله ---
    app.setStyleSheet(QSS_STYLE)
    
    window = main()
    window.show()
    sys.exit(app.exec())