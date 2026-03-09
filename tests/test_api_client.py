from src.api_client import PowercordApiClient


def test_api_client_init():
    client = PowercordApiClient(base_url="http://test.com", api_key="123")
    assert client.base_url == "http://test.com"
    assert client.api_key == "123"
