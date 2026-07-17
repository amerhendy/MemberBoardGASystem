# -*- coding: utf-8 -*-
"""
dashboard_screen.py
شاشة لوحة التحكم المطورة - Premium Dashboard Screen
"""
import os
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGridLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor

# استيراد رقم الإصدار من ملف الإعدادات
from config import MEMBER_TYPE_LABELS_AR, APP_VERSION
from assets import get_pixmap, get_icon


class KpiCard(QFrame):
    """بطاقة مؤشرات أداء (KPI) متطورة مع تأثيرات ظل وحواف دائرية أنيقة"""
    def __init__(self, title: str, value: str, color: str = "#2F5496", icon_char: str = ""):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # تصميم فخم بـ QSS مع تدرج لوني خفيف أو حواف ناعمة
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        self.setMinimumSize(220, 110)

        # إضافة تأثير الظل (Shadow Effect) لمنح الكارت بُعداً بصرياً فخماً
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # التخطيط الداخلي للكارت
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(5)

        # الهيدر الداخلي للكارت (يحتوي على العنوان والأيقونة التعبيرية)
        header_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-size: 13px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(title_label)
        
        # إضافة إيموجي أو أيقونة تعبيرية صغيرة بجانب عنوان الكارت
        if icon_char:
            icon_label = QLabel(icon_char)
            icon_label.setStyleSheet("font-size: 18px; color: white; background: rgba(255,255,255,0.15); border-radius: 6px; padding: 2px 6px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            header_layout.addWidget(icon_label)
            
        layout.addLayout(header_layout)

        # قيمة المؤشر (الرقم)
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; margin-top: 5px;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(value_label)


class DashboardScreen(QWidget):
    def __init__(self, member_service, meeting_service, evaluation_service):
        super().__init__()
        self.member_service = member_service
        self.meeting_service = meeting_service
        self.evaluation_service = evaluation_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # تخطيط رأسي رئيسي بهوامش فخمة
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 20, 25, 20)
        self.main_layout.setSpacing(20)

        # ---------- 1. الهيدر (أيقونة + عنوان) ----------
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.setSpacing(12)

        # الاستيراد الآمن من الـ Base64 مباشرة لعدم فقد الأيقونة في الـ EXE
        self.icon_label = QLabel()
        pixmap = get_pixmap("dashboard_icon") # تأكد من تسجيل هذا الاسم في الـ Registry بملف __init__.py
        
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                32, 32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            self.icon_label.setText("📊")
            self.icon_label.setStyleSheet("font-size: 26px;")

        header = QLabel("لوحة التحكم الرئيسية")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")

        title_layout.addWidget(self.icon_label)
        title_layout.addWidget(header)
        self.main_layout.addLayout(title_layout)

        # ---------- 2. شبكة بطاقات الـ KPI ----------
        # جعل المسافات بين الكروت متناسقة وجميلة
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(15)
        self.main_layout.addLayout(self.kpi_grid)

        # ---------- 3. شعار أو صورة النظام الوسطية ----------
        image_container = QHBoxLayout()
        self.image_label = QLabel()
        
        pixmap = get_pixmap("dashboardimg")
        if not pixmap.isNull():
            # جعل مقاس الصورة 350x350 ليترك متسعاً مريحاً لعناصر الواجهة الأخرى
            scaled_pixmap = pixmap.scaled(
                350, 350,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("🏛️")
            self.image_label.setStyleSheet("font-size: 120px;")
        
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_container.addWidget(self.image_label)
        self.main_layout.addLayout(image_container)

        # ---------- 4. نصوص معلومات المصمم والإصدار (Footer) ----------
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(10, 10, 10, 10)
        
        style_info = "font-size: 11px; color: #7f8c8d; font-weight: bold;"

        designer_label = QLabel("Designed By: Amer Hendy")
        designer_label.setStyleSheet(style_info)
        
        email_label = QLabel("Email: amer.hendy@yahoo.com")
        email_label.setStyleSheet(style_info)

        version_label = QLabel(f"Version: {APP_VERSION}")
        version_label.setStyleSheet(style_info)

        # توزيع البيانات بشكل متفرق وأنيق في شريط التذييل (Footer)
        footer_layout.addWidget(designer_label)
        footer_layout.addStretch()
        footer_layout.addWidget(email_label)
        footer_layout.addStretch()
        footer_layout.addWidget(version_label)

        self.main_layout.addLayout(footer_layout)

    def refresh(self):
        # تفريغ الشبكة لتجنب تكرار الكروت عند التحديث
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # جلب البيانات من الخدمات
        counts = self.member_service.counts_by_type()
        active_board = sum(c["cnt"] for c in counts if c["member_type"] == "Board" and c["status"] == "Active")
        active_assembly = sum(c["cnt"] for c in counts if c["member_type"] == "Assembly" and c["status"] == "Active")

        today = date.today().isoformat()
        month_start = date.today().replace(day=1).isoformat()
        financial_this_month = self.evaluation_service.financial_report(month_start, today)
        total_paid_month = sum(r["total_paid"] for r in financial_this_month)

        upcoming_meetings = self.meeting_service.list_meetings(date_from=today)

        # كروت الأداء مع الألوان والأيقونات المعبرة المضافة حديثاً
        cards = [
            (f"أعضاء {MEMBER_TYPE_LABELS_AR['Board']} النشطون", str(active_board), "#2980b9", "👥"),
            (f"أعضاء {MEMBER_TYPE_LABELS_AR['Assembly']} النشطون", str(active_assembly), "#27ae60", "🏛️"),
            ("إجمالي المصروف هذا الشهر", f"{total_paid_month:,.2f} ج.م", "#c0392b", "💵"),
            ("الجلسات القادمة", str(len(upcoming_meetings)), "#8e44ad", "📅"),
        ]
        
        # توزيع الكروت في جدول ثنائي الأبعاد (صفوف وأعمدة)
        for idx, (title, value, color, icon) in enumerate(cards):
            self.kpi_grid.addWidget(KpiCard(title, value, color, icon), idx // 2, idx % 2)