var e = {
    d: (n, t) => {
      for (var r in t)
        e.o(t, r) &&
          !e.o(n, r) &&
          Object.defineProperty(n, r, { enumerable: !0, get: t[r] });
    },
    o: (e, n) => Object.prototype.hasOwnProperty.call(e, n),
  },
  n = {};
e.d(n, { A: () => t });
const t = {
  RendererPlugin: {
    handle_preview_renderers: {},
    data_overlay_renderers: {},
    data_preview_renderers: {},
    data_view_renderers: {},
    input_renderers: {},
  },
  renderpluginfactory: function (e) {
    var n = e.React,
      t = e.fnrf_zst;
    return {
      input_renderers: {
        "funcnodes_files.FileUpload": function (e) {
          var r = e.io,
            a = n.useRef(null);
          return n.createElement(
            "div",
            null,
            n.createElement("input", {
              className: "nodedatainput styledinput",
              type: "file",
              onChange: function (e) {
                var n = e.target.files;
                if (n && 0 !== n.length) {
                  var a = new FileReader();
                  (a.onload = function () {
                    var e,
                      l = a.result,
                      i = l.split(",")[1],
                      o = {
                        filename: n[0].name,
                        content: i,
                        path: n[0].webkitRelativePath || "/",
                      };
                    l &&
                      (null === (e = t.worker) ||
                        void 0 === e ||
                        e.set_io_value({
                          nid: r.node,
                          ioid: r.id,
                          value: o,
                          set_default: !1,
                        }));
                  }),
                    a.readAsDataURL(n[0]);
                }
              },
              disabled: r.connected,
              style: { display: "none" },
              ref: a,
            }),
            n.createElement(
              "button",
              {
                className: "nodedatainput styledinput",
                disabled: r.connected,
                onClick: function () {
                  var e;
                  null === (e = a.current) || void 0 === e || e.click();
                },
              },
              "Upload File"
            )
          );
        },
        "funcnodes_files.FolderUpload": function (e) {
          var r = e.io,
            a = n.useRef(null);
          return n.createElement(
            "div",
            null,
            n.createElement("input", {
              className: "nodedatainput styledinput",
              type: "file",
              onChange: function (e) {
                var n = e.target.files;
                if (n && 0 !== n.length) {
                  var a = Array.from(n).map(function (e) {
                    return new Promise(function (n, t) {
                      var r = new FileReader();
                      (r.onload = function () {
                        var a = r.result.split(",")[1];
                        a
                          ? n({
                              filename: e.name,
                              path: e.webkitRelativePath || e.name,
                              content: a,
                            })
                          : t(new Error("Failed to read file content"));
                      }),
                        (r.onerror = function () {
                          return t(new Error("File reading failed"));
                        }),
                        r.readAsDataURL(e);
                    });
                  });
                  Promise.all(a)
                    .then(function (e) {
                      var n,
                        a = {
                          nid: r.node,
                          ioid: r.id,
                          value: e,
                          set_default: !1,
                        };
                      return null === (n = t.worker) || void 0 === n
                        ? void 0
                        : n.set_io_value(a);
                    })
                    .then(function () {
                      console.log("Folder uploaded");
                    })
                    .catch(function (e) {
                      console.error("Error uploading folder:", e);
                    });
                }
              },
              disabled: r.connected,
              style: { display: "none" },
              ref: a,
              webkitdirectory: "",
            }),
            n.createElement(
              "button",
              {
                className: "nodedatainput styledinput",
                disabled: r.connected,
                onClick: function () {
                  var e;
                  null === (e = a.current) || void 0 === e || e.click();
                },
              },
              "Upload Folder"
            )
          );
        },
      },
    };
  },
};
var r = n.A;
export { r as default };
