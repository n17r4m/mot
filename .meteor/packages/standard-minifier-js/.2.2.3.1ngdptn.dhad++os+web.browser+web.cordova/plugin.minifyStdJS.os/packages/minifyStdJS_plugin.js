(function () {

/* Imports */
var meteorJsMinify = Package['minifier-js'].meteorJsMinify;
var Babel = Package['babel-compiler'].Babel;
var BabelCompiler = Package['babel-compiler'].BabelCompiler;
var ECMAScript = Package.ecmascript.ECMAScript;
var meteorInstall = Package.modules.meteorInstall;
var meteorBabelHelpers = Package['babel-runtime'].meteorBabelHelpers;
var Promise = Package.promise.Promise;

var require = meteorInstall({"node_modules":{"meteor":{"minifyStdJS":{"plugin":{"minify-js.js":function(require,exports,module){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                             //
// packages/minifyStdJS/plugin/minify-js.js                                                                    //
//                                                                                                             //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                               //
let extractModuleSizesTree;
module.watch(require("./stats.js"), {
  extractModuleSizesTree(v) {
    extractModuleSizesTree = v;
  }

}, 0);
Plugin.registerMinifier({
  extensions: ['js'],
  archMatching: 'web'
}, function () {
  var minifier = new MeteorBabelMinifier();
  return minifier;
});

function MeteorBabelMinifier() {}

;

MeteorBabelMinifier.prototype.processFilesForBundle = function (files, options) {
  var mode = options.minifyMode; // don't minify anything for development

  if (mode === 'development') {
    files.forEach(function (file) {
      file.addJavaScript({
        data: file.getContentsAsBuffer(),
        sourceMap: file.getSourceMap(),
        path: file.getPathInBundle()
      });
    });
    return;
  }

  function maybeThrowMinifyErrorBySourceFile(error, file) {
    var minifierErrorRegex = /^(.*?)\s?\((\d+):(\d+)\)$/;
    var parseError = minifierErrorRegex.exec(error.message);

    if (!parseError) {
      // If we were unable to parse it, just let the usual error handling work.
      return;
    }

    var lineErrorMessage = parseError[1];
    var lineErrorLineNumber = parseError[2];
    var parseErrorContentIndex = lineErrorLineNumber - 1; // Unlikely, since we have a multi-line fixed header in this file.

    if (parseErrorContentIndex < 0) {
      return;
    } /*
       What we're parsing looks like this:
       /////////////////////////////////////////
      //                                     //
      // path/to/file.js                     //
      //                                     //
      /////////////////////////////////////////
                                             // 1
         var illegalECMAScript = true;       // 2
                                             // 3
      /////////////////////////////////////////
       Btw, the above code is intentionally not newer ECMAScript so
      we don't break ourselves.
       */

    var contents = file.getContentsAsString().split(/\n/);
    var lineContent = contents[parseErrorContentIndex]; // Try to grab the line number, which sometimes doesn't exist on
    // line, abnormally-long lines in a larger block.

    var lineSrcLineParts = /^(.*?)(?:\s*\/\/ (\d+))?$/.exec(lineContent); // The line didn't match at all?  Let's just not try.

    if (!lineSrcLineParts) {
      return;
    }

    var lineSrcLineContent = lineSrcLineParts[1];
    var lineSrcLineNumber = lineSrcLineParts[2]; // Count backward from the failed line to find the filename.

    for (var c = parseErrorContentIndex - 1; c >= 0; c--) {
      var sourceLine = contents[c]; // If the line is a boatload of slashes, we're in the right place.

      if (/^\/\/\/{6,}$/.test(sourceLine)) {
        // If 4 lines back is the same exact line, we've found the framing.
        if (contents[c - 4] === sourceLine) {
          // So in that case, 2 lines back is the file path.
          var parseErrorPath = contents[c - 2].substring(3).replace(/\s+\/\//, "");
          var minError = new Error("Babili minification error " + "within " + file.getPathInBundle() + ":\n" + parseErrorPath + (lineSrcLineNumber ? ", line " + lineSrcLineNumber : "") + "\n" + "\n" + lineErrorMessage + ":\n" + "\n" + lineSrcLineContent + "\n");
          throw minError;
        }
      }
    }
  }

  const toBeAdded = {
    data: "",
    stats: Object.create(null)
  };
  files.forEach(file => {
    // Don't reminify *.min.js.
    if (/\.min\.js$/.test(file.getPathInBundle())) {
      toBeAdded.data += file.getContentsAsString();
    } else {
      var minified;

      try {
        minified = meteorJsMinify(file.getContentsAsString());

        if (!(minified && typeof minified.code === "string")) {
          throw new Error();
        }
      } catch (err) {
        var filePath = file.getPathInBundle();
        maybeThrowMinifyErrorBySourceFile(err, file);
        err.message += " while minifying " + filePath;
        throw err;
      }

      const tree = extractModuleSizesTree(minified.code);

      if (tree) {
        toBeAdded.stats[file.getPathInBundle()] = [Buffer.byteLength(minified.code), tree];
      } else {
        toBeAdded.stats[file.getPathInBundle()] = Buffer.byteLength(minified.code);
      }

      toBeAdded.data += minified.code;
    }

    toBeAdded.data += '\n\n';
    Plugin.nudge();
  });

  if (files.length) {
    files[0].addJavaScript(toBeAdded);
  }
};
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

},"stats.js":function(require,exports,module){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                             //
// packages/minifyStdJS/plugin/stats.js                                                                        //
//                                                                                                             //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                               //
module.export({
  extractModuleSizesTree: () => extractModuleSizesTree
});
let Visitor;
module.watch(require("./visitor.js"), {
  default(v) {
    Visitor = v;
  }

}, 0);
// This RegExp will be used to scan the source for calls to meteorInstall,
// taking into consideration that the function name may have been mangled
// to something other than "meteorInstall" by the minifier.
const meteorInstallRegExp = new RegExp([// If meteorInstall is called by its unminified name, then that's what
// we should be looking for in the AST.
/\b(meteorInstall)\(\{/, // If the meteorInstall function name has been minified, we can figure
// out its mangled name by examining the import assingment.
/\b(\w+)=Package\.modules\.meteorInstall\b/, /\b(\w+)=Package\["modules-runtime"\].meteorInstall\b/, // Sometimes uglify-es will inline (0,Package.modules.meteorInstall) as
// a call expression.
/\(0,Package\.modules\.(meteorInstall)\)\(/, /\(0,Package\["modules-runtime"\]\.(meteorInstall)\)\(/].map(exp => exp.source).join("|"));

function extractModuleSizesTree(source) {
  const match = meteorInstallRegExp.exec(source);

  if (match) {
    const ast = Babel.parse(source);
    let meteorInstallName = "meteorInstall";
    match.some((name, i) => i > 0 && (meteorInstallName = name));
    meteorInstallVisitor.visit(ast, meteorInstallName, source);
    return meteorInstallVisitor.tree;
  }
}

const meteorInstallVisitor = new class extends Visitor {
  reset(root, meteorInstallName, source) {
    this.name = meteorInstallName;
    this.source = source;
    this.tree = null;
  }

  visitCallExpression(node) {
    if (this.tree !== null) {
      return;
    }

    if (hasIdWithName(node.callee, this.name)) {
      const source = this.source;

      function walk(expr) {
        if (expr.type !== "ObjectExpression") {
          return Buffer.byteLength(source.slice(expr.start, expr.end));
        }

        const contents = Object.create(null);
        expr.properties.forEach(prop => {
          const keyName = getKeyName(prop.key);

          if (typeof keyName === "string") {
            contents[keyName] = walk(prop.value);
          }
        });
        return contents;
      }

      this.tree = walk(node.arguments[0]);
    } else {
      this.visitChildren(node);
    }
  }

}();

function hasIdWithName(node, name) {
  switch (node && node.type) {
    case "SequenceExpression":
      const last = node.expressions[node.expressions.length - 1];
      return hasIdWithName(last, name);

    case "MemberExpression":
      return hasIdWithName(node.property, name);

    case "Identifier":
      return node.name === name;

    default:
      return false;
  }
}

function getKeyName(key) {
  if (key.type === "Identifier") {
    return key.name;
  }

  if (key.type === "StringLiteral" || key.type === "Literal") {
    return key.value;
  }

  return null;
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

},"visitor.js":function(require,exports,module){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                             //
// packages/minifyStdJS/plugin/visitor.js                                                                      //
//                                                                                                             //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                               //
"use strict";

module.export({
  default: () => Visitor
});
let isObject, isNodeLike;
module.watch(require("./utils.js"), {
  isObject(v) {
    isObject = v;
  },

  isNodeLike(v) {
    isNodeLike = v;
  }

}, 0);
const codeOfUnderscore = "_".charCodeAt(0);

class Visitor {
  visit(root) {
    this.reset.apply(this, arguments);
    this.visitWithoutReset(root);
  }

  visitWithoutReset(node) {
    if (Array.isArray(node)) {
      node.forEach(this.visitWithoutReset, this);
    } else if (isNodeLike(node)) {
      const method = this["visit" + node.type];

      if (typeof method === "function") {
        // The method must call this.visitChildren(node) to continue
        // traversing.
        method.call(this, node);
      } else {
        this.visitChildren(node);
      }
    }
  }

  visitChildren(node) {
    if (!isNodeLike(node)) {
      return;
    }

    const keys = Object.keys(node);
    const keyCount = keys.length;

    for (let i = 0; i < keyCount; ++i) {
      const key = keys[i];

      if (key === "loc" || // Ignore .loc.{start,end} objects.
      // Ignore "private" properties added by Babel.
      key.charCodeAt(0) === codeOfUnderscore) {
        continue;
      }

      const child = node[key];

      if (!isObject(child)) {
        // Ignore properties whose values aren't objects.
        continue;
      }

      this.visitWithoutReset(child);
    }
  }

}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

},"utils.js":function(require,exports,module){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                             //
// packages/minifyStdJS/plugin/utils.js                                                                        //
//                                                                                                             //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                               //
"use strict";

module.export({
  isObject: () => isObject,
  isNodeLike: () => isNodeLike
});
const codeOfA = "A".charCodeAt(0);
const codeOfZ = "Z".charCodeAt(0);

function isObject(value) {
  return typeof value === "object" && value !== null;
}

function isNodeLike(value) {
  return isObject(value) && !Array.isArray(value) && isCapitalized(value.type);
}

function isCapitalized(string) {
  if (typeof string !== "string") {
    return false;
  }

  const code = string.charCodeAt(0);
  return code >= codeOfA && code <= codeOfZ;
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}}}}}},{
  "extensions": [
    ".js",
    ".json"
  ]
});
require("./node_modules/meteor/minifyStdJS/plugin/minify-js.js");
require("./node_modules/meteor/minifyStdJS/plugin/stats.js");
require("./node_modules/meteor/minifyStdJS/plugin/visitor.js");
require("./node_modules/meteor/minifyStdJS/plugin/utils.js");

/* Exports */
if (typeof Package === 'undefined') Package = {};
Package.minifyStdJS = {};

})();







//# sourceURL=meteor://💻app/packages/minifyStdJS_plugin.js
//# sourceMappingURL=data:application/json;charset=utf8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZ5U3RkSlMvcGx1Z2luL21pbmlmeS1qcy5qcyIsIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZ5U3RkSlMvcGx1Z2luL3N0YXRzLmpzIiwibWV0ZW9yOi8v8J+Su2FwcC9wYWNrYWdlcy9taW5pZnlTdGRKUy9wbHVnaW4vdmlzaXRvci5qcyIsIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZ5U3RkSlMvcGx1Z2luL3V0aWxzLmpzIl0sIm5hbWVzIjpbImV4dHJhY3RNb2R1bGVTaXplc1RyZWUiLCJtb2R1bGUiLCJ3YXRjaCIsInJlcXVpcmUiLCJ2IiwiUGx1Z2luIiwicmVnaXN0ZXJNaW5pZmllciIsImV4dGVuc2lvbnMiLCJhcmNoTWF0Y2hpbmciLCJtaW5pZmllciIsIk1ldGVvckJhYmVsTWluaWZpZXIiLCJwcm90b3R5cGUiLCJwcm9jZXNzRmlsZXNGb3JCdW5kbGUiLCJmaWxlcyIsIm9wdGlvbnMiLCJtb2RlIiwibWluaWZ5TW9kZSIsImZvckVhY2giLCJmaWxlIiwiYWRkSmF2YVNjcmlwdCIsImRhdGEiLCJnZXRDb250ZW50c0FzQnVmZmVyIiwic291cmNlTWFwIiwiZ2V0U291cmNlTWFwIiwicGF0aCIsImdldFBhdGhJbkJ1bmRsZSIsIm1heWJlVGhyb3dNaW5pZnlFcnJvckJ5U291cmNlRmlsZSIsImVycm9yIiwibWluaWZpZXJFcnJvclJlZ2V4IiwicGFyc2VFcnJvciIsImV4ZWMiLCJtZXNzYWdlIiwibGluZUVycm9yTWVzc2FnZSIsImxpbmVFcnJvckxpbmVOdW1iZXIiLCJwYXJzZUVycm9yQ29udGVudEluZGV4IiwiY29udGVudHMiLCJnZXRDb250ZW50c0FzU3RyaW5nIiwic3BsaXQiLCJsaW5lQ29udGVudCIsImxpbmVTcmNMaW5lUGFydHMiLCJsaW5lU3JjTGluZUNvbnRlbnQiLCJsaW5lU3JjTGluZU51bWJlciIsImMiLCJzb3VyY2VMaW5lIiwidGVzdCIsInBhcnNlRXJyb3JQYXRoIiwic3Vic3RyaW5nIiwicmVwbGFjZSIsIm1pbkVycm9yIiwiRXJyb3IiLCJ0b0JlQWRkZWQiLCJzdGF0cyIsIk9iamVjdCIsImNyZWF0ZSIsIm1pbmlmaWVkIiwibWV0ZW9ySnNNaW5pZnkiLCJjb2RlIiwiZXJyIiwiZmlsZVBhdGgiLCJ0cmVlIiwiQnVmZmVyIiwiYnl0ZUxlbmd0aCIsIm51ZGdlIiwibGVuZ3RoIiwiZXhwb3J0IiwiVmlzaXRvciIsImRlZmF1bHQiLCJtZXRlb3JJbnN0YWxsUmVnRXhwIiwiUmVnRXhwIiwibWFwIiwiZXhwIiwic291cmNlIiwiam9pbiIsIm1hdGNoIiwiYXN0IiwiQmFiZWwiLCJwYXJzZSIsIm1ldGVvckluc3RhbGxOYW1lIiwic29tZSIsIm5hbWUiLCJpIiwibWV0ZW9ySW5zdGFsbFZpc2l0b3IiLCJ2aXNpdCIsInJlc2V0Iiwicm9vdCIsInZpc2l0Q2FsbEV4cHJlc3Npb24iLCJub2RlIiwiaGFzSWRXaXRoTmFtZSIsImNhbGxlZSIsIndhbGsiLCJleHByIiwidHlwZSIsInNsaWNlIiwic3RhcnQiLCJlbmQiLCJwcm9wZXJ0aWVzIiwicHJvcCIsImtleU5hbWUiLCJnZXRLZXlOYW1lIiwia2V5IiwidmFsdWUiLCJhcmd1bWVudHMiLCJ2aXNpdENoaWxkcmVuIiwibGFzdCIsImV4cHJlc3Npb25zIiwicHJvcGVydHkiLCJpc09iamVjdCIsImlzTm9kZUxpa2UiLCJjb2RlT2ZVbmRlcnNjb3JlIiwiY2hhckNvZGVBdCIsImFwcGx5IiwidmlzaXRXaXRob3V0UmVzZXQiLCJBcnJheSIsImlzQXJyYXkiLCJtZXRob2QiLCJjYWxsIiwia2V5cyIsImtleUNvdW50IiwiY2hpbGQiLCJjb2RlT2ZBIiwiY29kZU9mWiIsImlzQ2FwaXRhbGl6ZWQiLCJzdHJpbmciXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUFBQSxJQUFJQSxzQkFBSjtBQUEyQkMsT0FBT0MsS0FBUCxDQUFhQyxRQUFRLFlBQVIsQ0FBYixFQUFtQztBQUFDSCx5QkFB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LENBQWYsTUFBc0JELGdCQUYxQixFQUU0QztBQUMxQztBQUNEOztBQUVELFlBQU1VLFFBQVFoQyxLQUFLYSxHQUFMLENBQWQ7O0FBQ0EsVUFBSSxDQUFFTyxTQUFTWSxLQUFULENBQU4sRUFBdUI7QUFDckI7QUFDQTtBQUNEOztBQUVELFdBQUtQLGlCQUFMLENBQXVCTyxLQUF2QjtBQUNEO0FBQ0Y7O0FBOUMwQixDOzs7Ozs7Ozs7OztBQ1Q3Qjs7QUFBQXJILE9BQU8rRCxNQUFQLENBQWM7QUFBQzBDLFlBQVMsTUFBSUEsUUFBZDtBQUF1QkMsY0FBVyxNQUFJQTtBQUF0QyxDQUFkO0FBRUEsTUFBTVksVUFBVSxJQUFJVixVQUFKLENBQWUsQ0FBZixDQUFoQjtBQUNBLE1BQU1XLFVBQVUsSUFBSVgsVUFBSixDQUFlLENBQWYsQ0FBaEI7O0FBRU8sU0FBU0gsUUFBVCxDQUFrQk4sS0FBbEIsRUFBeUI7QUFDOUIsU0FBTyxPQUFPQSxLQUFQLEtBQWlCLFFBQWpCLElBQTZCQSxVQUFVLElBQTlDO0FBQ0Q7O0FBTU0sU0FBU08sVUFBVCxDQUFvQlAsS0FBcEIsRUFBMkI7QUFDaEMsU0FBT00sU0FBU04sS0FBVCxLQUNMLENBQUVZLE1BQU1DLE9BQU4sQ0FBY2IsS0FBZCxDQURHLElBRUxxQixjQUFjckIsTUFBTVQsSUFBcEIsQ0FGRjtBQUdEOztBQUVELFNBQVM4QixhQUFULENBQXVCQyxNQUF2QixFQUErQjtBQUM3QixNQUFJLE9BQU9BLE1BQVAsS0FBa0IsUUFBdEIsRUFBZ0M7QUFDOUIsV0FBTyxLQUFQO0FBQ0Q7O0FBQ0QsUUFBTWxFLE9BQU9rRSxPQUFPYixVQUFQLENBQWtCLENBQWxCLENBQWI7QUFDQSxTQUFPckQsUUFBUStELE9BQVIsSUFBbUIvRCxRQUFRZ0UsT0FBbEM7QUFDRCxDIiwiZmlsZSI6Ii9wYWNrYWdlcy9taW5pZnlTdGRKU19wbHVnaW4uanMiLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBleHRyYWN0TW9kdWxlU2l6ZXNUcmVlIH0gZnJvbSBcIi4vc3RhdHMuanNcIjtcblxuUGx1Z2luLnJlZ2lzdGVyTWluaWZpZXIoe1xuICBleHRlbnNpb25zOiBbJ2pzJ10sXG4gIGFyY2hNYXRjaGluZzogJ3dlYidcbn0sIGZ1bmN0aW9uICgpIHtcbiAgdmFyIG1pbmlmaWVyID0gbmV3IE1ldGVvckJhYmVsTWluaWZpZXIoKTtcbiAgcmV0dXJuIG1pbmlmaWVyO1xufSk7XG5cbmZ1bmN0aW9uIE1ldGVvckJhYmVsTWluaWZpZXIgKCkge307XG5cbk1ldGVvckJhYmVsTWluaWZpZXIucHJvdG90eXBlLnByb2Nlc3NGaWxlc0ZvckJ1bmRsZSA9IGZ1bmN0aW9uKGZpbGVzLCBvcHRpb25zKSB7XG4gIHZhciBtb2RlID0gb3B0aW9ucy5taW5pZnlNb2RlO1xuXG4gIC8vIGRvbid0IG1pbmlmeSBhbnl0aGluZyBmb3IgZGV2ZWxvcG1lbnRcbiAgaWYgKG1vZGUgPT09ICdkZXZlbG9wbWVudCcpIHtcbiAgICBmaWxlcy5mb3JFYWNoKGZ1bmN0aW9uIChmaWxlKSB7XG4gICAgICBmaWxlLmFkZEphdmFTY3JpcHQoe1xuICAgICAgICBkYXRhOiBmaWxlLmdldENvbnRlbnRzQXNCdWZmZXIoKSxcbiAgICAgICAgc291cmNlTWFwOiBmaWxlLmdldFNvdXJjZU1hcCgpLFxuICAgICAgICBwYXRoOiBmaWxlLmdldFBhdGhJbkJ1bmRsZSgpLFxuICAgICAgfSk7XG4gICAgfSk7XG4gICAgcmV0dXJuO1xuICB9XG5cbiAgZnVuY3Rpb24gbWF5YmVUaHJvd01pbmlmeUVycm9yQnlTb3VyY2VGaWxlKGVycm9yLCBmaWxlKSB7XG4gICAgdmFyIG1pbmlmaWVyRXJyb3JSZWdleCA9IC9eKC4qPylcXHM/XFwoKFxcZCspOihcXGQrKVxcKSQvO1xuICAgIHZhciBwYXJzZUVycm9yID0gbWluaWZpZXJFcnJvclJlZ2V4LmV4ZWMoZXJyb3IubWVzc2FnZSk7XG5cbiAgICBpZiAoIXBhcnNlRXJyb3IpIHtcbiAgICAgIC8vIElmIHdlIHdlcmUgdW5hYmxlIHRvIHBhcnNlIGl0LCBqdXN0IGxldCB0aGUgdXN1YWwgZXJyb3IgaGFuZGxpbmcgd29yay5cbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICB2YXIgbGluZUVycm9yTWVzc2FnZSA9IHBhcnNlRXJyb3JbMV07XG4gICAgdmFyIGxpbmVFcnJvckxpbmVOdW1iZXIgPSBwYXJzZUVycm9yWzJdO1xuXG4gICAgdmFyIHBhcnNlRXJyb3JDb250ZW50SW5kZXggPSBsaW5lRXJyb3JMaW5lTnVtYmVyIC0gMTtcblxuICAgIC8vIFVubGlrZWx5LCBzaW5jZSB3ZSBoYXZlIGEgbXVsdGktbGluZSBmaXhlZCBoZWFkZXIgaW4gdGhpcyBmaWxlLlxuICAgIGlmIChwYXJzZUVycm9yQ29udGVudEluZGV4IDwgMCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIC8qXG5cbiAgICBXaGF0IHdlJ3JlIHBhcnNpbmcgbG9va3MgbGlrZSB0aGlzOlxuXG4gICAgLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy9cbiAgICAvLyAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAvL1xuICAgIC8vIHBhdGgvdG8vZmlsZS5qcyAgICAgICAgICAgICAgICAgICAgIC8vXG4gICAgLy8gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgLy9cbiAgICAvLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vL1xuICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIC8vIDFcbiAgICAgICB2YXIgaWxsZWdhbEVDTUFTY3JpcHQgPSB0cnVlOyAgICAgICAvLyAyXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgLy8gM1xuICAgIC8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vXG5cbiAgICBCdHcsIHRoZSBhYm92ZSBjb2RlIGlzIGludGVudGlvbmFsbHkgbm90IG5ld2VyIEVDTUFTY3JpcHQgc29cbiAgICB3ZSBkb24ndCBicmVhayBvdXJzZWx2ZXMuXG5cbiAgICAqL1xuXG4gICAgdmFyIGNvbnRlbnRzID0gZmlsZS5nZXRDb250ZW50c0FzU3RyaW5nKCkuc3BsaXQoL1xcbi8pO1xuICAgIHZhciBsaW5lQ29udGVudCA9IGNvbnRlbnRzW3BhcnNlRXJyb3JDb250ZW50SW5kZXhdO1xuXG4gICAgLy8gVHJ5IHRvIGdyYWIgdGhlIGxpbmUgbnVtYmVyLCB3aGljaCBzb21ldGltZXMgZG9lc24ndCBleGlzdCBvblxuICAgIC8vIGxpbmUsIGFibm9ybWFsbHktbG9uZyBsaW5lcyBpbiBhIGxhcmdlciBibG9jay5cbiAgICB2YXIgbGluZVNyY0xpbmVQYXJ0cyA9IC9eKC4qPykoPzpcXHMqXFwvXFwvIChcXGQrKSk/JC8uZXhlYyhsaW5lQ29udGVudCk7XG5cbiAgICAvLyBUaGUgbGluZSBkaWRuJ3QgbWF0Y2ggYXQgYWxsPyAgTGV0J3MganVzdCBub3QgdHJ5LlxuICAgIGlmICghbGluZVNyY0xpbmVQYXJ0cykge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHZhciBsaW5lU3JjTGluZUNvbnRlbnQgPSBsaW5lU3JjTGluZVBhcnRzWzFdO1xuICAgIHZhciBsaW5lU3JjTGluZU51bWJlciA9IGxpbmVTcmNMaW5lUGFydHNbMl07XG5cbiAgICAvLyBDb3VudCBiYWNrd2FyZCBmcm9tIHRoZSBmYWlsZWQgbGluZSB0byBmaW5kIHRoZSBmaWxlbmFtZS5cbiAgICBmb3IgKHZhciBjID0gcGFyc2VFcnJvckNvbnRlbnRJbmRleCAtIDE7IGMgPj0gMDsgYy0tKSB7XG4gICAgICB2YXIgc291cmNlTGluZSA9IGNvbnRlbnRzW2NdO1xuXG4gICAgICAvLyBJZiB0aGUgbGluZSBpcyBhIGJvYXRsb2FkIG9mIHNsYXNoZXMsIHdlJ3JlIGluIHRoZSByaWdodCBwbGFjZS5cbiAgICAgIGlmICgvXlxcL1xcL1xcL3s2LH0kLy50ZXN0KHNvdXJjZUxpbmUpKSB7XG5cbiAgICAgICAgLy8gSWYgNCBsaW5lcyBiYWNrIGlzIHRoZSBzYW1lIGV4YWN0IGxpbmUsIHdlJ3ZlIGZvdW5kIHRoZSBmcmFtaW5nLlxuICAgICAgICBpZiAoY29udGVudHNbYyAtIDRdID09PSBzb3VyY2VMaW5lKSB7XG5cbiAgICAgICAgICAvLyBTbyBpbiB0aGF0IGNhc2UsIDIgbGluZXMgYmFjayBpcyB0aGUgZmlsZSBwYXRoLlxuICAgICAgICAgIHZhciBwYXJzZUVycm9yUGF0aCA9IGNvbnRlbnRzW2MgLSAyXVxuICAgICAgICAgICAgLnN1YnN0cmluZygzKVxuICAgICAgICAgICAgLnJlcGxhY2UoL1xccytcXC9cXC8vLCBcIlwiKTtcblxuICAgICAgICAgIHZhciBtaW5FcnJvciA9IG5ldyBFcnJvcihcbiAgICAgICAgICAgIFwiQmFiaWxpIG1pbmlmaWNhdGlvbiBlcnJvciBcIiArXG4gICAgICAgICAgICBcIndpdGhpbiBcIiArIGZpbGUuZ2V0UGF0aEluQnVuZGxlKCkgKyBcIjpcXG5cIiArXG4gICAgICAgICAgICBwYXJzZUVycm9yUGF0aCArXG4gICAgICAgICAgICAobGluZVNyY0xpbmVOdW1iZXIgPyBcIiwgbGluZSBcIiArIGxpbmVTcmNMaW5lTnVtYmVyIDogXCJcIikgKyBcIlxcblwiICtcbiAgICAgICAgICAgIFwiXFxuXCIgK1xuICAgICAgICAgICAgbGluZUVycm9yTWVzc2FnZSArIFwiOlxcblwiICtcbiAgICAgICAgICAgIFwiXFxuXCIgK1xuICAgICAgICAgICAgbGluZVNyY0xpbmVDb250ZW50ICsgXCJcXG5cIlxuICAgICAgICAgICk7XG5cbiAgICAgICAgICB0aHJvdyBtaW5FcnJvcjtcbiAgICAgICAgfVxuICAgICAgfVxuICAgIH1cbiAgfVxuXG4gIGNvbnN0IHRvQmVBZGRlZCA9IHtcbiAgICBkYXRhOiBcIlwiLFxuICAgIHN0YXRzOiBPYmplY3QuY3JlYXRlKG51bGwpXG4gIH07XG5cbiAgZmlsZXMuZm9yRWFjaChmaWxlID0+IHtcbiAgICAvLyBEb24ndCByZW1pbmlmeSAqLm1pbi5qcy5cbiAgICBpZiAoL1xcLm1pblxcLmpzJC8udGVzdChmaWxlLmdldFBhdGhJbkJ1bmRsZSgpKSkge1xuICAgICAgdG9CZUFkZGVkLmRhdGEgKz0gZmlsZS5nZXRDb250ZW50c0FzU3RyaW5nKCk7XG4gICAgfSBlbHNlIHtcbiAgICAgIHZhciBtaW5pZmllZDtcblxuICAgICAgdHJ5IHtcbiAgICAgICAgbWluaWZpZWQgPSBtZXRlb3JKc01pbmlmeShmaWxlLmdldENvbnRlbnRzQXNTdHJpbmcoKSk7XG5cbiAgICAgICAgaWYgKCEobWluaWZpZWQgJiYgdHlwZW9mIG1pbmlmaWVkLmNvZGUgPT09IFwic3RyaW5nXCIpKSB7XG4gICAgICAgICAgdGhyb3cgbmV3IEVycm9yKCk7XG4gICAgICAgIH1cblxuICAgICAgfSBjYXRjaCAoZXJyKSB7XG4gICAgICAgIHZhciBmaWxlUGF0aCA9IGZpbGUuZ2V0UGF0aEluQnVuZGxlKCk7XG5cbiAgICAgICAgbWF5YmVUaHJvd01pbmlmeUVycm9yQnlTb3VyY2VGaWxlKGVyciwgZmlsZSk7XG5cbiAgICAgICAgZXJyLm1lc3NhZ2UgKz0gXCIgd2hpbGUgbWluaWZ5aW5nIFwiICsgZmlsZVBhdGg7XG4gICAgICAgIHRocm93IGVycjtcbiAgICAgIH1cblxuICAgICAgY29uc3QgdHJlZSA9IGV4dHJhY3RNb2R1bGVTaXplc1RyZWUobWluaWZpZWQuY29kZSk7XG4gICAgICBpZiAodHJlZSkge1xuICAgICAgICB0b0JlQWRkZWQuc3RhdHNbZmlsZS5nZXRQYXRoSW5CdW5kbGUoKV0gPVxuICAgICAgICAgIFtCdWZmZXIuYnl0ZUxlbmd0aChtaW5pZmllZC5jb2RlKSwgdHJlZV07XG4gICAgICB9IGVsc2Uge1xuICAgICAgICB0b0JlQWRkZWQuc3RhdHNbZmlsZS5nZXRQYXRoSW5CdW5kbGUoKV0gPVxuICAgICAgICAgIEJ1ZmZlci5ieXRlTGVuZ3RoKG1pbmlmaWVkLmNvZGUpO1xuICAgICAgfVxuXG4gICAgICB0b0JlQWRkZWQuZGF0YSArPSBtaW5pZmllZC5jb2RlO1xuICAgIH1cblxuICAgIHRvQmVBZGRlZC5kYXRhICs9ICdcXG5cXG4nO1xuXG4gICAgUGx1Z2luLm51ZGdlKCk7XG4gIH0pO1xuXG4gIGlmIChmaWxlcy5sZW5ndGgpIHtcbiAgICBmaWxlc1swXS5hZGRKYXZhU2NyaXB0KHRvQmVBZGRlZCk7XG4gIH1cbn07XG4iLCJpbXBvcnQgVmlzaXRvciBmcm9tIFwiLi92aXNpdG9yLmpzXCI7XG5cbi8vIFRoaXMgUmVnRXhwIHdpbGwgYmUgdXNlZCB0byBzY2FuIHRoZSBzb3VyY2UgZm9yIGNhbGxzIHRvIG1ldGVvckluc3RhbGwsXG4vLyB0YWtpbmcgaW50byBjb25zaWRlcmF0aW9uIHRoYXQgdGhlIGZ1bmN0aW9uIG5hbWUgbWF5IGhhdmUgYmVlbiBtYW5nbGVkXG4vLyB0byBzb21ldGhpbmcgb3RoZXIgdGhhbiBcIm1ldGVvckluc3RhbGxcIiBieSB0aGUgbWluaWZpZXIuXG5jb25zdCBtZXRlb3JJbnN0YWxsUmVnRXhwID0gbmV3IFJlZ0V4cChbXG4gIC8vIElmIG1ldGVvckluc3RhbGwgaXMgY2FsbGVkIGJ5IGl0cyB1bm1pbmlmaWVkIG5hbWUsIHRoZW4gdGhhdCdzIHdoYXRcbiAgLy8gd2Ugc2hvdWxkIGJlIGxvb2tpbmcgZm9yIGluIHRoZSBBU1QuXG4gIC9cXGIobWV0ZW9ySW5zdGFsbClcXChcXHsvLFxuICAvLyBJZiB0aGUgbWV0ZW9ySW5zdGFsbCBmdW5jdGlvbiBuYW1lIGhhcyBiZWVuIG1pbmlmaWVkLCB3ZSBjYW4gZmlndXJlXG4gIC8vIG91dCBpdHMgbWFuZ2xlZCBuYW1lIGJ5IGV4YW1pbmluZyB0aGUgaW1wb3J0IGFzc2luZ21lbnQuXG4gIC9cXGIoXFx3Kyk9UGFja2FnZVxcLm1vZHVsZXNcXC5tZXRlb3JJbnN0YWxsXFxiLyxcbiAgL1xcYihcXHcrKT1QYWNrYWdlXFxbXCJtb2R1bGVzLXJ1bnRpbWVcIlxcXS5tZXRlb3JJbnN0YWxsXFxiLyxcbiAgLy8gU29tZXRpbWVzIHVnbGlmeS1lcyB3aWxsIGlubGluZSAoMCxQYWNrYWdlLm1vZHVsZXMubWV0ZW9ySW5zdGFsbCkgYXNcbiAgLy8gYSBjYWxsIGV4cHJlc3Npb24uXG4gIC9cXCgwLFBhY2thZ2VcXC5tb2R1bGVzXFwuKG1ldGVvckluc3RhbGwpXFwpXFwoLyxcbiAgL1xcKDAsUGFja2FnZVxcW1wibW9kdWxlcy1ydW50aW1lXCJcXF1cXC4obWV0ZW9ySW5zdGFsbClcXClcXCgvLFxuXS5tYXAoZXhwID0+IGV4cC5zb3VyY2UpLmpvaW4oXCJ8XCIpKTtcblxuZXhwb3J0IGZ1bmN0aW9uIGV4dHJhY3RNb2R1bGVTaXplc1RyZWUoc291cmNlKSB7XG4gIGNvbnN0IG1hdGNoID0gbWV0ZW9ySW5zdGFsbFJlZ0V4cC5leGVjKHNvdXJjZSk7XG4gIGlmIChtYXRjaCkge1xuICAgIGNvbnN0IGFzdCA9IEJhYmVsLnBhcnNlKHNvdXJjZSk7XG4gICAgbGV0IG1ldGVvckluc3RhbGxOYW1lID0gXCJtZXRlb3JJbnN0YWxsXCI7XG4gICAgbWF0Y2guc29tZSgobmFtZSwgaSkgPT4gKGkgPiAwICYmIChtZXRlb3JJbnN0YWxsTmFtZSA9IG5hbWUpKSk7XG4gICAgbWV0ZW9ySW5zdGFsbFZpc2l0b3IudmlzaXQoYXN0LCBtZXRlb3JJbnN0YWxsTmFtZSwgc291cmNlKTtcbiAgICByZXR1cm4gbWV0ZW9ySW5zdGFsbFZpc2l0b3IudHJlZTtcbiAgfVxufVxuXG5jb25zdCBtZXRlb3JJbnN0YWxsVmlzaXRvciA9IG5ldyAoY2xhc3MgZXh0ZW5kcyBWaXNpdG9yIHtcbiAgcmVzZXQocm9vdCwgbWV0ZW9ySW5zdGFsbE5hbWUsIHNvdXJjZSkge1xuICAgIHRoaXMubmFtZSA9IG1ldGVvckluc3RhbGxOYW1lO1xuICAgIHRoaXMuc291cmNlID0gc291cmNlO1xuICAgIHRoaXMudHJlZSA9IG51bGw7XG4gIH1cblxuICB2aXNpdENhbGxFeHByZXNzaW9uKG5vZGUpIHtcbiAgICBpZiAodGhpcy50cmVlICE9PSBudWxsKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgaWYgKGhhc0lkV2l0aE5hbWUobm9kZS5jYWxsZWUsIHRoaXMubmFtZSkpIHtcbiAgICAgIGNvbnN0IHNvdXJjZSA9IHRoaXMuc291cmNlO1xuXG4gICAgICBmdW5jdGlvbiB3YWxrKGV4cHIpIHtcbiAgICAgICAgaWYgKGV4cHIudHlwZSAhPT0gXCJPYmplY3RFeHByZXNzaW9uXCIpIHtcbiAgICAgICAgICByZXR1cm4gQnVmZmVyLmJ5dGVMZW5ndGgoc291cmNlLnNsaWNlKGV4cHIuc3RhcnQsIGV4cHIuZW5kKSk7XG4gICAgICAgIH1cblxuICAgICAgICBjb25zdCBjb250ZW50cyA9IE9iamVjdC5jcmVhdGUobnVsbCk7XG5cbiAgICAgICAgZXhwci5wcm9wZXJ0aWVzLmZvckVhY2gocHJvcCA9PiB7XG4gICAgICAgICAgY29uc3Qga2V5TmFtZSA9IGdldEtleU5hbWUocHJvcC5rZXkpO1xuICAgICAgICAgIGlmICh0eXBlb2Yga2V5TmFtZSA9PT0gXCJzdHJpbmdcIikge1xuICAgICAgICAgICAgY29udGVudHNba2V5TmFtZV0gPSB3YWxrKHByb3AudmFsdWUpO1xuICAgICAgICAgIH1cbiAgICAgICAgfSk7XG5cbiAgICAgICAgcmV0dXJuIGNvbnRlbnRzO1xuICAgICAgfVxuXG4gICAgICB0aGlzLnRyZWUgPSB3YWxrKG5vZGUuYXJndW1lbnRzWzBdKTtcblxuICAgIH0gZWxzZSB7XG4gICAgICB0aGlzLnZpc2l0Q2hpbGRyZW4obm9kZSk7XG4gICAgfVxuICB9XG59KTtcblxuZnVuY3Rpb24gaGFzSWRXaXRoTmFtZShub2RlLCBuYW1lKSB7XG4gIHN3aXRjaCAobm9kZSAmJiBub2RlLnR5cGUpIHtcbiAgY2FzZSBcIlNlcXVlbmNlRXhwcmVzc2lvblwiOlxuICAgIGNvbnN0IGxhc3QgPSBub2RlLmV4cHJlc3Npb25zW25vZGUuZXhwcmVzc2lvbnMubGVuZ3RoIC0gMV07XG4gICAgcmV0dXJuIGhhc0lkV2l0aE5hbWUobGFzdCwgbmFtZSk7XG4gIGNhc2UgXCJNZW1iZXJFeHByZXNzaW9uXCI6XG4gICAgcmV0dXJuIGhhc0lkV2l0aE5hbWUobm9kZS5wcm9wZXJ0eSwgbmFtZSk7XG4gIGNhc2UgXCJJZGVudGlmaWVyXCI6XG4gICAgcmV0dXJuIG5vZGUubmFtZSA9PT0gbmFtZTtcbiAgZGVmYXVsdDpcbiAgICByZXR1cm4gZmFsc2U7XG4gIH1cbn1cblxuZnVuY3Rpb24gZ2V0S2V5TmFtZShrZXkpIHtcbiAgaWYgKGtleS50eXBlID09PSBcIklkZW50aWZpZXJcIikge1xuICAgIHJldHVybiBrZXkubmFtZTtcbiAgfVxuXG4gIGlmIChrZXkudHlwZSA9PT0gXCJTdHJpbmdMaXRlcmFsXCIgfHxcbiAgICAgIGtleS50eXBlID09PSBcIkxpdGVyYWxcIikge1xuICAgIHJldHVybiBrZXkudmFsdWU7XG4gIH1cblxuICByZXR1cm4gbnVsbDtcbn0iLCJcInVzZSBzdHJpY3RcIjtcblxuaW1wb3J0IHtcbiAgaXNPYmplY3QsXG4gIGlzTm9kZUxpa2UsXG59IGZyb20gXCIuL3V0aWxzLmpzXCI7XG5cbmNvbnN0IGNvZGVPZlVuZGVyc2NvcmUgPSBcIl9cIi5jaGFyQ29kZUF0KDApO1xuXG5leHBvcnQgZGVmYXVsdCBjbGFzcyBWaXNpdG9yIHtcbiAgdmlzaXQocm9vdCkge1xuICAgIHRoaXMucmVzZXQuYXBwbHkodGhpcywgYXJndW1lbnRzKTtcbiAgICB0aGlzLnZpc2l0V2l0aG91dFJlc2V0KHJvb3QpO1xuICB9XG5cbiAgdmlzaXRXaXRob3V0UmVzZXQobm9kZSkge1xuICAgIGlmIChBcnJheS5pc0FycmF5KG5vZGUpKSB7XG4gICAgICBub2RlLmZvckVhY2godGhpcy52aXNpdFdpdGhvdXRSZXNldCwgdGhpcyk7XG4gICAgfSBlbHNlIGlmIChpc05vZGVMaWtlKG5vZGUpKSB7XG4gICAgICBjb25zdCBtZXRob2QgPSB0aGlzW1widmlzaXRcIiArIG5vZGUudHlwZV07XG4gICAgICBpZiAodHlwZW9mIG1ldGhvZCA9PT0gXCJmdW5jdGlvblwiKSB7XG4gICAgICAgIC8vIFRoZSBtZXRob2QgbXVzdCBjYWxsIHRoaXMudmlzaXRDaGlsZHJlbihub2RlKSB0byBjb250aW51ZVxuICAgICAgICAvLyB0cmF2ZXJzaW5nLlxuICAgICAgICBtZXRob2QuY2FsbCh0aGlzLCBub2RlKTtcbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIHRoaXMudmlzaXRDaGlsZHJlbihub2RlKTtcbiAgICAgIH1cbiAgICB9XG4gIH1cblxuICB2aXNpdENoaWxkcmVuKG5vZGUpIHtcbiAgICBpZiAoISBpc05vZGVMaWtlKG5vZGUpKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgY29uc3Qga2V5cyA9IE9iamVjdC5rZXlzKG5vZGUpO1xuICAgIGNvbnN0IGtleUNvdW50ID0ga2V5cy5sZW5ndGg7XG5cbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IGtleUNvdW50OyArK2kpIHtcbiAgICAgIGNvbnN0IGtleSA9IGtleXNbaV07XG5cbiAgICAgIGlmIChrZXkgPT09IFwibG9jXCIgfHwgLy8gSWdub3JlIC5sb2Mue3N0YXJ0LGVuZH0gb2JqZWN0cy5cbiAgICAgICAgICAvLyBJZ25vcmUgXCJwcml2YXRlXCIgcHJvcGVydGllcyBhZGRlZCBieSBCYWJlbC5cbiAgICAgICAgICBrZXkuY2hhckNvZGVBdCgwKSA9PT0gY29kZU9mVW5kZXJzY29yZSkge1xuICAgICAgICBjb250aW51ZTtcbiAgICAgIH1cblxuICAgICAgY29uc3QgY2hpbGQgPSBub2RlW2tleV07XG4gICAgICBpZiAoISBpc09iamVjdChjaGlsZCkpIHtcbiAgICAgICAgLy8gSWdub3JlIHByb3BlcnRpZXMgd2hvc2UgdmFsdWVzIGFyZW4ndCBvYmplY3RzLlxuICAgICAgICBjb250aW51ZTtcbiAgICAgIH1cblxuICAgICAgdGhpcy52aXNpdFdpdGhvdXRSZXNldChjaGlsZCk7XG4gICAgfVxuICB9XG59XG4iLCJcInVzZSBzdHJpY3RcIjtcblxuY29uc3QgY29kZU9mQSA9IFwiQVwiLmNoYXJDb2RlQXQoMCk7XG5jb25zdCBjb2RlT2ZaID0gXCJaXCIuY2hhckNvZGVBdCgwKTtcblxuZXhwb3J0IGZ1bmN0aW9uIGlzT2JqZWN0KHZhbHVlKSB7XG4gIHJldHVybiB0eXBlb2YgdmFsdWUgPT09IFwib2JqZWN0XCIgJiYgdmFsdWUgIT09IG51bGw7XG59XG5cbi8vIFdpdGhvdXQgYSBjb21wbGV0ZSBsaXN0IG9mIE5vZGUgLnR5cGUgbmFtZXMsIHdlIGhhdmUgdG8gc2V0dGxlIGZvciB0aGlzXG4vLyBmdXp6eSBtYXRjaGluZyBvZiBvYmplY3Qgc2hhcGVzLiBIb3dldmVyLCB0aGUgaW5mZWFzaWJpbGl0eSBvZlxuLy8gbWFpbnRhaW5pbmcgYSBjb21wbGV0ZSBsaXN0IG9mIHR5cGUgbmFtZXMgaXMgb25lIG9mIHRoZSByZWFzb25zIHdlJ3JlXG4vLyB1c2luZyB0aGUgRmFzdFBhdGgvVmlzaXRvciBhYnN0cmFjdGlvbiBpbiB0aGUgZmlyc3QgcGxhY2UuXG5leHBvcnQgZnVuY3Rpb24gaXNOb2RlTGlrZSh2YWx1ZSkge1xuICByZXR1cm4gaXNPYmplY3QodmFsdWUpICYmXG4gICAgISBBcnJheS5pc0FycmF5KHZhbHVlKSAmJlxuICAgIGlzQ2FwaXRhbGl6ZWQodmFsdWUudHlwZSk7XG59XG5cbmZ1bmN0aW9uIGlzQ2FwaXRhbGl6ZWQoc3RyaW5nKSB7XG4gIGlmICh0eXBlb2Ygc3RyaW5nICE9PSBcInN0cmluZ1wiKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG4gIGNvbnN0IGNvZGUgPSBzdHJpbmcuY2hhckNvZGVBdCgwKTtcbiAgcmV0dXJuIGNvZGUgPj0gY29kZU9mQSAmJiBjb2RlIDw9IGNvZGVPZlo7XG59XG4iXX0=
