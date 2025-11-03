"""
Password validation utilities
Provides password complexity checking and strength validation
"""

import re


class PasswordValidator:
    """
    Password complexity validator

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    """

    MIN_LENGTH = 8
    MAX_LENGTH = 100

    # Password complexity patterns
    UPPERCASE_PATTERN = re.compile(r"[A-Z]")
    LOWERCASE_PATTERN = re.compile(r"[a-z]")
    DIGIT_PATTERN = re.compile(r"\d")
    SPECIAL_CHAR_PATTERN = re.compile(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]')

    @classmethod
    def validate(cls, password):
        """
        Validate password complexity

        Args:
            password (str): Password to validate

        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        if not password:
            return False, ["Password is required"]

        errors = []

        # Check length
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")

        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")

        # Check complexity requirements
        if not cls.UPPERCASE_PATTERN.search(password):
            errors.append("Password must contain at least one uppercase letter")

        if not cls.LOWERCASE_PATTERN.search(password):
            errors.append("Password must contain at least one lowercase letter")

        if not cls.DIGIT_PATTERN.search(password):
            errors.append("Password must contain at least one number")

        if not cls.SPECIAL_CHAR_PATTERN.search(password):
            errors.append("Password must contain at least one special character (!@#$%^&*...)")

        return len(errors) == 0, errors

    @classmethod
    def get_strength(cls, password):
        """
        Calculate password strength score (0-5)

        Args:
            password (str): Password to evaluate

        Returns:
            int: Strength score from 0 (very weak) to 5 (very strong)
        """
        if not password:
            return 0

        score = 0

        # Length score
        if len(password) >= cls.MIN_LENGTH:
            score += 1
        if len(password) >= 12:
            score += 1

        # Complexity scores
        if cls.UPPERCASE_PATTERN.search(password):
            score += 1
        if cls.LOWERCASE_PATTERN.search(password):
            score += 1
        if cls.DIGIT_PATTERN.search(password):
            score += 1
        if cls.SPECIAL_CHAR_PATTERN.search(password):
            score += 1

        # Cap at 5
        return min(score, 5)

    @classmethod
    def get_strength_label(cls, password):
        """
        Get human-readable strength label

        Args:
            password (str): Password to evaluate

        Returns:
            str: Strength label (Very Weak, Weak, Fair, Good, Strong, Very Strong)
        """
        score = cls.get_strength(password)

        labels = {
            0: "Very Weak",
            1: "Weak",
            2: "Weak",
            3: "Fair",
            4: "Good",
            5: "Strong",
        }

        return labels.get(score, "Very Weak")


def validate_password_complexity(password):
    """
    Convenience function to validate password complexity

    Args:
        password (str): Password to validate

    Raises:
        ValueError: If password doesn't meet complexity requirements

    Returns:
        bool: True if valid
    """
    is_valid, errors = PasswordValidator.validate(password)

    if not is_valid:
        raise ValueError(". ".join(errors))

    return True
