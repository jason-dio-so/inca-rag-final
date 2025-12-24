"""
Policy Parser Registry (STEP 8)

Purpose: Central registry for insurer-specific policy parsers

Constitutional guarantee:
- Only registered insurers can be processed
- Unregistered insurers → NotImplementedError
- Adding new insurer = add file + register() call only
"""
from typing import Dict, List
from .base_parser import BasePolicyParser


class PolicyParserRegistry:
    """
    Central registry for insurer-specific policy parsers

    Usage:
    1. Create parser class (inherit BasePolicyParser)
    2. Register: PolicyParserRegistry.register(MyParser())
    3. Get parser: PolicyParserRegistry.get_parser('INSURER_CODE')
    """

    _parsers: Dict[str, BasePolicyParser] = {}

    @classmethod
    def register(cls, parser: BasePolicyParser) -> None:
        """
        Register a parser for an insurer

        Args:
            parser: Parser instance implementing BasePolicyParser

        Raises:
            ValueError: If parser with same insurer_code already registered
        """
        insurer_code = parser.insurer_code

        if insurer_code in cls._parsers:
            raise ValueError(
                f"Parser for {insurer_code} already registered. "
                f"Cannot register duplicate parsers."
            )

        cls._parsers[insurer_code] = parser

    @classmethod
    def get_parser(cls, insurer_code: str) -> BasePolicyParser:
        """
        Get parser for insurer

        Args:
            insurer_code: Insurer code (e.g., 'SAMSUNG')

        Returns:
            BasePolicyParser instance for the insurer

        Raises:
            NotImplementedError: If parser not registered for this insurer
        """
        if insurer_code not in cls._parsers:
            available = list(cls._parsers.keys())
            raise NotImplementedError(
                f"Policy parser for {insurer_code} not yet implemented.\n"
                f"Available parsers: {available}\n"
                f"To add {insurer_code}: Create parser class and call register()"
            )

        return cls._parsers[insurer_code]

    @classmethod
    def list_supported_insurers(cls) -> List[str]:
        """
        List all registered insurers

        Returns:
            List of insurer codes with registered parsers
        """
        return list(cls._parsers.keys())

    @classmethod
    def is_supported(cls, insurer_code: str) -> bool:
        """
        Check if insurer is supported

        Args:
            insurer_code: Insurer code to check

        Returns:
            True if parser registered, False otherwise
        """
        return insurer_code in cls._parsers

    @classmethod
    def get_parser_info(cls, insurer_code: str) -> Dict[str, any]:
        """
        Get parser info for insurer

        Args:
            insurer_code: Insurer code

        Returns:
            Dict with parser info (supported_concepts, implementation_status)

        Raises:
            NotImplementedError: If parser not registered
        """
        parser = cls.get_parser(insurer_code)

        return {
            'insurer_code': parser.insurer_code,
            'supported_concepts': parser.supported_concepts,
            'implementation_status': parser.implementation_status
        }

    @classmethod
    def clear_registry(cls) -> None:
        """
        Clear all registered parsers

        WARNING: Only use in tests. Production code should never clear registry.
        """
        cls._parsers.clear()
