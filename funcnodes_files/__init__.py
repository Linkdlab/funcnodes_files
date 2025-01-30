"""Frontend for working with data"""

import funcnodes as fn
import requests
import os
import base64
from dataclasses import dataclass
from typing import List, Union, Optional
import funcnodes_core
from pathlib import Path
from urllib.parse import unquote
from io import BytesIO
import asyncio
import shutil

__version__ = "0.2.10"


def path_encoder(obj, preview=False):
    """
    Encodes Path objects to strings.
    """
    if isinstance(obj, Path):
        return fn.Encdata(data=obj.as_posix(), handeled=True)
    return fn.Encdata(data=obj, handeled=False)


fn.JSONEncoder.add_encoder(path_encoder, enc_cls=[Path])


@dataclass
class FileInfoData:
    name: str
    path: str
    size: int
    modified: float
    created: float


@dataclass
class PathDictData:
    path: Path
    files: List[FileInfoData]
    dirs: List["PathDictData"]
    name: str


def make_file_info(fullpath: Path, root: Path) -> FileInfoData:
    return FileInfoData(
        name=fullpath.name,
        path=fullpath.relative_to(root),
        size=os.path.getsize(fullpath),
        modified=os.path.getmtime(fullpath),
        created=os.path.getctime(fullpath),
    )


def make_path_dict(fullpath: Path, root: Path, levels=999) -> PathDictData:
    def _recurisive_fill(
        path: Path,
        _levels: int,
    ) -> PathDictData:
        files = []
        dirs = []
        if _levels > 0:
            content = os.listdir(path)
            for f in content:
                fpath = path / f
                if os.path.isdir(fpath):
                    dirs.append(_recurisive_fill(fpath, _levels=_levels - 1))
                else:
                    files.append(
                        make_file_info(
                            fullpath=fpath,
                            root=root,
                        )
                    )
        relpath = path.relative_to(root)
        return PathDictData(
            path=relpath,
            files=files,
            dirs=dirs,
            name=relpath.name,
        )

    return _recurisive_fill(fullpath, _levels=levels)


def validate_path(path: Path, root: Path):
    if not path.is_absolute():
        path = (root / path).resolve()
    # check if path is in root
    if not path.is_relative_to(root):
        raise Exception("Path is not in root")

    return path


class PathDict(fn.Node):
    """
    Seriealizes a path to dict
    """

    node_id = "files.path_dict"
    node_name = "Path Dict"
    parent = fn.NodeInput(id="parent", type=Union[str, PathDictData], default=".")
    path = fn.NodeInput(id="path", type=str, default=".")
    data = fn.NodeOutput(id="data", type=PathDictData)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_input("parent").on("after_set_value", self._update_keys)

    def _update_keys(self, *args, **kwargs):
        try:
            d = self.get_input("parent").value
        except KeyError:
            return
        if isinstance(d, PathDictData):
            self.get_input("path").update_value_options(
                options=funcnodes_core.io.EnumOf(
                    type="enum",
                    values=[sub.path for sub in d.dirs],
                    keys=[sub.name for sub in d.dirs],
                    nullable=False,
                )
            )
        else:
            self.get_input("path").update_value_options(options=None)

    async def func(self, path: str, parent: Union[str, PathDictData] = ".") -> None:
        if self.nodespace is None:
            raise Exception("Node not in a nodespace")

        root = Path(self.nodespace.get_property("files_dir"))
        if isinstance(parent, str):
            parent = make_path_dict(validate_path(Path(parent), root), root, levels=1)

        if path == "." and parent:
            self.outputs["data"].value = parent
            return
        if parent:
            path = parent.path / path
        targetpath = Path(path)
        fullpath = validate_path(targetpath, root)

        self.outputs["data"].value = make_path_dict(fullpath, root)


class BrowseFolder(fn.Node):
    """
    Browse a folder
    """

    node_id = "files.browse_folder"
    node_name = "Browse Folder"

    path = fn.NodeInput(id="path", type=Union[str, PathDictData], default="")
    files = fn.NodeOutput(id="files", type=List[FileInfoData])
    dirs = fn.NodeOutput(id="dirs", type=List[PathDictData])

    async def func(self, path: Union[str, PathDictData]) -> None:
        """
        Uploads a file to a given URL.

        Args:
          url (str): The URL to upload the file to.
          file (str): The path to the file to upload.
        """
        if self.nodespace is None:
            raise Exception("Node not in a nodespace")
        root = Path(self.nodespace.get_property("files_dir"))
        if not isinstance(path, PathDictData):
            fullpath = validate_path(Path(path), root)
            path = make_path_dict(fullpath, root)

        validate_path(path.path, root)

        self.inputs["path"].set_value(path.path, does_trigger=False)
        self.outputs["files"].value = path.files
        self.outputs["dirs"].value = path.dirs


