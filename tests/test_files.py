import funcnodes_files as fnf
import unittest


class TestFiles(unittest.IsolatedAsyncioTestCase):
    async def test_file_download(self):
        node = fnf.FileDownloadNode()
        node.inputs["url"].value = "https://www.google.com"
        await node
        self.assertIsInstance(node.get_output("data").value, bytes)

    async def test_bytes_to_string(self):
        node = fnf.BytesToStringNode()
        node.inputs["data"].value = b"Hello, World!"
        await node
        self.assertIsInstance(node.get_output("string").value, str)
