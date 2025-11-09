# Yealink Remote Phonebook

קבצים נוצרים אוטומטית מתוך האקסל `גור   אלפון מעודכן.xlsx`.
תבנית הצגה: שם משפחה + שם פרטי. ממשק טלפון בעברית.

## מבנה
- `index.xml` – אינדקס אותיות (א–ת)
- `*.xml` – לכל אות (alef.xml, bet.xml, ...)

## הפעלה ב-GitHub Pages
1. צור ריפו חדש ב-GitHub, לדוגמה `yealink-phonebook`.
2. העלה את כל הקבצים האלו לתיקיית השורש של הריפו.
3. ב-Settings → Pages → Source: `Deploy from a branch` → Branch: `main` → `/root` → Save.
4. הכתובת תהיה בערך: `https://USERNAME.github.io/yealink-phonebook/`

## חיבור בטלפון Yealink
בתפריט ספרי טלפון מרוחקים הזן את ה-URL של הקובץ הראשי:
```
https://USERNAME.github.io/yealink-phonebook/index.xml
```
או אם הקבצים בתיקייה אחרת:
```
https://USERNAME.github.io/REPO/index.xml
```

## הערות
- עד 3 מספרים מוצמדים לשם: Mobile / Office / Other. מספרים נוספים נרשמים כשדות `Telephone` נוספים באותו איש קשר.
- למספרים הוסרה פורמטציה (מקפים/רווחים). 972 הומר ל-0 בתחילת מספר ישראלי.
- מיון לפי האות הראשונה של שם המשפחה.

נוצר: 2025-11-09 10:05
