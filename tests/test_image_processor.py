import unittest
from utils.image_processor import construct_label_color_mapping, draw_bboxes, annotate_image, extract_frame_at_time
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

class TestImageProcessor(unittest.TestCase):
    def test_construct_label_color_mapping(self):
        # Test basic label mapping
        labels = ['car', 'person', 'bike']
        colors = [(255, 0, 0), (0, 255, 0)]
        mapping = construct_label_color_mapping(labels, colors)

        expected_mapping = {
            'car': colors[0],
            'person': colors[1],
            'bike': colors[0]  # Cycles back to the first color
        }
        self.assertEqual(mapping, expected_mapping)

        # Test empty labels
        self.assertIsNone(construct_label_color_mapping(None, colors))
    
    def test_draw_bboxes(self):
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        bboxes = [[10, 10, 50, 50], [60, 60, 90, 90]]
        labels = ['car', 'bike']
        track_ids = [1, 2]

        output_image = draw_bboxes(image, bboxes, labels, track_ids)

        # Ensure output image is of the same shape and not the same instance as the input image
        self.assertEqual(output_image.shape, image.shape)
        self.assertIsNot(output_image, image)

    def test_annotate_image(self):
        image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        text1, text2, text3 = "Label 1", "Label 2", "Label 3"

        annotated_image = annotate_image(image, text1, text2, text3)

        # Ensure the new image has the expected additional height
        self.assertEqual(annotated_image.shape[0], image.shape[0] + 100)
        self.assertEqual(annotated_image.shape[1], image.shape[1])

        # Check that the original part of the image is unchanged (white pixels)
        np.testing.assert_array_equal(annotated_image[:100, :], image)
    
    @patch('utils.image_processor.subprocess.run')  # the grabber shells out to FFmpeg, not OpenCV
    def test_extract_frame_at_time(self, mock_run):
        test_frame = np.full((480, 640, 3), 200, dtype=np.uint8)

        def fake_ffmpeg(cmd, **kwargs):
            cv2.imwrite(cmd[-1], test_frame)  # last argument is the output jpg
            return MagicMock(returncode=0, stderr="")
        mock_run.side_effect = fake_ffmpeg

        grabbed_frame = extract_frame_at_time("test_video.mp4", 1000)

        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], 'ffmpeg')
        self.assertEqual(cmd[cmd.index('-ss') + 1], '1.0')
        self.assertEqual(cmd[cmd.index('-i') + 1], 'test_video.mp4')
        self.assertIsInstance(grabbed_frame, np.ndarray)
        self.assertEqual(grabbed_frame.shape, test_frame.shape)

    @patch('utils.image_processor.subprocess.run')
    def test_extract_frame_at_time_raises_when_ffmpeg_fails(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="boom")
        with self.assertRaises(RuntimeError):
            extract_frame_at_time("test_video.mp4", 1000)
