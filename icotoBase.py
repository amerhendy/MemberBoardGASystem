import base64

# ضع اسم ملف الصورة الخاص بك هنا
icon_path = "assets/dashboard.ico"  

with open(icon_path, "rb") as icon_file:
    encoded_string = base64.b64encode(icon_file.read()).decode('utf-8')

with open("dashboardIco.py", "w") as text_file:
    text_file.write(encoded_string)

print("تم تحويل الأيقونة بنجاح! انسخ النص من ملف icon_base64.txt")