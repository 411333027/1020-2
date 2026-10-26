import json

import pytest

from food_agent.analyzer import AnalysisError, extract_json_object, parse_claude_output, validate_analysis

GOOD = {
    "is_food": True,
    "name": "雞腿便當",
    "ingredients": [
        {"name": "白飯", "weight_g": 200, "kcal": 280},
        {"name": "炸雞腿", "weight_g": "150", "kcal": 380.4},
    ],
    "total_weight_g": 999,
    "total_kcal": 1,
}


def test_valid_food_uses_sum_of_ingredients():
    result = validate_analysis(GOOD)
    assert result.is_food
    assert result.total_weight_g == 350
    assert result.total_kcal == 660


def test_not_food_needs_only_name():
    result = validate_analysis({"is_food": False, "name": "馬克杯", "ingredients": [], "total_weight_g": 0, "total_kcal": 0})
    assert not result.is_food and result.name == "馬克杯" and result.total_kcal == 0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(is_food="yes"),
        lambda d: d.update(name=""),
        lambda d: d.update(name=123),
        lambda d: d.update(ingredients=[]),
        lambda d: d.update(ingredients="白飯"),
        lambda d: d["ingredients"][0].update(weight_g="很多"),
        lambda d: d["ingredients"][0].update(weight_g="200g"),
        lambda d: d["ingredients"][0].update(kcal=-5),
        lambda d: d["ingredients"][0].update(kcal=float("nan")),
        lambda d: d["ingredients"][0].update(kcal=float("inf")),
        lambda d: d["ingredients"][0].update(kcal=True),
        lambda d: d["ingredients"][0].update(kcal=None),
        lambda d: d["ingredients"][0].update(weight_g=10**6),
        lambda d: d["ingredients"].append("bad"),
        lambda d: d.update(name="x" * 500),
    ],
)
def test_bad_values_raise_analysis_error_not_crash(mutate):
    data = json.loads(json.dumps(GOOD))
    mutate(data)
    with pytest.raises(AnalysisError):
        validate_analysis(data)


def test_extract_json_handles_fences_and_noise():
    assert extract_json_object('好的：\n```json\n{"a": 1}\n```') == {"a": 1}


@pytest.mark.parametrize("text", ["", "no json here", "{bad json}", "[1,2]", "{"])
def test_extract_json_rejects_garbage(text):
    with pytest.raises(AnalysisError):
        extract_json_object(text)


def test_parse_claude_output_variants():
    envelope = {"type": "result", "is_error": False, "result": json.dumps(GOOD)}
    assert parse_claude_output(json.dumps(envelope)).total_kcal == 660
    structured = {"is_error": False, "result": "", "structured_output": GOOD}
    assert parse_claude_output(json.dumps(structured)).total_kcal == 660


@pytest.mark.parametrize(
    "raw", ["not json", "[]", json.dumps({"is_error": True, "result": "limit"}), json.dumps({"result": 5})]
)
def test_parse_claude_output_failures(raw):
    with pytest.raises(AnalysisError):
        parse_claude_output(raw)
