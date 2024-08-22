"""Frontend for working with data"""

import funcnodes as fn
import requests
import os
import base64
from dataclasses import dataclass
from typing import List

__version__ = "0.1.2"


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


class BytesToStringNode(fn.Node):
    """
    Converts bytes to a string using the specified encoding.

    Args:
      data (bytes): The bytes to convert to a string.
      encoding (str): The encoding to use for the conversion. Defaults to "utf-8".
    """

    node_id = "files.b2s"
    node_name = "Bytes to String"

    data = fn.NodeInput(id="data", type=bytes)
    encoding = fn.NodeInput(
        id="encoding",
        type=str,
        default="utf-8",
        value_options=[
            "ascii",
            "big5",
            "big5hkscs",
            "cp037",
            "cp273",
            "cp424",
            "cp437",
            "cp500",
            "cp720",
            "cp737",
            "cp775",
            "cp850",
            "cp852",
            "cp855",
            "cp856",
            "cp857",
            "cp858",
            "cp860",
            "cp861",
            "cp862",
            "cp863",
            "cp864",
            "cp865",
            "cp866",
            "cp869",
            "cp874",
            "cp875",
            "cp932",
            "cp949",
            "cp950",
            "cp1006",
            "cp1026",
            "cp1125",
            "cp1140",
            "cp1250",
            "cp1251",
            "cp1252",
            "cp1253",
            "cp1254",
            "cp1255",
            "cp1256",
            "cp1257",
            "cp1258",
            "euc_jp",
            "euc_jis_2004",
            "euc_jisx0213",
            "euc_kr",
            "gb2312",
            "gbk",
            "gb18030",
            "hz",
            "iso2022_jp",
            "iso2022_jp_1",
            "iso2022_jp_2",
            "iso2022_jp_2004",
            "iso2022_jp_3",
            "iso2022_jp_ext",
            "iso2022_kr",
            "latin_1",
            "iso8859_2",
            "iso8859_3",
            "iso8859_4",
            "iso8859_5",
            "iso8859_6",
            "iso8859_7",
            "iso8859_8",
            "iso8859_9",
            "iso8859_10",
            "iso8859_11",
            "iso8859_13",
            "iso8859_14",
            "iso8859_15",
            "iso8859_16",
            "johab",
            "koi8_r",
            "koi8_t",
            "koi8_u",
            "kz1048",
            "mac_cyrillic",
            "mac_greek",
            "mac_iceland",
            "mac_latin2",
            "mac_roman",
            "mac_turkish",
            "ptcp154",
            "shift_jis",
            "shift_jis_2004",
            "shift_jisx0213",
            "utf_32",
            "utf_32_be",
            "utf_32_le",
            "utf_16",
            "utf_16_be",
            "utf_16_le",
            "utf_7",
            "utf_8",
            "utf_8_sig",
        ],
    )
    string = fn.NodeOutput(id="string", type=str)

    async def func(self, data: bytes, encoding: str) -> None:
        """
        Converts bytes to a string using the specified encoding and sets the "string" output to the result.

        Args:
          data (bytes): The bytes to convert to a string.
          encoding (str): The encoding to use for the conversion.
        """
        self.outputs["string"].value = data.decode(encoding, errors="replace")


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
    nodes=[FileDownloadNode, BytesToStringNode, FileUploadNode, FolderUploadNode],
    description="Nodes for working with data and files.",
    subshelves=[],
)


REACT_PLUGIN = {
    "module": os.path.join(os.path.dirname(__file__), "react_plugin", "js", "main.js"),
}
