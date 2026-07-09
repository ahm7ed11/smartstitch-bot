"""
شغّل الملف ده مرة واحدة بس عشان تسجل دخول بحسابك على جوجل درايف.
هيفتحلك المتصفح، تختار حسابك، توافق على الصلاحيات، وهيتحفظلك ملف token.json
هيستخدمه البوت بعد كده أوتوماتيك من غير ما تسجل دخول تاني (بيجدد نفسه لوحده).

الخطوات قبل ما تشغل الملف ده:
1) روح على Google Cloud Console وسوي OAuth Client ID من نوع "Desktop app"
2) نزل ملف الـ JSON بتاعه وسمّيه oauth_client.json وحطه جنب bot.py
3) شغّل: python authorize_drive.py
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

import config
from services.drive_service import SCOPES


def main():
    if not os.path.exists(config.GOOGLE_OAUTH_CLIENT_FILE):
        print(
            f"❌ ملف {config.GOOGLE_OAUTH_CLIENT_FILE} مش موجود.\n"
            "روح Google Cloud Console -> Credentials -> Create Credentials -> "
            "OAuth client ID -> Desktop app، نزّل الـ JSON وسمّيه "
            f"{config.GOOGLE_OAUTH_CLIENT_FILE} وحطه جنب bot.py."
        )
        return

    flow = InstalledAppFlow.from_client_secrets_file(config.GOOGLE_OAUTH_CLIENT_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(config.GOOGLE_TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"✅ تم تسجيل الدخول بنجاح! اتحفظ التوكن في: {config.GOOGLE_TOKEN_FILE}")
    print("تقدر دلوقتي تشغل البوت عادي: python bot.py")


if __name__ == "__main__":
    main()
