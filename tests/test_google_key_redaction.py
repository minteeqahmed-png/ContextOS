import base64
import io
import unittest
from PIL import Image
from vision_privacy import redact, sanitize_text


class GoogleKeyRedactionTests(unittest.TestCase):
    def test_unlabelled_key_is_removed_from_query(self):
        # Construct a dummy, nonfunctional value; never use a real credential.
        key = 'AIza' + 'x' * 35
        self.assertEqual(sanitize_text('Look for ' + key), 'Look for [REDACTED]')
        self.assertEqual(sanitize_text('AIza is a prefix'), 'AIza is a prefix')

    def test_ocr_region_containing_key_is_opaquely_masked(self):
        buf = io.BytesIO()
        Image.new('RGB', (100,100), 'white').save(buf, format='PNG')
        original = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
        sanitized, masks, warnings = redact(original, [{
            'text': 'AIza' + 'x' * 35, 'box': [.2,.2,.8,.4], 'confidence': .99
        }], [])
        result = Image.open(io.BytesIO(base64.b64decode(sanitized.split(',')[1])))
        self.assertEqual(result.getpixel((50,30)), (0,0,0))
        self.assertEqual(result.getpixel((0,0)), (255,255,255))
        self.assertEqual(masks, [[.2,.2,.8,.4]])
        self.assertTrue(warnings)
        self.assertNotEqual(original, sanitized)
