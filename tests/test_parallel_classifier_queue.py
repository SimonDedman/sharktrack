import threading
import unittest

from utils.parallel_classifier import ParallelSpeciesClassifier, ClassificationTask


def _task(i):
    return ClassificationTask(track_id=i, track_metadata="m", video_path="v.mp4", time="00:00:01",
                              xmin=0, ymin=0, xmax=1, ymax=1, confidence=0.9, row_index=i)


class TestClassificationQueueBackpressure(unittest.TestCase):
    def test_full_queue_blocks_then_succeeds_no_drop(self):
        pc = ParallelSpeciesClassifier(None, queue_size=1)
        pc.worker_thread = threading.Thread(target=lambda: threading.Event().wait(5), daemon=True)
        pc.worker_thread.start()
        pc.submit_task(_task(0))
        threading.Timer(1.5, pc.task_queue.get).start()  # frees the slot after the first 1 s timeout
        pc.submit_task(_task(1))  # must block, not drop
        self.assertEqual(pc.submitted, 2)
        self.assertEqual(pc.task_queue.get_nowait().row_index, 1)

    def test_full_queue_with_dead_worker_raises(self):
        pc = ParallelSpeciesClassifier(None, queue_size=1)  # worker never started
        pc.task_queue.put(_task(0))
        with self.assertRaises(RuntimeError):
            pc.submit_task(_task(1))


if __name__ == "__main__":
    unittest.main()
