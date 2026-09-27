class Results:

    def __init__(self):
        self.write_ok = 0
        self.skipped = 0
        self.no_match = 0
        self.error = 0

    def incr_write_ok(self) -> None:
        self.write_ok += 1

    def incr_skipped(self) -> None:
        self.skipped += 1

    def incr_no_match(self) -> None:
        self.no_match += 1

    def incr_error(self) -> None:
        self.error += 1

    def total(self) -> int:
        return self.write_ok + self.skipped + self.no_match + self.error
