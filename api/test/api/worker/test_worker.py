# # import numpy as np
# # import pytest
# from unittest.mock import patch

# # from api.separator import ABCSeparator
# from api.worker import separate, perform_separation


# # class TestSeparator(ABCSeparator):
# #     def __init__(self, stems: int):
# #         self.stems = stems

# #     def separate(self, audio: np.ndarray):
# #         predictions = {f"{i}": audio.copy() for i in range(self.stems)}
# #         return predictions


# @patch("api.worker.task.perform_separation")
# def test_separate(separate_mock):
#     separate.apply(args=(None, None))
#     assert separate_mock.called


# # @pytest.mark.parametrize(
# #     "stems",
# #     (2, 3, 4)
# # )
# # def test_perform_separation(signal, stems):
# #     with patch.object(
# #         "api.worker.task", "get_separator", return_value=TestSeparator
# #     ):
# #         perform_separation(None, signal, stems)
