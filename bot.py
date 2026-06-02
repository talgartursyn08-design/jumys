"""
ЗП Бот v7 — RSS + Claude AI парсинг
"""

import requests
import time
import json
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

RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://hh.ru/",
}


def get_rss_titles(position, area_id):
    """RSS-тан вакансия тақырыптарын алу"""
    try:
        r = requests.get(
            "https://hh.ru/search/vacancy/rss",
            params={
                "text": position,
                "area": area_id,
                "per_page": 50,
                "only_with_salary": "true",
            },
            headers=RSS_HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        titles = []
        for item in root.findall(".//item"):
            t = item.findtext("title", "") or ""
            if t:
                titles.append(t.strip())
        print(f"  RSS {r.status_code}, titles={len(titles)}")
        return titles
    except Exception as e:
        print(f"  RSS error: {e}")
        return []


def ai_extract_salaries(titles):
    if not titles:
        return []

    titles_text = "\n".join(f"- {t}" for t in titles[:40])

    prompt = f"""Мына вакансия тақырыптарынан жалақы сомаларын тауып, тізім ретінде қайтар.

Тақырыптар:
{titles_text}

Ереже:
- Тек тенге (₸, тг, KZT) немесе рубль (руб, ₽) сомаларын ал
- Рубльді теңгеге айналдыр: 1 руб = 5.5 теңге
- Егер "от X до Y" болса: (X+Y)/2 ал
- Егер тек "от X" болса: X ал
- 80000-ден төмен сандарды өткіз
- Тек сандарды қайтар, JSON array форматында
- Мысал: [350000, 500000, 280000]
- Басқа ештеңе жазба, тек JSON"""

    try:
        import os
        api_key = os.environ.get("OPENAI_API_KEY", "")
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if r.status_code != 200:
            print(f"  AI error: {r.status_code} {r.text}")
            return []

        text = r.json()["choices"][0]["message"]["content"].strip()
        match = __import__("re").search(r"\[[\d,\s]+\]", text)
        if match:
            salaries = json.loads(match.group())
            print(f"  AI -> {len(salaries)} жалақы")
            return salaries
        return []
    except Exception as e:
        print(f"  AI error: {e}")
        return []


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
    month_ago = today - timedelta(days=30)
    date_range = f"{month_ago.strftime('%d.%m.%Y')}–{today.strftime('%d.%m.%Y')}"
    lines = [f"📊 *Айлық орташа жалақы есебі*", f"_{date_range}_", ""]

    total = len(POSITIONS) * len(CITIES)
    done = 0

    for position in POSITIONS:
        city_results = {}
        for city_name, area_id in CITIES.items():
            print(f"[{done+1}/{total}] {position} / {city_name}")
            titles = get_rss_titles(position, area_id)
            salaries = ai_extract_salaries(titles)
            avg = round(sum(salaries) / len(salaries)) if salaries else None
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
