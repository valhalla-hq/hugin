"""Layout/raster boundary: oversized input must never silently lose pixels."""
import unittest

from hugin.branding import MAX_SURFACE_SIDE, surface_size
from hugin.ui import window_geometry


class SurfaceBounds(unittest.TestCase):
    def test_surface_contract_keeps_exact_dimensions_or_refuses(self):
        self.assertEqual(surface_size(2048,1600),(2048,1600))
        for size in ((3000,1600),(620,3000),(0,100)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                surface_size(*size)

    def test_window_initial_and_minimum_geometry_fit_the_raster_at_high_dpi(self):
        for dpi in (1,1.5,2,3,4,8):
            for screen_height in (1080,2160,4320,8640):
                with self.subTest(dpi=dpi,screen=screen_height):
                    scale,width,height,min_width,min_height=window_geometry(dpi,screen_height)
                    self.assertEqual(surface_size(width,height),(width,height))
                    self.assertEqual(surface_size(min_width,min_height),(min_width,min_height))
                    self.assertLessEqual(min_width,width)
                    self.assertLessEqual(min_height,height)
                    self.assertGreaterEqual(height/scale,479)
                    self.assertLessEqual(height,screen_height)
                    self.assertLessEqual(scale,dpi)
        self.assertEqual(window_geometry(2,2160),(2,1240,1560,920,1240))
