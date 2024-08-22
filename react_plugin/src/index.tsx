import {
  // IOType,
  RendererPlugin,
  FuncNodesReactPlugin,
  RenderPluginFactoryProps,
} from "@linkdlab/funcnodes_react_flow";
import { InputRendererProps } from "@linkdlab/funcnodes_react_flow/dist/types/states/nodeio.t";

type FileUploadProps = {
  filename: string;
  content: string;
  path: string;
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

  return {
    input_renderers: {
      "funcnodes_files.FileUpload": FileInput,
      "funcnodes_files.FolderUpload": FolderInput,
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
