import numpy as np
import pandas as pd

from .enums import Segment, Correction
from .utils import (
    get_segment_columns,
    get_correction_column,
    BiomechCoordinateSystem,
    biomech_direction_string_to_enum,
    biomech_origin_string_to_enum,
    Joint,
    joint_string_to_enum,
    segment_str_to_enum,
    euler_sequence_to_enum,
    correction_str_to_enum,
    convert_rotation_matrix_from_one_coordinate_system_to_another,
)

from .angle_conversion_callbacks import (
    get_angle_conversion_callback_from_tuple,
    get_angle_conversion_callback_from_sequence,
    get_angle_conversion_callback_to_isb_with_sequence,
)

from .checks import (
    check_segment_filled_with_nan,
    check_is_isb_segment,
    check_is_euler_sequence_provided,
    check_is_translation_provided,
    check_parent_child_joint,
    check_same_orientation,
)


class RowData:
    """
    This class is used to store the data of a row of the dataset and make it accessible through attributes and methods.
    """

    def __init__(self, row: pd.Series):
        """
        Parameters
        ----------
        row : pandas.Series
            The row of the dataset to store.
        """

        self.row = row

        self.joint = None

        self.parent_segment = segment_str_to_enum(self.row.parent)
        self.parent_columns = get_segment_columns(self.parent_segment)
        self.parent_biomech_sys = None

        self.child_segment = segment_str_to_enum(self.row.child)
        self.child_columns = get_segment_columns(self.child_segment)
        self.child_biomech_sys = None

        self.has_rotation_data = None
        self.has_translation_data = None

        self.parent_segment_usable_for_rotation_data = None
        self.child_segment_usable_for_rotation_data = None

        self.parent_segment_usable_for_translation_data = None
        self.child_segment_usable_for_translation_data = None

        self.parent_definition_risk = None
        self.child_definition_risk = None

        self.usable_rotation_data = None
        self.usable_translation_data = None

        self.rotation_data_risk = None
        self.translation_data_risk = None

        self.rotation_correction_callback = None
        self.translation_correction_callback = None

    def check_all_segments_validity(self, print_warnings: bool = False) -> bool:
        """
        Check all the segments of the row are valid.
        First, we check if the segment is provided, i.e., no NaN values.
        Second, we check if the segment defined as is_isb = True or False in the dataset
        and if the orientations of axis defined in the dataset fits with isb definition.

        (we don't mind if it's not a isb segment, we just don't want to have a segment
        that matches the is_isb given)

        Third, we check the frame are direct, det(R) = 1. We want to have a direct frame.

        Returns
        -------
        bool
            True if all the segments are valid, False otherwise.
        """
        output = True
        for segment_enum in Segment:
            segment_cols = get_segment_columns(segment_enum)
            # first check
            if check_segment_filled_with_nan(self.row, segment_cols, print_warnings=print_warnings):
                continue

            # build the coordinate system
            bsys = BiomechCoordinateSystem.from_biomech_directions(
                x=biomech_direction_string_to_enum(self.row[segment_cols[0]]),
                y=biomech_direction_string_to_enum(self.row[segment_cols[1]]),
                z=biomech_direction_string_to_enum(self.row[segment_cols[2]]),
                origin=biomech_origin_string_to_enum(self.row[segment_cols[3]]),
                segment=segment_enum,
            )
            # second check
            if not check_is_isb_segment(self.row, bsys, print_warnings=print_warnings):
                output = False

            # third check if the segment is direct or not
            if not bsys.is_direct():
                if print_warnings:
                    print(
                        f"{self.row.article_author_year}, "
                        f"Segment {segment_enum.value} is not direct, "
                        f"it should be !!!"
                    )
                output = False

        return output

    def check_joint_validity(self, print_warnings: bool = False) -> bool:
        """
        Check if the joint defined in the dataset is valid.
        We expect the joint to have a valid euler sequence, i.e., no NaN values., three letters and valid letters.
        If not we expect the joint to have a valid translation, i.e., no NaN values.

        We expect the joint to have good parent and child definitions
        We expect the joint to have defined parent and child segments, i.e., no NaN values.

        Returns
        -------
        bool
            True if the joint is valid, False otherwise.
        """
        output = True

        # todo: separate as much as possible the rotations checks and the translations checks

        no_euler_sequence = not check_is_euler_sequence_provided(self.row, print_warnings=print_warnings)
        no_translation = not check_is_translation_provided(self.row, print_warnings=print_warnings)

        self.has_rotation_data = not no_euler_sequence
        self.has_translation_data = not no_translation

        if no_euler_sequence and no_translation:
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has no euler sequence defined, "
                    f" and no translation defined, "
                    f"it should not be empty !!!"
                )
            return output

        if no_euler_sequence:  # Only translation is provided
            self.joint = Joint(
                joint_type=joint_string_to_enum(self.row.joint),
                euler_sequence=euler_sequence_to_enum(self.row.euler_sequence),  # throw a None
                translation_origin=biomech_origin_string_to_enum(self.row.origin_displacement),
                translation_frame=segment_str_to_enum(self.row.displacement_cs),
            )

        elif no_translation:  # Only rotation is provided
            self.joint = Joint(
                joint_type=joint_string_to_enum(self.row.joint),
                euler_sequence=euler_sequence_to_enum(self.row.euler_sequence),
                translation_origin=None,
                translation_frame=None,
            )

        else:  # translation and rotation are both provided
            self.joint = Joint(
                joint_type=joint_string_to_enum(self.row.joint),
                euler_sequence=euler_sequence_to_enum(self.row.euler_sequence),
                translation_origin=biomech_origin_string_to_enum(self.row.origin_displacement),
                translation_frame=segment_str_to_enum(self.row.displacement_cs),
            )

        if not check_parent_child_joint(self.joint, row=self.row, print_warnings=print_warnings):
            output = False

        # check database if nan in one the segment of the joint
        if check_segment_filled_with_nan(self.row, self.parent_columns, print_warnings=print_warnings):
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has a NaN value in the parent segment {self.row.parent}, "
                    f"it should not be empty !!!"
                )

        if check_segment_filled_with_nan(self.row, self.child_columns, print_warnings=print_warnings):
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has a NaN value in the child segment {self.row.child}, "
                    f"it should not be empty !!!"
                )

        return output

    def set_segments(self):
        """
        Set the parent and child segments of the joint.
        """

        self.parent_biomech_sys = BiomechCoordinateSystem.from_biomech_directions(
            x=biomech_direction_string_to_enum(self.row[self.parent_columns[0]]),
            y=biomech_direction_string_to_enum(self.row[self.parent_columns[1]]),
            z=biomech_direction_string_to_enum(self.row[self.parent_columns[2]]),
            origin=biomech_origin_string_to_enum(self.row[self.parent_columns[3]]),
            segment=self.parent_segment,
        )
        self.child_biomech_sys = BiomechCoordinateSystem.from_biomech_directions(
            x=biomech_direction_string_to_enum(self.row[self.child_columns[0]]),
            y=biomech_direction_string_to_enum(self.row[self.child_columns[1]]),
            z=biomech_direction_string_to_enum(self.row[self.child_columns[2]]),
            origin=biomech_origin_string_to_enum(self.row[self.child_columns[3]]),
            segment=self.child_segment,
        )

    def extract_corrections(self, segment: Segment) -> str:
        """
        Extract the correction cell of the correction column.
        ex: if the correction column is parent_to_isb, we extract the correction cell parent_to_isb
        """
        correction_column = get_correction_column(segment)
        correction_cell = self.row[correction_column]

        if correction_cell == "nan":
            correction_cell = None
        if not isinstance(correction_cell, str):
            if np.isnan(correction_cell):
                correction_cell = None
        else:
            # separate strings with a comma in several element of list
            correction_cell = correction_cell.replace(" ", "").split(",")
            for i, correction in enumerate(correction_cell):
                correction_cell[i] = correction_str_to_enum(correction)

        return correction_cell

    def _check_segment_has_no_correction(self, correction, print_warnings: bool = False) -> bool:
        if correction is not None:
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has a correction value in the child segment {self.row.parent}, "
                    f"it should be empty !!!, because the segment is isb. "
                    f"Parent correction: {correction}"
                )
        else:
            output = True
        return output

    def _check_segment_has_kolz_correction(self, correction, print_warnings: bool = False) -> bool:
        correction = [] if correction is None else correction
        condition_scapula = (
            Correction.SCAPULA_KOLZ_AC_TO_PA_ROTATION in correction
            or Correction.SCAPULA_KOLZ_GLENOID_TO_PA_ROTATION in correction
        )
        if not condition_scapula:
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has no correction value in the parent segment {self.row.parent}, "
                    f"it should be filled with a {Correction.SCAPULA_KOLZ_AC_TO_PA_ROTATION} or a "
                    f"{Correction.SCAPULA_KOLZ_GLENOID_TO_PA_ROTATION} correction, because the segment "
                    f"origin is not on an isb axis. "
                    f"Current value: {correction}"
                )
        else:
            output = True
        return output

    def _check_segment_has_to_isb_correction(self, correction, print_warnings: bool = False) -> bool:
        correction = [] if correction is None else correction
        if not (Correction.TO_ISB_ROTATION in correction):
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has no correction value in the parent segment {self.row.parent}, "
                    f"it should be filled with a {Correction.TO_ISB_ROTATION}, because the segment is not isb. "
                    f"Current value: {correction}"
                )
        else:
            output = True
        return output

    def _check_segment_has_to_isb_like_correction(self, correction, print_warnings: bool = False) -> bool:
        correction = [] if correction is None else correction
        if not (Correction.TO_ISB_LIKE_ROTATION in correction):
            output = False
            if print_warnings:
                print(
                    f"Joint {self.row.joint} has no correction value in the parent segment {self.row.parent}, "
                    f"it should be filled with a "
                    f"{Correction.TO_ISB_LIKE_ROTATION} correction, because the segment is not isb. "
                    f"Current value: {correction}"
                )
        else:
            output = True
        return output

    def check_segments_correction_validity(self, print_warnings: bool = False) -> tuple[bool, bool]:
        """
        We expect the correction columns to be filled with valid values.
        ex: if both segment are not isb, we expect the correction to_isb to be filled
        ex: if both segment are isb, we expect no correction to be filled
        ex: if both segment are isb, and euler sequence is isb, we expect no correction to be filled
        ex: if both segment are isb, and euler sequence is not isb, we expect the correction to_isb to be filled
        etc...

        Return
        ------
        output:tuple[bool, bool]
            rotation_data_validity, translation_data_validity
        """
        parent_output = True
        child_output = True

        parent_correction = self.extract_corrections(self.parent_segment)
        child_correction = self.extract_corrections(self.child_segment)

        # if both segments are isb, we expect no correction to be filled
        if self.parent_biomech_sys.is_isb() and self.child_biomech_sys.is_isb():
            parent_output = self._check_segment_has_no_correction(parent_correction, print_warnings=print_warnings)
            child_output = self._check_segment_has_no_correction(child_correction, print_warnings=print_warnings)

            if not (parent_output and child_output):
                if print_warnings:
                    print(
                        f"Joint {self.row.joint} has a correction value in the parent segment {self.row.parent}, "
                        f" and in the child segment {self.row.child}, "
                        f"they should be empty !!!, because the segment is isb. "
                        f"Parent correction: {parent_correction}"
                        f"Child correction: {child_correction}"
                    )
            self.parent_segment_usable_for_rotation_data = parent_output
            self.child_segment_usable_for_rotation_data = child_output
            self.parent_segment_usable_for_translation_data = parent_output
            self.child_segment_usable_for_translation_data = child_output

        # if both segments are isb oriented, but origin is on an isb axis, we expect no correction be filled
        # so that we can consider rotation data as isb
        if self.parent_biomech_sys.is_isb_oriented() and self.parent_biomech_sys.is_origin_on_an_isb_axis():
            parent_output = self._check_segment_has_no_correction(parent_correction, print_warnings=print_warnings)
            self.parent_segment_usable_for_rotation_data = parent_output
            self.parent_segment_usable_for_translation_data = False

        if self.child_biomech_sys.is_isb_oriented() and self.child_biomech_sys.is_origin_on_an_isb_axis():
            child_output = self._check_segment_has_no_correction(child_correction, print_warnings=print_warnings)
            self.child_segment_usable_for_rotation_data = child_output
            self.child_segment_usable_for_translation_data = False

        if self.parent_biomech_sys.is_isb_oriented() and not self.parent_biomech_sys.is_origin_on_an_isb_axis():
            if self.parent_segment == Segment.SCAPULA:
                parent_output = self._check_segment_has_kolz_correction(
                    parent_correction, print_warnings=print_warnings
                )
            else:
                self.parent_definition_risk = True
            self.parent_segment_usable_for_rotation_data = parent_output
            self.parent_segment_usable_for_translation_data = False

        if self.child_biomech_sys.is_isb_oriented() and not self.child_biomech_sys.is_origin_on_an_isb_axis():
            if self.child_segment == Segment.SCAPULA:
                parent_output = self._check_segment_has_kolz_correction(child_correction, print_warnings=print_warnings)
            else:
                self.child_definition_risk = True
            self.child_segment_usable_for_rotation_data = child_output
            self.child_segment_usable_for_translation_data = False

        # if segments are not isb, we expect the correction to_isb to be filled
        if not self.parent_biomech_sys.is_isb_oriented() and self.parent_biomech_sys.is_origin_on_an_isb_axis():
            parent_output = self._check_segment_has_to_isb_correction(parent_correction, print_warnings=print_warnings)
            if self.parent_segment == Segment.SCAPULA:
                parent_output = self._check_segment_has_kolz_correction(
                    parent_correction, print_warnings=print_warnings
                )
            self.parent_segment_usable_for_rotation_data = parent_output
            self.parent_segment_usable_for_translation_data = False

        if not self.child_biomech_sys.is_isb_oriented() and self.child_biomech_sys.is_origin_on_an_isb_axis():
            child_output = self._check_segment_has_to_isb_correction(child_correction, print_warnings=print_warnings)
            if self.child_segment == Segment.SCAPULA:
                child_output = self._check_segment_has_kolz_correction(child_correction, print_warnings=print_warnings)
            self.child_segment_usable_for_rotation_data = child_output
            self.child_segment_usable_for_translation_data = False

        if not self.parent_biomech_sys.is_isb_oriented() and not self.parent_biomech_sys.is_origin_on_an_isb_axis():
            parent_output = self._check_segment_has_to_isb_like_correction(
                parent_correction, print_warnings=print_warnings
            )
            if self.parent_segment == Segment.SCAPULA:
                parent_output = self._check_segment_has_kolz_correction(
                    parent_correction, print_warnings=print_warnings
                )
            self.parent_segment_usable_for_rotation_data = parent_output
            self.parent_segment_usable_for_translation_data = False
            self.parent_definition_risk = True
            # todo: please implement the following risks
            # self.parent_definition_risk = Risk.LOW  # known and corrected from the literature
            # self.parent_definition_risk = Risk.HIGH  # unknown and uncorrected from the literature

        if not self.child_biomech_sys.is_isb_oriented() and not self.child_biomech_sys.is_origin_on_an_isb_axis():
            child_output = self._check_segment_has_to_isb_like_correction(
                child_correction, print_warnings=print_warnings
            )
            if self.child_segment == Segment.SCAPULA:
                child_output = self._check_segment_has_kolz_correction(child_correction, print_warnings=print_warnings)
            self.child_segment_usable_for_rotation_data = child_output
            self.child_segment_usable_for_translation_data = False
            self.child_definition_risk = True

        # finally check the combination of parent and child to determine if usable for rotation and translation
        self.usable_rotation_data = (
            self.child_segment_usable_for_rotation_data and self.parent_segment_usable_for_rotation_data
        )
        self.usable_translation_data = (
            self.child_segment_usable_for_translation_data and self.parent_segment_usable_for_translation_data
        )

        # todo: risk level implementation
        # self.rotation_risk = Risk.LOW
        # self.translation_risk = Risk.HIGH

        return self.usable_rotation_data, self.usable_translation_data

    def set_rotation_correction_callback(self):
        """
        Set the rotation correction callback, for the joint.
        """
        parent_isb = self.parent_biomech_sys.is_isb_oriented()
        child_isb = self.child_biomech_sys.is_isb_oriented()

        if parent_isb and child_isb:
            if self.joint.is_joint_sequence_isb():
                self.usable_rotation_data = True
                self.rotation_correction_callback = get_angle_conversion_callback_from_tuple((1, 1, 1))
            else:
                # -- TO ISB SEQUENCE --
                # rebuild the rotation matrix from angles and sequence and identify the ISB angles from the rotation matrix
                self.usable_rotation_data = True
                self.rotation_correction_callback = get_angle_conversion_callback_from_sequence(
                    previous_sequence=self.joint.euler_sequence,
                    new_sequence=self.joint.isb_euler_sequence(),
                )

        elif not parent_isb or not child_isb:  # This is to isb correction !
            # 1. Check if the two segments are oriented in the same direction
            if not check_same_orientation(parent=self.parent_biomech_sys, child=self.child_biomech_sys):
                # todo: i don't know yet if useful
                self.usable_rotation_data = False
                self.rotation_correction_callback = None
                raise NotImplementedError("Not implemented yet, I don't know what to do yet.")

            # 2.If they are the same orientation,
            # convert the euler angles to get them such that the two segments are ISB oriented
            # NOTE: we don't actually convert the coordinate systems, we just convert the euler angles
            # Deprecated
            # output = get_conversion_from_not_isb_to_isb_oriented(
            #     parent=self.parent_biomech_sys,
            #     child=self.child_biomech_sys,
            #     joint=self.joint,
            # )
            # New method
            (
                is_sequence_convertible_through_factors,
                sign_factors,
            ) = convert_rotation_matrix_from_one_coordinate_system_to_another(
                bsys=self.parent_biomech_sys,
                initial_sequence=self.joint.euler_sequence,
                sequence_wanted=self.joint.isb_euler_sequence(),
            )
            # Note: an extra check need to be done in the previous function

            if (
                self.joint.is_sequence_convertible_through_factors(print_warning=True)
                and is_sequence_convertible_through_factors
            ):
                self.usable_rotation_data = True
                self.rotation_correction_callback = get_angle_conversion_callback_from_tuple(sign_factors)
            else:
                self.usable_rotation_data = True
                self.rotation_correction_callback = get_angle_conversion_callback_to_isb_with_sequence(
                    previous_sequence=self.joint.euler_sequence,
                    new_sequence=self.joint.isb_euler_sequence(),
                    bsys_child=self.child_biomech_sys,
                    bsys_parent=self.parent_biomech_sys,
                )

            # it may not include the step where we check if the origin is on an isb axis, especially for the scapula, consider kolz conversion
            # build the rotation matrix from the euler angles and sequence, applied kolz conversion to the rotation matrix
            # identify again the euler angles from the rotation matrix

        else:
            raise NotImplementedError("Check conversion not implemented yet")
