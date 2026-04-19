import pytest
from cronwrap.grouping import group_by_tag, tag_summary, jobs_with_all_tags


JOBS = [
    {"id": "a", "tags": {"env": "prod", "team": "ops"}},
    {"id": "b", "tags": {"env": "dev", "team": "ops"}},
    {"id": "c", "tags": {"env": "prod", "team": "dev"}},
    {"id": "d", "tags": {}},
]


def test_group_by_tag_env():
    groups = group_by_tag(JOBS, "env")
    assert sorted(groups["prod"], key=lambda j: j["id"]) == [
        {"id": "a", "tags": {"env": "prod", "team": "ops"}},
        {"id": "c", "tags": {"env": "prod", "team": "dev"}},
    ]
    assert len(groups["dev"]) == 1


def test_group_by_tag_untagged():
    groups = group_by_tag(JOBS, "env")
    assert groups["__untagged__"] == [{"id": "d", "tags": {}}]


def test_group_by_tag_empty():
    assert group_by_tag([], "env") == {}


def test_tag_summary():
    summary = tag_summary(JOBS)
    assert summary["env"] == 3
    assert summary["team"] == 3


def test_tag_summary_empty():
    assert tag_summary([]) == {}


def test_jobs_with_all_tags_match():
    result = jobs_with_all_tags(JOBS, {"env": "prod", "team": "ops"})
    assert [j["id"] for j in result] == ["a"]


def test_jobs_with_all_tags_no_match():
    result = jobs_with_all_tags(JOBS, {"env": "staging"})
    assert result == []


def test_jobs_with_all_tags_single():
    result = jobs_with_all_tags(JOBS, {"team": "ops"})
    assert {j["id"] for j in result} == {"a", "b"}
