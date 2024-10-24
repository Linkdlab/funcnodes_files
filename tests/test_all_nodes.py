from all_nodes_test_base import TestAllNodesBase
import funcnodes_files as fnmodule
import dataclasses


class TestAllNodes(TestAllNodesBase):
    async def test_file_download(self):
        node = fnmodule.FileDownloadNode()
        node.inputs["url"].value = "https://www.google.com"
        await node
        self.assertIsInstance(node.get_output("data").value, bytes)

    async def test_file_upload(self):
        node = fnmodule.FileUploadNode()
        data = fnmodule.FileUpload(
            content="AAAA", filename="test.txt", path="tests/test.txt"
        )

        node.inputs["input_data"].value = dataclasses.asdict(data)
        await node
        print(node.get_output("data").value)
        self.assertEqual(node.get_output("data").value, b"\x00\x00\x00")
        self.assertEqual(node.get_output("filename").value, "test.txt")
        self.assertEqual(node.get_output("path").value, "tests/test.txt")

    async def test_folder_upload(self):
        node = fnmodule.FolderUploadNode()
        data = fnmodule.FolderUpload(
            [
                fnmodule.FileUpload(
                    content="AAAA", filename="test.txt", path="tests/test.txt"
                )
            ]
        )

        node.inputs["input_data"].value = [dataclasses.asdict(d) for d in data.files]
        await node
        self.assertEqual(node.get_output("dates").value, [b"\x00\x00\x00"])
        self.assertEqual(node.get_output("filenames").value, ["test.txt"])
        self.assertEqual(node.get_output("paths").value, ["tests/test.txt"])
        self.assertEqual(
            node.get_output("files").value,
            [
                fnmodule.FileUpload(
                    content="AAAA", filename="test.txt", path="tests/test.txt"
                )
            ],
        )

    async def test_file_download_local(self):
        node = fnmodule.FileDownloadLocal()
        data = fnmodule.FileDownload(filename="test.txt", content="AAAA")
        node.inputs["data"].value = data.bytedata
        node.inputs["filename"].value = data.filename
        await node
        self.assertEqual(node.get_output("output_data").value, data)
