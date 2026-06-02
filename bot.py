"""
ЗП Бот — hh.kz бойынша апталық орташа жалақы есебі
"""

import requests
import time
from datetime import datetime, timedelta

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
    "Учитель репетитор онлайн",
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
    "Хантер продажи",
    "HR директор",
    "HR менеджер",
    "Рекрутер",
    "Руководитель АХО",
    "Менеджер административный",
]


def get_avg_salary(position, area_id):
    salaries = []
    for page in range(3):
        try:
            r = requests.get(
                "https://api.hh.ru/vacancies",
                params={
                    "text": position,
                    "area": area_id,
                    "per_page": 100,
                    "page": page,
                    "only_with_salary": False,
                },
                headers={"User-Agent": "Mozilla/5.0 SalaryBot/2.0"},
                timeout=10,
            )
            if r.status_code != 200:
                break
            items = r.json().get("items", [])
            if not items:
                break
            for v in items:
                s = v.get("salary")
                if not s:
                    continue
                f, t, cur = s.get("from"), s.get("to"), s.get("currency", "KZT")
                rate = {"KZT": 1, "RUR": 5.5, "USD": 470, "EUR": 515}.get(cur, 1)
                if f and t:
                    salaries.append((f + t) / 2 * rate)
                elif f:
                    salaries.append(f * rate)
                elif t:
                    salaries.append(t * rate)
            time.sleep(0.2)
        except Exception:
            break
    return round(sum(salaries) / len(salaries)) if salaries else None


def fmt(amount):
    if amount is None:
        return "деректер жоқ"
    return f"{amount:,.0f}".replace(",", " ") + " ₸"


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
            avg = get_avg_salary(position, area_id)
            city_results[city_name] = avg
            done += 1
            print(f"[{done}/{total}] {position} / {city_name}: {avg}")

        if all(v is None for v in city_results.values()):
            continue

        lines.append(f"*{position}*")
        for city_name, avg in city_results.items():
            lines.append(f"  {city_name}: {fmt(avg)}")
        lines.append("")

    lines.append("_hh.kz деректері негізінде_")
    text = "\n".join(lines)

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
        time.sleep(0.5)

    print("Дайын!")


if __name__ == "__main__":
    main()
