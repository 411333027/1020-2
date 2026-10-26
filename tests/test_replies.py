from datetime import date, datetime

from food_agent import replies
from food_agent.analyzer import Analysis, Ingredient
from food_agent.storage import Meal

FOOD = Analysis(True, "便當", (Ingredient("白飯", 200, 280),), 200, 280)


def test_food_reply_has_everything():
    text = replies.format_result(FOOD, date(2026, 10, 26), 1450)
    for part in ("是食物", "便當", "白飯", "200 g", "280 大卡", "整餐", "當日已攝取熱量", "1450"):
        assert part in text


def test_not_food_reply_still_shows_daily_total():
    text = replies.format_result(Analysis(False, "馬克杯", (), 0, 0), date(2026, 10, 26), 100)
    assert "不是食物" in text and "馬克杯" in text and "當日已攝取熱量" in text and "100" in text


def test_mentions_in_model_text_are_neutralised():
    evil = Analysis(True, "@everyone", (Ingredient("@here", 1, 1),), 1, 1)
    text = replies.format_result(evil, date(2026, 10, 26), 1)
    assert "@everyone" not in text and "@here" not in text


def test_query_empty_and_total():
    assert "還沒有記錄" in replies.format_daily_query(date(2026, 10, 26), [])
    meals = [
        Meal(datetime(2026, 10, 26, 8, 0), "小明", "早餐", 300),
        Meal(datetime(2026, 10, 26, 12, 0), "小華", "午餐", 700),
    ]
    text = replies.format_daily_query(date(2026, 10, 26), meals)
    assert text.splitlines()[-1] == "2026/10/26 總共約 1000 大卡"


def test_query_truncates_but_keeps_full_total():
    meals = [Meal(datetime(2026, 10, 26, 8, 0), "u" * 20, "食物" * 20, 10) for _ in range(500)]
    text = replies.format_daily_query(date(2026, 10, 26), meals)
    assert len(text) < 2000 and text.splitlines()[-1].endswith("總共約 5000 大卡")
