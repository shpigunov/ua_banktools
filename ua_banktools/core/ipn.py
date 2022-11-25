import datetime as dt


class IPNValidationError(Exception):
    pass


class IPN:
    """A class representing an Individual Taxpayer Identification number for
    Ukrainian residents. Contains a 10-dicgit code, validation methods and
    properties that allow to infer the bearer's date of birth and sex."""

    def __init__(self, code: str) -> None:

        # Validation block

        # A valid IPN consists of 10 characters
        if len(code) != 10:
            raise IPNValidationError("Invalid number of digits")
        # All characters must be digits
        if not code.isdigit():
            raise IPNValidationError("Only digits are allowed in an IPN code")
        # Check control digit
        if not self.validate_control_digit(code):
            raise IPNValidationError("Control digit invalid")

        self.code = code

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return f"IPN: {self.code}"

    @property
    def inferred_dob(self) -> dt.date:
        """The first five digits encode the bearer's date of birth: usually, it's
        the 5-digit number corresponding to the number of days elapsed from
        December 31, 1899 to the bearer's date of birth.

        However, if over 5,000 men or women happen to be born on a particular day,
        some of them may have different digits in this section of the IPN. For
        example, for January 1, 1947, the number can start with both `1` and `8`.
        """

        return dt.date(1899, 12, 31) + dt.timedelta(int(self.code[0:5]))

    @property
    def inferred_sex(self) -> str:
        """The digit before the last one encodes the bearer's sex:
        * male if the digit is odd, and
        * female if the digit is even."""

        return "female" if int(self.code[-2]) % 2 == 0 else "male"

    @staticmethod
    def validate_control_digit(code: str) -> bool:
        """The digit in the tenth (last) position serves as a checksum digit."""

        # The checksum algorithm is as follows:
        # If the code has the format `ABCDEFGHIJ`, calculate the checksum as:
        # Х = A*(-1) + B*5 + C*7 + D*9 + E*4 + F*6 + G*10 + H*5 + I*7
        d = [int(c) for c in code]
        X = (
            d[0] * -1
            + d[1] * 5
            + d[2] * 7
            + d[3] * 9
            + d[4] * 4
            + d[5] * 6
            + d[6] * 10
            + d[7] * 5
            + d[8] * 7
        )

        # The remainder from the division of the checksum by 11 will be the check
        # number: check_number = X - (11 * (X // 11)), or:
        check_number = X % 11

        # The check number may turn out to be between 0 to 10. In case the
        # remainder is 10, the `1` in the first position is dropped. The resulting
        # one digit must coincide with the last digit of the IPN.
        return check_number % 10 == d[-1]
