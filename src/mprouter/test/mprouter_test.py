#!/usr/bin/env python3

import logging
import unittest
import mprouter

logging.getLogger().setLevel(logging.DEBUG)

longlat_tudelft = (4.37212, 52.00234)
add_tudelft = "TU aula, delft"
longlat_kijkduin = (4.22200, 52.06965)
add_kijkduin = "deltaplein, den haag"
longlat_denhaag = (4.31527, 52.08040) # Mauritshuis
add_denhaag = "Mauritshuis, Den Haag"


class TestMapBox(unittest.TestCase):
    def test_route(self):
        sumcar = mprouter.mapbox_route(longlat_tudelft, longlat_kijkduin, "car")
        logging.debug("car summary: %s", sumcar)
        sumbike = mprouter.mapbox_route(longlat_tudelft, longlat_kijkduin, "bike")
        sumfoot = mprouter.mapbox_route(longlat_tudelft, longlat_kijkduin, "foot")
        assert sumcar.duration < sumbike.duration < sumfoot.duration
        # In NL, on foot can be further than by bike
        assert sumcar.distance >= sumbike.distance #>= sumfoot.distance
        assert sumcar.price > 0
        assert sumcar.co2 > 0
        
    def test_geocoder_fw(self):
        dh = mprouter.mapbox_geocoder_fw(add_denhaag)
        self.assertAlmostEqual(dh[0], longlat_denhaag[0], delta=0.01)
        self.assertAlmostEqual(dh[1], longlat_denhaag[1], delta=0.01)
        
        dh = mprouter.mapbox_geocoder_fw(add_kijkduin)
        self.assertAlmostEqual(dh[0], longlat_kijkduin[0], delta=0.01)
        self.assertAlmostEqual(dh[1], longlat_kijkduin[1], delta=0.01)


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

    def test_closest_parking(self):
        pk_kijkduin = mprouter.cache_monotch_list_parkings(longlat_kijkduin)[0]
        print(pk_kijkduin)
        pk_denhaag = mprouter.cache_monotch_list_parkings(longlat_denhaag)[0]
        dist = mprouter.get_distance(pk_denhaag.coordinates, longlat_denhaag)
        print(pk_denhaag)
        self.assertLessEqual(dist, 1000)


class TestPRRoute(unittest.TestCase):
    def test_pr_route(self):
        departt = 1542387791 # 2018-11-16 @ 16:30
        #journeys = mprouter.pr_route(longlat_tudelft, longlat_kijkduin, departt)
        journeys = mprouter.pr_route(longlat_tudelft, longlat_denhaag, departt)
        logging.debug("Got journeys: %s", journeys)
        for j in journeys:
            print(j.to_struct())
            print("https://www.openstreetmap.org/directions?engine=osrm_car&route=%f,%f;%f,%f" % 
                  (longlat_tudelft[1], longlat_tudelft[0], j.parking.coordinates[1], j.parking.coordinates[0]))
        self.assertGreaterEqual(len(journeys), 2)
        for j in journeys:
            self.assertGreaterEqual(j.duration, j.car.duration + j.pt.duration)
            self.assertGreater(j.car.depart_time, departt - 600)

    def test_pr_route_night(self):
        departt = 1542420000 # 2018-11-17 @ 03:00
        journeys = mprouter.pr_route(longlat_tudelft, longlat_kijkduin, departt)
        #journeys = mprouter.pr_route(longlat_tudelft, longlat_denhaag, departt)
        logging.debug("Got journeys: %s", journeys)
        for j in journeys:
            print(j.to_struct())
            print("https://www.openstreetmap.org/directions?engine=osrm_car&route=%f,%f;%f,%f" % 
                  (longlat_tudelft[1], longlat_tudelft[0], j.parking.coordinates[1], j.parking.coordinates[0]))
        self.assertGreaterEqual(len(journeys), 2)
        for j in journeys:
            self.assertGreaterEqual(j.duration, j.car.duration + j.pt.duration)
            self.assertGreater(j.car.depart_time, departt - 600)

    def test_pr_route_add(self):
        departt = 1542387791 # 2018-11-16 @ 16:30
        car_only, journeys = mprouter.pr_route_address(add_tudelft, add_kijkduin, departt)
        logging.debug("Just by car: %s", car_only.to_struct())
        logging.debug("Got journeys: %s", journeys)
        for j in journeys:
            print(j.to_struct())
            print("https://www.openstreetmap.org/directions?engine=osrm_car&route=%f,%f;%f,%f" % 
                  (longlat_tudelft[1], longlat_tudelft[0], j.parking.coordinates[1], j.parking.coordinates[0]))
        self.assertGreaterEqual(len(journeys), 2)
        for j in journeys:
            self.assertGreaterEqual(j.duration, j.car.duration + j.pt.duration)
            self.assertGreater(j.car.depart_time, departt - 600)

    def test_bbox(self):
        bbox = mprouter.get_bbox(longlat_tudelft, 10000)
        self.assertEqual(len(bbox), 4)


if __name__ == "__main__":
    unittest.main()
