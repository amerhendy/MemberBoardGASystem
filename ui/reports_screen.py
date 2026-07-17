# -*- coding: utf-8 -*-
"""
reports_screen.py
شاشة التقارير المطورة - Premium Report Generator Screen
- شريط فلاتر أفقي فخم ومدمج لتحقيق أقصى استغلال للمساحة البصرية.
- جداول ممتدة ومريحة للعين مع تبويبات ذكية وأزرار تصدير تفاعلية مصممة بعناية.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QMessageBox,
    QTabWidget, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from config import MEMBER_TYPES, MEMBER_TYPE_LABELS_AR


class ReportsScreen(QWidget):
    def __init__(self, evaluation_service, export_service):
        super().__init__()
        self.evaluation_service = evaluation_service
        self.export_service = export_service
        self.last_evaluation_rows = []
        self.last_financial_rows = []

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # ---------- الهيدر العلوي ----------
        header_layout = QHBoxLayout()
        title_label = QLabel("نظام توليد واستخراج التقارير")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f5f6fa;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # ---------- شريط الفلاتر الأفقي الأنيق ----------
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        filter_bar.addWidget(QLabel("من تاريخ:"))
        self.date_from_input = QDateEdit(calendarPopup=True)
        self.date_from_input.setMinimumHeight(35)
        self.date_from_input.setDate(QDate.currentDate().addMonths(-1))
        filter_bar.addWidget(self.date_from_input)

        filter_bar.addWidget(QLabel("إلى تاريخ:"))
        self.date_to_input = QDateEdit(calendarPopup=True)
        self.date_to_input.setMinimumHeight(35)
        self.date_to_input.setDate(QDate.currentDate())
        filter_bar.addWidget(self.date_to_input)

        filter_bar.addWidget(QLabel("الفئة:"))
        self.category_input = QComboBox()
        self.category_input.setMinimumHeight(35)
        self.category_input.setMinimumWidth(130)
        self.category_input.addItem("كلاهما", None)
        for t in MEMBER_TYPES:
            self.category_input.addItem(MEMBER_TYPE_LABELS_AR[t], t)
        filter_bar.addWidget(self.category_input)

        # زر توليد التقارير التفاعلي
        generate_btn = QPushButton("توليد التقارير")
        generate_btn.setFixedSize(120, 35)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0097e6; }
        """)
        generate_btn.clicked.connect(self._generate_reports)
        filter_bar.addWidget(generate_btn)

        main_layout.addLayout(filter_bar)

        # ---------- التبويبات الرئيسية ----------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(self._get_tab_stylesheet())

        # 1. تبويب التقييم والأيام النشطة
        eval_tab = QWidget()
        eval_layout = QVBoxLayout(eval_tab)
        eval_layout.setContentsMargins(10, 15, 10, 10)
        eval_layout.setSpacing(12)

        self.evaluation_table = QTableWidget(0, 5)
        self.evaluation_table.setHorizontalHeaderLabels(
            ["الاسم الكريم", "النوع", "تاريخ التعيين", "الأيام النشطة", "نسبة التقييم %"]
        )
        self.evaluation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.evaluation_table.setAlternatingRowColors(True)
        self.evaluation_table.setStyleSheet(self._get_table_stylesheet_for_grid())
        eval_layout.addWidget(self.evaluation_table)

        export_eval_btn = QPushButton("تصدير تقرير التقييم إلى Excel")
        export_eval_btn.setMinimumHeight(38)
        export_eval_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #219653; }
        """)
        export_eval_btn.clicked.connect(self._export_evaluation)
        eval_layout.addWidget(export_eval_btn)

        self.tabs.addTab(eval_tab, "تقرير الأيام النشطة والتقييم")

        # 2. التبويب المالي
        fin_tab = QWidget()
        fin_layout = QVBoxLayout(fin_tab)
        fin_layout.setContentsMargins(10, 15, 10, 10)
        fin_layout.setSpacing(12)

        self.financial_table = QTableWidget(0, 4)
        self.financial_table.setHorizontalHeaderLabels(
            ["الاسم الكريم", "النوع", "عدد مرات الحضور", "إجمالي البدل المصروف"]
        )
        self.financial_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.financial_table.setAlternatingRowColors(True)
        self.financial_table.setStyleSheet(self._get_table_stylesheet_for_grid())
        fin_layout.addWidget(self.financial_table)

        export_fin_btn = QPushButton("تصدير التقرير المالي إلى Excel")
        export_fin_btn.setMinimumHeight(38)
        export_fin_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #219653; }
        """)
        export_fin_btn.clicked.connect(self._export_financial)
        fin_layout.addWidget(export_fin_btn)

        self.tabs.addTab(fin_tab, "التقرير المالي")

        main_layout.addWidget(self.tabs)

    # ------------------------------------------------------------- تنسيقات الواجهة الفخمة
    def _get_tab_stylesheet(self):
        return """
            QTabWidget::pane {
                border: 1px solid #718093;
                background-color: #2f3640;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1e272e;
                color: #dcdde1;
                font-weight: bold;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #2f3640;
                color: #00a8ff;
            }
        """

    def _get_table_stylesheet_for_grid(self):
        return """
            QTableWidget {
                background-color: #2f3640;
                alternate-background-color: #1e272e;
                color: #f5f6fa;
                gridline-color: #718093;
                border: none;
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

    # ------------------------------------------------------------- منطق العمليات والبيانات
    def _generate_reports(self):
        period_start = self.date_from_input.date().toString("yyyy-MM-dd")
        period_end = self.date_to_input.date().toString("yyyy-MM-dd")
        member_type = self.category_input.currentData()

        if self.date_from_input.date() > self.date_to_input.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية.")
            return

        self.last_evaluation_rows = self.evaluation_service.evaluation_report(
            period_start, period_end, member_type
        )
        self.last_financial_rows = self.evaluation_service.financial_report(
            period_start, period_end, member_type
        )

        self._fill_evaluation_table()
        self._fill_financial_table()

    def _fill_evaluation_table(self):
        rows = self.last_evaluation_rows
        self.evaluation_table.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            self.evaluation_table.setRowHeight(row_idx, 42)
            values = [
                r["full_name"],
                MEMBER_TYPE_LABELS_AR[r["member_type"]],
                r["start_date"],
                str(r["active_days"]),
                f"{r['evaluation_percent']:.2f}%",
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.evaluation_table.setItem(row_idx, col_idx, item)

    def _fill_financial_table(self):
        rows = self.last_financial_rows
        self.financial_table.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            self.financial_table.setRowHeight(row_idx, 42)
            values = [
                r["full_name"],
                MEMBER_TYPE_LABELS_AR[r["member_type"]],
                str(r["attended_count"] or 0),
                f"{r['total_paid']:,.2f}",
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.financial_table.setItem(row_idx, col_idx, item)

    def _export_evaluation(self):
        if not self.last_evaluation_rows:
            QMessageBox.information(self, "تنبيه", "الرجاء توليد التقرير أولاً.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ ملف Excel", "evaluation_report.xlsx", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        rows = []
        for r in self.last_evaluation_rows:
            rows.append({**r, "member_type_label": MEMBER_TYPE_LABELS_AR[r["member_type"]]})
        headers = {
            "full_name": "الاسم",
            "member_type_label": "النوع",
            "start_date": "تاريخ التعيين",
            "end_date": "تاريخ الانتهاء",
            "active_days": "الأيام النشطة",
            "evaluation_percent": "نسبة التقييم %",
        }
        self.export_service.export_to_excel(rows, headers, file_path, sheet_title="Evaluation")
        QMessageBox.information(self, "تم", f"تم التصدير بنجاح إلى:\n{file_path}")

    def _export_financial(self):
        if not self.last_financial_rows:
            QMessageBox.information(self, "تنبيه", "الرجاء توليد التقرير أولاً.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ ملف Excel", "financial_report.xlsx", "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        rows = []
        for r in self.last_financial_rows:
            rows.append({**r, "member_type_label": MEMBER_TYPE_LABELS_AR[r["member_type"]]})
        headers = {
            "full_name": "الاسم",
            "member_type_label": "النوع",
            "sessions_count": "عدد الجلسات المرتبطة",
            "attended_count": "عدد مرات الحضور",
            "total_paid": "إجمالي المصروف",
        }
        self.export_service.export_to_excel(rows, headers, file_path, sheet_title="Financial")
        QMessageBox.information(self, "تم", f"تم التصدير بنجاح إلى:\n{file_path}")