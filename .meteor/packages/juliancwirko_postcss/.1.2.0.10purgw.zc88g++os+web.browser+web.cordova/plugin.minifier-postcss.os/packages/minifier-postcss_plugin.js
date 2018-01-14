(function () {

/* Imports */
var ECMAScript = Package.ecmascript.ECMAScript;
var CssTools = Package['minifier-css'].CssTools;
var meteorInstall = Package.modules.meteorInstall;
var Buffer = Package.modules.Buffer;
var process = Package.modules.process;
var Symbol = Package['ecmascript-runtime'].Symbol;
var Map = Package['ecmascript-runtime'].Map;
var Set = Package['ecmascript-runtime'].Set;
var meteorBabelHelpers = Package['babel-runtime'].meteorBabelHelpers;
var Promise = Package.promise.Promise;

var require = meteorInstall({"node_modules":{"meteor":{"minifier-postcss":{"plugin":{"minify-css.js":["babel-runtime/helpers/typeof",function(require,exports,module){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                //
// packages/minifier-postcss/plugin/minify-css.js                                                                 //
//                                                                                                                //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                  //
var _typeof;module.import('babel-runtime/helpers/typeof',{"default":function(v){_typeof=v}});                     //
var appModulePath = Npm.require('app-module-path');                                                               // 1
appModulePath.addPath(process.cwd() + '/node_modules/');                                                          // 2
                                                                                                                  //
var Future = Npm.require('fibers/future');                                                                        // 4
var fs = Plugin.fs;                                                                                               // 5
var path = Plugin.path;                                                                                           // 6
var postCSS = Npm.require('postcss');                                                                             // 7
var sourcemap = Npm.require('source-map');                                                                        // 8
                                                                                                                  //
Plugin.registerMinifier({                                                                                         // 10
    extensions: ['css']                                                                                           // 11
}, function () {                                                                                                  // 10
    var minifier = new CssToolsMinifier();                                                                        // 13
    return minifier;                                                                                              // 14
});                                                                                                               // 15
                                                                                                                  //
var PACKAGES_FILE = 'package.json';                                                                               // 17
                                                                                                                  //
var packageFile = path.resolve(process.cwd(), PACKAGES_FILE);                                                     // 19
                                                                                                                  //
var loadJSONFile = function loadJSONFile(filePath) {                                                              // 21
    var content = void 0;                                                                                         // 22
    try {                                                                                                         // 23
        content = fs.readFileSync(filePath);                                                                      // 24
        try {                                                                                                     // 25
            return JSON.parse(content);                                                                           // 26
        } catch (e) {                                                                                             // 27
            console.log('Error: failed to parse ', filePath, ' as JSON');                                         // 28
            return {};                                                                                            // 29
        }                                                                                                         // 30
    } catch (e) {                                                                                                 // 31
        return false;                                                                                             // 32
    }                                                                                                             // 33
};                                                                                                                // 34
                                                                                                                  //
var postcssConfigPlugins;                                                                                         // 36
var postcssConfigParser;                                                                                          // 37
var postcssConfigExcludedPackages;                                                                                // 38
                                                                                                                  //
var jsonContent = loadJSONFile(packageFile);                                                                      // 40
                                                                                                                  //
if ((typeof jsonContent === 'undefined' ? 'undefined' : _typeof(jsonContent)) === 'object') {                     // 42
    postcssConfigPlugins = jsonContent.postcss && jsonContent.postcss.plugins;                                    // 43
    postcssConfigParser = jsonContent.postcss && jsonContent.postcss.parser;                                      // 44
    postcssConfigExcludedPackages = jsonContent.postcss && jsonContent.postcss.excludedPackages;                  // 45
}                                                                                                                 // 46
                                                                                                                  //
var getPostCSSPlugins = function getPostCSSPlugins() {                                                            // 48
    var plugins = [];                                                                                             // 49
    if (postcssConfigPlugins) {                                                                                   // 50
        Object.keys(postcssConfigPlugins).forEach(function (pluginName) {                                         // 51
            var postCSSPlugin = Npm.require(pluginName);                                                          // 52
            if (postCSSPlugin && postCSSPlugin.name === 'creator' && postCSSPlugin().postcssPlugin) {             // 53
                plugins.push(postCSSPlugin(postcssConfigPlugins ? postcssConfigPlugins[pluginName] : {}));        // 54
            }                                                                                                     // 55
        });                                                                                                       // 56
    }                                                                                                             // 57
    return plugins;                                                                                               // 58
};                                                                                                                // 59
                                                                                                                  //
var getPostCSSParser = function getPostCSSParser() {                                                              // 61
    var parser = null;                                                                                            // 62
    if (postcssConfigParser) {                                                                                    // 63
        parser = Npm.require(postcssConfigParser);                                                                // 64
    }                                                                                                             // 65
    return parser;                                                                                                // 66
};                                                                                                                // 67
                                                                                                                  //
var getExcludedPackages = function getExcludedPackages() {                                                        // 69
    var excluded = null;                                                                                          // 70
    if (postcssConfigExcludedPackages && postcssConfigExcludedPackages instanceof Array) {                        // 71
        excluded = postcssConfigExcludedPackages;                                                                 // 72
    }                                                                                                             // 73
    return excluded;                                                                                              // 74
};                                                                                                                // 75
                                                                                                                  //
var isNotInExcludedPackages = function isNotInExcludedPackages(excludedPackages, pathInBundle) {                  // 77
    var processedPackageName = void 0;                                                                            // 78
    var exclArr = [];                                                                                             // 79
    if (excludedPackages && excludedPackages instanceof Array) {                                                  // 80
        exclArr = excludedPackages.map(function (packageName) {                                                   // 81
            processedPackageName = packageName && packageName.replace(':', '_');                                  // 82
            return pathInBundle && pathInBundle.indexOf('packages/' + processedPackageName) > -1;                 // 83
        });                                                                                                       // 84
    }                                                                                                             // 85
    return exclArr.indexOf(true) === -1;                                                                          // 86
};                                                                                                                // 87
                                                                                                                  //
var isNotImport = function isNotImport(inputFileUrl) {                                                            // 89
    return !(/\.import\.css$/.test(inputFileUrl) || /(?:^|\/)imports\//.test(inputFileUrl));                      // 90
};                                                                                                                // 92
                                                                                                                  //
function CssToolsMinifier() {};                                                                                   // 94
                                                                                                                  //
CssToolsMinifier.prototype.processFilesForBundle = function (files, options) {                                    // 96
    var mode = options.minifyMode;                                                                                // 97
                                                                                                                  //
    if (!files.length) return;                                                                                    // 99
                                                                                                                  //
    var filesToMerge = [];                                                                                        // 101
                                                                                                                  //
    files.forEach(function (file) {                                                                               // 103
        if (isNotImport(file._source.url)) {                                                                      // 104
            filesToMerge.push(file);                                                                              // 105
        }                                                                                                         // 106
    });                                                                                                           // 107
                                                                                                                  //
    var merged = mergeCss(filesToMerge);                                                                          // 109
                                                                                                                  //
    if (mode === 'development') {                                                                                 // 111
        files[0].addStylesheet({                                                                                  // 112
            data: merged.code,                                                                                    // 113
            sourceMap: merged.sourceMap,                                                                          // 114
            path: 'merged-stylesheets.css'                                                                        // 115
        });                                                                                                       // 112
        return;                                                                                                   // 117
    }                                                                                                             // 118
                                                                                                                  //
    var minifiedFiles = CssTools.minifyCss(merged.code);                                                          // 120
                                                                                                                  //
    if (files.length) {                                                                                           // 122
        minifiedFiles.forEach(function (minified) {                                                               // 123
            files[0].addStylesheet({                                                                              // 124
                data: minified                                                                                    // 125
            });                                                                                                   // 124
        });                                                                                                       // 127
    }                                                                                                             // 128
};                                                                                                                // 129
                                                                                                                  //
// Lints CSS files and merges them into one file, fixing up source maps and                                       // 131
// pulling any @import directives up to the top since the CSS spec does not                                       // 132
// allow them to appear in the middle of a file.                                                                  // 133
var mergeCss = function mergeCss(css) {                                                                           // 134
    // Filenames passed to AST manipulator mapped to their original files                                         // 135
    var originals = {};                                                                                           // 136
    var excludedPackagesArr = getExcludedPackages();                                                              // 137
                                                                                                                  //
    var cssAsts = css.map(function (file) {                                                                       // 139
        var filename = file.getPathInBundle();                                                                    // 140
        originals[filename] = file;                                                                               // 141
                                                                                                                  //
        var f = new Future();                                                                                     // 143
                                                                                                                  //
        var css;                                                                                                  // 145
        var postres;                                                                                              // 146
        var isFileForPostCSS;                                                                                     // 147
                                                                                                                  //
        if (isNotInExcludedPackages(excludedPackagesArr, file.getPathInBundle())) {                               // 149
            isFileForPostCSS = true;                                                                              // 150
        } else {                                                                                                  // 151
            isFileForPostCSS = false;                                                                             // 152
        }                                                                                                         // 153
                                                                                                                  //
        postCSS(isFileForPostCSS ? getPostCSSPlugins() : []).process(file.getContentsAsString(), {                // 155
            from: process.cwd() + file._source.url,                                                               // 157
            parser: getPostCSSParser()                                                                            // 158
        }).then(function (result) {                                                                               // 156
            result.warnings().forEach(function (warn) {                                                           // 161
                process.stderr.write(warn.toString());                                                            // 162
            });                                                                                                   // 163
            f['return'](result);                                                                                  // 164
        })['catch'](function (error) {                                                                            // 165
            var errMsg = error.message;                                                                           // 167
            if (error.name === 'CssSyntaxError') {                                                                // 168
                errMsg = error.message + '\n\n' + 'Css Syntax Error.' + '\n\n' + error.message + error.showSourceCode();
            }                                                                                                     // 170
            error.message = errMsg;                                                                               // 171
            f['return'](error);                                                                                   // 172
        });                                                                                                       // 173
                                                                                                                  //
        try {                                                                                                     // 175
            var parseOptions = {                                                                                  // 176
                source: filename,                                                                                 // 177
                position: true                                                                                    // 178
            };                                                                                                    // 176
                                                                                                                  //
            postres = f.wait();                                                                                   // 181
                                                                                                                  //
            if (postres.name === 'CssSyntaxError') {                                                              // 183
                throw postres;                                                                                    // 184
            }                                                                                                     // 185
                                                                                                                  //
            css = postres.css;                                                                                    // 187
                                                                                                                  //
            var ast = CssTools.parseCss(css, parseOptions);                                                       // 189
            ast.filename = filename;                                                                              // 190
        } catch (e) {                                                                                             // 191
                                                                                                                  //
            if (e.name === 'CssSyntaxError') {                                                                    // 193
                file.error({                                                                                      // 194
                    message: e.message,                                                                           // 195
                    line: e.line,                                                                                 // 196
                    column: e.column                                                                              // 197
                });                                                                                               // 194
            } else if (e.reason) {                                                                                // 199
                file.error({                                                                                      // 200
                    message: e.reason,                                                                            // 201
                    line: e.line,                                                                                 // 202
                    column: e.column                                                                              // 203
                });                                                                                               // 200
            } else {                                                                                              // 205
                // Just in case it's not the normal error the library makes.                                      // 206
                file.error({                                                                                      // 207
                    message: e.message                                                                            // 208
                });                                                                                               // 207
            }                                                                                                     // 210
                                                                                                                  //
            return {                                                                                              // 212
                type: "stylesheet",                                                                               // 213
                stylesheet: {                                                                                     // 214
                    rules: []                                                                                     // 215
                },                                                                                                // 214
                filename: filename                                                                                // 217
            };                                                                                                    // 212
        }                                                                                                         // 219
                                                                                                                  //
        return ast;                                                                                               // 221
    });                                                                                                           // 222
                                                                                                                  //
    var warnCb = function warnCb(filename, msg) {                                                                 // 224
        // XXX make this a buildmessage.warning call rather than a random log.                                    // 225
        //     this API would be like buildmessage.error, but wouldn't cause                                      // 226
        //     the build to fail.                                                                                 // 227
        console.log(filename + ': warn: ' + msg);                                                                 // 228
    };                                                                                                            // 229
                                                                                                                  //
    var mergedCssAst = CssTools.mergeCssAsts(cssAsts, warnCb);                                                    // 231
                                                                                                                  //
    // Overwrite the CSS files list with the new concatenated file                                                // 233
    var stringifiedCss = CssTools.stringifyCss(mergedCssAst, {                                                    // 234
        sourcemap: true,                                                                                          // 235
        // don't try to read the referenced sourcemaps from the input                                             // 236
        inputSourcemaps: false                                                                                    // 237
    });                                                                                                           // 234
                                                                                                                  //
    if (!stringifiedCss.code) {                                                                                   // 240
        return {                                                                                                  // 241
            code: ''                                                                                              // 242
        };                                                                                                        // 241
    }                                                                                                             // 244
                                                                                                                  //
    // Add the contents of the input files to the source map of the new file                                      // 246
    stringifiedCss.map.sourcesContent = stringifiedCss.map.sources.map(function (filename) {                      // 247
        return originals[filename].getContentsAsString();                                                         // 249
    });                                                                                                           // 250
                                                                                                                  //
    // If any input files had source maps, apply them.                                                            // 252
    // Ex.: less -> css source map should be composed with css -> css source map                                  // 253
    var newMap = sourcemap.SourceMapGenerator.fromSourceMap(new sourcemap.SourceMapConsumer(stringifiedCss.map));
                                                                                                                  //
    Object.keys(originals).forEach(function (name) {                                                              // 257
        var file = originals[name];                                                                               // 258
        if (!file.getSourceMap()) return;                                                                         // 259
        try {                                                                                                     // 261
            newMap.applySourceMap(new sourcemap.SourceMapConsumer(file.getSourceMap()), name);                    // 262
        } catch (err) {                                                                                           // 264
            // If we can't apply the source map, silently drop it.                                                // 265
            //                                                                                                    // 266
            // XXX This is here because there are some less files that                                            // 267
            // produce source maps that throw when consumed. We should                                            // 268
            // figure out exactly why and fix it, but this will do for now.                                       // 269
        }                                                                                                         // 270
    });                                                                                                           // 271
                                                                                                                  //
    return {                                                                                                      // 273
        code: stringifiedCss.code,                                                                                // 274
        sourceMap: newMap.toString()                                                                              // 275
    };                                                                                                            // 273
};                                                                                                                // 277
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}]}}}}},{"extensions":[".js",".json"]});
require("./node_modules/meteor/minifier-postcss/plugin/minify-css.js");

/* Exports */
if (typeof Package === 'undefined') Package = {};
Package['minifier-postcss'] = {};

})();



//# sourceURL=meteor://💻app/packages/minifier-postcss_plugin.js
//# sourceMappingURL=data:application/json;charset=utf8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvbWluaWZpZXItcG9zdGNzcy9wbHVnaW4vbWluaWZ5LWNzcy5qcyJdLCJuYW1lcyI6WyJhcHBNb2R1bGVQYXRoIiwiTnBtIiwicmVxdWlyZSIsImFkZFBhdGgiLCJwcm9jZXNzIiwiY3dkIiwiRnV0dXJlIiwiZnMiLCJQbHVnaW4iLCJwYXRoIiwicG9zdENTUyIsInNvdXJjZW1hcCIsInJlZ2lzdGVyTWluaWZpZXIiLCJleHRlbnNpb25zIiwibWluaWZpZXIiLCJDc3NUb29sc01pbmlmaWVyIiwiUEFDS0FHRVNfRklMRSIsInBhY2thZ2VGaWxlIiwicmVzb2x2ZSIsImxvYWRKU09ORmlsZSIsImZpbGVQYXRoIiwiY29udGVudCIsInJlYWRGaWxlU3luYyIsIkpTT04iLCJwYXJzZSIsImUiLCJjb25zb2xlIiwibG9nIiwicG9zdGNzc0NvbmZpZ1BsdWdpbnMiLCJwb3N0Y3NzQ29uZmlnUGFyc2VyIiwicG9zdGNzc0NvbmZpZ0V4Y2x1ZGVkUGFja2FnZXMiLCJqc29uQ29udGVudCIsInBvc3Rjc3MiLCJwbHVnaW5zIiwicGFyc2VyIiwiZXhjbHVkZWRQYWNrYWdlcyIsImdldFBvc3RDU1NQbHVnaW5zIiwiT2JqZWN0Iiwia2V5cyIsImZvckVhY2giLCJwbHVnaW5OYW1lIiwicG9zdENTU1BsdWdpbiIsIm5hbWUiLCJwb3N0Y3NzUGx1Z2luIiwicHVzaCIsImdldFBvc3RDU1NQYXJzZXIiLCJnZXRFeGNsdWRlZFBhY2thZ2VzIiwiZXhjbHVkZWQiLCJBcnJheSIsImlzTm90SW5FeGNsdWRlZFBhY2thZ2VzIiwicGF0aEluQnVuZGxlIiwicHJvY2Vzc2VkUGFja2FnZU5hbWUiLCJleGNsQXJyIiwibWFwIiwicGFja2FnZU5hbWUiLCJyZXBsYWNlIiwiaW5kZXhPZiIsImlzTm90SW1wb3J0IiwiaW5wdXRGaWxlVXJsIiwidGVzdCIsInByb3RvdHlwZSIsInByb2Nlc3NGaWxlc0ZvckJ1bmRsZSIsImZpbGVzIiwib3B0aW9ucyIsIm1vZGUiLCJtaW5pZnlNb2RlIiwibGVuZ3RoIiwiZmlsZXNUb01lcmdlIiwiZmlsZSIsIl9zb3VyY2UiLCJ1cmwiLCJtZXJnZWQiLCJtZXJnZUNzcyIsImFkZFN0eWxlc2hlZXQiLCJkYXRhIiwiY29kZSIsInNvdXJjZU1hcCIsIm1pbmlmaWVkRmlsZXMiLCJDc3NUb29scyIsIm1pbmlmeUNzcyIsIm1pbmlmaWVkIiwiY3NzIiwib3JpZ2luYWxzIiwiZXhjbHVkZWRQYWNrYWdlc0FyciIsImNzc0FzdHMiLCJmaWxlbmFtZSIsImdldFBhdGhJbkJ1bmRsZSIsImYiLCJwb3N0cmVzIiwiaXNGaWxlRm9yUG9zdENTUyIsImdldENvbnRlbnRzQXNTdHJpbmciLCJmcm9tIiwidGhlbiIsInJlc3VsdCIsIndhcm5pbmdzIiwid2FybiIsInN0ZGVyciIsIndyaXRlIiwidG9TdHJpbmciLCJlcnJvciIsImVyck1zZyIsIm1lc3NhZ2UiLCJzaG93U291cmNlQ29kZSIsInBhcnNlT3B0aW9ucyIsInNvdXJjZSIsInBvc2l0aW9uIiwid2FpdCIsImFzdCIsInBhcnNlQ3NzIiwibGluZSIsImNvbHVtbiIsInJlYXNvbiIsInR5cGUiLCJzdHlsZXNoZWV0IiwicnVsZXMiLCJ3YXJuQ2IiLCJtc2ciLCJtZXJnZWRDc3NBc3QiLCJtZXJnZUNzc0FzdHMiLCJzdHJpbmdpZmllZENzcyIsInN0cmluZ2lmeUNzcyIsImlucHV0U291cmNlbWFwcyIsInNvdXJjZXNDb250ZW50Iiwic291cmNlcyIsIm5ld01hcCIsIlNvdXJjZU1hcEdlbmVyYXRvciIsImZyb21Tb3VyY2VNYXAiLCJTb3VyY2VNYXBDb25zdW1lciIsImdldFNvdXJjZU1hcCIsImFwcGx5U291cmNlTWFwIiwiZXJyIl0sIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUFBLElBQUlBLGdCQUFnQkMsSUFBSUMsT0FBSixDQUFZLGlCQUFaLENBQXBCO0FBQ0FGLGNBQWNHLE9BQWQsQ0FBc0JDLFFBQVFDLEdBQVIsS0FBZ0IsZ0JBQXRD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QTJCdEUsR0FBM0IsQ0FBK0IsVUFBVWdDLFFBQVYsRUFBb0I7QUFDL0MsZUFBT0gsVUFBVUcsUUFBVixFQUFvQkssbUJBQXBCLEVBQVA7QUFDSCxLQUZELENBREo7O0FBS0E7QUFDQTtBQUNBLFFBQUlrQyxTQUFTakgsVUFBVWtILGtCQUFWLENBQTZCQyxhQUE3QixDQUNULElBQUluSCxVQUFVb0gsaUJBQWQsQ0FBZ0NSLGVBQWVsRSxHQUEvQyxDQURTLENBQWI7O0FBR0FoQixXQUFPQyxJQUFQLENBQVk0QyxTQUFaLEVBQXVCM0MsT0FBdkIsQ0FBK0IsVUFBVUcsSUFBVixFQUFnQjtBQUMzQyxZQUFJMEIsT0FBT2MsVUFBVXhDLElBQVYsQ0FBWDtBQUNBLFlBQUksQ0FBQzBCLEtBQUs0RCxZQUFMLEVBQUwsRUFDSTtBQUNKLFlBQUk7QUFDQUosbUJBQU9LLGNBQVAsQ0FDSSxJQUFJdEgsVUFBVW9ILGlCQUFkLENBQWdDM0QsS0FBSzRELFlBQUwsRUFBaEMsQ0FESixFQUMwRHRGLElBRDFEO0FBRUgsU0FIRCxDQUdFLE9BQU93RixHQUFQLEVBQVk7QUFDVjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0g7QUFDSixLQWREOztBQWdCQSxXQUFPO0FBQ0h2RCxjQUFNNEMsZUFBZTVDLElBRGxCO0FBRUhDLG1CQUFXZ0QsT0FBTzFCLFFBQVA7QUFGUixLQUFQO0FBSUgsQ0EvSUQsdUgiLCJmaWxlIjoiL3BhY2thZ2VzL21pbmlmaWVyLXBvc3Rjc3NfcGx1Z2luLmpzIiwic291cmNlc0NvbnRlbnQiOlsidmFyIGFwcE1vZHVsZVBhdGggPSBOcG0ucmVxdWlyZSgnYXBwLW1vZHVsZS1wYXRoJyk7XG5hcHBNb2R1bGVQYXRoLmFkZFBhdGgocHJvY2Vzcy5jd2QoKSArICcvbm9kZV9tb2R1bGVzLycpO1xuXG52YXIgRnV0dXJlID0gTnBtLnJlcXVpcmUoJ2ZpYmVycy9mdXR1cmUnKTtcbnZhciBmcyA9IFBsdWdpbi5mcztcbnZhciBwYXRoID0gUGx1Z2luLnBhdGg7XG52YXIgcG9zdENTUyA9IE5wbS5yZXF1aXJlKCdwb3N0Y3NzJyk7XG52YXIgc291cmNlbWFwID0gTnBtLnJlcXVpcmUoJ3NvdXJjZS1tYXAnKTtcblxuUGx1Z2luLnJlZ2lzdGVyTWluaWZpZXIoe1xuICAgIGV4dGVuc2lvbnM6IFsnY3NzJ11cbn0sIGZ1bmN0aW9uICgpIHtcbiAgICBjb25zdCBtaW5pZmllciA9IG5ldyBDc3NUb29sc01pbmlmaWVyKCk7XG4gICAgcmV0dXJuIG1pbmlmaWVyO1xufSk7XG5cbnZhciBQQUNLQUdFU19GSUxFID0gJ3BhY2thZ2UuanNvbic7XG5cbnZhciBwYWNrYWdlRmlsZSA9IHBhdGgucmVzb2x2ZShwcm9jZXNzLmN3ZCgpLCBQQUNLQUdFU19GSUxFKTtcblxudmFyIGxvYWRKU09ORmlsZSA9IGZ1bmN0aW9uIChmaWxlUGF0aCkge1xuICAgIGxldCBjb250ZW50O1xuICAgIHRyeSB7XG4gICAgICAgIGNvbnRlbnQgPSBmcy5yZWFkRmlsZVN5bmMoZmlsZVBhdGgpO1xuICAgICAgICB0cnkge1xuICAgICAgICAgICAgcmV0dXJuIEpTT04ucGFyc2UoY29udGVudCk7XG4gICAgICAgIH0gY2F0Y2ggKGUpIHtcbiAgICAgICAgICAgIGNvbnNvbGUubG9nKCdFcnJvcjogZmFpbGVkIHRvIHBhcnNlICcsIGZpbGVQYXRoLCAnIGFzIEpTT04nKTtcbiAgICAgICAgICAgIHJldHVybiB7fTtcbiAgICAgICAgfVxuICAgIH0gY2F0Y2ggKGUpIHtcbiAgICAgICAgcmV0dXJuIGZhbHNlO1xuICAgIH1cbn07XG5cbnZhciBwb3N0Y3NzQ29uZmlnUGx1Z2lucztcbnZhciBwb3N0Y3NzQ29uZmlnUGFyc2VyO1xudmFyIHBvc3Rjc3NDb25maWdFeGNsdWRlZFBhY2thZ2VzO1xuXG52YXIganNvbkNvbnRlbnQgPSBsb2FkSlNPTkZpbGUocGFja2FnZUZpbGUpO1xuXG5pZiAodHlwZW9mIGpzb25Db250ZW50ID09PSAnb2JqZWN0Jykge1xuICAgIHBvc3Rjc3NDb25maWdQbHVnaW5zID0ganNvbkNvbnRlbnQucG9zdGNzcyAmJiBqc29uQ29udGVudC5wb3N0Y3NzLnBsdWdpbnM7XG4gICAgcG9zdGNzc0NvbmZpZ1BhcnNlciA9IGpzb25Db250ZW50LnBvc3Rjc3MgJiYganNvbkNvbnRlbnQucG9zdGNzcy5wYXJzZXI7XG4gICAgcG9zdGNzc0NvbmZpZ0V4Y2x1ZGVkUGFja2FnZXMgPSBqc29uQ29udGVudC5wb3N0Y3NzICYmIGpzb25Db250ZW50LnBvc3Rjc3MuZXhjbHVkZWRQYWNrYWdlcztcbn1cblxudmFyIGdldFBvc3RDU1NQbHVnaW5zID0gZnVuY3Rpb24gKCkge1xuICAgIGxldCBwbHVnaW5zID0gW107XG4gICAgaWYgKHBvc3Rjc3NDb25maWdQbHVnaW5zKSB7XG4gICAgICAgIE9iamVjdC5rZXlzKHBvc3Rjc3NDb25maWdQbHVnaW5zKS5mb3JFYWNoKGZ1bmN0aW9uIChwbHVnaW5OYW1lKSB7XG4gICAgICAgICAgICBsZXQgcG9zdENTU1BsdWdpbiA9IE5wbS5yZXF1aXJlKHBsdWdpbk5hbWUpO1xuICAgICAgICAgICAgaWYgKHBvc3RDU1NQbHVnaW4gJiYgcG9zdENTU1BsdWdpbi5uYW1lID09PSAnY3JlYXRvcicgJiYgcG9zdENTU1BsdWdpbigpLnBvc3Rjc3NQbHVnaW4pIHtcbiAgICAgICAgICAgICAgICBwbHVnaW5zLnB1c2gocG9zdENTU1BsdWdpbihwb3N0Y3NzQ29uZmlnUGx1Z2lucyA/IHBvc3Rjc3NDb25maWdQbHVnaW5zW3BsdWdpbk5hbWVdIDoge30pKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfSk7XG4gICAgfVxuICAgIHJldHVybiBwbHVnaW5zO1xufTtcblxudmFyIGdldFBvc3RDU1NQYXJzZXIgPSBmdW5jdGlvbiAoKSB7XG4gICAgbGV0IHBhcnNlciA9IG51bGw7XG4gICAgaWYgKHBvc3Rjc3NDb25maWdQYXJzZXIpIHtcbiAgICAgICAgcGFyc2VyID0gTnBtLnJlcXVpcmUocG9zdGNzc0NvbmZpZ1BhcnNlcik7XG4gICAgfVxuICAgIHJldHVybiBwYXJzZXI7XG59O1xuXG52YXIgZ2V0RXhjbHVkZWRQYWNrYWdlcyA9IGZ1bmN0aW9uICgpIHtcbiAgICBsZXQgZXhjbHVkZWQgPSBudWxsO1xuICAgIGlmIChwb3N0Y3NzQ29uZmlnRXhjbHVkZWRQYWNrYWdlcyAmJiBwb3N0Y3NzQ29uZmlnRXhjbHVkZWRQYWNrYWdlcyBpbnN0YW5jZW9mIEFycmF5KSB7XG4gICAgICAgIGV4Y2x1ZGVkID0gcG9zdGNzc0NvbmZpZ0V4Y2x1ZGVkUGFja2FnZXM7XG4gICAgfVxuICAgIHJldHVybiBleGNsdWRlZDtcbn07XG5cbnZhciBpc05vdEluRXhjbHVkZWRQYWNrYWdlcyA9IGZ1bmN0aW9uIChleGNsdWRlZFBhY2thZ2VzLCBwYXRoSW5CdW5kbGUpIHtcbiAgICBsZXQgcHJvY2Vzc2VkUGFja2FnZU5hbWU7XG4gICAgbGV0IGV4Y2xBcnIgPSBbXTtcbiAgICBpZiAoZXhjbHVkZWRQYWNrYWdlcyAmJiBleGNsdWRlZFBhY2thZ2VzIGluc3RhbmNlb2YgQXJyYXkpIHtcbiAgICAgICAgZXhjbEFyciA9IGV4Y2x1ZGVkUGFja2FnZXMubWFwKHBhY2thZ2VOYW1lID0+IHtcbiAgICAgICAgICAgIHByb2Nlc3NlZFBhY2thZ2VOYW1lID0gcGFja2FnZU5hbWUgJiYgcGFja2FnZU5hbWUucmVwbGFjZSgnOicsICdfJyk7XG4gICAgICAgICAgICByZXR1cm4gcGF0aEluQnVuZGxlICYmIHBhdGhJbkJ1bmRsZS5pbmRleE9mKCdwYWNrYWdlcy8nICsgcHJvY2Vzc2VkUGFja2FnZU5hbWUpID4gLTE7XG4gICAgICAgIH0pO1xuICAgIH1cbiAgICByZXR1cm4gZXhjbEFyci5pbmRleE9mKHRydWUpID09PSAtMTtcbn07XG5cbnZhciBpc05vdEltcG9ydCA9IGZ1bmN0aW9uIChpbnB1dEZpbGVVcmwpIHtcbiAgICByZXR1cm4gISgvXFwuaW1wb3J0XFwuY3NzJC8udGVzdChpbnB1dEZpbGVVcmwpIHx8XG4gICAgICAgICAgICAgLyg/Ol58XFwvKWltcG9ydHNcXC8vLnRlc3QoaW5wdXRGaWxlVXJsKSk7XG59O1xuXG5mdW5jdGlvbiBDc3NUb29sc01pbmlmaWVyKCkge307XG5cbkNzc1Rvb2xzTWluaWZpZXIucHJvdG90eXBlLnByb2Nlc3NGaWxlc0ZvckJ1bmRsZSA9IGZ1bmN0aW9uIChmaWxlcywgb3B0aW9ucykge1xuICAgIHZhciBtb2RlID0gb3B0aW9ucy5taW5pZnlNb2RlO1xuXG4gICAgaWYgKCFmaWxlcy5sZW5ndGgpIHJldHVybjtcblxuICAgIHZhciBmaWxlc1RvTWVyZ2UgPSBbXTtcblxuICAgIGZpbGVzLmZvckVhY2goZnVuY3Rpb24gKGZpbGUpIHtcbiAgICAgICAgaWYgKGlzTm90SW1wb3J0KGZpbGUuX3NvdXJjZS51cmwpKSB7XG4gICAgICAgICAgICBmaWxlc1RvTWVyZ2UucHVzaChmaWxlKTtcbiAgICAgICAgfVxuICAgIH0pO1xuXG4gICAgdmFyIG1lcmdlZCA9IG1lcmdlQ3NzKGZpbGVzVG9NZXJnZSk7XG5cbiAgICBpZiAobW9kZSA9PT0gJ2RldmVsb3BtZW50Jykge1xuICAgICAgICBmaWxlc1swXS5hZGRTdHlsZXNoZWV0KHtcbiAgICAgICAgICAgIGRhdGE6IG1lcmdlZC5jb2RlLFxuICAgICAgICAgICAgc291cmNlTWFwOiBtZXJnZWQuc291cmNlTWFwLFxuICAgICAgICAgICAgcGF0aDogJ21lcmdlZC1zdHlsZXNoZWV0cy5jc3MnXG4gICAgICAgIH0pO1xuICAgICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgdmFyIG1pbmlmaWVkRmlsZXMgPSBDc3NUb29scy5taW5pZnlDc3MobWVyZ2VkLmNvZGUpO1xuXG4gICAgaWYgKGZpbGVzLmxlbmd0aCkge1xuICAgICAgICBtaW5pZmllZEZpbGVzLmZvckVhY2goZnVuY3Rpb24gKG1pbmlmaWVkKSB7XG4gICAgICAgICAgICBmaWxlc1swXS5hZGRTdHlsZXNoZWV0KHtcbiAgICAgICAgICAgICAgICBkYXRhOiBtaW5pZmllZFxuICAgICAgICAgICAgfSk7XG4gICAgICAgIH0pO1xuICAgIH1cbn07XG5cbi8vIExpbnRzIENTUyBmaWxlcyBhbmQgbWVyZ2VzIHRoZW0gaW50byBvbmUgZmlsZSwgZml4aW5nIHVwIHNvdXJjZSBtYXBzIGFuZFxuLy8gcHVsbGluZyBhbnkgQGltcG9ydCBkaXJlY3RpdmVzIHVwIHRvIHRoZSB0b3Agc2luY2UgdGhlIENTUyBzcGVjIGRvZXMgbm90XG4vLyBhbGxvdyB0aGVtIHRvIGFwcGVhciBpbiB0aGUgbWlkZGxlIG9mIGEgZmlsZS5cbnZhciBtZXJnZUNzcyA9IGZ1bmN0aW9uIChjc3MpIHtcbiAgICAvLyBGaWxlbmFtZXMgcGFzc2VkIHRvIEFTVCBtYW5pcHVsYXRvciBtYXBwZWQgdG8gdGhlaXIgb3JpZ2luYWwgZmlsZXNcbiAgICB2YXIgb3JpZ2luYWxzID0ge307XG4gICAgdmFyIGV4Y2x1ZGVkUGFja2FnZXNBcnIgPSBnZXRFeGNsdWRlZFBhY2thZ2VzKCk7XG5cbiAgICB2YXIgY3NzQXN0cyA9IGNzcy5tYXAoZnVuY3Rpb24gKGZpbGUpIHtcbiAgICAgICAgdmFyIGZpbGVuYW1lID0gZmlsZS5nZXRQYXRoSW5CdW5kbGUoKTtcbiAgICAgICAgb3JpZ2luYWxzW2ZpbGVuYW1lXSA9IGZpbGU7XG5cbiAgICAgICAgdmFyIGYgPSBuZXcgRnV0dXJlO1xuXG4gICAgICAgIHZhciBjc3M7XG4gICAgICAgIHZhciBwb3N0cmVzO1xuICAgICAgICB2YXIgaXNGaWxlRm9yUG9zdENTUztcblxuICAgICAgICBpZiAoaXNOb3RJbkV4Y2x1ZGVkUGFja2FnZXMoZXhjbHVkZWRQYWNrYWdlc0FyciwgZmlsZS5nZXRQYXRoSW5CdW5kbGUoKSkpIHtcbiAgICAgICAgICAgIGlzRmlsZUZvclBvc3RDU1MgPSB0cnVlO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgaXNGaWxlRm9yUG9zdENTUyA9IGZhbHNlO1xuICAgICAgICB9XG5cbiAgICAgICAgcG9zdENTUyhpc0ZpbGVGb3JQb3N0Q1NTID8gZ2V0UG9zdENTU1BsdWdpbnMoKSA6IFtdKVxuICAgICAgICAgICAgLnByb2Nlc3MoZmlsZS5nZXRDb250ZW50c0FzU3RyaW5nKCksIHtcbiAgICAgICAgICAgICAgICBmcm9tOiBwcm9jZXNzLmN3ZCgpICsgZmlsZS5fc291cmNlLnVybCxcbiAgICAgICAgICAgICAgICBwYXJzZXI6IGdldFBvc3RDU1NQYXJzZXIoKVxuICAgICAgICAgICAgfSlcbiAgICAgICAgICAgIC50aGVuKGZ1bmN0aW9uIChyZXN1bHQpIHtcbiAgICAgICAgICAgICAgICByZXN1bHQud2FybmluZ3MoKS5mb3JFYWNoKGZ1bmN0aW9uICh3YXJuKSB7XG4gICAgICAgICAgICAgICAgICAgIHByb2Nlc3Muc3RkZXJyLndyaXRlKHdhcm4udG9TdHJpbmcoKSk7XG4gICAgICAgICAgICAgICAgfSk7XG4gICAgICAgICAgICAgICAgZi5yZXR1cm4ocmVzdWx0KTtcbiAgICAgICAgICAgIH0pXG4gICAgICAgICAgICAuY2F0Y2goZnVuY3Rpb24gKGVycm9yKSB7XG4gICAgICAgICAgICAgICAgdmFyIGVyck1zZyA9IGVycm9yLm1lc3NhZ2U7XG4gICAgICAgICAgICAgICAgaWYgKGVycm9yLm5hbWUgPT09ICdDc3NTeW50YXhFcnJvcicpIHtcbiAgICAgICAgICAgICAgICAgICAgZXJyTXNnID0gZXJyb3IubWVzc2FnZSArICdcXG5cXG4nICsgJ0NzcyBTeW50YXggRXJyb3IuJyArICdcXG5cXG4nICsgZXJyb3IubWVzc2FnZSArIGVycm9yLnNob3dTb3VyY2VDb2RlKClcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgZXJyb3IubWVzc2FnZSA9IGVyck1zZztcbiAgICAgICAgICAgICAgICBmLnJldHVybihlcnJvcik7XG4gICAgICAgICAgICB9KTtcblxuICAgICAgICB0cnkge1xuICAgICAgICAgICAgdmFyIHBhcnNlT3B0aW9ucyA9IHtcbiAgICAgICAgICAgICAgICBzb3VyY2U6IGZpbGVuYW1lLFxuICAgICAgICAgICAgICAgIHBvc2l0aW9uOiB0cnVlXG4gICAgICAgICAgICB9O1xuXG4gICAgICAgICAgICBwb3N0cmVzID0gZi53YWl0KCk7XG5cbiAgICAgICAgICAgIGlmIChwb3N0cmVzLm5hbWUgPT09ICdDc3NTeW50YXhFcnJvcicpIHtcbiAgICAgICAgICAgICAgICB0aHJvdyBwb3N0cmVzO1xuICAgICAgICAgICAgfVxuXG4gICAgICAgICAgICBjc3MgPSBwb3N0cmVzLmNzcztcblxuICAgICAgICAgICAgdmFyIGFzdCA9IENzc1Rvb2xzLnBhcnNlQ3NzKGNzcywgcGFyc2VPcHRpb25zKTtcbiAgICAgICAgICAgIGFzdC5maWxlbmFtZSA9IGZpbGVuYW1lO1xuICAgICAgICB9IGNhdGNoIChlKSB7XG5cbiAgICAgICAgICAgIGlmIChlLm5hbWUgPT09ICdDc3NTeW50YXhFcnJvcicpIHtcbiAgICAgICAgICAgICAgICBmaWxlLmVycm9yKHtcbiAgICAgICAgICAgICAgICAgICAgbWVzc2FnZTogZS5tZXNzYWdlLFxuICAgICAgICAgICAgICAgICAgICBsaW5lOiBlLmxpbmUsXG4gICAgICAgICAgICAgICAgICAgIGNvbHVtbjogZS5jb2x1bW5cbiAgICAgICAgICAgICAgICB9KTtcbiAgICAgICAgICAgIH0gZWxzZSBpZiAoZS5yZWFzb24pIHtcbiAgICAgICAgICAgICAgICBmaWxlLmVycm9yKHtcbiAgICAgICAgICAgICAgICAgICAgbWVzc2FnZTogZS5yZWFzb24sXG4gICAgICAgICAgICAgICAgICAgIGxpbmU6IGUubGluZSxcbiAgICAgICAgICAgICAgICAgICAgY29sdW1uOiBlLmNvbHVtblxuICAgICAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgICAgICAvLyBKdXN0IGluIGNhc2UgaXQncyBub3QgdGhlIG5vcm1hbCBlcnJvciB0aGUgbGlicmFyeSBtYWtlcy5cbiAgICAgICAgICAgICAgICBmaWxlLmVycm9yKHtcbiAgICAgICAgICAgICAgICAgICAgbWVzc2FnZTogZS5tZXNzYWdlXG4gICAgICAgICAgICAgICAgfSk7XG4gICAgICAgICAgICB9XG5cbiAgICAgICAgICAgIHJldHVybiB7XG4gICAgICAgICAgICAgICAgdHlwZTogXCJzdHlsZXNoZWV0XCIsXG4gICAgICAgICAgICAgICAgc3R5bGVzaGVldDoge1xuICAgICAgICAgICAgICAgICAgICBydWxlczogW11cbiAgICAgICAgICAgICAgICB9LFxuICAgICAgICAgICAgICAgIGZpbGVuYW1lOiBmaWxlbmFtZVxuICAgICAgICAgICAgfTtcbiAgICAgICAgfVxuXG4gICAgICAgIHJldHVybiBhc3Q7XG4gICAgfSk7XG5cbiAgICB2YXIgd2FybkNiID0gZnVuY3Rpb24gKGZpbGVuYW1lLCBtc2cpIHtcbiAgICAgICAgLy8gWFhYIG1ha2UgdGhpcyBhIGJ1aWxkbWVzc2FnZS53YXJuaW5nIGNhbGwgcmF0aGVyIHRoYW4gYSByYW5kb20gbG9nLlxuICAgICAgICAvLyAgICAgdGhpcyBBUEkgd291bGQgYmUgbGlrZSBidWlsZG1lc3NhZ2UuZXJyb3IsIGJ1dCB3b3VsZG4ndCBjYXVzZVxuICAgICAgICAvLyAgICAgdGhlIGJ1aWxkIHRvIGZhaWwuXG4gICAgICAgIGNvbnNvbGUubG9nKGZpbGVuYW1lICsgJzogd2FybjogJyArIG1zZyk7XG4gICAgfTtcblxuICAgIHZhciBtZXJnZWRDc3NBc3QgPSBDc3NUb29scy5tZXJnZUNzc0FzdHMoY3NzQXN0cywgd2FybkNiKTtcblxuICAgIC8vIE92ZXJ3cml0ZSB0aGUgQ1NTIGZpbGVzIGxpc3Qgd2l0aCB0aGUgbmV3IGNvbmNhdGVuYXRlZCBmaWxlXG4gICAgdmFyIHN0cmluZ2lmaWVkQ3NzID0gQ3NzVG9vbHMuc3RyaW5naWZ5Q3NzKG1lcmdlZENzc0FzdCwge1xuICAgICAgICBzb3VyY2VtYXA6IHRydWUsXG4gICAgICAgIC8vIGRvbid0IHRyeSB0byByZWFkIHRoZSByZWZlcmVuY2VkIHNvdXJjZW1hcHMgZnJvbSB0aGUgaW5wdXRcbiAgICAgICAgaW5wdXRTb3VyY2VtYXBzOiBmYWxzZVxuICAgIH0pO1xuXG4gICAgaWYgKCFzdHJpbmdpZmllZENzcy5jb2RlKSB7XG4gICAgICAgIHJldHVybiB7XG4gICAgICAgICAgICBjb2RlOiAnJ1xuICAgICAgICB9O1xuICAgIH1cblxuICAgIC8vIEFkZCB0aGUgY29udGVudHMgb2YgdGhlIGlucHV0IGZpbGVzIHRvIHRoZSBzb3VyY2UgbWFwIG9mIHRoZSBuZXcgZmlsZVxuICAgIHN0cmluZ2lmaWVkQ3NzLm1hcC5zb3VyY2VzQ29udGVudCA9XG4gICAgICAgIHN0cmluZ2lmaWVkQ3NzLm1hcC5zb3VyY2VzLm1hcChmdW5jdGlvbiAoZmlsZW5hbWUpIHtcbiAgICAgICAgICAgIHJldHVybiBvcmlnaW5hbHNbZmlsZW5hbWVdLmdldENvbnRlbnRzQXNTdHJpbmcoKTtcbiAgICAgICAgfSk7XG5cbiAgICAvLyBJZiBhbnkgaW5wdXQgZmlsZXMgaGFkIHNvdXJjZSBtYXBzLCBhcHBseSB0aGVtLlxuICAgIC8vIEV4LjogbGVzcyAtPiBjc3Mgc291cmNlIG1hcCBzaG91bGQgYmUgY29tcG9zZWQgd2l0aCBjc3MgLT4gY3NzIHNvdXJjZSBtYXBcbiAgICB2YXIgbmV3TWFwID0gc291cmNlbWFwLlNvdXJjZU1hcEdlbmVyYXRvci5mcm9tU291cmNlTWFwKFxuICAgICAgICBuZXcgc291cmNlbWFwLlNvdXJjZU1hcENvbnN1bWVyKHN0cmluZ2lmaWVkQ3NzLm1hcCkpO1xuXG4gICAgT2JqZWN0LmtleXMob3JpZ2luYWxzKS5mb3JFYWNoKGZ1bmN0aW9uIChuYW1lKSB7XG4gICAgICAgIHZhciBmaWxlID0gb3JpZ2luYWxzW25hbWVdO1xuICAgICAgICBpZiAoIWZpbGUuZ2V0U291cmNlTWFwKCkpXG4gICAgICAgICAgICByZXR1cm47XG4gICAgICAgIHRyeSB7XG4gICAgICAgICAgICBuZXdNYXAuYXBwbHlTb3VyY2VNYXAoXG4gICAgICAgICAgICAgICAgbmV3IHNvdXJjZW1hcC5Tb3VyY2VNYXBDb25zdW1lcihmaWxlLmdldFNvdXJjZU1hcCgpKSwgbmFtZSk7XG4gICAgICAgIH0gY2F0Y2ggKGVycikge1xuICAgICAgICAgICAgLy8gSWYgd2UgY2FuJ3QgYXBwbHkgdGhlIHNvdXJjZSBtYXAsIHNpbGVudGx5IGRyb3AgaXQuXG4gICAgICAgICAgICAvL1xuICAgICAgICAgICAgLy8gWFhYIFRoaXMgaXMgaGVyZSBiZWNhdXNlIHRoZXJlIGFyZSBzb21lIGxlc3MgZmlsZXMgdGhhdFxuICAgICAgICAgICAgLy8gcHJvZHVjZSBzb3VyY2UgbWFwcyB0aGF0IHRocm93IHdoZW4gY29uc3VtZWQuIFdlIHNob3VsZFxuICAgICAgICAgICAgLy8gZmlndXJlIG91dCBleGFjdGx5IHdoeSBhbmQgZml4IGl0LCBidXQgdGhpcyB3aWxsIGRvIGZvciBub3cuXG4gICAgICAgIH1cbiAgICB9KTtcblxuICAgIHJldHVybiB7XG4gICAgICAgIGNvZGU6IHN0cmluZ2lmaWVkQ3NzLmNvZGUsXG4gICAgICAgIHNvdXJjZU1hcDogbmV3TWFwLnRvU3RyaW5nKClcbiAgICB9O1xufTtcbiJdfQ==
