"""
Unit tests for the main module of the IndigoBot application.
"""

import unittest
from unittest.mock import MagicMock, patch


class TestMainModule(unittest.TestCase):
    """Test cases for the __main__.py module."""

    @patch("indigobot.__main__.start_loader")
    @patch("indigobot.__main__.threading.Thread")
    @patch("indigobot.__main__.time.sleep")
    def test_main_success(self, mock_sleep, mock_thread, mock_start_loader):
        """Test the main function with successful execution."""
        # Setup mocks
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        # Make sleep raise exception to break the infinite loop
        mock_sleep.side_effect = KeyboardInterrupt()

        # Import and call main
        from indigobot.__main__ import main

        # Execute the function under test
        with self.assertRaises(KeyboardInterrupt):
            main()

        # Verify the expected calls were made
        mock_start_loader.assert_called_once()
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        mock_sleep.assert_called_once_with(3600)

    @patch("indigobot.__main__.start_loader")
    @patch("indigobot.__main__.threading.Thread")
    @patch("indigobot.__main__.print")
    def test_main_loader_error(self, mock_print, mock_thread, mock_start_loader):
        """Test the main function when loader raises an exception."""
        # Setup mocks
        mock_start_loader.side_effect = Exception("Test loader error")
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        # Make thread.start raise exception to break the infinite loop
        mock_thread_instance.start.side_effect = KeyboardInterrupt()

        # Import and call main
        from indigobot.__main__ import main

        # Execute the function under test
        with self.assertRaises(KeyboardInterrupt):
            main()

        # Verify the expected calls were made
        mock_start_loader.assert_called_once()
        mock_print.assert_called_once_with("Error booting loader: Test loader error")

    @patch("indigobot.__main__.start_loader")
    @patch("indigobot.__main__.threading.Thread")
    @patch("indigobot.__main__.start_api")
    @patch("indigobot.__main__.print")
    def test_main_api_error(
        self, mock_print, mock_start_api, mock_thread, mock_start_loader
    ):
        """Test the main function when API thread raises an exception."""
        # Setup mocks
        mock_thread.side_effect = Exception("Test API error")

        # Import and call main
        from indigobot.__main__ import main

        # Execute the function under test
        main()

        # Verify the expected calls were made
        mock_start_loader.assert_called_once()
        mock_print.assert_called_once_with("Error booting API: Test API error")

    @patch("indigobot.__main__.start_loader")
    @patch("indigobot.__main__.threading.Thread")
    @patch("indigobot.__main__.time.sleep")
    @patch("indigobot.__main__.print")
    def test_main_sleep_interrupted(
        self, mock_print, mock_sleep, mock_thread, mock_start_loader
    ):
        """Test the main function when sleep is interrupted."""
        # Setup mocks
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        # Make sleep raise exception to break the infinite loop
        mock_sleep.side_effect = Exception("Test sleep error")

        # Import and call main
        from indigobot.__main__ import main

        # Execute the function under test
        main()

        # Verify the expected calls were made
        mock_start_loader.assert_called_once()
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        mock_sleep.assert_called_once_with(3600)
        mock_print.assert_called_once_with("Error booting API: Test sleep error")

    def test_main_execution(self):
        """Test the if __name__ == '__main__' block."""
        # We can't directly test the if __name__ == "__main__" block in a normal import
        # Instead, we'll verify the code structure is correct
        import inspect

        import indigobot.__main__

        # Get the source code
        source = inspect.getsource(indigobot.__main__)

        # Check that the module has the expected if __name__ == "__main__" block
        self.assertIn('if __name__ == "__main__":', source)
        self.assertIn("main()", source)


if __name__ == "__main__":
    unittest.main()
