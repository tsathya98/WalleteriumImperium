"""
Advanced validation system for Receipt Scanner Agent
Multi-layer validation: semantic, mathematical, business logic, and data quality
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from config.constants import TRANSACTION_CATEGORIES, VENDOR_TYPES

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of validation with details about any issues found"""

    def __init__(
        self,
        is_valid: bool = True,
        errors: List[str] = None,
        warnings: List[str] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        """Add an error and mark as invalid"""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """Add a warning (doesn't invalidate)"""
        self.warnings.append(warning)


class ReceiptValidator:
    """Advanced validator for receipt analysis results"""

    def __init__(self, tolerance: float = 0.02):
        """
        Initialize validator

        Args:
            tolerance: Tolerance for mathematical validation (default $0.02)
        """
        self.tolerance = tolerance

    def validate_comprehensive(self, ai_result: Dict[str, Any]) -> ValidationResult:
        """
        Perform comprehensive validation of AI result

        Args:
            ai_result: Raw AI analysis result

        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult()

        # Layer 1: Semantic Validation
        self._validate_semantic(ai_result, result)

        # Layer 2: Mathematical Validation
        self._validate_mathematical(ai_result, result)

        # Layer 3: Business Logic Validation
        self._validate_business_logic(ai_result, result)

        # Layer 4: Data Quality Assurance
        self._validate_data_quality(ai_result, result)

        logger.info(
            f"Validation completed: valid={result.is_valid}, "
            f"errors={len(result.errors)}, warnings={len(result.warnings)}"
        )

        return result

    def _validate_semantic(self, ai_result: Dict[str, Any], result: ValidationResult):
        """Layer 1: Semantic Validation"""

        # Check required top-level fields
        required_fields = ["store_info", "items", "totals", "classification"]
        for field in required_fields:
            if field not in ai_result:
                result.add_error(f"Missing required field: {field}")

        # Validate categories exist in predefined list
        classification = ai_result.get("classification", {})
        overall_category = classification.get("overall_category")
        if overall_category and overall_category not in TRANSACTION_CATEGORIES:
            result.add_error(f"Invalid overall category: {overall_category}")

        # Validate vendor type
        vendor_type = classification.get("vendor_type")
        if vendor_type and vendor_type not in VENDOR_TYPES:
            result.add_error(f"Invalid vendor type: {vendor_type}")

        # Validate item categories
        items = ai_result.get("items", [])
        for i, item in enumerate(items):
            item_category = item.get("category")
            if item_category and item_category not in TRANSACTION_CATEGORIES:
                result.add_error(f"Invalid category for item {i}: {item_category}")

    def _validate_mathematical(
        self, ai_result: Dict[str, Any], result: ValidationResult
    ):
        """Layer 2: Mathematical Validation"""

        items = ai_result.get("items", [])
        totals = ai_result.get("totals", {})

        # Check if total is missing
        if "total" not in totals:
            result.add_warning(
                "Missing 'total' field in 'totals' object. Amount will be calculated from items."
            )

        # Calculate sum of item prices
        calculated_total = sum(item.get("total_price", 0) for item in items)
        declared_total = totals.get("total", 0)

        # Check total mismatch with tolerance
        if abs(calculated_total - declared_total) > self.tolerance:
            result.add_error(
                f"Total mismatch: calculated ${calculated_total:.2f} vs "
                f"declared ${declared_total:.2f} (diff: ${abs(calculated_total - declared_total):.2f})"
            )

        # Validate all prices are positive
        for i, item in enumerate(items):
            total_price = item.get("total_price", 0)
            unit_price = item.get("unit_price")
            quantity = item.get("quantity", 0)

            if total_price < 0:
                result.add_error(f"Negative total price for item {i}: ${total_price}")

            if unit_price is not None and unit_price < 0:
                result.add_error(f"Negative unit price for item {i}: ${unit_price}")

            if quantity < 0:
                result.add_error(f"Negative quantity for item {i}: {quantity}")

            # Warn about unusually high quantities
            if quantity > 100:
                result.add_warning(f"Unusually high quantity for item {i}: {quantity}")

        # Validate totals components
        subtotal = totals.get("subtotal")
        tax = totals.get("tax")
        discount = totals.get("discount")

        if subtotal is not None and subtotal < 0:
            result.add_error(f"Negative subtotal: ${subtotal}")
        if tax is not None and tax < 0:
            result.add_error(f"Negative tax: ${tax}")
        if discount is not None and discount < 0:
            result.add_error(f"Negative discount: ${discount}")

    def _validate_business_logic(
        self, ai_result: Dict[str, Any], result: ValidationResult
    ):
        """Layer 3: Business Logic Validation"""

        classification = ai_result.get("classification", {})
        vendor_type = classification.get("vendor_type")
        items = ai_result.get("items", [])

        # Restaurant validation
        if vendor_type == "RESTAURANT":
            categories = set(item.get("category") for item in items)
            non_restaurant_categories = categories - {"Restaurant, fast-food"}
            if non_restaurant_categories:
                result.add_warning(
                    f"Restaurant receipt has non-restaurant categories: {non_restaurant_categories}"
                )

        # Supermarket validation
        elif vendor_type == "SUPERMARKET":
            categories = set(item.get("category") for item in items)
            if len(categories) == 1 and len(items) > 3:
                result.add_warning(
                    f"Supermarket receipt with {len(items)} items has only one category: {categories}"
                )

        # Validate warranty consistency
        has_warranties_flag = classification.get("has_warranties", False)
        actual_warranties = any(item.get("warranty") for item in items)
        if has_warranties_flag != actual_warranties:
            result.add_error(
                f"Warranty flag mismatch: flag={has_warranties_flag}, actual={actual_warranties}"
            )

        # Validate subscription consistency
        has_subscriptions_flag = classification.get("has_subscriptions", False)
        actual_subscriptions = any(item.get("recurring") for item in items)
        if has_subscriptions_flag != actual_subscriptions:
            result.add_error(
                f"Subscription flag mismatch: flag={has_subscriptions_flag}, actual={actual_subscriptions}"
            )

    def _validate_data_quality(
        self, ai_result: Dict[str, Any], result: ValidationResult
    ):
        """Layer 4: Data Quality Assurance"""

        store_info = ai_result.get("store_info", {})
        items = ai_result.get("items", [])

        # Check for required fields
        if not store_info.get("name"):
            result.add_error("Missing store name")

        if not items:
            result.add_error("No items found in receipt")

        # Check for placeholder values
        if store_info.get("name") in ["Unknown", "Unknown Store"]:
            result.add_warning("Store name is placeholder value")

        # Validate date/time formats
        date_str = store_info.get("date")
        time_str = store_info.get("time")

        if date_str and date_str != "Unknown":
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                result.add_error(f"Invalid date format: {date_str}")

        if time_str and time_str != "Unknown":
            try:
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                result.add_error(f"Invalid time format: {time_str}")

        # Validate item descriptions
        for i, item in enumerate(items):
            name = item.get("name", "")
            description = item.get("description", "")

            if not name.strip():
                result.add_error(f"Empty item name for item {i}")

            if len(description) < 10:
                result.add_warning(
                    f"Very short description for item {i}: '{description}'"
                )


def validate_and_fix_result(
    ai_result: Dict[str, Any]
) -> Tuple[Dict[str, Any], ValidationResult]:
    """
    Validate AI result and apply automatic fixes where possible

    Args:
        ai_result: Raw AI analysis result

    Returns:
        Tuple of (fixed_result, validation_result)
    """
    validator = ReceiptValidator()
    validation_result = validator.validate_comprehensive(ai_result)

    # Create a copy for fixing
    fixed_result = ai_result.copy()

    # Apply automatic fixes
    _apply_automatic_fixes(fixed_result, validation_result)

    return fixed_result, validation_result


def _apply_automatic_fixes(result: Dict[str, Any], validation: ValidationResult):
    """Apply automatic fixes to common issues"""

    # Fix missing store name
    store_info = result.get("store_info", {})
    if not store_info.get("name"):
        store_info["name"] = "Unknown Store"
        logger.info("Applied fix: Set default store name")

    # Fix missing date/time
    if not store_info.get("date") or store_info.get("date") == "Unknown":
        store_info["date"] = datetime.now().strftime("%Y-%m-%d")
        logger.info("Applied fix: Set current date")

    if not store_info.get("time") or store_info.get("time") == "Unknown":
        store_info["time"] = "12:00"
        logger.info("Applied fix: Set default time")

    # Fix negative values
    items = result.get("items", [])
    for item in items:
        if item.get("total_price", 0) < 0:
            item["total_price"] = abs(item["total_price"])
            logger.info("Applied fix: Made negative total_price positive")

        if item.get("unit_price", 0) < 0:
            item["unit_price"] = abs(item["unit_price"])
            logger.info("Applied fix: Made negative unit_price positive")

        if item.get("quantity", 0) < 0:
            item["quantity"] = abs(item["quantity"])
            logger.info("Applied fix: Made negative quantity positive")
