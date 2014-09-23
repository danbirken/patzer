class SingleMoveEngine():
    def __init__(self, patzer):
        self.patzer = patzer

    def initialize(self):
        self.patzer.initialize_engine()
        self.patzer.set_option('threads', 4)
        self.patzer.set_option('contempt factor', 50)
        self.patzer.set_option('hash', 500)
        self.patzer.set_option('ponder', False)

    def set_position(self, fen, moves):
        self.patzer.new_game()
        self.patzer.set_fen_position(fen, moves=moves)

    def make_best_move(self, fen, moves, timeout=None, **kwargs):
        best_move = self.patzer.go_and_get_best_move(timeout=timeout, **kwargs)
        self.patzer.set_fen_position(fen, moves=moves + [best_move.best_move])
