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


//# sourceMappingURL=minifyStdJS_plugin.js.map
