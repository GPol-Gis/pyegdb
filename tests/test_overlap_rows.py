import pyegdb
import pyegdb.layout
import pyegdb.subdb


def test_overlap_rows() -> None:
    pyegdb.layout.debug_reset()
    pyegdb.layout.initialize(layout=pyegdb.layout.BoardLayout.ENGLISH)

    assert pyegdb.subdb.overlap_rows(0, 0) == 0
    assert pyegdb.subdb.overlap_rows(3, 3) == 0
    assert pyegdb.subdb.overlap_rows(0, 6) == 0
    assert pyegdb.subdb.overlap_rows(6, 0) == 0
    assert pyegdb.subdb.overlap_rows(6, 6) == 6
