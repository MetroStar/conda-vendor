from unittest.mock import Mock, patch
from requests import Response

from conda_vendor.conda_vendor import _improved_download


@patch("requests.Session.get")
def test_improved_download(mock) -> None:
    mock.return_value = Mock(Response)
    test_url = "https://NOT_REAL.com"
    result = _improved_download(test_url)
    result_called_with = mock.call_args[0][0]
    assert result_called_with == test_url
    assert mock.call_count == 1
    assert isinstance(result, Response)
