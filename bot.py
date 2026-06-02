"""
ЗП Бот — hh.kz бойынша апталық орташа жалақы есебі
Іске қосу: python bot.py
"""

import requests
import time
import os
from datetime import datetime, timedelta

# ─────────────────────────────────────────
# ОСЫНЫ ӨЗГЕРТ
TELEGRAM_TOKEN = "МҰНДА_ТОКЕНДІ_ЖАЗ"
TELEGRAM_CHAT_ID = "МҰНДА_CHAT_ID_ЖАЗ"
# ─────────────────────────────────────────

# Қалалар (hh.kz area ID)
CITIES = {
    "Алматы":   159,
    "Астана":   161,
    "Шымкент":  162,
}

# 53 позиция
POSITIONS = [
    "CTO (Chief Technical Officer)",
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
    "Оператор-монтажер",
    "Руководитель отдела сервиса",
    "Руководитель по развитию бизнеса",
    "Product manager",
    "Product Assistant",
    "Руководитель отдела продукта",
    "Методист",
    "ЕНТ продуктолог",
    "Project manager",
    "Контент менеджер",
    "Тимлид",
    "Учитель ЕНТ (онлайн)",
    "Учитель ЕНТ (офлайн)",
    "Учитель НКД (онлайн)",
    "Редактор",
    "Куратор",
    "Операционный куратор",
    "Руководитель отдела контроля качества",
    "Менеджер по возврату",
    "Менеджер по качеству",
    "Менеджер по госзакупкам",
    "B2G менеджер",
    "Менеджер по лидогенерации",
    "РОП (руководитель отдела продаж)",
    "Менеджер по продажам",
    "Сервис-менеджер",
    "Хантер",
    "HR директор",
    "HR менеджер",
    "Рекрутер (точечный подбор)",
    "Рекрутер (массовый подбор)",
    "Руководитель АХО",
    "Менеджер по уюту",
]


def get_avg_salary(position: str, area_id: int) -> int | None:
    """hh.kz API арқылы орташа ЗП алу"""
    try:
        resp = requests.get(
            "https://api.hh.ru/vacancies",
            params={
                "text": position,
                "area": area_id,
                "per_page": 100,
                "only_with_salary": False,
                "currency": "KZT",
            },
            headers={"User-Agent": "SalaryBot/1.0 (talgar.salary@gmail.com)"},
            timeout=15,
        )
        if resp.status_code != 200:
            return None

        vacancies = resp.json().get("items", [])
        salaries = []

        for v in vacancies:
            s = v.get("salary")
            if not s:
                continue

            sal_from = s.get("from")
            sal_to = s.get("to")
            currency = s.get("currency", "KZT")

            # Валютаны теңгеге айналдыру
            rates = {"KZT": 1, "RUR": 5.5, "USD": 470, "EUR": 515}
            rate = rates.get(currency, 1)

            if sal_from and sal_to:
                mid = (sal_from + sal_to) / 2 * rate
            elif sal_from:
                mid = sal_from * rate
            elif sal_to:
                mid = sal_to * rate
            else:
                continue

            salaries.append(mid)

        if not salaries:
            return None

        return round(sum(salaries) / len(salaries))

    except Exception:
        return None


def collect_all_stats() -> dict:
    """Барлық позициялар мен қалалар бойынша ЗП жинау"""
    results = {}
    total = len(POSITIONS) * len(CITIES)
    done = 0

    for position in POSITIONS:
        results[position] = {}
        for city_name, area_id in CITIES.items():
            avg = get_avg_salary(position, area_id)
            results[position][city_name] = avg
            done += 1
            print(f"[{done}/{total}] {position} / {city_name}: {avg}")
            time.sleep(0.3)  # API-ға жүктеме бермеу үшін

    return results


def format_salary(amount: int | None) -> str:
    if amount is None:
        return "деректер жоқ"
    return f"{amount:,}".replace(",", " ") + " ₸"


def build_message(stats: dict) -> str:
    """Telegram-ға арналған хабарлама жасау"""
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    date_range = f"{week_ago.strftime('%d.%m.%Y')}–{today.strftime('%d.%m.%Y')}"

    lines = [f"📊 *Апталық орташа жалақы есебі*", f"_{date_range}_", ""]

    for position, city_data in stats.items():
        # Кем дегенде бір қалада деректер болса ғана көрсет
        if all(v is None for v in city_data.values()):
            continue

        lines.append(f"*{position}*")
        for city_name, avg in city_data.items():
            lines.append(f"  {city_name}: {format_salary(avg)}")
        lines.append("")

    lines.append("_hh.kz деректері негізінде_")
    return "\n".join(lines)


def send_telegram(text: str):
    """Telegram-ға жіберу (ұзын хабарларды бөліп жібереді)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # 4000 символдан асса бөлу
    chunks = []
    while len(text) > 4000:
        split_at = text.rfind("\n", 0, 4000)
        if split_at == -1:
            split_at = 4000
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    chunks.append(text)

    for chunk in chunks:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
        }, timeout=15)
        print("Telegram:", resp.status_code, resp.json().get("ok"))
        time.sleep(0.5)


if __name__ == "__main__":
    print("Деректер жиналуда...")
    stats = collect_all_stats()

    print("\nTelegram-ға жіберілуде...")
    message = build_message(stats)
    send_telegram(message)

    print("Дайын!")
