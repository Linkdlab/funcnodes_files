from all_nodes_test_base import TestAllNodesBase
import funcnodes_files as fnmodule
import funcnodes as fn
import os
from pathlib import Path


class TestAllNodes(TestAllNodesBase):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.ns = fn.NodeSpace()
        self.root = Path(os.path.join(os.path.dirname(__file__), "files"))
        self.ns.set_property("files_dir", str(self.root))
        # in case the test file is deleted
        self.testfile = Path(os.path.join(self.root, "test.txt"))
        # copy testfile
        with open(self.testfile, "wb") as f:
            f.write(b"hello\n")

        self.testfile = Path(os.path.join(self.root, "test.txt"))
        self.reltestfilepath = self.testfile.relative_to(self.root)

    async def test_file_download(self):
        node = fnmodule.FileDownloadNode()
        node.inputs[
            "url"
        ].value = "https://upload.wikimedia.org/wikipedia/commons/2/2b/Cyborglog-of-eating-old-apple-d360.jpg"
        await node
        self.assertIsInstance(node.get_output("data").value, bytes)

    async def test_file_upload(self):
        node = fnmodule.FileUploadNode()

        self.ns.add_node_instance(node)
        data = fnmodule.FileUpload(self.reltestfilepath)

        node.inputs["input_data"].value = data
        node.inputs["save"].value = True

        assert node.inputs_ready()
        await node

        print(
            node.get_output("data").value,
        )
        self.assertEqual(
            node.get_output("data").value, b"hello\n"
        )  # since load is turnedd off
        fid = node.get_output("file").value
        self.assertIsInstance(fid, fnmodule.FileInfoData)
        self.assertEqual(fid.name, self.reltestfilepath.name)
        self.assertEqual(fid.path, self.reltestfilepath)

    async def test_folder_upload(self):
        node = fnmodule.FolderUploadNode()
        self.ns.add_node_instance(node)
        data = fnmodule.FolderUpload(".")

        node.inputs["input_data"].value = data
        await node
        pathdict = node.get_output("dir").value
        self.assertIsInstance(pathdict, fnmodule.PathDictData)
        self.assertEqual(
            pathdict.files[0].path,
            fnmodule.make_file_info(self.testfile, self.testfile.parent).path,
        )

    async def test_file_download_local(self):
        node = fnmodule.FileDownloadLocal()
        data = fnmodule.FileDownload(filename="test.txt", content="AAAA")
        node.inputs["data"].value = data.bytedata
        node.inputs["filename"].value = data.filename
        await node
        self.assertEqual(node.get_output("output_data").value, data)

    async def test_browse_folder(self):
        node = fnmodule.BrowseFolder()
        node = self.ns.add_node_instance(node)

        await node
        self.assertIsInstance(node.get_output("dirs").value, list)
        self.assertIsInstance(node.get_output("files").value, list)

    async def test_open_file(self):
        node = fnmodule.OpenFile()
        self.ns.add_node_instance(node)
        node.inputs["path"].value = self.reltestfilepath.as_posix()
        await node
        self.assertIsInstance(node.get_output("data").value, bytes)

    async def test_fileinfo(self):
        node = fnmodule.FileInfo()
        self.ns.add_node_instance(node)
        node.inputs["path"].value = self.reltestfilepath.as_posix()
        await node
        self.assertIsInstance(node.get_output("size").value, int)
        self.assertIsInstance(node.get_output("created").value, float)
        self.assertIsInstance(node.get_output("modified").value, float)
        self.assertEqual(node.get_output("filename").value, "test.txt")

    async def test_pathdict(self):
        node = fnmodule.PathDict()
        self.ns.add_node_instance(node)
        node.inputs["path"].value = "."
        await node
        self.assertIsInstance(node.get_output("data").value, fnmodule.PathDictData)

    async def test_delete_file(self):
        node = fnmodule.FileDeleteNode()
        self.ns.add_node_instance(node)

        testfile = self.testfile.parent / "test_delete.txt"
        with open(testfile, "w") as f:
            f.write("test")

        self.assertTrue(testfile.exists())

        node.inputs["data"].value = fnmodule.make_file_info(
            testfile, self.testfile.parent
        )
        await node
        self.assertFalse(testfile.exists())

    async def test_save_file(self):
        node = fnmodule.SaveFile()
        self.ns.add_node_instance(node)
        node.inputs["data"].value = b"test"
        node.inputs["filename"].value = "test_save.txt"
        await node
        self.assertTrue((self.root / "test_save.txt").exists())
        os.remove(self.root / "test_save.txt")

        node.inputs["path"].value = "savetest"
        await node
        self.assertTrue((self.root / "savetest" / "test_save.txt").exists())
        os.remove(self.root / "savetest" / "test_save.txt")
        os.rmdir(self.root / "savetest")
