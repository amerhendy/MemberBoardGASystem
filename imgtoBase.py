import base64

# ضع اسم ملف الصورة الخاص بك هنا
image_path = "assets/user.png"  

with open(image_path, "rb") as image_file:
    # قراءة الصورة وتحويلها إلى Base64
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

# حفظ النص في ملف خارجي لنسخه بسهولة
with open("user.py", "w") as text_file:
    text_file.write(encoded_string)

print("تم تحويل الصورة بنجاح! ستجد النص في ملف user.py")