from tools import board

def get_board_from_stockfish_patzer(patzer, timeout=None):
    for line in patzer.custom_command('d', timeout=timeout):
        if line.startswith('Fen:'):
            return board.Board(line[5:])
