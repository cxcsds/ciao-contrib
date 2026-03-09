import pytest
import numpy as np

from ..criss_cross import line_point, line_line

# Define some positions and vectors that are used in several fo the tests below.
x = np.array([1, 2, 3])
y = np.array([4, 5.5, 6.5])
xy = np.array([x, y]).T
angle = np.deg2rad(45)
N = np.array([np.cos(angle), np.sin(angle)])
N2 = np.array([1, 0])

# Use the following code to draw an image of the specific examples with
# these numbers:
#
# import matplotlib.pyplot as plt
# fig, ax = plt.subplots()
# scat = ax.scatter(xy[:, 0], xy[:, 1], c=np.arange(xy.shape[0]))
# k_arr = np.linspace(-3, 3, 2)
# for i in range(xy.shape[0]):
#    c = f"C{i}"
#    ax.plot(xy[i, 0], xy[i, 1], "o", color=c, label=f"Source {i}")
#    for vec, ls in zip([vec_norm1, N2], ["-", ":"]):
#        ax.plot(xy[i, 0] + k_arr * vec[0], xy[i, 1] + k_arr * vec[1],
#            color=c, linestyle=ls,
#            label=f"Line {i} {'HEG' if ls == '-' else 'MEG'}")
#        ax.arrow(xy[i, 0], xy[i, 1], vec[0], vec[1],
#            ls=ls, color=c, head_width=0.1, head_length=0.1,
#            length_includes_head=True)
# ax.legend()
# ax.grid()

rng = np.random.default_rng()


def test_line_line_exception():
    with pytest.raises(
        ValueError, match="norm_arm1 needs to be normalized to length 1."
    ):
        line_line(src_pos=xy, norm_arm1=np.array([2, 0]), norm_arm2=N)
    with pytest.raises(
        ValueError, match="norm_arm1 needs to be normalized to length 1."
    ):
        line_line(src_pos=xy, norm_arm1=np.array([0.1, 0.2]), norm_arm2=N)
    with pytest.raises(
        ValueError, match="norm_arm2 needs to be normalized to length 1."
    ):
        line_line(src_pos=xy, norm_arm1=N, norm_arm2=np.array([-1.1, 0.5]))
    with pytest.raises(
        ValueError,
        match="norm_arm1 and norm_arm2 are parallel, so there are no intersection point.",
    ):
        line_line(src_pos=xy, norm_arm1=N, norm_arm2=N)


def test_line_point_generic():
    """Test some generic properties for line_point function.

    We run this with random numbers, so each time the test is run
    angles and positions will be different, but the properties
    being tested should always hold.
    """
    src_pos = rng.uniform(size=(10, 2))
    angle = np.random.uniform(0, 2 * np.pi)
    norm_vec = np.array([np.sin(angle), np.cos(angle)])
    k, d = line_point(src_pos, norm_vec)
    # We get back a 10*10 array
    assert k.shape == (10, 10)
    assert d.shape == (10, 10)
    # Distance from line to point that is the origin of the line
    assert d.diagonal() == pytest.approx(0)
    # and be located at the at the origin
    assert k.diagonal() == pytest.approx(0)
    # Distances are always positive
    assert np.all(d >= 0)
    # Since lines are parallel, the distance from point i to line j
    # should be the same as the distance from point j to line i.
    assert d.T == pytest.approx(d)
    # The distance to the closed point on one line, is the same,
    # but in the opposite direction, as the distance to the closest
    # point on the other line.
    assert k.T == pytest.approx(-k)


def test_line_point_example():
    """Test line_point with a simple example where we know the answer."""
    k, d = line_point(xy, N)
    # Point 1 and 2 are on the same line.
    assert d[1, 2] == pytest.approx(0)
    assert d[0, 1] == pytest.approx(3.53553391e-01)
    # Because 1 and 2 are on the same line, they have the same distance to 0
    assert d[0, 2] == pytest.approx(d[0, 1])
    assert k[1, 2] == pytest.approx(np.sqrt(2))
    # Point is 1 "in the middle" between 0 and 2, so the distances need to sum up.
    assert k[2, 0] == pytest.approx(k[2, 1] + k[1, 0])


def test_line_line_generic():
    """Test some generic properties for line_line function.

    We run this with random numbers, so each time the test is run
    angles and positions will be different, but the properties
    being tested should always hold.
    """
    src_pos = rng.uniform(size=(10, 2))
    angle1 = np.random.uniform(0, 2 * np.pi)
    # We can't have parallel lines, but the probability of that
    # happening with random numbers is basically zero.
    # I would worry about that in production code, but for testing this is fine.
    angle2 = np.random.uniform(0, 2 * np.pi)
    norm_vec1 = np.array([np.sin(angle1), np.cos(angle1)])
    norm_vec2 = np.array([np.sin(angle2), np.cos(angle2)])
    k1, k2 = line_line(src_pos, norm_vec1, norm_vec2)
    # We get back a 10*10 array
    assert k1.shape == (10, 10)
    assert k2.shape == (10, 10)
    # Distance from a point to itself is 0
    assert k1.diagonal() == pytest.approx(0)
    assert k2.diagonal() == pytest.approx(0)
    # We can get the point of intersection either by starting
    # from line 1 and going k1 along norm_vec1, or by starting
    # from line 2 and going k2 along norm_vec2.
    intersect1 = src_pos + k1[:, :, None] * norm_vec1
    intersect2 = src_pos + k2[:, :, None] * norm_vec2
    assert intersect1 == pytest.approx(intersect2)
    # All HEG and all MEG lines are parallel, so the following forms a
    # parallelogram, and the distance from point i along the HEG to the intersection
    # of HEG and MEG should be the same as the negative distance from point j
    # along it's HEG line to the intersection with the MEG of point i.
    assert k1.T == pytest.approx(-k1)
    assert k2.T == pytest.approx(-k2)


def test_line_line_example():
    """We use somewhat special values for the angles here to make sure the
    lines intersect at a point that's easy to verify.
    """
    k1, k2 = line_line(xy, N, N2)
    assert k1[0, :] == pytest.approx([0, 1.5 * np.sqrt(2), 2.5 * np.sqrt(2)])
    assert k2[0, :] == pytest.approx([0, -0.5, -0.5])
    assert k1[1, 2] == pytest.approx(np.sqrt(2))
    # Points 1 and 2 are on the same HEG line
    assert k2[1, 2] == pytest.approx(0)
