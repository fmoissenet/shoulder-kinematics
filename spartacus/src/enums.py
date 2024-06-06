from enum import Enum
from pathlib import Path

import numpy as np


class DatasetCSV(Enum):
    """Enum for the dataset csv files, with dynamic path"""

    RAW = Path(__file__).parent.parent / "dataset" / "only_dataset_raw.csv"
    CLEAN = Path(__file__).parent.parent / "dataset" / "dataset_clean.csv"


class DataFolder(Enum):
    BEGON_2014 = Path(__file__).parent.parent / "data" / "#1_Begon_et_al"
    BOURNE_2003 = Path(__file__).parent.parent / "data" / "#2_Bourne_et_al"
    CHU_2012 = Path(__file__).parent.parent / "data" / "#3_Chu_et_al"
    FUNG_2001 = Path(__file__).parent.parent / "data" / "#4_Fung_et_al"
    GUTIERREZ_DELGADO_2017 = Path(__file__).parent.parent / "data" / "#5_Gutierrez_Delgado_et_al"
    KOLZ_2020 = Path(__file__).parent.parent / "data" / "Kolz et al 2020"
    MCCLURE_2001 = Path(__file__).parent.parent / "data" / "#7_Karduna_et_al"
    KIJIMA_2015 = Path(__file__).parent.parent / "data" / "#8_Kijima_et_al"
    KIM_2017 = Path(__file__).parent.parent / "data" / "#9_Kim_et_al"
    KONOZO_2017 = Path(__file__).parent.parent / "data" / "#10_Kozono_et_al"
    LAWRENCE_2014 = Path(__file__).parent.parent / "data" / "#11_Ludewig_et_al"
    MATSUKI_2011 = Path(__file__).parent.parent / "data" / "#12_Matsuki_et_al"
    # MATSUKI_2011 = Path(__file__).parent.parent / "data" / "Matsuki et al 2011"
    # MATSUKI_2012 = Path(__file__).parent.parent / "data" / "Matsuki et al 2012"
    # MATSUKI_2014 = Path(__file__).parent.parent / "data" / "Matsuki et al 2014"
    MATSUMURA_2013 = Path(__file__).parent.parent / "data" / "#13_Matsumura_et_al"
    MOISSENET = Path(__file__).parent.parent / "data" / "#14_Moissenet_et_al"
    NISHINAKA_2008 = Path(__file__).parent.parent / "data" / "#15_Nishinaka_et_al"
    OKI_2012 = Path(__file__).parent.parent / "data" / "#16_Oki_et_al"
    SAHARA_2006 = Path(__file__).parent.parent / "data" / "#17_Sahara_et_al"
    # SAHARA_2006 = Path(__file__).parent.parent / "data" / "Sahara et al 2006"
    # SAHARA_2007 = Path(__file__).parent.parent / "data" / "Sahara et al 2007"
    SUGI_2021 = Path(__file__).parent.parent / "data" / "#18_Sugi_et_al"
    TEECE_2008 = Path(__file__).parent.parent / "data" / "#19_Teece_et_al"
    YOSHIDA_2023 = Path(__file__).parent.parent / "data" / "#20_Yoshida_et_al"
    # MALBERG = "TODO"

    @classmethod
    def from_string(cls, data_folder: str):
        folder_name_to_enum = {
            "#1_Begon_et_al": cls.BEGON_2014,
            "#2_Bourne_et_al": cls.BOURNE_2003,
            "#3_Chu_et_al": cls.CHU_2012,  # "Chu et al 2012"
            "#4_Fung_et_al": cls.FUNG_2001,  # "Fung et al 2001"
            "#5_Gutierrez_Delgado_et_al": cls.GUTIERREZ_DELGADO_2017,  # "Gutierrez Delgado et al 2017"
            "Kolz et al 2020": cls.KOLZ_2020,  # "Kolz et al 2020
            "#7_Karduna_et_al": cls.MCCLURE_2001,
            "#8_Kijima_et_al": cls.KIJIMA_2015,  # "Kijima et al 2015"
            "#9_Kim_et_al": cls.KIM_2017,  # "Kim et al 2017"
            "#10_Kozono_et_al": cls.KONOZO_2017,  # "Kozono et al 2017"
            "#11_Ludewig_et_al": cls.LAWRENCE_2014,
            "#12_Matsuki_et_al": cls.MATSUKI_2011,  # "Matsuki et al 2011"
            # "Matsuki et al 2011": cls.MATSUKI_2011,
            # "Matsuki et al 2012": cls.MATSUKI_2012,
            # "Matsuki et al 2014": cls.MATSUKI_2014,
            "#13_Matsumura_et_al": cls.MATSUMURA_2013,  # "Matsumura et al 2013"
            "#14_Moissenet_et_al": cls.MOISSENET,  # "Moissenet et al"
            "#15_Nishinaka_et_al": cls.NISHINAKA_2008,  # "Nishinaka et al 2008"
            "#16_Oki_et_al": cls.OKI_2012,  # "Oki et al 2012"
            "#17_Sahara_et_al": cls.SAHARA_2006,  # "Sahara et al 2006"
            # "Sahara et al 2006": cls.SAHARA_2006,
            # "Sahara et al 2007": cls.SAHARA_2007,
            "#18_Sugi_et_al": cls.SUGI_2021,  # "Sugi et al 2021"
            "#19_Teece_et_al": cls.TEECE_2008,  # "Teece et al 2008"
            "#20_Yoshida_et_al": cls.YOSHIDA_2023,  # "Yoshida et al 2023"
            # "#XX_Malberg": cls.MALBERG, TODO
        }

        the_enum = folder_name_to_enum.get(data_folder)
        if the_enum is None:
            raise ValueError(f"Unknown data folder: {data_folder}")

        return the_enum

    def to_dataset_author(self):
        enum_to_dataset_author = {
            self.BEGON_2014: "Begon et al.",
            self.BOURNE_2003: "Bourne et al.",
            self.CHU_2012: "Chu et al.",
            self.FUNG_2001: "Fung et al.",
            self.GUTIERREZ_DELGADO_2017: "Gutierrez Delgado et al.",
            self.KOLZ_2020: "Kolz et al.",
            self.MCCLURE_2001: "McClure et al.",
            self.KIJIMA_2015: "Kijima et al.",
            self.KIM_2017: "Kim et al.",
            self.KONOZO_2017: "Kozono et al.",
            self.LAWRENCE_2014: "Lawrence et al.",
            self.MATSUKI_2011: "Matsuki et al.",
            self.MATSUMURA_2013: "Matsumura et al.",
            self.MOISSENET: "Moissenet et al.",
            self.NISHINAKA_2008: "Nishinaka et al.",
            self.OKI_2012: "Oki et al.",
            self.SAHARA_2006: "Sahara et al.",
            self.SUGI_2021: "Sugi et al.",
            self.TEECE_2008: "Teece et al.",
            self.YOSHIDA_2023: "Yoshida et al.",
        }

        the_dataset_author = enum_to_dataset_author.get(self)
        if the_dataset_author is None:
            raise ValueError(f"Unknown data folder: {self}")

        return the_dataset_author
