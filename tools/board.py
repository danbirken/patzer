class Error(Exception):
    pass

class InvalidFen(Error):
    pass

class Board():
    def __init__(self, fen):
        parts = fen.split()

        if len(parts) != 6:
            raise InvalidFen()

        self.position = parts[0]
        self.move = parts[1]
        self.castle = parts[2]
        self.en_passant = parts[3]

        try:
            self.halfmove = int(parts[4])
            self.fullmove = int(parts[5])
        except ValueError:
            raise InvalidFen()

    def as_cvtv_output(self):
        output = []

        rows = self.position.split('/')
        for row in rows:
            for letter in row:
                if letter.lower() in ('rnbqkp'):
                    if letter.islower():
                        output.append('b' + letter.lower())
                    else:
                        output.append('w' + letter.lower())
                else:
                    blanks = int(letter)
                    output.extend(['--'] * blanks)

        return ''.join(output)