class OpenFile(fn.Node):
    """
    Open a file
    """

    node_id = "files.open_file"
    node_name = "Open File"
    parent = fn.NodeInput(id="parent", type=Union[str, PathDictData], default=".")
    path = fn.NodeInput(
        id="path",
        type=Union[str, FileInfoData],
    )

    data = fn.NodeOutput(id="data", type=fn.types.databytes)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_input("parent").on("after_set_value", self._update_keys)

    def _update_keys(self, *args, **kwargs):
        try:
            d = self.get_input("parent").value
        except KeyError:
            return
        if isinstance(d, PathDictData):
            self.get_input("path").update_value_options(
                options=funcnodes_core.io.EnumOf(
                    type="enum",
                    values=[sub.path for sub in d.files],
                    keys=[sub.name for sub in d.files],
                    nullable=False,
                )
            )
        else:
            self.get_input("path").update_value_options(options=None)

    async def func(
        self,
        path: Union[str, FileInfoData],
        parent: Union[str, PathDictData] = ".",
    ) -> None:
        """
        Uploads a file to a given URL.

        Args:
          url (str): The URL to upload the file to.
          file (str): The path to the file to upload.
        """
        if self.nodespace is None:
            raise Exception("Node not in a nodespace")
        root = Path(self.nodespace.get_property("files_dir"))
        if isinstance(parent, str):
            parent = make_path_dict(validate_path(Path(parent), root), root, levels=1)
        if isinstance(path, str):
            if parent:
                path = parent.path / path
            fullpath = validate_path(Path(path), root)
            path = make_file_info(fullpath, root)

        fullpath = validate_path(path.path, root)
        with open(fullpath, "rb") as file:
            self.outputs["data"].value = fn.types.databytes(file.read())


