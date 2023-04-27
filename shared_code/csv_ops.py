from dataclasses import dataclass
import os
import glob


@dataclass
class CSV_ops:
    """takes the prefix of the data file and can preform a few CSV_ops on it"""

    prefix: str = "vehicles"
    file_extension: str = "csv"

    def get_latest(self):
        """Find the most recent csv file in the data folder"""
        list_of_files = glob.glob(f"data/{self.prefix}_*.{self.file_extension}")
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file

    def get_second_latest(self):
        """Find the most recent csv file in the data folder"""
        list_of_files = glob.glob(f"data/{self.prefix}_*.{self.file_extension}")
        latest_file = sorted(list_of_files, key=os.path.getctime)
        return latest_file[-2]

    def delete_old_data(self):
        """Delete old data files"""
        list_of_files = glob.glob(f"data/{self.prefix}_*.{self.file_extension}")
        sorted_files = sorted(list_of_files, key=os.path.getctime)
        for file in list_of_files:
            if file not in sorted_files[-2:]:
                try:
                    os.remove(file)
                except PermissionError:
                    pass
