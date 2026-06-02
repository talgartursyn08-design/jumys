"""
ЗП Бот v5 — hh.ru API, дұрыс парсинг
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
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
}


def get_avg_salary(position, area_id):
    salaries = []
    try:
        for page in range(5):
            r = requests.get(
                "https://api.hh.ru/vacancies",
                params={
                    "text": position,
                    "area": area_id,
                    "per_page": 100,
                    "page": page,
                    "only_with_salary": False,
                    "currency": "KZT",
                },
                headers=HEADERS,
                timeout=15,
            )
            print(f"  status={r.status_code} page={page}")
            if r.status_code != 200:
                break
            data = r.json()
            items = data.get("items", [])
            if not items:
                break

            for v in items:
                s = v.get("salary")
                if not s:
                    continue
                # Тек нақты ЗП өрістерін алу
                sal_from = s.get("from")
                sal_to = s.get("to")
                cur = s.get("currency", "KZT")
                # Тек KZT, RUR, USD қабылдаймыз
                if cur not in ("KZT", "RUR", "USD", "EUR"):
                    continue
                rate = {"KZT": 1, "RUR": 5.5, "USD": 470, "EUR": 515}[cur]
                # Минимум 50,000 ₸ болу керек (спам сүзгі)
                if sal_from and sal_from * rate < 50000:
                    sal_from = None
                if sal_to and sal_to * rate < 50000:
                    sal_to = None

                if sal_from and sal_to:
                    salaries.append((sal_from + sal_to) / 2 * rate)
                elif sal_from:
                    salaries.append(sal_from * rate)
                elif sal_to:
                    salaries.append(sal_to * rate)

            if page >= data.get("pages", 1) - 1:
                break
            time.sleep(0.3)

    except Exception as e:
        print(f"  Error: {e}")

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
            avg = get_avg_salary(position, area_id)
            city_results[city_name] = avg
            done += 1

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
