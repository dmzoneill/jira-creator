from typing import Any, Dict, List


def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processed_data: List[Dict[str, Any]] = []

    for item in data:
        if "id" in item and isinstance(item["id"], int):
            processed_item: Dict[str, Any] = {
                "id": item["id"],
                "value": item.get("value", 0) * 2,
            }
            processed_data.append(processed_item)

    return processed_data


def main() -> None:
    sample_data: List[Dict[str, Any]] = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3},
    ]

    result: List[Dict[str, Any]] = process_data(sample_data)
    print(result)


if __name__ == "__main__":
    main()
