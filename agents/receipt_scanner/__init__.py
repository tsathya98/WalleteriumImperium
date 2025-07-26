# Receipt Scanner Agent Module
from .agent import EnhancedReceiptScannerAgent, get_enhanced_receipt_scanner_agent

# Export the main agent components
__all__ = ["EnhancedReceiptScannerAgent", "get_enhanced_receipt_scanner_agent"]

# Make the agent available as 'root_agent' for backward compatibility
root_agent = get_enhanced_receipt_scanner_agent()
