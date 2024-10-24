import {
  // IOType,
  RendererPlugin,
  FuncNodesReactPlugin,
  RenderPluginFactoryProps,
} from "@linkdlab/funcnodes_react_flow";
import {
  InputRendererProps,
  OutputRendererProps,
} from "@linkdlab/funcnodes_react_flow/dist/types/states/nodeio.t";

type FileUploadProps = {
  filename: string;
  content: string;
  path: string;
};

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

    const on_change = (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;
      var reader = new FileReader();
      reader.onload = function () {
        const base64 = reader.result as string;
        const pureBase64 = base64.split(",")[1];

        const fileupload: FileUploadProps = {
          filename: files[0].name,
          content: pureBase64,
          path: files[0].webkitRelativePath || "/",
        };

        if (!base64) return;
        fnrf_zst.worker?.set_io_value({
          nid: io.node,
          ioid: io.id,
          value: fileupload,
          set_default: false,
        });
      };
      reader.readAsDataURL(files[0]);
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

    const on_change = (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      const filePromises = Array.from(files).map((file) => {
        return new Promise<FileUploadProps>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = function () {
            const base64 = reader.result as string;
            const pureBase64 = base64.split(",")[1];
            if (pureBase64) {
              resolve({
                filename: file.name,
                path: file.webkitRelativePath || file.name,
                content: pureBase64,
              });
            } else {
              reject(new Error("Failed to read file content"));
            }
          };
          reader.onerror = () => reject(new Error("File reading failed"));
          reader.readAsDataURL(file);
        });
      });

      Promise.all(filePromises)
        .then((filesData) => {
          const payload = {
            nid: io.node,
            ioid: io.id,
            value: filesData,
            set_default: false,
          };

          return fnrf_zst.worker?.set_io_value(payload);
        })
        .then(() => {
          console.log("Folder uploaded");
        })
        .catch((err) => {
          console.error("Error uploading folder:", err);
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
          webkitdirectory=""
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
const PlotlyRendererPlugin: RendererPlugin = {
  handle_preview_renderers: {},
  data_overlay_renderers: {},
  data_preview_renderers: {},
  data_view_renderers: {},
  input_renderers: {},
};

const Plugin: FuncNodesReactPlugin = {
  RendererPlugin: PlotlyRendererPlugin,
  renderpluginfactory: renderpluginfactory,
};

export default Plugin;
