import unittest
from pydantic import ValidationError
from vision_privacy import Region, parse_descriptor


class VisionSchemaTests(unittest.TestCase):
    def test_partial_description_keeps_valid_evidence_and_flags_bad_region(self):
        result, warnings = parse_descriptor({'summary':'Green line dips', 'entities':[
            {'id':'bad','description':'title','box':[.4,.4,.3,.7]},
            {'id':'good','description':'red dot','box':[.8,.6,.9,.7]}]})
        self.assertEqual(result['summary'], 'Green line dips')
        self.assertEqual([x['id'] for x in result['entities']], ['good'])
        self.assertEqual(len(warnings), 1)

    def test_single_wrapped_rectangle_is_normalized(self):
        region = Region(description='indicator', box=[[.1, .2, .3, .4]])
        self.assertEqual(region.box, [.1, .2, .3, .4])

    def test_ambiguous_or_invalid_rectangles_remain_rejected(self):
        for box in ([[0, 0, 1, 1], [0, 0, .5, .5]], [[0, 0, 2, 1]], [[.5, 0, .1, 1]], [[[0, 0, 1, 1]]]):
            with self.subTest(box=box), self.assertRaises(ValidationError):
                Region(description='invalid', box=box)
