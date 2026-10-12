from app.services.inventory import get_item, load_inventory


def test_inventory_size_within_required_range():
    items = load_inventory()
    assert 30 <= len(items) <= 50


def test_inventory_ids_are_unique_and_stable():
    items = load_inventory()
    ids = [item.product_id for item in items]
    assert len(ids) == len(set(ids))
    assert all(pid.startswith("SV-") for pid in ids)


def test_inventory_items_validate_against_schema():
    items = load_inventory()
    for item in items:
        assert item.unit_price > 0
        assert item.currency == "USD"
        assert item.center_stone_carat_min <= item.center_stone_carat_max


def test_get_item_found_and_missing():
    items = load_inventory()
    first_id = items[0].product_id
    assert get_item(first_id) is not None
    assert get_item("DOES-NOT-EXIST") is None
