from nyayalay.router import route_domain


def test_router_schema_exists():
    result = route_domain
    assert callable(result)
