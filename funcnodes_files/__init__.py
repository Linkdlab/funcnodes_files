"""Frontend for working with data"""

import funcnodes as fn
import requests
import os
import base64
from dataclasses import dataclass
from typing import List

__version__ = "0.2.0"


class FileDownloadNode(fn.Node):
    """
    Downloads a file from a given URL and returns the file's content as bytes.
    """

    node_id = "files.dld"
    node_name = "File Download"

    url = fn.NodeInput(id="url", type="str")
    timeout = fn.NodeInput(id="timeout", type="float", default=10)

    data = fn.NodeOutput(id="data", type=bytes)

    serperate_thread = True

    async def func(self, url: str, timeout: float) -> None:
        """
        Downloads a file from a given URL and sets the "data" output to the file's content as bytes.

        Args:
          url (str): The URL of the file to download.
          timeout (float): The timeout in seconds for the download request.
        """
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                # set user agent to avoid 403 forbidden error
                "User-Agent": "Mozilla/5.0",
                # allow download of files
                "Accept": "*/*",
            },
        )
        self.outputs["data"].value = response.content


@dataclass
class FileUpload:
    filename: str
    content: str
    path: str

    @property
    def bytedata(self):
        return fn.types.databytes(base64.b64decode(self.content))

    def __str__(self) -> str:
        return f"FileUpload(filename={self.filename}, path={self.path})"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class FolderUpload:
    files: List[FileUpload]

    @property
    def bytedates(self):
        return [file.bytedata for file in self.files]

    @property
    def filenames(self):
        return [file.filename for file in self.files]

    @property
    def paths(self):
        return [file.path for file in self.files]

    def __str__(self) -> str:
        return f"FolderUpload(files={self.files}, paths={self.paths})"

    def __repr__(self) -> str:
        return self.__str__()


class FileUploadNode(fn.Node):
    """
    Uploads a file
    """

    node_id = "files.upl"
    node_name = "File Upload"

    input_data = fn.NodeInput(id="input_data", type=FileUpload)
    data = fn.NodeOutput(id="data", type=fn.types.databytes)
    filename = fn.NodeOutput(id="filename", type=str)
    path = fn.NodeOutput(id="path", type=str)

    async def func(self, input_data: dict) -> None:
        """
        Uploads a file to a given URL.

        Args:
          url (str): The URL to upload the file to.
          file (str): The path to the file to upload.
        """

        fileupload = FileUpload(**input_data)

        self.outputs["data"].value = fileupload.bytedata
        self.outputs["filename"].value = fileupload.filename
        self.outputs["path"].value = fileupload.path


class FolderUploadNode(fn.Node):
    """
    Uploads a file
    """

    node_id = "files.upl_folder"
    node_name = "Folder Upload"

    input_data = fn.NodeInput(id="input_data", type=FolderUpload)
    dates = fn.NodeOutput(id="dates", type=List[fn.types.databytes])
    filenames = fn.NodeOutput(id="filenames", type=List[str])
    paths = fn.NodeOutput(id="paths", type=List[str])

    files = fn.NodeOutput(id="files", type=List[FileUpload])

    async def func(self, input_data: List[dict]) -> None:
        """
        Uploads a file to a given URL.

        Args:
          url (str): The URL to upload the file to.
          file (str): The path to the file to upload.
        """

        print(input_data)
        folderupload = FolderUpload([FileUpload(**file) for file in input_data])

        self.outputs["dates"].value = folderupload.bytedates
        self.outputs["filenames"].value = folderupload.filenames
        self.outputs["paths"].value = folderupload.paths
        self.outputs["files"].value = folderupload.files


NODE_SHELF = fn.Shelf(
    name="Files",  # The name of the shelf.
    nodes=[FileDownloadNode, FileUploadNode, FolderUploadNode],
    description="Nodes for working with data and files.",
    subshelves=[],
)


REACT_PLUGIN = {
    "module": os.path.join(os.path.dirname(__file__), "react_plugin", "js", "main.js"),
}
