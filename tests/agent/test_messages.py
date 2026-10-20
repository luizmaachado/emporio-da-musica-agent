"""Reading the text of a message."""
from emporio.agent.messages import content_text


def test_a_plain_string_is_returned_as_is():
    assert content_text("olá") == "olá"


def test_text_blocks_are_joined():
    assert content_text([{"type": "text", "text": "a"}, "b", {"text": "c"}]) == "abc"


def test_other_blocks_are_kept_as_json():
    assert content_text([{"type": "image", "url": "x"}]) == '{"type": "image", "url": "x"}'
