import {
  // IOType,
  RendererPlugin,
  FuncNodesReactPlugin,
  RenderPluginFactoryProps,
  // FuncNodesContext,
  // FuncNodesReactFlowZustandInterface,
  InputRendererProps,
  OutputRendererProps,
} from "@linkdlab/funcnodes_react_flow";

// type FileUploadProps = {
//   filename: string;
//   content: string;
//   path: string;
// };

type FileDownloadProps = {
  filename: string;
  content: string;
};

const renderpluginfactory = ({
  React,
  fnrf_zst,
}: RenderPluginFactoryProps): RendererPlugin => {
  const FileInput = ({ io }: InputRendererProps) => {
    const fileInput = React.useRef<HTMLInputElement>(null);
    const setProgress = (
      p: number,
      total: number | undefined,
      start: number
    ) => {
      fnrf_zst.on_node_action({
        type: "update",
        id: io.node,
        node: {
          progress: {
            prefix: "Uploading",
            n: p,
            total: total,
            elapsed: (new Date().getTime() - start) / 1000,
            unit_scale: true,
            unit: "B",
            unit_divisor: 1024,
          },
        },
        from_remote: true,
      });
    };

    const on_change = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;
      const nodestore = fnrf_zst.nodespace.get_node(io.node);
      if (!nodestore) return;
      let node = nodestore.getState();
      let parent_io = node.io["parent"];
      if (!parent_io) return;
      let parentpath = undefined;
      for (let i = 0; i < 10; i++) {
        if (parent_io.fullvalue) {
          parentpath = parent_io.fullvalue.path;
          break;
        }
        if (parent_io.try_get_full_value === undefined) {
          break;
        }
        parent_io.try_get_full_value();
        await new Promise((resolve) => setTimeout(resolve, 500));
        node = nodestore.getState();
        parent_io = node.io["parent"];
        if (!parent_io) break;
      }

      const start = new Date().getTime();

      const resp: string[] | undefined = await fnrf_zst.worker?.upload_file({
        files: files,
        onProgressCallback: (loaded: number, total?: number) => {
          setProgress(loaded, total, start);
        },
        root: parentpath,
      });

      fnrf_zst.worker?.set_io_value({
        nid: io.node,
        ioid: io.id,
        value: resp?.[0],
        set_default: true,
      });
    };

    return (
      <div>
        <input
          className="nodedatainput styledinput"
          type="file"
          // value={v}
          onChange={on_change}
          disabled={io.connected}
          style={{ display: "none" }}
          ref={fileInput}
        />
        <button
          className="nodedatainput styledinput"
          disabled={io.connected}
          onClick={() => {
            fileInput.current?.click();
          }}
        >
          Upload File
        </button>
      </div>
    );
  };

  const FolderInput = ({ io }: InputRendererProps) => {
    const fileInput = React.useRef<HTMLInputElement>(null);

    const setProgress = (
      p: number,
      total: number | undefined,
      start: number
    ) => {
      fnrf_zst.on_node_action({
        type: "update",
        id: io.node,
        node: {
          progress: {
            prefix: "Uploading",
            n: p,
            total: total,
            elapsed: (new Date().getTime() - start) / 1000,
            unit_scale: true,
            unit: "B",
            unit_divisor: 1024,
          },
        },
        from_remote: true,
      });
    };
    const on_change = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;
      const nodestore = fnrf_zst.nodespace.get_node(io.node);
      if (!nodestore) return;
      let node = nodestore.getState();
      let parent_io = node.io["parent"];
      if (!parent_io) return;
      let parentpath = undefined;
      for (let i = 0; i < 10; i++) {
        if (parent_io.fullvalue) {
          parentpath = parent_io.fullvalue.path;
          break;
        }
        if (parent_io.try_get_full_value === undefined) {
          break;
        }
        parent_io.try_get_full_value();
        await new Promise((resolve) => setTimeout(resolve, 500));
        node = nodestore.getState();
        parent_io = node.io["parent"];
        if (!parent_io) break;
      }

      const start = new Date().getTime();

      const resp: string[] | undefined = await fnrf_zst.worker?.upload_file({
        files: files,
        onProgressCallback: (loaded: number, total?: number) => {
          setProgress(loaded, total, start);
        },
        root: parentpath,
      });
      fnrf_zst.worker?.set_io_value({
        nid: io.node,
        ioid: io.id,
        value: resp,
        set_default: true,
      });
    };
    return (
      <div>
        <input
          className="nodedatainput styledinput"
          type="file"
          onChange={on_change}
          disabled={io.connected}
          style={{ display: "none" }}
          ref={fileInput}
          /* @ts-expect-error */
          webkitdirectory="true"
          directory="true"
          multiple
        />
        <button
          className="nodedatainput styledinput"
          disabled={io.connected}
          onClick={() => {
            fileInput.current?.click();
          }}
        >
          Upload Folder
        </button>
      </div>
    );
  };

  const FileDownload = ({ io }: OutputRendererProps) => {
    const fileDownload = React.useRef<HTMLAnchorElement>(null);

    const download = async () => {
      const fullvalue = await fnrf_zst.worker?.get_io_full_value({
        nid: io.node,
        ioid: io.id,
      });
      const { filename, content } = fullvalue as FileDownloadProps;
      // Convert the base64 content to a binary buffer
      const byteCharacters = atob(content);
      const byteNumbers = new Array(byteCharacters.length)
        .fill(null)
        .map((_, i) => byteCharacters.charCodeAt(i));
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray]); // Blob defaults to a generic MIME type (e.g., "application/octet-stream")

      const url = URL.createObjectURL(blob); // Create an object URL for the blob
      const a = fileDownload.current;
      a?.setAttribute("href", url);
      a?.setAttribute("download", filename);
      a?.click();
    };

    return (
      <div>
        <a
          ref={fileDownload}
          style={{ display: "none" }}
          href=""
          download=""
        ></a>

        <button className="nodedatainput styledinput" onClick={download}>
          Download File
        </button>
      </div>
    );
  };

  return {
    input_renderers: {
      "funcnodes_files.FileUpload": FileInput,
      "funcnodes_files.FolderUpload": FolderInput,
    },
    output_renderers: {
      "funcnodes_files.FileDownload": FileDownload,
    },
  };
};

const Plugin: FuncNodesReactPlugin = {
  renderpluginfactory: renderpluginfactory,
};

export default Plugin;
