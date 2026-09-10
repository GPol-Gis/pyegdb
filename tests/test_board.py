import pyegdb

# from pyegdb.layout import BoardLayout
import pyegdb.layout
import pyegdb.state
import pyegdb.subdb


def test_board_size() -> None:
    pyegdb.layout.debug_reset()
    pyegdb.layout.initialize(layout=pyegdb.layout.BoardLayout.ENGLISH)
    assert pyegdb.layout.DIMENSION == 8
    assert pyegdb.layout.is_initialized()


def test_material_division_size() -> None:
    pyegdb.layout.initialize(
        layout=pyegdb.layout.BoardLayout.ENGLISH,
    )

    dbsize = pyegdb.subdb.size(
        pyegdb.state.Material(bm=4, wm=2),
    )
    assert dbsize == 5_933_850


def test_lead_men_division_size() -> None:
    pyegdb.layout.initialize(
        layout=pyegdb.layout.BoardLayout.ENGLISH,
    )

    dbsize = pyegdb.subdb.size(
        pyegdb.state.Material(bm=2, wm=2), black_man_rank=2, white_man_rank=2
    )
    assert dbsize == 1_444
