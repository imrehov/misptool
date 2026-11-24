import pytest

from src.misptool.domain.scorer import Scorer


CONNECTOR = 'misp-galaxy:threat-actor="Anunak"'


@pytest.mark.parametrize("node", [
    {"Tag": [{"name": CONNECTOR}, {"name": "tlp:amber"}]},
    {"Galaxy": [{"GalaxyCluster": [{"tag_name": CONNECTOR}]}]},
])
@pytest.mark.parametrize("scope", ["event", "attribute", "object_attribute"])
def test_collects_connector_tags_at_each_scope(node, scope):
    if scope == "event":
        event = node
    elif scope == "attribute":
        event = {"Attribute": [node]}
    else:
        event = {"Object": [{"Attribute": [node]}]}

    scorer = Scorer({"scoring": {"galaxy_tag_score": 3}})
    snapshot = scorer.build_event_snapshot({"Event": event})

    assert snapshot["galaxy_tag_names"] == [CONNECTOR]
    assert snapshot["score"] == 3


def test_connector_tags_are_unique_sorted_and_preserved():
    other = 'misp-galaxy:malware="Example \\"quoted\\" / ü"'
    event = {
        "Tag": [{"name": CONNECTOR}],
        "Galaxy": [{"GalaxyCluster": [{"tag_name": other}, {"tag_name": CONNECTOR}]}],
        "Attribute": [{"Tag": [{"name": CONNECTOR}]}],
    }
    scorer = Scorer({})

    assert scorer.get_galaxy_tag_names(event) == sorted([CONNECTOR, other])
    original = scorer.build_event_snapshot(event)
    event["Galaxy"][0]["GalaxyCluster"].reverse()
    assert scorer.build_event_snapshot(event)["fingerprint"] == original["fingerprint"]


@pytest.mark.parametrize("event", [
    {},
    {"Galaxy": None, "Attribute": None, "Object": None},
    {"Galaxy": [{"GalaxyCluster": [{}, {"tag_name": None}, {"tag_name": "tlp:amber"}]}]},
    {"Galaxy": [{"GalaxyCluster": [{"value": "Anunak", "GalaxyClusterRelation": [
        {"GalaxyCluster": {"tag_name": CONNECTOR}},
    ]}]}]},
])
def test_does_not_invent_connector_tags_or_collect_related_clusters(event):
    assert Scorer({}).get_galaxy_tag_names(event) == []
