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
/\b(\w+)=Package.modules.meteorInstall\b/, /\b(\w+)=Package\["modules-runtime"\].meteorInstall\b/].map(exp => exp.source).join("|"));

function extractModuleSizesTree(source) {
  const match = meteorInstallRegExp.exec(source);

  if (match) {
    const ast = Babel.parse(source);
    const name = match[1] || match[2] || match[3];
    meteorInstallVisitor.visit(ast, name, source);
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

    if (isIdWithName(node.callee, this.name)) {
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

function isIdWithName(node, name) {
  return node && node.type === "Identifier" && node.name === name;
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
//# sourceMappingURL=data:application/json;charset=utf8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZ5U3RkSlMvcGx1Z2luL21pbmlmeS1qcy5qcyIsIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZ5U3RkSlMvcGx1Z2luL3N0YXRzLmpzIiwibWV0ZW9yOi8v8J+Su2FwcC9wYWNrYWdlcy9taW5pZnlTdGRKUy9wbHVnaW4vdmlzaXRvci5qcyIsIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZ5U3RkSlMvcGx1Z2luL3V0aWxzLmpzIl0sIm5hbWVzIjpbImV4dHJhY3RNb2R1bGVTaXplc1RyZWUiLCJtb2R1bGUiLCJ3YXRjaCIsInJlcXVpcmUiLCJ2IiwiUGx1Z2luIiwicmVnaXN0ZXJNaW5pZmllciIsImV4dGVuc2lvbnMiLCJhcmNoTWF0Y2hpbmciLCJtaW5pZmllciIsIk1ldGVvckJhYmVsTWluaWZpZXIiLCJwcm90b3R5cGUiLCJwcm9jZXNzRmlsZXNGb3JCdW5kbGUiLCJmaWxlcyIsIm9wdGlvbnMiLCJtb2RlIiwibWluaWZ5TW9kZSIsImZvckVhY2giLCJmaWxlIiwiYWRkSmF2YVNjcmlwdCIsImRhdGEiLCJnZXRDb250ZW50c0FzQnVmZmVyIiwic291cmNlTWFwIiwiZ2V0U291cmNlTWFwIiwicGF0aCIsImdldFBhdGhJbkJ1bmRsZSIsIm1heWJlVGhyb3dNaW5pZnlFcnJvckJ5U291cmNlRmlsZSIsImVycm9yIiwibWluaWZpZXJFcnJvclJlZ2V4IiwicGFyc2VFcnJvciIsImV4ZWMiLCJtZXNzYWdlIiwibGluZUVycm9yTWVzc2FnZSIsImxpbmVFcnJvckxpbmVOdW1iZXIiLCJwYXJzZUVycm9yQ29udGVudEluZGV4IiwiY29udGVudHMiLCJnZXRDb250ZW50c0FzU3RyaW5nIiwic3BsaXQiLCJsaW5lQ29udGVudCIsImxpbmVTcmNMaW5lUGFydHMiLCJsaW5lU3JjTGluZUNvbnRlbnQiLCJsaW5lU3JjTGluZU51bWJlciIsImMiLCJzb3VyY2VMaW5lIiwidGVzdCIsInBhcnNlRXJyb3JQYXRoIiwic3Vic3RyaW5nIiwicmVwbGFjZSIsIm1pbkVycm9yIiwiRXJyb3IiLCJ0b0JlQWRkZWQiLCJzdGF0cyIsIk9iamVjdCIsImNyZWF0ZSIsIm1pbmlmaWVkIiwibWV0ZW9ySnNNaW5pZnkiLCJjb2RlIiwiZXJyIiwiZmlsZVBhdGgiLCJ0cmVlIiwiQnVmZmVyIiwiYnl0ZUxlbmd0aCIsIm51ZGdlIiwibGVuZ3RoIiwiZXhwb3J0IiwiVmlzaXRvciIsImRlZmF1bHQiLCJtZXRlb3JJbnN0YWxsUmVnRXhwIiwiUmVnRXhwIiwibWFwIiwiZXhwIiwic291cmNlIiwiam9pbiIsIm1hdGNoIiwiYXN0IiwiQmFiZWwiLCJwYXJzZSIsIm5hbWUiLCJtZXRlb3JJbnN0YWxsVmlzaXRvciIsInZpc2l0IiwicmVzZXQiLCJyb290IiwibWV0ZW9ySW5zdGFsbE5hbWUiLCJ2aXNpdENhbGxFeHByZXNzaW9uIiwibm9kZSIsImlzSWRXaXRoTmFtZSIsImNhbGxlZSIsIndhbGsiLCJleHByIiwidHlwZSIsInNsaWNlIiwic3RhcnQiLCJlbmQiLCJwcm9wZXJ0aWVzIiwicHJvcCIsImtleU5hbWUiLCJnZXRLZXlOYW1lIiwia2V5IiwidmFsdWUiLCJhcmd1bWVudHMiLCJ2aXNpdENoaWxkcmVuIiwiaXNPYmplY3QiLCJpc05vZGVMaWtlIiwiY29kZU9mVW5kZXJzY29yZSIsImNoYXJDb2RlQXQiLCJhcHBseSIsInZpc2l0V2l0aG91dFJlc2V0IiwiQXJyYXkiLCJpc0FycmF5IiwibWV0aG9kIiwiY2FsbCIsImtleXMiLCJrZXlDb3VudCIsImkiLCJjaGlsZCIsImNvZGVPZkEiLCJjb2RlT2ZaIiwiaXNDYXBpdGFsaXplZCIsInN0cmluZyJdLCJtYXBwaW5ncyI6Ijs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUFBLElBQUlBLHNCQUFKO0FBQTJCQyxPQUFPQyxLQUFQLENBQWFDLFFBQVEsWUFBUixDQUFiLEVBQW1DO0FBQUNILHlCQUF1QkksQ0FBdkIsRUFBeUI7QUFBQ0osNkJBQXVCSSxDQUF2QjtBQUF5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SCxRQUFULENBQWtCSCxLQUFsQixFQUF5QjtBQUM5QixTQUFPLE9BQU9BLEtBQVAsS0FBaUIsUUFBakIsSUFBNkJBLFVBQVUsSUFBOUM7QUFDRDs7QUFNTSxTQUFTSSxVQUFULENBQW9CSixLQUFwQixFQUEyQjtBQUNoQyxTQUFPRyxTQUFTSCxLQUFULEtBQ0wsQ0FBRVMsTUFBTUMsT0FBTixDQUFjVixLQUFkLENBREcsSUFFTG1CLGNBQWNuQixNQUFNVCxJQUFwQixDQUZGO0FBR0Q7O0FBRUQsU0FBUzRCLGFBQVQsQ0FBdUJDLE1BQXZCLEVBQStCO0FBQzdCLE1BQUksT0FBT0EsTUFBUCxLQUFrQixRQUF0QixFQUFnQztBQUM5QixXQUFPLEtBQVA7QUFDRDs7QUFDRCxRQUFNOUQsT0FBTzhELE9BQU9kLFVBQVAsQ0FBa0IsQ0FBbEIsQ0FBYjtBQUNBLFNBQU9oRCxRQUFRMkQsT0FBUixJQUFtQjNELFFBQVE0RCxPQUFsQztBQUNELEMiLCJmaWxlIjoiL3BhY2thZ2VzL21pbmlmeVN0ZEpTX3BsdWdpbi5qcyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7IGV4dHJhY3RNb2R1bGVTaXplc1RyZWUgfSBmcm9tIFwiLi9zdGF0cy5qc1wiO1xuXG5QbHVnaW4ucmVnaXN0ZXJNaW5pZmllcih7XG4gIGV4dGVuc2lvbnM6IFsnanMnXSxcbiAgYXJjaE1hdGNoaW5nOiAnd2ViJ1xufSwgZnVuY3Rpb24gKCkge1xuICB2YXIgbWluaWZpZXIgPSBuZXcgTWV0ZW9yQmFiZWxNaW5pZmllcigpO1xuICByZXR1cm4gbWluaWZpZXI7XG59KTtcblxuZnVuY3Rpb24gTWV0ZW9yQmFiZWxNaW5pZmllciAoKSB7fTtcblxuTWV0ZW9yQmFiZWxNaW5pZmllci5wcm90b3R5cGUucHJvY2Vzc0ZpbGVzRm9yQnVuZGxlID0gZnVuY3Rpb24oZmlsZXMsIG9wdGlvbnMpIHtcbiAgdmFyIG1vZGUgPSBvcHRpb25zLm1pbmlmeU1vZGU7XG5cbiAgLy8gZG9uJ3QgbWluaWZ5IGFueXRoaW5nIGZvciBkZXZlbG9wbWVudFxuICBpZiAobW9kZSA9PT0gJ2RldmVsb3BtZW50Jykge1xuICAgIGZpbGVzLmZvckVhY2goZnVuY3Rpb24gKGZpbGUpIHtcbiAgICAgIGZpbGUuYWRkSmF2YVNjcmlwdCh7XG4gICAgICAgIGRhdGE6IGZpbGUuZ2V0Q29udGVudHNBc0J1ZmZlcigpLFxuICAgICAgICBzb3VyY2VNYXA6IGZpbGUuZ2V0U291cmNlTWFwKCksXG4gICAgICAgIHBhdGg6IGZpbGUuZ2V0UGF0aEluQnVuZGxlKCksXG4gICAgICB9KTtcbiAgICB9KTtcbiAgICByZXR1cm47XG4gIH1cblxuICBmdW5jdGlvbiBtYXliZVRocm93TWluaWZ5RXJyb3JCeVNvdXJjZUZpbGUoZXJyb3IsIGZpbGUpIHtcbiAgICB2YXIgbWluaWZpZXJFcnJvclJlZ2V4ID0gL14oLio/KVxccz9cXCgoXFxkKyk6KFxcZCspXFwpJC87XG4gICAgdmFyIHBhcnNlRXJyb3IgPSBtaW5pZmllckVycm9yUmVnZXguZXhlYyhlcnJvci5tZXNzYWdlKTtcblxuICAgIGlmICghcGFyc2VFcnJvcikge1xuICAgICAgLy8gSWYgd2Ugd2VyZSB1bmFibGUgdG8gcGFyc2UgaXQsIGp1c3QgbGV0IHRoZSB1c3VhbCBlcnJvciBoYW5kbGluZyB3b3JrLlxuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHZhciBsaW5lRXJyb3JNZXNzYWdlID0gcGFyc2VFcnJvclsxXTtcbiAgICB2YXIgbGluZUVycm9yTGluZU51bWJlciA9IHBhcnNlRXJyb3JbMl07XG5cbiAgICB2YXIgcGFyc2VFcnJvckNvbnRlbnRJbmRleCA9IGxpbmVFcnJvckxpbmVOdW1iZXIgLSAxO1xuXG4gICAgLy8gVW5saWtlbHksIHNpbmNlIHdlIGhhdmUgYSBtdWx0aS1saW5lIGZpeGVkIGhlYWRlciBpbiB0aGlzIGZpbGUuXG4gICAgaWYgKHBhcnNlRXJyb3JDb250ZW50SW5kZXggPCAwKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgLypcblxuICAgIFdoYXQgd2UncmUgcGFyc2luZyBsb29rcyBsaWtlIHRoaXM6XG5cbiAgICAvLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vL1xuICAgIC8vICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIC8vXG4gICAgLy8gcGF0aC90by9maWxlLmpzICAgICAgICAgICAgICAgICAgICAgLy9cbiAgICAvLyAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAvL1xuICAgIC8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgLy8gMVxuICAgICAgIHZhciBpbGxlZ2FsRUNNQVNjcmlwdCA9IHRydWU7ICAgICAgIC8vIDJcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAvLyAzXG4gICAgLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy8vLy9cblxuICAgIEJ0dywgdGhlIGFib3ZlIGNvZGUgaXMgaW50ZW50aW9uYWxseSBub3QgbmV3ZXIgRUNNQVNjcmlwdCBzb1xuICAgIHdlIGRvbid0IGJyZWFrIG91cnNlbHZlcy5cblxuICAgICovXG5cbiAgICB2YXIgY29udGVudHMgPSBmaWxlLmdldENvbnRlbnRzQXNTdHJpbmcoKS5zcGxpdCgvXFxuLyk7XG4gICAgdmFyIGxpbmVDb250ZW50ID0gY29udGVudHNbcGFyc2VFcnJvckNvbnRlbnRJbmRleF07XG5cbiAgICAvLyBUcnkgdG8gZ3JhYiB0aGUgbGluZSBudW1iZXIsIHdoaWNoIHNvbWV0aW1lcyBkb2Vzbid0IGV4aXN0IG9uXG4gICAgLy8gbGluZSwgYWJub3JtYWxseS1sb25nIGxpbmVzIGluIGEgbGFyZ2VyIGJsb2NrLlxuICAgIHZhciBsaW5lU3JjTGluZVBhcnRzID0gL14oLio/KSg/OlxccypcXC9cXC8gKFxcZCspKT8kLy5leGVjKGxpbmVDb250ZW50KTtcblxuICAgIC8vIFRoZSBsaW5lIGRpZG4ndCBtYXRjaCBhdCBhbGw/ICBMZXQncyBqdXN0IG5vdCB0cnkuXG4gICAgaWYgKCFsaW5lU3JjTGluZVBhcnRzKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgdmFyIGxpbmVTcmNMaW5lQ29udGVudCA9IGxpbmVTcmNMaW5lUGFydHNbMV07XG4gICAgdmFyIGxpbmVTcmNMaW5lTnVtYmVyID0gbGluZVNyY0xpbmVQYXJ0c1syXTtcblxuICAgIC8vIENvdW50IGJhY2t3YXJkIGZyb20gdGhlIGZhaWxlZCBsaW5lIHRvIGZpbmQgdGhlIGZpbGVuYW1lLlxuICAgIGZvciAodmFyIGMgPSBwYXJzZUVycm9yQ29udGVudEluZGV4IC0gMTsgYyA+PSAwOyBjLS0pIHtcbiAgICAgIHZhciBzb3VyY2VMaW5lID0gY29udGVudHNbY107XG5cbiAgICAgIC8vIElmIHRoZSBsaW5lIGlzIGEgYm9hdGxvYWQgb2Ygc2xhc2hlcywgd2UncmUgaW4gdGhlIHJpZ2h0IHBsYWNlLlxuICAgICAgaWYgKC9eXFwvXFwvXFwvezYsfSQvLnRlc3Qoc291cmNlTGluZSkpIHtcblxuICAgICAgICAvLyBJZiA0IGxpbmVzIGJhY2sgaXMgdGhlIHNhbWUgZXhhY3QgbGluZSwgd2UndmUgZm91bmQgdGhlIGZyYW1pbmcuXG4gICAgICAgIGlmIChjb250ZW50c1tjIC0gNF0gPT09IHNvdXJjZUxpbmUpIHtcblxuICAgICAgICAgIC8vIFNvIGluIHRoYXQgY2FzZSwgMiBsaW5lcyBiYWNrIGlzIHRoZSBmaWxlIHBhdGguXG4gICAgICAgICAgdmFyIHBhcnNlRXJyb3JQYXRoID0gY29udGVudHNbYyAtIDJdXG4gICAgICAgICAgICAuc3Vic3RyaW5nKDMpXG4gICAgICAgICAgICAucmVwbGFjZSgvXFxzK1xcL1xcLy8sIFwiXCIpO1xuXG4gICAgICAgICAgdmFyIG1pbkVycm9yID0gbmV3IEVycm9yKFxuICAgICAgICAgICAgXCJCYWJpbGkgbWluaWZpY2F0aW9uIGVycm9yIFwiICtcbiAgICAgICAgICAgIFwid2l0aGluIFwiICsgZmlsZS5nZXRQYXRoSW5CdW5kbGUoKSArIFwiOlxcblwiICtcbiAgICAgICAgICAgIHBhcnNlRXJyb3JQYXRoICtcbiAgICAgICAgICAgIChsaW5lU3JjTGluZU51bWJlciA/IFwiLCBsaW5lIFwiICsgbGluZVNyY0xpbmVOdW1iZXIgOiBcIlwiKSArIFwiXFxuXCIgK1xuICAgICAgICAgICAgXCJcXG5cIiArXG4gICAgICAgICAgICBsaW5lRXJyb3JNZXNzYWdlICsgXCI6XFxuXCIgK1xuICAgICAgICAgICAgXCJcXG5cIiArXG4gICAgICAgICAgICBsaW5lU3JjTGluZUNvbnRlbnQgKyBcIlxcblwiXG4gICAgICAgICAgKTtcblxuICAgICAgICAgIHRocm93IG1pbkVycm9yO1xuICAgICAgICB9XG4gICAgICB9XG4gICAgfVxuICB9XG5cbiAgY29uc3QgdG9CZUFkZGVkID0ge1xuICAgIGRhdGE6IFwiXCIsXG4gICAgc3RhdHM6IE9iamVjdC5jcmVhdGUobnVsbClcbiAgfTtcblxuICBmaWxlcy5mb3JFYWNoKGZpbGUgPT4ge1xuICAgIC8vIERvbid0IHJlbWluaWZ5ICoubWluLmpzLlxuICAgIGlmICgvXFwubWluXFwuanMkLy50ZXN0KGZpbGUuZ2V0UGF0aEluQnVuZGxlKCkpKSB7XG4gICAgICB0b0JlQWRkZWQuZGF0YSArPSBmaWxlLmdldENvbnRlbnRzQXNTdHJpbmcoKTtcbiAgICB9IGVsc2Uge1xuICAgICAgdmFyIG1pbmlmaWVkO1xuXG4gICAgICB0cnkge1xuICAgICAgICBtaW5pZmllZCA9IG1ldGVvckpzTWluaWZ5KGZpbGUuZ2V0Q29udGVudHNBc1N0cmluZygpKTtcblxuICAgICAgICBpZiAoIShtaW5pZmllZCAmJiB0eXBlb2YgbWluaWZpZWQuY29kZSA9PT0gXCJzdHJpbmdcIikpIHtcbiAgICAgICAgICB0aHJvdyBuZXcgRXJyb3IoKTtcbiAgICAgICAgfVxuXG4gICAgICB9IGNhdGNoIChlcnIpIHtcbiAgICAgICAgdmFyIGZpbGVQYXRoID0gZmlsZS5nZXRQYXRoSW5CdW5kbGUoKTtcblxuICAgICAgICBtYXliZVRocm93TWluaWZ5RXJyb3JCeVNvdXJjZUZpbGUoZXJyLCBmaWxlKTtcblxuICAgICAgICBlcnIubWVzc2FnZSArPSBcIiB3aGlsZSBtaW5pZnlpbmcgXCIgKyBmaWxlUGF0aDtcbiAgICAgICAgdGhyb3cgZXJyO1xuICAgICAgfVxuXG4gICAgICBjb25zdCB0cmVlID0gZXh0cmFjdE1vZHVsZVNpemVzVHJlZShtaW5pZmllZC5jb2RlKTtcbiAgICAgIGlmICh0cmVlKSB7XG4gICAgICAgIHRvQmVBZGRlZC5zdGF0c1tmaWxlLmdldFBhdGhJbkJ1bmRsZSgpXSA9XG4gICAgICAgICAgW0J1ZmZlci5ieXRlTGVuZ3RoKG1pbmlmaWVkLmNvZGUpLCB0cmVlXTtcbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIHRvQmVBZGRlZC5zdGF0c1tmaWxlLmdldFBhdGhJbkJ1bmRsZSgpXSA9XG4gICAgICAgICAgQnVmZmVyLmJ5dGVMZW5ndGgobWluaWZpZWQuY29kZSk7XG4gICAgICB9XG5cbiAgICAgIHRvQmVBZGRlZC5kYXRhICs9IG1pbmlmaWVkLmNvZGU7XG4gICAgfVxuXG4gICAgdG9CZUFkZGVkLmRhdGEgKz0gJ1xcblxcbic7XG5cbiAgICBQbHVnaW4ubnVkZ2UoKTtcbiAgfSk7XG5cbiAgaWYgKGZpbGVzLmxlbmd0aCkge1xuICAgIGZpbGVzWzBdLmFkZEphdmFTY3JpcHQodG9CZUFkZGVkKTtcbiAgfVxufTtcbiIsImltcG9ydCBWaXNpdG9yIGZyb20gXCIuL3Zpc2l0b3IuanNcIjtcblxuLy8gVGhpcyBSZWdFeHAgd2lsbCBiZSB1c2VkIHRvIHNjYW4gdGhlIHNvdXJjZSBmb3IgY2FsbHMgdG8gbWV0ZW9ySW5zdGFsbCxcbi8vIHRha2luZyBpbnRvIGNvbnNpZGVyYXRpb24gdGhhdCB0aGUgZnVuY3Rpb24gbmFtZSBtYXkgaGF2ZSBiZWVuIG1hbmdsZWRcbi8vIHRvIHNvbWV0aGluZyBvdGhlciB0aGFuIFwibWV0ZW9ySW5zdGFsbFwiIGJ5IHRoZSBtaW5pZmllci5cbmNvbnN0IG1ldGVvckluc3RhbGxSZWdFeHAgPSBuZXcgUmVnRXhwKFtcbiAgLy8gSWYgbWV0ZW9ySW5zdGFsbCBpcyBjYWxsZWQgYnkgaXRzIHVubWluaWZpZWQgbmFtZSwgdGhlbiB0aGF0J3Mgd2hhdFxuICAvLyB3ZSBzaG91bGQgYmUgbG9va2luZyBmb3IgaW4gdGhlIEFTVC5cbiAgL1xcYihtZXRlb3JJbnN0YWxsKVxcKFxcey8sXG4gIC8vIElmIHRoZSBtZXRlb3JJbnN0YWxsIGZ1bmN0aW9uIG5hbWUgaGFzIGJlZW4gbWluaWZpZWQsIHdlIGNhbiBmaWd1cmVcbiAgLy8gb3V0IGl0cyBtYW5nbGVkIG5hbWUgYnkgZXhhbWluaW5nIHRoZSBpbXBvcnQgYXNzaW5nbWVudC5cbiAgL1xcYihcXHcrKT1QYWNrYWdlLm1vZHVsZXMubWV0ZW9ySW5zdGFsbFxcYi8sXG4gIC9cXGIoXFx3Kyk9UGFja2FnZVxcW1wibW9kdWxlcy1ydW50aW1lXCJcXF0ubWV0ZW9ySW5zdGFsbFxcYi8sXG5dLm1hcChleHAgPT4gZXhwLnNvdXJjZSkuam9pbihcInxcIikpO1xuXG5leHBvcnQgZnVuY3Rpb24gZXh0cmFjdE1vZHVsZVNpemVzVHJlZShzb3VyY2UpIHtcbiAgY29uc3QgbWF0Y2ggPSBtZXRlb3JJbnN0YWxsUmVnRXhwLmV4ZWMoc291cmNlKTtcbiAgaWYgKG1hdGNoKSB7XG4gICAgY29uc3QgYXN0ID0gQmFiZWwucGFyc2Uoc291cmNlKTtcbiAgICBjb25zdCBuYW1lID0gbWF0Y2hbMV0gfHwgbWF0Y2hbMl0gfHwgbWF0Y2hbM107XG4gICAgbWV0ZW9ySW5zdGFsbFZpc2l0b3IudmlzaXQoYXN0LCBuYW1lLCBzb3VyY2UpO1xuICAgIHJldHVybiBtZXRlb3JJbnN0YWxsVmlzaXRvci50cmVlO1xuICB9XG59XG5cbmNvbnN0IG1ldGVvckluc3RhbGxWaXNpdG9yID0gbmV3IChjbGFzcyBleHRlbmRzIFZpc2l0b3Ige1xuICByZXNldChyb290LCBtZXRlb3JJbnN0YWxsTmFtZSwgc291cmNlKSB7XG4gICAgdGhpcy5uYW1lID0gbWV0ZW9ySW5zdGFsbE5hbWU7XG4gICAgdGhpcy5zb3VyY2UgPSBzb3VyY2U7XG4gICAgdGhpcy50cmVlID0gbnVsbDtcbiAgfVxuXG4gIHZpc2l0Q2FsbEV4cHJlc3Npb24obm9kZSkge1xuICAgIGlmICh0aGlzLnRyZWUgIT09IG51bGwpIHtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICBpZiAoaXNJZFdpdGhOYW1lKG5vZGUuY2FsbGVlLCB0aGlzLm5hbWUpKSB7XG4gICAgICBjb25zdCBzb3VyY2UgPSB0aGlzLnNvdXJjZTtcblxuICAgICAgZnVuY3Rpb24gd2FsayhleHByKSB7XG4gICAgICAgIGlmIChleHByLnR5cGUgIT09IFwiT2JqZWN0RXhwcmVzc2lvblwiKSB7XG4gICAgICAgICAgcmV0dXJuIEJ1ZmZlci5ieXRlTGVuZ3RoKHNvdXJjZS5zbGljZShleHByLnN0YXJ0LCBleHByLmVuZCkpO1xuICAgICAgICB9XG5cbiAgICAgICAgY29uc3QgY29udGVudHMgPSBPYmplY3QuY3JlYXRlKG51bGwpO1xuXG4gICAgICAgIGV4cHIucHJvcGVydGllcy5mb3JFYWNoKHByb3AgPT4ge1xuICAgICAgICAgIGNvbnN0IGtleU5hbWUgPSBnZXRLZXlOYW1lKHByb3Aua2V5KTtcbiAgICAgICAgICBpZiAodHlwZW9mIGtleU5hbWUgPT09IFwic3RyaW5nXCIpIHtcbiAgICAgICAgICAgIGNvbnRlbnRzW2tleU5hbWVdID0gd2Fsayhwcm9wLnZhbHVlKTtcbiAgICAgICAgICB9XG4gICAgICAgIH0pO1xuXG4gICAgICAgIHJldHVybiBjb250ZW50cztcbiAgICAgIH1cblxuICAgICAgdGhpcy50cmVlID0gd2Fsayhub2RlLmFyZ3VtZW50c1swXSk7XG5cbiAgICB9IGVsc2Uge1xuICAgICAgdGhpcy52aXNpdENoaWxkcmVuKG5vZGUpO1xuICAgIH1cbiAgfVxufSk7XG5cbmZ1bmN0aW9uIGlzSWRXaXRoTmFtZShub2RlLCBuYW1lKSB7XG4gIHJldHVybiBub2RlICYmXG4gICAgbm9kZS50eXBlID09PSBcIklkZW50aWZpZXJcIiAmJlxuICAgIG5vZGUubmFtZSA9PT0gbmFtZTtcbn1cblxuZnVuY3Rpb24gZ2V0S2V5TmFtZShrZXkpIHtcbiAgaWYgKGtleS50eXBlID09PSBcIklkZW50aWZpZXJcIikge1xuICAgIHJldHVybiBrZXkubmFtZTtcbiAgfVxuXG4gIGlmIChrZXkudHlwZSA9PT0gXCJTdHJpbmdMaXRlcmFsXCIgfHxcbiAgICAgIGtleS50eXBlID09PSBcIkxpdGVyYWxcIikge1xuICAgIHJldHVybiBrZXkudmFsdWU7XG4gIH1cblxuICByZXR1cm4gbnVsbDtcbn0iLCJcInVzZSBzdHJpY3RcIjtcblxuaW1wb3J0IHtcbiAgaXNPYmplY3QsXG4gIGlzTm9kZUxpa2UsXG59IGZyb20gXCIuL3V0aWxzLmpzXCI7XG5cbmNvbnN0IGNvZGVPZlVuZGVyc2NvcmUgPSBcIl9cIi5jaGFyQ29kZUF0KDApO1xuXG5leHBvcnQgZGVmYXVsdCBjbGFzcyBWaXNpdG9yIHtcbiAgdmlzaXQocm9vdCkge1xuICAgIHRoaXMucmVzZXQuYXBwbHkodGhpcywgYXJndW1lbnRzKTtcbiAgICB0aGlzLnZpc2l0V2l0aG91dFJlc2V0KHJvb3QpO1xuICB9XG5cbiAgdmlzaXRXaXRob3V0UmVzZXQobm9kZSkge1xuICAgIGlmIChBcnJheS5pc0FycmF5KG5vZGUpKSB7XG4gICAgICBub2RlLmZvckVhY2godGhpcy52aXNpdFdpdGhvdXRSZXNldCwgdGhpcyk7XG4gICAgfSBlbHNlIGlmIChpc05vZGVMaWtlKG5vZGUpKSB7XG4gICAgICBjb25zdCBtZXRob2QgPSB0aGlzW1widmlzaXRcIiArIG5vZGUudHlwZV07XG4gICAgICBpZiAodHlwZW9mIG1ldGhvZCA9PT0gXCJmdW5jdGlvblwiKSB7XG4gICAgICAgIC8vIFRoZSBtZXRob2QgbXVzdCBjYWxsIHRoaXMudmlzaXRDaGlsZHJlbihub2RlKSB0byBjb250aW51ZVxuICAgICAgICAvLyB0cmF2ZXJzaW5nLlxuICAgICAgICBtZXRob2QuY2FsbCh0aGlzLCBub2RlKTtcbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIHRoaXMudmlzaXRDaGlsZHJlbihub2RlKTtcbiAgICAgIH1cbiAgICB9XG4gIH1cblxuICB2aXNpdENoaWxkcmVuKG5vZGUpIHtcbiAgICBpZiAoISBpc05vZGVMaWtlKG5vZGUpKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgY29uc3Qga2V5cyA9IE9iamVjdC5rZXlzKG5vZGUpO1xuICAgIGNvbnN0IGtleUNvdW50ID0ga2V5cy5sZW5ndGg7XG5cbiAgICBmb3IgKGxldCBpID0gMDsgaSA8IGtleUNvdW50OyArK2kpIHtcbiAgICAgIGNvbnN0IGtleSA9IGtleXNbaV07XG5cbiAgICAgIGlmIChrZXkgPT09IFwibG9jXCIgfHwgLy8gSWdub3JlIC5sb2Mue3N0YXJ0LGVuZH0gb2JqZWN0cy5cbiAgICAgICAgICAvLyBJZ25vcmUgXCJwcml2YXRlXCIgcHJvcGVydGllcyBhZGRlZCBieSBCYWJlbC5cbiAgICAgICAgICBrZXkuY2hhckNvZGVBdCgwKSA9PT0gY29kZU9mVW5kZXJzY29yZSkge1xuICAgICAgICBjb250aW51ZTtcbiAgICAgIH1cblxuICAgICAgY29uc3QgY2hpbGQgPSBub2RlW2tleV07XG4gICAgICBpZiAoISBpc09iamVjdChjaGlsZCkpIHtcbiAgICAgICAgLy8gSWdub3JlIHByb3BlcnRpZXMgd2hvc2UgdmFsdWVzIGFyZW4ndCBvYmplY3RzLlxuICAgICAgICBjb250aW51ZTtcbiAgICAgIH1cblxuICAgICAgdGhpcy52aXNpdFdpdGhvdXRSZXNldChjaGlsZCk7XG4gICAgfVxuICB9XG59XG4iLCJcInVzZSBzdHJpY3RcIjtcblxuY29uc3QgY29kZU9mQSA9IFwiQVwiLmNoYXJDb2RlQXQoMCk7XG5jb25zdCBjb2RlT2ZaID0gXCJaXCIuY2hhckNvZGVBdCgwKTtcblxuZXhwb3J0IGZ1bmN0aW9uIGlzT2JqZWN0KHZhbHVlKSB7XG4gIHJldHVybiB0eXBlb2YgdmFsdWUgPT09IFwib2JqZWN0XCIgJiYgdmFsdWUgIT09IG51bGw7XG59XG5cbi8vIFdpdGhvdXQgYSBjb21wbGV0ZSBsaXN0IG9mIE5vZGUgLnR5cGUgbmFtZXMsIHdlIGhhdmUgdG8gc2V0dGxlIGZvciB0aGlzXG4vLyBmdXp6eSBtYXRjaGluZyBvZiBvYmplY3Qgc2hhcGVzLiBIb3dldmVyLCB0aGUgaW5mZWFzaWJpbGl0eSBvZlxuLy8gbWFpbnRhaW5pbmcgYSBjb21wbGV0ZSBsaXN0IG9mIHR5cGUgbmFtZXMgaXMgb25lIG9mIHRoZSByZWFzb25zIHdlJ3JlXG4vLyB1c2luZyB0aGUgRmFzdFBhdGgvVmlzaXRvciBhYnN0cmFjdGlvbiBpbiB0aGUgZmlyc3QgcGxhY2UuXG5leHBvcnQgZnVuY3Rpb24gaXNOb2RlTGlrZSh2YWx1ZSkge1xuICByZXR1cm4gaXNPYmplY3QodmFsdWUpICYmXG4gICAgISBBcnJheS5pc0FycmF5KHZhbHVlKSAmJlxuICAgIGlzQ2FwaXRhbGl6ZWQodmFsdWUudHlwZSk7XG59XG5cbmZ1bmN0aW9uIGlzQ2FwaXRhbGl6ZWQoc3RyaW5nKSB7XG4gIGlmICh0eXBlb2Ygc3RyaW5nICE9PSBcInN0cmluZ1wiKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG4gIGNvbnN0IGNvZGUgPSBzdHJpbmcuY2hhckNvZGVBdCgwKTtcbiAgcmV0dXJuIGNvZGUgPj0gY29kZU9mQSAmJiBjb2RlIDw9IGNvZGVPZlo7XG59XG4iXX0=
