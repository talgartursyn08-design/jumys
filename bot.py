"""
ЗП Бот v6 — RSS + дұрыс сан сүзгісі
"""

import requests
import time
import re
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN = "МҰНДА_ТОКЕНДІ_ЖАЗ"
TELEGRAM_CHAT_ID = "МҰНДА_CHAT_ID_ЖАЗ"

CITIES = {
    "Алматы":  159,
    "Астана":  161,
    "Шымкент": 162,
}

POSITIONS = [
    "CTO Chief Technical Officer",
    "backend разработчик",
    "frontend разработчик",
    "Исполнительный директор",
    "Операционный директор",
    "Операционный менеджер",
    "Финансовый директор",
    "Бухгалтер",
    "Помощник бухгалтера",
    "Руководитель юридического отдела",
    "Юрист",
    "PR менеджер",
    "Маркетолог",
    "Таргетолог",
    "Performance manager",
    "SMM менеджер",
    "Копирайтер",
    "Графический дизайнер",
    "Видеограф",
    "Оператор монтажер",
    "Руководитель отдела сервиса",
    "Руководитель по развитию бизнеса",
    "Product manager",
    "Product Assistant",
    "Руководитель отдела продукта",
    "Методист",
    "Project manager",
    "Контент менеджер",
    "Тимлид",
    "Редактор",
    "Куратор",
    "Операционный куратор",
    "Руководитель отдела контроля качества",
    "Менеджер по возврату",
    "Менеджер по качеству",
    "Менеджер по госзакупкам",
    "B2G менеджер",
    "Менеджер по лидогенерации",
    "Руководитель отдела продаж",
    "Менеджер по продажам",
    "Сервис менеджер",
    "Хантер",
    "HR директор",
    "HR менеджер",
    "Рекрутер",
    "Руководитель АХО",
    "Менеджер по уюту",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://hh.ru/",
}


def extract_salary(title):
    """Тек тақырыптан ЗП алу: 'Бухгалтер (300 000 – 500 000 тг)'"""
    # ЗП тақырыпта болса ғана — description-дан емес
    # Үлгі: "300 000" немесе "300 000 – 500 000" немесе "от 300 000"
    title = title.replace("\xa0", " ").replace(" ", "")
    
    # Екі санды іздеу: 200000-9999999 аралығы
    pattern = r"(\d{6,7})"
    nums = re.findall(pattern, title)
    nums = [int(n) for n in nums if 100000 <= int(n) <= 9999999]
    
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    elif len(nums) == 1:
        return float(nums[0])
    return None


def get_avg_salary_rss(position, area_id):
    salaries = []
    try:
        r = requests.get(
            "https://hh.ru/search/vacancy/rss",
            params={
                "text": position,
                "area": area_id,
                "per_page": 50,
                "only_with_salary": "true",
            },
            headers=HEADERS,
            timeout=15,
        )
        print(f"  RSS {r.status_code}")
        if r.status_code != 200:
            return None

        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        print(f"  items={len(items)}")

        for item in items:
            title = item.findtext("title", "") or ""
            sal = extract_salary(title)
            if sal:
                salaries.append(sal)

    except Exception as e:
        print(f"  Error: {e}")
        return None

    avg = round(sum(salaries) / len(salaries)) if salaries else None
    print(f"  -> {len(salaries)} вак. avg={avg}")
    return avg


def fmt(amount):
    if amount is None:
        return "деректер жоқ"
    return f"{amount:,.0f}".replace(",", " ") + " ₸"


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = []
    while len(text) > 4000:
        i = text.rfind("\n", 0, 4000)
        if i == -1:
            i = 4000
        chunks.append(text[:i])
        text = text[i:].lstrip()
    chunks.append(text)
    for chunk in chunks:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
        }, timeout=15)
        print("Telegram:", r.status_code, r.json().get("ok"))
        time.sleep(0.3)


def main():
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    date_range = f"{week_ago.strftime('%d.%m.%Y')}–{today.strftime('%d.%m.%Y')}"
    lines = [f"📊 *Апталық орташа жалақы есебі*", f"_{date_range}_", ""]
    total = len(POSITIONS) * len(CITIES)
    done = 0

    for position in POSITIONS:
        city_results = {}
        for city_name, area_id in CITIES.items():
            print(f"[{done+1}/{total}] {position} / {city_name}")
            avg = get_avg_salary_rss(position, area_id)
            city_results[city_name] = avg
            done += 1
            time.sleep(0.3)

        if all(v is None for v in city_results.values()):
            continue

        lines.append(f"*{position}*")
        for city_name, avg in city_results.items():
            lines.append(f"  {city_name}: {fmt(avg)}")
        lines.append("")

    lines.append("_hh.kz деректері негізінде_")
    send_telegram("\n".join(lines))
    print("Дайын!")


if __name__ == "__main__":
    main()
