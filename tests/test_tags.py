import pytest
from cronwrap.tags import parse_tags, format_tags, filter_by_tag, merge_tags


def test_parse_tags_key_value():
    assert parse_tags("env=prod,team=ops") == {"env": "prod", "team": "ops"}


def test_parse_tags_bare_keys():
    assert parse_tags("critical,nightly") == {"critical": "true", "nightly": "true"}


def test_parse_tags_mixed():
    result = parse_tags("env=staging,critical")
    assert result == {"env": "staging", "critical": "true"}


def test_parse_tags_empty_string():
    assert parse_tags("") == {}


def test_parse_tags_whitespace():
    assert parse_tags("  ") == {}


def test_parse_tags_ignores_empty_parts():
    assert parse_tags("a=1,,b=2") == {"a": "1", "b": "2"}


def test_format_tags_roundtrip():
    tags = {"env": "prod", "team": "ops"}
    assert parse_tags(format_tags(tags)) == tags


def test_format_tags_bare_key():
    assert format_tags({"critical": "true"}) == "critical"


def test_filter_by_tag_key_only():
    jobs = [
        {"id": "a", "tags": {"env": "prod"}},
        {"id": "b", "tags": {"env": "dev"}},
        {"id": "c", "tags": {}},
    ]
    result = filter_by_tag(jobs, "env")
    assert [j["id"] for j in result] == ["a", "b"]


def test_filter_by_tag_key_and_value():
    jobs = [
        {"id": "a", "tags": {"env": "prod"}},
        {"id": "b", "tags": {"env": "dev"}},
    ]
    result = filter_by_tag(jobs, "env", "prod")
    assert [j["id"] for j in result] == ["a"]


def test_filter_by_tag_no_match():
    jobs = [{"id": "a", "tags": {"env": "prod"}}]
    assert filter_by_tag(jobs, "team") == []


def test_merge_tags_override():
    base = {"env": "dev", "team": "ops"}
    override = {"env": "prod", "region": "us"}
    result = merge_tags(base, override)
    assert result == {"env": "prod", "team": "ops", "region": "us"}


def test_merge_tags_no_mutation():
    base = {"env": "dev"}
    override = {"env": "prod"}
    merge_tags(base, override)
    assert base["env"] == "dev"
