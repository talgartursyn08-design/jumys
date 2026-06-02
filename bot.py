"""
ЗП Бот v8 — AI Agent (OpenAI)
"""

import requests
import time
import json
import os
import re
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

TELEGRAM_TOKEN = "МҰНДА_ТОКЕНДІ_ЖАЗ"
TELEGRAM_CHAT_ID = "МҰНДА_CHAT_ID_ЖАЗ"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

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
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://hh.ru/",
}


def gpt(prompt, max_tokens=300):
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "max_tokens": max_tokens,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if r.status_code != 200:
            print(f"  GPT error: {r.status_code}")
            return ""
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  GPT exception: {e}")
        return ""


def get_search_keywords(position):
    resp = gpt(f"""Мына лауазым үшін hh.kz-де іздеу үшін ең жақсы 3 кілт сөзді бер.
Лауазым: {position}
Тек JSON array қайтар, мысал: ["маркетолог", "marketing manager", "менеджер по маркетингу"]
Басқа ештеңе жазба.""", max_tokens=100)
    try:
        match = re.search(r"\[.+?\]", resp, re.DOTALL)
        if match:
            keywords = json.loads(match.group())
            return keywords[:3]
    except:
        pass
    return [position]


def get_rss_titles(keyword, area_id):
    try:
        r = requests.get(
            "https://hh.ru/search/vacancy/rss",
            params={
                "text": keyword,
                "area": area_id,
                "per_page": 50,
                "only_with_salary": "false",
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
            if t.strip():
                titles.append(t.strip())
        return titles
    except Exception as e:
        print(f"  RSS error: {e}")
        return []


def ai_extract_salaries(position, titles):
    if not titles:
        return []
    titles_text = "\n".join(f"- {t}" for t in titles[:50])
    resp = gpt(f"""Мына вакансия тақырыптарынан "{position}" лауазымына сәйкес жалақыларды тауып қайтар.

{titles_text}

Ережелер:
- Тек осы лауазымға сәйкес тақырыптарды қара
- Тенге (₸, тг, KZT): тікелей қолдан
- Рубль (руб, ₽): 5.5-ке көбейт
- "от X до Y" → (X+Y)/2
- "от X" → X
- 80000-ден төмен → өткіз
- Тек JSON number array қайтар: [350000, 500000]
- Жалақы жоқ болса: []
- Басқа ештеңе жазба""", max_tokens=200)
    try:
        match = re.search(r"\[[\d,\s]*\]", resp)
        if match:
            salaries = json.loads(match.group())
            salaries = [s for s in salaries if isinstance(s, (int, float)) and s >= 80000]
            return salaries
    except:
        pass
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

    for i, position in enumerate(POSITIONS):
        print(f"\n[{i+1}/{len(POSITIONS)}] {position}")
        keywords = get_search_keywords(position)
        print(f"  keywords: {keywords}")

        city_results = {}
        for city_name, area_id in CITIES.items():
            all_titles = []
            for kw in keywords:
                titles = get_rss_titles(kw, area_id)
                all_titles.extend(titles)
                time.sleep(0.3)
            all_titles = list(dict.fromkeys(all_titles))
            print(f"  {city_name}: {len(all_titles)} тақырып")
            salaries = ai_extract_salaries(position, all_titles)
            avg = round(sum(salaries) / len(salaries)) if salaries else None
            print(f"  {city_name} -> {len(salaries)} ЗП, avg={avg}")
            city_results[city_name] = avg
            time.sleep(0.5)

        if all(v is None for v in city_results.values()):
            continue

        lines.append(f"*{position}*")
        for city_name, avg in city_results.items():
            lines.append(f"  {city_name}: {fmt(avg)}")
        lines.append("")

    lines.append("_hh.kz деректері негізінде_")
    send_telegram("\n".join(lines))
    print("\nДайын!")


if __name__ == "__main__":
    main()
