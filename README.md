# ua-banktools

A collection of Python tools and APIs for interacting with Ukrainian banks

## Banks currently supported

- PrivatBank (legal entities only)
- monobank (personal only)

## Features

- Object-oriented as much as possible, with IBANs validated by `schwifty`, timestamps automatically parsed into `datetime` objects, and known categorical values parsed into `enum`s.
- Multiple banks in one package.
