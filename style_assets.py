QSS_STYLE="""
    /* الخلفية العامة للتطبيق */
    QWidget {
        background-color: #1e272e;
        color: #f5f6fa;
        font-family: "Segoe UI", "Segoe UI Arabic", Arial;
        font-size: 14px;
    }

    /* تنسيق أزرار البرنامج العادية لتصبح فخمة وتفاعلية */
    QPushButton {
        background-color: #2f3640;
        border: 1px solid #718093;
        border-radius: 6px;
        padding: 8px 15px;
        font-weight: bold;
        min-width: 40px;
    }

    /* تأثير مرور الماوس فوق الأزرار (Hover) */
    QPushButton:hover {
        background-color: #00a8ff;
        color: #ffffff;
        border: 1px solid #00a8ff;
    }

    /* تأثير الضغط على الزر (Pressed) */
    QPushButton:pressed {
        background-color: #0088cc;
    }

    /* تنسيق حقول الإدخال (Inputs) */
    QLineEdit, QTextEdit {
        background-color: #2f3640;
        border: 2px solid #718093;
        border-radius: 6px;
        padding: 6px;
        color: #ffffff;
    }

    /* عند التركيز والكتابة داخل الحقل */
    QLineEdit:focus, QTextEdit:focus {
        border: 2px solid #00a8ff;
    }

    /* شريط الأدوات (ToolBar) */
    QToolBar {
        background-color: #2f3640;
        border-bottom: 1px solid #718093;
        spacing: 10px;
        padding: 5px;
    }

    /* الأزرار داخل شريط الأدوات */
    QToolBar QToolButton {
        background-color: transparent;
        border: none;
        border-radius: 4px;
        padding: 5px;
    }

    QToolBar QToolButton:hover {
        background-color: #00a8ff;
    }

    /* تنسيق الجداول والـ Lists */
    QTableWidget, QListWidget {
        background-color: #2f3640;
        border: 1px solid #718093;
        border-radius: 8px;
        gridline-color: #718093;
    }

    /* 1. إطار جسم المحتوى (اللوحة السفلية) */
    QTabWidget::pane {
        border: 1px solid #718093; /* إطار رمادي أنيق */
        background-color: #2f3640;  /* نفس لون الخلفية الثانوية */
        position: absolute;
        top: -1px; /* يدمج الإطار العلوي للمحتوى مع التبويبة النشطة بشكل سلس */
        border-radius: 6px;
        border-top-left-radius: 0px; /* لجعل الزاوية تحت التبويبة الأولى مستقيمة */
    }

    /* 2. شريط التبويبات بالكامل */
    QTabBar {
        background-color: transparent;
        qproperty-drawBase: 0; /* يلغي الخط الافتراضي القديم أسفل التبويبات */
    }

    /* 3. تصميم التبويبة الفردية (غير النشطة) */
    QTabBar::tab {
        background-color: #1e272e; /* خلفية أغمق لتبدو غير نشطة */
        color: #a5b1c2; /* لون نص باهت قليلاً */
        border: 1px solid #718093;
        border-bottom-color: none; /* إخفاء الخط السفلي لكي تندمج مع المحتوى لاحقاً */
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 20px;
        margin-right: 4px; /* مسافة بسيطة بين كل تبويبة وأخرى */
    }

    /* 4. تأثير مرور الماوس فوق التبويبة (Hover) */
    QTabBar::tab:hover {
        background-color: #353b48;
        color: #ffffff;
    }

    /* 5. تصميم التبويبة النشطة (المحددة حالياً) */
    QTabBar::tab:selected {
        background-color: #2f3640; /* نفس لون خلفية المحتوى لتندمج معه تماماً */
        color: #00a8ff; /* لون النص المضيء (الـ Accent Color) */
        border-bottom: 2px solid #00a8ff; /* خط فوسفوري مضيء أسفل التبويبة النشطة */
        font-weight: bold;
    }

    /* 6. في حال كانت التبويبة النشطة ليست الأولى (لتنسيق الحواف الديناميكي) */
    QTabBar::tab:!selected {
        margin-top: 2px; /* جعل التبويبات غير النشطة أنزل قليلاً لتعطي عمقاً بصرياً (3D) */
    }
    """