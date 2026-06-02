# ЗП Бот

Дүйсенбі сайын 53 позиция бойынша Алматы, Астана, Шымкент қалаларының орташа жалақысын Telegram-ға жібереді.

---

## Орнату — 3 қадам

### 1. Telegram Bot жасау
1. Telegram-да [@BotFather](https://t.me/BotFather) ашу
2. `/newbot` жазу → атын беру
3. **Token** алу — мысалы: `7123456789:AAHxxxxxxx`
4. Ботыңды өзіңнің чатыңа қос, бір хабар жібер
5. Мына сілтемені ашып Chat ID алу:
   `https://api.telegram.org/bot<ТОКЕН>/getUpdates`
   → `"chat":{"id": МҰНДА_СЕН_ІЗДЕГЕН_ID}`

### 2. GitHub-қа жүктеу
```bash
git init
git add .
git commit -m "start"
git remote add origin https://github.com/СЕНІҢ_АТЫ/zp-bot.git
git push -u origin main
```

### 3. Secrets қосу
GitHub репода: **Settings → Secrets → Actions → New secret**

| Аты | Мәні |
|-----|------|
| `TELEGRAM_TOKEN` | Ботыңның токені |
| `TELEGRAM_CHAT_ID` | Чатыңның ID-сі |

**Бітті.** Енді бот дүйсенбі сайын таңертең 09:00-де (Алматы) өзі жіберіп тұрады.

---

## Қолмен іске қосу (тест үшін)
GitHub → Actions → Апталық ЗП есебі → **Run workflow**

---

## Хабарлама үлгісі
```
📊 Апталық орташа жалақы есебі
01.06.2026–07.06.2026

Маркетолог
  Алматы: 515 000 ₸
  Астана: 414 000 ₸
  Шымкент: 250 000 ₸

Backend разработчик
  Алматы: 850 000 ₸
  Астана: 720 000 ₸
  Шымкент: деректер жоқ
...
```
