"""
ЗП Бот v4 — hh.ru RSS арқылы
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
    "CTO", "backend разработчик", "frontend разработчик",
    "Исполнительный директор", "Операционный директор",
    "Операционный менеджер", "Финансовый директор",
    "Бухгалтер", "Помощник бухгалтера", "Юрист",
    "PR менеджер", "Маркетолог", "Таргетолог",
    "Performance manager", "SMM менеджер", "Копирайтер",
    "Графический дизайнер", "Видеограф", "Оператор монтажер",
    "Product manager", "Product Assistant", "Методист",
    "Project manager", "Контент менеджер", "Тимлид",
    "Редактор", "Куратор", "Менеджер по качеству",
    "Менеджер по госзакупкам", "B2G менеджер",
    "Руководитель отдела продаж", "Менеджер по продажам",
    "Сервис менеджер", "HR директор", "HR менеджер", "Рекрутер",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://hh.ru/",
}


def parse_salary_from_text(text):
    if not text:
        return None, None
    text = text.replace("\xa0", " ").replace(" ", "")
    nums = re.findall(r"\d{4,7}", text)
    nums = [int(n) for n in nums if 10000 <= int(n) <= 10000000]
    if len(nums) >= 2:
        return nums[0], nums[1]
    elif len(nums) == 1:
        return nums[0], None
    return None, None


def get_avg_salary_rss(position, area_id):
    salaries = []
    try:
        r = requests.get(
            "https://hh.ru/search/vacancy/rss",
            params={
                "text": position,
                "area": area_id,
                "per_page": 50,
                "only_with_salary": "false",
            },
            headers=HEADERS,
            timeout=15,
        )
        print(f"  RSS status: {r.status_code}")
        if r.status_code != 200:
            return None

        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        print(f"  RSS items: {len(items)}")

        for item in items:
            desc = item.findtext("description", "") or ""
            title = item.findtext("title", "") or ""
            sal_from, sal_to = parse_salary_from_text(title + " " + desc)
            if sal_from and sal_to:
                salaries.append((sal_from + sal_to) / 2)
            elif sal_from:
                salaries.append(sal_from)
            elif sal_to:
                salaries.append(sal_to)

    except Exception as e:
        print(f"  RSS Error: {e}")
        return None

    avg = round(sum(salaries) / len(salaries)) if salaries else None
    print(f"  -> {len(salaries)} вакансия с ЗП, avg={avg}")
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
            time.sleep(0.5)

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
