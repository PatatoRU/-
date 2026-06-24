from app.agents.query_agent import QueryUnderstandingAgent


def test_query_agent_detects_food_and_city():
    parsed = QueryUnderstandingAgent().parse("Найди кафе в Казани")
    assert parsed.category == "food"
    assert parsed.city == "Казань"
    assert parsed.needs_location is False


def test_query_agent_detects_nearby_request():
    parsed = QueryUnderstandingAgent().parse("Что есть рядом со мной?")
    assert parsed.category == "nearby"
    assert parsed.needs_location is True
