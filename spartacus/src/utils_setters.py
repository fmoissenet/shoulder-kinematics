from .biomech_system import BiomechCoordinateSystem
from .enums_biomech import Segment, JointType, EulerSequence, AnatomicalLandmark, FrameType
from .frame_reader import Frame
from .joint import Joint
from .thoracohumeral_angle import ThoracohumeralAngle
from .utils import get_segment_columns_direction


def set_parent_segment_from_row(row, segment: Segment):
    segment_cols_direction = get_segment_columns_direction(segment)
    method = (
        Frame.from_global_thorax_strings
        if segment == Segment.THORAX and row.thorax_is_global
        else Frame.from_xyz_string
    )
    frame_parent = method(
        x_axis=row[segment_cols_direction[0]],
        y_axis=row[segment_cols_direction[1]],
        z_axis=row[segment_cols_direction[2]],
        origin=row[segment_cols_direction[3]],
        segment=segment,
        side="right" if row.side_as_right or segment == Segment.THORAX else row.side,
    )
    parent_biomech_sys = BiomechCoordinateSystem.from_frame(frame_parent)
    return parent_biomech_sys


def set_child_segment_from_row(row, segment: Segment):
    segment_cols_direction = get_segment_columns_direction(segment)
    frame_child = Frame.from_xyz_string(
        x_axis=row[segment_cols_direction[0]],
        y_axis=row[segment_cols_direction[1]],
        z_axis=row[segment_cols_direction[2]],
        origin=row[segment_cols_direction[3]],
        segment=segment,
        side="right" if row.side_as_right else row.side,
    )
    child_biomech_sys = BiomechCoordinateSystem.from_frame(frame_child)
    return child_biomech_sys


def set_joint_from_row(row, joint: JointType):

    try:
        translation_frame = FrameType.from_string(row.displacement_cs)
    except:
        translation_frame = None

    return Joint(
        joint_type=JointType.from_string(row.joint),
        euler_sequence=EulerSequence.from_string(row.euler_sequence),  # throw a None
        translation_origin=AnatomicalLandmark.from_string(row.origin_displacement),
        translation_frame=translation_frame,
        parent_segment=set_parent_segment_from_row(row, joint.parent),
        child_segment=set_child_segment_from_row(row, joint.child),
    )


def set_thoracohumeral_angle_from_row(row, joint: Joint):
    return ThoracohumeralAngle(
        euler_sequence=EulerSequence.from_string(row.thoracohumeral_sequence),
        angle=row.thoracohumeral_angle,
        parent_segment=joint.parent_segment,
        child_segment=joint.child_segment,
    )
