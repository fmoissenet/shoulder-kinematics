import pandas as pd
import pytest

from spartacus import DatasetCSV, Segment, BiomechDirection, BiomechCoordinateSystem, AnatomicalLandmark
from spartacus.src.checks import (
    check_segment_filled_with_nan,
)
from spartacus.src.frame_reader import Frame
from spartacus.src.utils import get_is_isb_column
from spartacus.src.utils import (
    get_segment_columns,
    get_segment_columns_direction,
)

print_warnings = True

to_pass_because_geometric = [
    ("Fung et al.", Segment.HUMERUS),  # geometric Humerus feature implement SoloVectors
    ("Kijima et al.", Segment.HUMERUS),
    ("Kim et al.", Segment.HUMERUS),
    ("Matsuki et al.", Segment.HUMERUS),
    ("Sugi et al.", Segment.HUMERUS),
]

df = pd.read_csv(DatasetCSV.CLEAN.value)
df = df.where(pd.notna(df), None)
authors = df["dataset_authors"].unique().tolist()


@pytest.mark.parametrize("author", authors)
def test_new_parsing(author):

    subdf = df[df["dataset_authors"] == author]

    for i, row in subdf.iterrows():
        print(row.dataset_authors)
        count = 0
        for segment_enum in Segment:
            print(segment_enum)
            tuple_test = (row.dataset_authors, segment_enum)

            if tuple_test in to_pass_because_geometric:
                count += 1
                continue

            if row.dataset_authors == "Bourne et al." and segment_enum == Segment.HUMERUS:
                print("")

            segment_cols = get_segment_columns(segment_enum)
            segment_cols_direction = get_segment_columns_direction(segment_enum)
            # first check
            if check_segment_filled_with_nan(row, segment_cols, print_warnings=print_warnings):
                continue

            if row.thorax_is_global and segment_enum == Segment.THORAX:
                print("Thorax is global", row.thorax_is_global)
                # build the coordinate system
                bsys_new = BiomechCoordinateSystem.from_biomech_directions(
                    x=BiomechDirection.from_string(row[segment_cols[0]]),
                    y=BiomechDirection.from_string(row[segment_cols[1]]),
                    z=BiomechDirection.from_string(row[segment_cols[2]]),
                    origin=None,
                    segment=segment_enum,
                )
            else:

                frame = Frame.from_xyz_string(
                    x_axis=row[segment_cols_direction[0]],
                    y_axis=row[segment_cols_direction[1]],
                    z_axis=row[segment_cols_direction[2]],
                    origin=row[segment_cols_direction[3]],
                    segment=segment_enum,
                    side="right" if row.side_as_right or segment_enum == Segment.THORAX else row.side,
                )
                print(frame.side)
                print(frame.x_axis.principal_direction())
                print(frame.x_axis.compute_default_vector())
                print(frame.y_axis.principal_direction())
                print(frame.y_axis.compute_default_vector())
                print(frame.z_axis.principal_direction())
                print(frame.z_axis.compute_default_vector())

                assert frame.x_axis.biomech_direction() == BiomechDirection.from_string(row[segment_cols[0]])
                assert frame.y_axis.biomech_direction() == BiomechDirection.from_string(row[segment_cols[1]])
                assert frame.z_axis.biomech_direction() == BiomechDirection.from_string(row[segment_cols[2]])

                try:
                    is_isb_col = get_is_isb_column(segment_enum)
                    assert frame.is_isb == row[is_isb_col]

                except Exception as e:
                    print(e)
                    print("MISLABELED ISB:")
                    print(tuple_test)
                    print("to check ISB:")
                    print("landmarks :", frame.landmarks)
                    print("expected landmarks :", frame.expected_isb_landmarks)

                    print(frame.origin)
                    print(frame.is_isb_oriented)
                    print("has isb landmark", frame.has_isb_landmarks)
                    print("####################")

                # build the coordinate system
                bsys_old = BiomechCoordinateSystem.from_biomech_directions(
                    x=BiomechDirection.from_string(row[segment_cols[0]]),
                    y=BiomechDirection.from_string(row[segment_cols[1]]),
                    z=BiomechDirection.from_string(row[segment_cols[2]]),
                    origin=AnatomicalLandmark.from_string(row[segment_cols[3]]),
                    segment=segment_enum,
                )
                bsys_new = BiomechCoordinateSystem.from_frame(frame)

                assert frame.postero_anterior_local_axis == bsys_new.anterior_posterior_axis
                assert frame.medio_lateral_local_axis == bsys_new.medio_lateral_axis
                assert frame.infero_superior_local_axis == bsys_new.infero_superior_axis

            # third check if the segment is direct or not
            if not bsys_new.is_direct():
                if print_warnings:
                    print(
                        f"{row.dataset_authors}, " f"Segment {segment_enum.value} is not direct, " f"it should be !!!"
                    )
                output = False
