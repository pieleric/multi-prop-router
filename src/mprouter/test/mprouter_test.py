#!/usr/bin/env python3

import logging
import unittest
import mprouter

logging.getLogger().setLevel(logging.DEBUG)

longlat_tudelft = (4.37212, 52.00234)
longlat_kijkduin = (4.22200, 52.06965)


class TestMapBox(unittest.TestCase):
    def test_route(self):
        sumcar = mprouter.mapbox_route(longlat_tudelft, longlat_kijkduin, "car")
        logging.debug("car summary: %s", sumcar)
        sumbike = mprouter.mapbox_route(longlat_tudelft, longlat_kijkduin, "bike")
        sumfoot = mprouter.mapbox_route(longlat_tudelft, longlat_kijkduin, "foot")
        assert sumcar.duration < sumbike.duration < sumfoot.duration
        # In NL, on foot can be further than by bike
        assert sumcar.distance >= sumbike.distance #>= sumfoot.distance


class Test9292(unittest.TestCase):
    def test_route(self):
        sumpt = mprouter.nl9292_route(longlat_tudelft, longlat_kijkduin, 1542387791)
        logging.debug("9292 summary: %s", sumpt)
        assert sumpt.duration > 600 # at leat 10 min
        assert sumpt.price > 3 # €

    def test_location_id(self):
        tudelft_id = mprouter.nl9292_get_location_id(longlat_tudelft)
        logging.debug("Got TUDelft ID = %s", tudelft_id)
        assert "delft" in tudelft_id


class TestMonotch(unittest.TestCase):
    def test_parking(self):
        pks1km = mprouter.monotch_list_parkings(longlat_kijkduin, 1000)
        logging.debug("Got parkings: %s", pks1km)
        pks10km = mprouter.monotch_list_parkings(longlat_kijkduin, 10000)
        logging.debug("Got parkings: %s", pks10km)
        for p in pks10km:
            print(p)
        self.assertGreaterEqual(len(pks10km), len(pks1km))


class TestPRRoute(unittest.TestCase):
    def test_pr_route(self):
        journeys = mprouter.pr_route(longlat_tudelft, longlat_kijkduin, 1542387791)
        logging.debug("Got journeys: %s", journeys)
        self.assertGreaterEqual(len(journeys), 2)


if __name__ == "__main__":
    unittest.main()
