"""
Unittests for the driver

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import unittest
import heapq
import tale.driver as driver


class TestDeferreds(unittest.TestCase):
    def testSortable(self):
        d1 = driver.Deferred(5, "owner", "callable", None, None)
        d2 = driver.Deferred(2, "owner", "callable", None, None)
        d3 = driver.Deferred(4, "owner", "callable", None, None)
        d4 = driver.Deferred(1, "owner", "callable", None, None)
        d5 = driver.Deferred(3, "owner", "callable", None, None)
        deferreds = sorted([d1, d2, d3, d4, d5])
        dues = [d.due for d in deferreds]
        self.assertEqual([1, 2, 3, 4, 5], dues)

    def testHeapq(self):
        d1 = driver.Deferred(5, "owner", "callable", None, None)
        d2 = driver.Deferred(2, "owner", "callable", None, None)
        d3 = driver.Deferred(4, "owner", "callable", None, None)
        d4 = driver.Deferred(1, "owner", "callable", None, None)
        d5 = driver.Deferred(3, "owner", "callable", None, None)
        heap = [d1, d2, d3, d4, d5]
        heapq.heapify(heap)
        dues = []
        while heap:
            dues.append(heapq.heappop(heap).due)
        self.assertEqual([1, 2, 3, 4, 5], dues)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
