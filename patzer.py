import threading
import queue
import collections

class Error(Exception):
    pass

class StreamOutOfSpaceError(Error):
    pass

class TimeoutExceeded(Error):
    pass

class BestMoveResponse(collections.namedtuple(
        'BestMoveResponse_', ['best_move', 'ponder', 'score']
        )):
    MATE_IN_ZERO = 1
    MATE_IN_ONE = 2
    DRAWN = 3

class EngineInterface():
    class StreamReader(threading.Thread):
        """Read the engine process streams in sep threads to avoid deadlock"""
        def __init__(self, stream, max_size=1000):
            threading.Thread.__init__(self)
            self.stream = stream
            self.queue = queue.Queue(max_size)
            self.daemon = True
            self.start()

        def run(self):
            for line in iter(self.stream.readline, b''):
                try:
                    self.queue.put_nowait(line)
                except queue.Full:
                    raise StreamOutOfSpaceError(
                        'Input stream for %r ran over max size' %
                        self.stream
                    )
            self.stream.close()

        def read(self, timeout=None):
            try:
                return str(self.queue.get(True, timeout), 'ascii').rstrip('\n')
            except queue.Empty:
                raise TimeoutExceeded()

    @classmethod
    def from_process(cls, engine_process):
        return cls(
            engine_process.stdin,
            engine_process.stdout
        )

    def __init__(self, input_stream, output_stream):
        self.input_stream = input_stream
        self.output_stream = self.StreamReader(output_stream)

    def write(self, command):
        self.input_stream.write(bytes(command + '\n', 'ascii'))
        self.input_stream.flush()

    def read(self, timeout=None):
        return self.output_stream.read(timeout=timeout)

    def wait_for(self, response, timeout=None):
        lines = []
        while True:
            value = self.read(timeout=timeout)
            lines.append(value)
            if value == response:
                return lines

    def wait_for_startswith(self, response_prefix, timeout=None):
        lines = []
        while True:
            value = self.read(timeout=timeout)
            lines.append(value)
            if value.startswith(response_prefix):
                return lines

class Patzer():
    def __init__(self, engine_interface):
        self.engine_interface = engine_interface

    def initialize_engine(self):
        self.engine_interface.write('uci')
        self.engine_interface.wait_for('uciok', timeout=10)

    def set_option(self, option, value):
        self.engine_interface.write(
            'setoption name %s value %s' % (option, value)
        )
        self.is_ready()

    def is_ready(self, timeout=10):
        self.engine_interface.write('isready')
        return self.engine_interface.wait_for('readyok', timeout=timeout)

    def new_game(self):
        self.engine_interface.write('ucinewgame')
        self.is_ready()

    def set_start_position(self, moves=None):
        self._set_position('startpos', moves=moves)

    def set_fen_position(self, fen, moves=None):
        self._set_position('fen %s' % fen, moves=moves)

    def _set_position(self, position, moves=None):
        suffix = ''
        if moves is not None:
            suffix = ' moves %s' % ' '.join(moves)
        self.engine_interface.write('position %s%s' % (position, suffix))

    def custom_command(self, command, timeout=None):
        self.engine_interface.write(command)
        return self.is_ready(timeout=timeout)[:-1]

    def go_and_get_best_move(self, timeout=None, **kwargs):
        self.go(**kwargs)
        return self.get_best_move(timeout=timeout)

    def go(self, movetime=None):
        go_command = self._get_go_command(movetime=movetime)
        self.engine_interface.write(go_command)

    def _parse_score(self, info_line):
        if 'score mate 0' in info_line:
            return BestMoveResponse.MATE_IN_ZERO
        elif 'score mate 1' in info_line:
            return BestMoveResponse.MATE_IN_ONE
        elif 'depth 0' in info_line and 'score cp 0' in info_line:
            return BestMoveResponse.DRAWN

    def get_best_move(self, timeout=None):
        move_info = self.engine_interface.wait_for_startswith(
            'bestmove', timeout=timeout
        )
        
        score = None
        info_line = None
        for line in reversed(move_info):
            if line.startswith('info depth'):
                score = self._parse_score(line)
                break

        best_move = move_info[-1]
        best_move_split = best_move.split()

        if 'ponder' in best_move:
            return BestMoveResponse(
                best_move=best_move_split[1],
                ponder=best_move_split[3],
                score=score
            )
        else:
            return BestMoveResponse(
                best_move=best_move_split[1],
                ponder=None,
                score=score
            )

    def _get_go_command(self, **kwargs):
        parameters = []
        for k, v in kwargs.items():
            if type(v) != bool:
                parameters.append('%s %s' % (k, v))
            else:
                if v:
                    parameters.append(k)
        return 'go ' + ' '.join(parameters)
