# -*- coding: utf-8 -*-
# Copyright (c) 2016 Ricoh Co., Ltd. All Rights Reserved.
# pylint: disable=C0302
# pylint: disable=missing-docstring
"""
Smoke test for a sample program.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from nose.tools import (assert_raises, eq_)
from remocon import validate_iso_and_shutter, validate_usr_param

class TestIsoShutter(object):

    def __init__(self):
        self.authorized_ss_frac = [
            '1/6400', '1/5000', '1/4000', '1/3200', '1/2500', '1/2000',
            '1/1600', '1/1250', '1/1000', '1/800', '1/640', '1/500',
            '1/400', '1/320', '1/250', '1/200', '1/160', '1/125',
            '1/100', '1/80', '1/60', '1/50', '1/40', '1/30',
            '1/25', '1/20', '1/15', '1/13', '1/10', '1/8', '1/6', '1/5',
            '1/4', '1/3', '1/2.5', '1/2', '1/1.6', '1/1.3', '1/1',
            '1.3/1', '1.6/1', '2/1', '2.5/1', '3.2/1', '4/1', '5/1',
            '6/1', '8/1', '10/1', '13/1', '15/1', '20/1', '25/1', '30/1', '60/1']

        self.authorized_ss = [
            0.00015625, 0.0002, 0.00025, 0.0003125, 0.0004, 0.0005,
            0.000625, 0.0008, 0.001, 0.00125, 0.0015625, 0.002,
            0.0025, 0.003125, 0.004, 0.005, 0.00625, 0.008,
            0.01, 0.0125, 0.01666666, 0.02, 0.025, 0.03333333,
            0.04, 0.05, 0.06666666, 0.07692307, 0.1, 0.125, 0.16666666, 0.2,
            0.25, 0.33333333, 0.4, 0.5, 0.625, 0.76923076, 1,
            1.3, 1.6, 2, 2.5, 3.2, 4, 5, 6, 8, 10, 13, 15, 20, 25, 30, 60]

        self.authorized_iso = [
            100, 125, 160, 200, 250, 320, 400, 500, 640, 800, 1000, 1250, 1600]


    def test_shutter_speed_ok(self):
        for (ind, ss_frac) in enumerate(self.authorized_ss_frac):
            _, speed = validate_iso_and_shutter(iso=100, s_speed=ss_frac)
            eq_(speed, self.authorized_ss[ind])

    def test_iso_ok(self):
        for (ind, iso) in enumerate(self.authorized_iso):
            _iso, _ = validate_iso_and_shutter(iso=iso, s_speed=None)
            eq_(_iso, self.authorized_iso[ind])

    @staticmethod
    def test_iso_assert():
        invalid_iso = [101, -100, 3200, 50, 150.5, '100']

        for iso in invalid_iso:
            assert_raises(ValueError, validate_iso_and_shutter, iso, None)

    @staticmethod
    def test_shutter_assert():
        invalid_ss = [0.015, -0.01, '0.01']
        for shutter in invalid_ss:
            assert_raises(ValueError, validate_iso_and_shutter, None, shutter)

        invalid_ss = [0.16666666, 0.5, 60, '1/1.6'] #invalid when iso value is not specified.
        for shutter in invalid_ss:
            assert_raises(ValueError, validate_iso_and_shutter, None, shutter)
            validate_iso_and_shutter(100, shutter)
            assert_raises(ValueError, validate_iso_and_shutter, 3200, shutter)


class TestUsrParam(object):

    @staticmethod
    def test_param_ok():
        test_param = ['{"_iso":100}', '{"_iso":200, "_shutterSpeed":0.25}',
                      '{"_shutterSpeed": "1/50"}']
        for param in test_param:
            validate_usr_param(param)

        eq_(None, validate_usr_param(None))

    @staticmethod
    def test_param_assert():
        assert_raises(ValueError, validate_usr_param, {"_iso": 100})
        assert_raises(ValueError, validate_usr_param, '{"_shutter"}')
