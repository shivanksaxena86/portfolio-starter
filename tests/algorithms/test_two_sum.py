import pytest
# Example placeholder; replace with real import once implemented
def two_sum(nums, target):
    lookup = {}
    for i, n in enumerate(nums):
        if target - n in lookup:
            return [lookup[target - n], i]
        lookup[n] = i
    return []
def test_two_sum():
    assert two_sum([2,7,11,15], 9) == [0,1]
