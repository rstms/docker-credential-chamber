from docker_credential_chamber.cli import decode_key, encode_server


def test_encoder():
    uri = "http://www.example.org:433"
    key = encode_server(uri)
    assert isinstance(key, str)
    assert key.lower() == key
    _uri = decode_key(key)
    assert isinstance(_uri, str)
    assert uri == _uri
