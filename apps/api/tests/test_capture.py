CR = "/api/v1/capture-requests"
BC = "/api/v1/business-cards"


def test_phone_capture_flow(client, alice, bob):
    doc = client.post(BC, json={}, headers=alice["headers"]).json()
    assert client.get(f"{CR}/pending", headers=alice["headers"]).json() is None

    first = client.post(CR, json={"document_id": doc["id"], "side": "front"}, headers=alice["headers"])
    assert first.status_code == 201
    second = client.post(CR, json={"document_id": doc["id"], "side": "back"}, headers=alice["headers"]).json()
    # a newer request replaces the previous one
    assert client.get(f"{CR}/{first.json()['id']}", headers=alice["headers"]).json()["status"] == "cancelled"
    pending = client.get(f"{CR}/pending", headers=alice["headers"]).json()
    assert pending["id"] == second["id"] and pending["side"] == "back"

    # other users neither see nor complete it, nor target someone else's document
    assert client.get(f"{CR}/pending", headers=bob["headers"]).json() is None
    assert client.post(f"{CR}/{second['id']}/done", headers=bob["headers"]).status_code == 404
    assert client.post(CR, json={"document_id": doc["id"], "side": "front"}, headers=bob["headers"]).status_code == 404

    assert client.post(f"{CR}/{second['id']}/done", headers=alice["headers"]).json()["status"] == "done"
    assert client.get(f"{CR}/pending", headers=alice["headers"]).json() is None
