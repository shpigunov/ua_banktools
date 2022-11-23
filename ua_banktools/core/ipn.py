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

    @property
    def inferred_dob(self) -> dt.date:
        """Перші п'ять цифр кодують дату народження власника номера — зазвичай,
        це п'ятизначне число є кількістю днів від 31 грудня 1899 року до дати
        народження особи.

        Однак, якщо однакову дату народження мають більше 5000 чоловіків (або
        5000 жінок)[8], то в деяких із них перші п'ять цифр будуть іншими.
        Наприклад, для дати народження 1 січня 1947 року реєстраційний номер
        може починатися як із цифри «1», так і з цифри «8»."""

        return dt.date(1899, 12, 31) + dt.timedelta(int(self.code[0:5]))

    @property
    def inferred_sex(self) -> str:
        """У передостанній цифрі закодовано стать власника:
        * якщо цифра непарна, стать — чоловіча
        * якщо парна — жіноча."""

        return "female" if int(self.code[-2]) % 2 == 0 else "male"

    @staticmethod
    def validate_control_digit(code: str) -> bool:
        """Десята цифра — контрольна."""

        # Алгоритм для її розрахунку такий (вважатимемо, що код має вигляд АБВГҐДЕЄЖЗ):
        # Розраховуємо контрольну суму Х = А*(-1) + Б*5 + В*7 + Г*9 + Ґ*4 + Д*6 + Е*10 + Є*5 + Ж*7
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

        # Остача від ділення контрольної суми на одинадцять буде контрольним
        # числом: Кч = Х - (11 * ціла частина від (Х/11)) (для Microsoft Excel
        # виглядає наступним чином =X-ROUND(X/11; 0)*11) або =ОСТАТ(X;11), для
        # англомовних версій та OpenOffice/LibreOffice Calc =MOD(X;11)).
        checksum = X - (11 * (X // 11))

        # Контрольне число може мати значення від нуля до десяти. У разі
        # залишку 10 старша одиниця відкидається. Контрольною цифрою буде
        # остання цифра контрольного числа (тобто, контрольне число за модулем 10):
        return checksum % 10 == d[-1]
