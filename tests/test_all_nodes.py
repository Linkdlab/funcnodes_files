from all_nodes_test_base import TestAllNodesBase
import funcnodes_files as fnmodule
import funcnodes as fn
import os

fn.config.IN_NODE_TEST = True


class TestAllNodes(TestAllNodesBase):
    async def test_file_download(self):
        node = fnmodule.FileDownloadNode()
        node.inputs["url"].value = "https://www.google.com"
        await node
        self.assertIsInstance(node.get_output("data").value, bytes)

    async def test_file_upload(self):
        ns = fn.NodeSpace()
        ns.set_property("files_dir", os.path.dirname(__file__))
        node = fnmodule.FileUploadNode()
        _fp = os.path.join("files", "test.txt")
        ns.add_file(_fp)
        ns.add_node_instance(node)
        data = fnmodule.FileUpload(_fp)

        node.inputs["input_data"].value = data
        await node
        print(node.get_output("data").value)
        self.assertEqual(node.get_output("data").value, b"hello\n")
        self.assertEqual(node.get_output("filename").value, "test.txt")
        self.assertEqual(
            node.get_output("path").value, os.path.join(os.path.dirname(__file__), _fp)
        )

    async def test_folder_upload(self):
        ns = fn.NodeSpace()
        ns.set_property("files_dir", os.path.dirname(__file__))
        node = fnmodule.FolderUploadNode()
        ns.add_node_instance(node)
        _fp = [os.path.join("files", "test.txt")]
        for f in _fp:
            ns.add_file(f)
        data = fnmodule.FolderUpload(_fp)

        node.inputs["input_data"].value = data
        await node
        self.assertEqual(node.get_output("dates").value, [b"hello\n"])
        self.assertEqual(node.get_output("filenames").value, ["test.txt"])
        self.assertEqual(
            node.get_output("paths").value,
            [os.path.join(os.path.dirname(__file__), _p) for _p in _fp],
        )

    async def test_file_download_local(self):
        node = fnmodule.FileDownloadLocal()
        data = fnmodule.FileDownload(filename="test.txt", content="AAAA")
        node.inputs["data"].value = data.bytedata
        node.inputs["filename"].value = data.filename
        await node
        self.assertEqual(node.get_output("output_data").value, data)
