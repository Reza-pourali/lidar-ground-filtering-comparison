import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lidar_ground_filter.lasinfo import parse_lasinfo


class TestLasInfoParser(unittest.TestCase):
    def test_parse_counts_and_crs(self):
        text = """
        number of point records:    2727891
        ProjectedCSTypeGeoKey: WGS 84 / UTM 17N
                 1325084  unclassified (1)
                 1402807  ground (2)
        """
        result = parse_lasinfo(text)

        self.assertEqual(result.total_points, 2727891)
        self.assertEqual(result.ground_points, 1402807)
        self.assertEqual(result.unclassified_points, 1325084)
        self.assertEqual(result.crs, "WGS 84 / UTM 17N")


if __name__ == "__main__":
    unittest.main()
