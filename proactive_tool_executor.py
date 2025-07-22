import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("Workload Proactive Tools")


def analyze_screen_context(json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not json_data:
        logger.warning("❌ No JSON data provided for screen analysis")
        return None

    screen_context = {}

    # Check for screenData structure (current format)
    if "screenData" in json_data:
        screen_data = json_data["screenData"]
        screen_context["screen_name"] = screen_data.get("Screen", "")
        screen_context["popups"] = screen_data.get("Popups", [])
        screen_context["data_fields"] = {}

        # Extract fields from root JSON
        for key, value in json_data.items():
            if key != "screenData" and isinstance(value, (str, int, float)):
                screen_context["data_fields"][key] = value

        # Extract fields from screenData.ScreensData (nested structure)
        screens_data = screen_data.get("ScreensData", {})
        for presenter_name, presenter_data in screens_data.items():
            if isinstance(presenter_data, dict):
                for field_name, field_value in presenter_data.items():
                    if isinstance(field_value, (str, int, float)):
                        # Use a unique key to avoid conflicts
                        screen_context["data_fields"][f"{presenter_name}.{field_name}"] = field_value
                        # Also add without prefix for backward compatibility
                        if field_name not in screen_context["data_fields"]:
                            screen_context["data_fields"][field_name] = field_value

        logger.info(f"✅ Screen context found: {screen_context['screen_name']}")
        logger.info(f"✅ Data fields available: {list(screen_context['data_fields'].keys())}")
        return screen_context

    # TODO: Add support for other JSON structures if needed
    logger.warning("❌ No screen context found in JSON data")
    return None