class FileInfo(fn.Node):
    """
    Get file
    """

    node_id = "files.file_info"
    node_name = "File Info"
    parent = fn.NodeInput(id="parent", type=Union[str, PathDictData], default=".")
    path = fn.NodeInput(
        id="path",
        type=Union[str, FileInfoData],
    )
    size = fn.NodeOutput(id="size", type=int)
    modified = fn.NodeOutput(id="modified", type=float)
    created = fn.NodeOutput(id="created", type=float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_input("parent").on("after_set_value", self._update_keys)

    def _update_keys(self, *args, **kwargs):
        try:
            d = self.get_input("parent").value
        except KeyError:
            return
        if isinstance(d, PathDictData):
            self.get_input("path").update_value_options(
                options=funcnodes_core.io.EnumOf(
                    type="enum",
                    values=[sub.path for sub in d.files],
                    keys=[sub.name for sub in d.files],
                    nullable=False,
                )
            )
        else:
            self.get_input("path").update_value_options(options=None)

    async def func(
        self,
        path: Union[str, FileInfoData],
        parent: Optional[PathDictData] = None,
    ) -> None:
        if self.nodespace is None:
            raise Exception("Node not in a nodespace")

        root = Path(self.nodespace.get_property("files_dir"))
        if isinstance(parent, str):
            parent = make_path_dict(validate_path(Path(parent), root), root, levels=1)

        if isinstance(path, str):
            if parent:
                path = parent.path / path
            fullpath = validate_path(Path(path), root)
            path = make_file_info(fullpath, root)

        fullpath = validate_path(path.path, root)
        self.outputs["size"].value = os.path.getsize(fullpath)
        self.outputs["modified"].value = os.path.getmtime(fullpath)
        self.outputs["created"].value = os.path.getctime(fullpath)


class FileUpload(str):
    pass


class FileUploadNode(fn.Node):
    """
    Uploads a file
    """

    node_id = "files.upl"
    node_name = "File Upload"

    parent = fn.NodeInput(
        id="parent",
        type=Union[str, PathDictData],
        default=".",
        does_trigger=False,
    )
    input_data = fn.NodeInput(id="input_data", type=FileUpload)
    load = fn.NodeInput(id="load", type=bool, default=True, does_trigger=False)
    save = fn.NodeInput(id="save", type=bool, default=False, does_trigger=False)

    data = fn.NodeOutput(id="data", type=fn.types.databytes)
    file = fn.NodeOutput(id="file", type=FileInfoData)

    async def func(
        self,
        input_data: FileUpload,
        load: bool = True,
        save: bool = False,
        parent: Optional[PathDictData] = None,  # noqa F821
    ) -> None:
        """
        Uploads a file to a given URL.

        Args:
          url (str): The URL to upload the file to.
          file (str): The path to the file to upload.
        """

        if not load and not save:
            raise Exception("Either load or save must be True")

        if self.nodespace is None:
            raise Exception("Node not in a nodespace")

        root = Path(self.nodespace.get_property("files_dir"))
        fp = validate_path(Path(input_data), root)
        print("XXX", load, save, fp)
        if fp is None or not os.path.exists(fp):
            raise Exception(f"File not found: {input_data}")

        if load:
            with open(fp, "rb") as file:
                filedata = file.read()
            self.outputs["data"].value = fn.types.databytes(filedata)
        else:
            self.outputs["data"].value = fn.NoValue

        if not save:
            os.remove(fp)
            self.outputs["file"].value = fn.NoValue
        else:
            self.outputs["file"].value = make_file_info(fp, root)


class FolderUpload(str):
    pass


class FolderUploadNode(fn.Node):
    """
    Uploads a file
    """

    node_id = "files.upl_folder"
    node_name = "Folder Upload"

    parent = fn.NodeInput(
        id="parent",
        type=Union[str, PathDictData],
        default=".",
        does_trigger=False,
    )
    input_data = fn.NodeInput(id="input_data", type=FolderUpload)

    dir = fn.NodeOutput(id="dir", type=PathDictData)

    async def func(
        self, input_data: FolderUpload, parent: Union[str, PathDictData] = "."
    ) -> None:
        """
        Uploads a file to a given URL.

        Args:
          url (str): The URL to upload the file to.
          file (str): The path to the file to upload.
        """

        if self.nodespace is None:
            raise Exception("Node not in a nodespace")

        root = Path(self.nodespace.get_property("files_dir"))
        fp = validate_path(Path(input_data), root)

        if not os.path.exists(fp):
            raise Exception(f"Folder not found: {input_data}")

        pathdict = make_path_dict(fp, root)
        self.outputs["dir"].value = pathdict


_DEFAULT_USER_AGENT = f"funcnodes-files/{__version__} funcnodes/{fn.__version__}"


class FileDownloadNode(fn.Node):
    """
    Downloads a file from a given URL and returns the file's content as bytes.
    """

    node_id = "files.dld"
    node_name = "File Download"

    url = fn.NodeInput(id="url", type="str")
    parent = fn.NodeInput(
        id="parent",
        type=Union[str, PathDictData],
        default=".",
        does_trigger=False,
    )
    load = fn.NodeInput(id="load", type=bool, default=True, does_trigger=False)
    save = fn.NodeInput(id="save", type=bool, default=False, does_trigger=False)
    filename = fn.NodeInput(
        id="filename", type=Optional[str], default=None, does_trigger=False
    )

    data = fn.NodeOutput(id="data", type=fn.types.databytes)
    file = fn.NodeOutput(id="file", type=FileInfoData)

    user_agent = fn.NodeInput(
        id="user_agent", type=str, default=_DEFAULT_USER_AGENT, hidden=True
    )
    headers = fn.NodeInput(id="headers", type=Optional[dict], default=None, hidden=True)
    default_trigger_on_create = False

    async def func(
        self,
        url: str,
        parent: Union[str, PathDictData] = ".",
        load: bool = True,
        save: bool = False,
        filename: Optional[str] = None,
        user_agent: str = _DEFAULT_USER_AGENT,
        headers: Optional[dict] = None,
    ) -> None:
        """
        Downloads a file from a given URL and sets the "data" output to the file's content as bytes.

        Args:
          url (str): The URL of the file to download.
          timeout (float): The timeout in seconds for the download request.
        """
        if not load and not save:
            raise Exception("Either load or save must be True")

        if save:
            if self.nodespace is None:
                raise Exception("Node not in a nodespace")
            root = Path(self.nodespace.get_property("files_dir"))
            if isinstance(parent, str):
                parent = make_path_dict(
                    validate_path(Path(parent), root), root, levels=1
                )
            if parent:
                path = validate_path(parent.path, root)
            else:
                path = root

        if headers is None:
            headers = {}
        if user_agent:
            headers["User-Agent"] = user_agent

        def _dl(filename, headers):
            with requests.get(url, stream=True, headers=headers) as r:
                r.raise_for_status()

                # Try to get the filename from the Content-Disposition header
                content_disposition = r.headers.get("Content-Disposition")
                if filename is None and save:
                    if content_disposition:
                        # Extract filename from Content-Disposition header
                        filename = (
                            content_disposition.split("filename=")[-1]
                            .strip('"')
                            .strip("'")
                        )
                        filename = unquote(
                            filename
                        )  # Decode URL-encoded characters if present
                    else:
                        # Fallback: Use the URL's last segment as filename
                        filename = unquote(url.split("/")[-1])
                # Get the total size from the headers
                total_size = int(r.headers.get("Content-Length", 0)) or None
                value = fn.NoValue

                if save:
                    fullpath = path / filename
                    with (
                        open(fullpath, "wb") as f,
                        self.progress(
                            total=total_size,
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=filename,
                        ) as progress,
                    ):
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(len(chunk))
                    if load:
                        with open(fullpath, "rb") as f:
                            value = fn.types.databytes(f.read())
                else:
                    with (
                        BytesIO() as f,
                        self.progress(
                            total=total_size,
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            desc=filename,
                        ) as progress,
                    ):
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(len(chunk))
                        value = fn.types.databytes(f.getvalue())

            self.outputs["data"].value = value
            if save:
                self.outputs["file"].value = make_file_info(fullpath, root)
            else:
                self.outputs["file"].value = fn.NoValue

        await asyncio.to_thread(_dl, filename=filename, headers=headers)


@dataclass
class FileDownload:
    filename: str
    content: str

    @property
    def bytedata(self):
        return fn.types.databytes(base64.b64decode(self.content))

    def __str__(self) -> str:
        return f"FileDownload(filename={self.filename})"

    def __repr__(self) -> str:
        return self.__str__()


class FileDownloadLocal(fn.Node):
    """
    Downloads a file the funcnodes stream to a local file
    """

    node_id = "files.dld_local"
    node_name = "File Download Local"

    output_data = fn.NodeOutput(id="output_data", type=FileDownload)
    data = fn.NodeInput(id="data", type=Union[fn.types.databytes, FileInfoData])
    filename = fn.NodeInput(id="filename", type=Optional[str], default=None)

    async def func(
        self, data: Union[fn.types.databytes, FileInfoData], filename: str = None
    ) -> None:
        """
        Downloads a file from a given URL and sets the "data" output to the file's content as bytes.

        Args:
          url (str): The URL of the file to download.
          timeout (float): The timeout in seconds for the download request.
        """
        if isinstance(data, FileInfoData):
            if self.nodespace is None:
                raise Exception("Node not in a nodespace")
            root = Path(self.nodespace.get_property("files_dir"))
            fullpath = validate_path(data.path, root)
            if filename is None:
                filename = data.name
            with open(fullpath, "rb") as file:
                data = file.read()

        if filename is None:
            raise Exception("Filename must be provided if the data is passed as bytes")

        self.outputs["output_data"].value = FileDownload(
            filename=filename,
            content=base64.b64encode(data).decode("utf-8"),
        )


class FileDeleteNode(fn.Node):
    """
    Deletes a file
    """

    node_id = "files.delete"
    node_name = "Delete File"

    data = fn.NodeInput(
        id="data",
        type=Union[PathDictData, FileInfoData],
        does_trigger=False,
    )

    async def func(self, data: Optional[Union[PathDictData, FileInfoData]]) -> None:
        """
        Deletes a file from the given path.

        Args:
          path (str): The path to the file to delete.
        """
        if self.nodespace is None:
            raise Exception("Node not in a nodespace")
        root = Path(self.nodespace.get_property("files_dir"))
        fullpath = validate_path(data.path, root)

        if os.path.isfile(fullpath):
            os.remove(fullpath)
        elif os.path.isdir(fullpath):
            # if fullpath is root, delete only the content
            if fullpath == root:
                for f in os.listdir(fullpath):
                    shutil.rmtree(fullpath / f)
            else:
                shutil.rmtree(fullpath)


class SaveFile(fn.Node):
    """
    Saves a file
    """

    node_id = "files.save"
    node_name = "Save File"

    data = fn.NodeInput(id="data", type=fn.types.databytes)
    filename = fn.NodeInput(id="filename", type=str)
    path = fn.NodeInput(
        id="path", type=Optional[Union[str, PathDictData]], default=None
    )

    async def func(
        self,
        data: fn.types.databytes,
        filename: str,
        path: Optional[Union[str, PathDictData]] = None,
    ) -> None:
        if self.nodespace is None:
            raise Exception("Node not in a nodespace")
        root = Path(self.nodespace.get_property("files_dir"))
        if isinstance(path, PathDictData):
            path = path.path
        elif path is None:
            path = root
        else:
            path = Path(path)

        path = path / filename

        path = validate_path(path, root)

        if not os.path.exists(path.parent):
            os.makedirs(path.parent)

        with open(path, "wb") as file:
            file.write(data)


NODE_SHELF = fn.Shelf(
    name="Files",  # The name of the shelf.
    nodes=[
        FileDownloadNode,
        FileUploadNode,
        FolderUploadNode,
        FileDownloadLocal,
        BrowseFolder,
        OpenFile,
        SaveFile,
        PathDict,
        FileInfo,
        FileDeleteNode,
    ],  # A list of node classes to include in the shelf.
    description="Nodes for working with data and files.",
    subshelves=[],
)


REACT_PLUGIN = {
    "module": os.path.join(os.path.dirname(__file__), "react_plugin", "js", "main.js"),
}
