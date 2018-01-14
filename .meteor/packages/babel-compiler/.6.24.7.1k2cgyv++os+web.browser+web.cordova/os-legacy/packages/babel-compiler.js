(function(){

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// packages/babel-compiler/babel.js                                           //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
                                                                              //
var meteorBabel = null;                                                       // 1
function getMeteorBabel() {                                                   // 2
  return meteorBabel || (meteorBabel = Npm.require("meteor-babel"));          // 3
}                                                                             // 4
                                                                              // 5
/**                                                                           // 6
 * Returns a new object containing default options appropriate for            // 7
 */                                                                           // 8
function getDefaultOptions(extraFeatures) {                                   // 9
  // See https://github.com/meteor/babel/blob/master/options.js for more      // 10
  // information about what the default options are.                          // 11
  var options = getMeteorBabel().getDefaultOptions(extraFeatures);            // 12
                                                                              // 13
  // The sourceMap option should probably be removed from the default         // 14
  // options returned by meteorBabel.getDefaultOptions.                       // 15
  delete options.sourceMap;                                                   // 16
                                                                              // 17
  return options;                                                             // 18
}                                                                             // 19
                                                                              // 20
Babel = {                                                                     // 21
  getDefaultOptions: getDefaultOptions,                                       // 22
                                                                              // 23
  // Deprecated, now a no-op.                                                 // 24
  validateExtraFeatures: Function.prototype,                                  // 25
                                                                              // 26
  parse: function (source) {                                                  // 27
    return getMeteorBabel().parse(source);                                    // 28
  },                                                                          // 29
                                                                              // 30
  compile: function (source, options) {                                       // 31
    options = options || getDefaultOptions();                                 // 32
    return getMeteorBabel().compile(source, options);                         // 33
  },                                                                          // 34
                                                                              // 35
  setCacheDir: function (cacheDir) {                                          // 36
    getMeteorBabel().setCacheDir(cacheDir);                                   // 37
  },                                                                          // 38
                                                                              // 39
  minify: function (source, options) {                                        // 40
    var options = options || getMeteorBabel().getMinifierOptions();           // 41
    return getMeteorBabel().minify(source, options);                          // 42
  },                                                                          // 43
                                                                              // 44
  getMinifierOptions: function (extraFeatures) {                              // 45
    return getMeteorBabel().getMinifierOptions(extraFeatures);                // 46
  }                                                                           // 47
};                                                                            // 48
                                                                              // 49
////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////
//                                                                            //
// packages/babel-compiler/babel-compiler.js                                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
                                                                              //
var semver = Npm.require("semver");                                           // 1
                                                                              // 2
/**                                                                           // 3
 * A compiler that can be instantiated with features and used inside          // 4
 * Plugin.registerCompiler                                                    // 5
 * @param {Object} extraFeatures The same object that getDefaultOptions takes
 */                                                                           // 7
BabelCompiler = function BabelCompiler(extraFeatures) {                       // 8
  this.extraFeatures = extraFeatures;                                         // 9
  this._babelrcCache = null;                                                  // 10
  this._babelrcWarnings = Object.create(null);                                // 11
};                                                                            // 12
                                                                              // 13
var BCp = BabelCompiler.prototype;                                            // 14
var excludedFileExtensionPattern = /\.(es5|min)\.js$/i;                       // 15
var hasOwn = Object.prototype.hasOwnProperty;                                 // 16
                                                                              // 17
// There's no way to tell the current Meteor version, but we can infer        // 18
// whether it's Meteor 1.4.4 or earlier by checking the Node version.         // 19
var isMeteorPre144 = semver.lt(process.version, "4.8.1");                     // 20
                                                                              // 21
BCp.processFilesForTarget = function (inputFiles) {                           // 22
  // Reset this cache for each batch processed.                               // 23
  this._babelrcCache = null;                                                  // 24
                                                                              // 25
  inputFiles.forEach(function (inputFile) {                                   // 26
    var toBeAdded = this.processOneFileForTarget(inputFile);                  // 27
    if (toBeAdded) {                                                          // 28
      inputFile.addJavaScript(toBeAdded);                                     // 29
    }                                                                         // 30
  }, this);                                                                   // 31
};                                                                            // 32
                                                                              // 33
// Returns an object suitable for passing to inputFile.addJavaScript, or      // 34
// null to indicate there was an error, and nothing should be added.          // 35
BCp.processOneFileForTarget = function (inputFile, source) {                  // 36
  this._babelrcCache = this._babelrcCache || Object.create(null);             // 37
                                                                              // 38
  if (typeof source !== "string") {                                           // 39
    // Other compiler plugins can call processOneFileForTarget with a         // 40
    // source string that's different from inputFile.getContentsAsString()    // 41
    // if they've already done some processing.                               // 42
    source = inputFile.getContentsAsString();                                 // 43
  }                                                                           // 44
                                                                              // 45
  var packageName = inputFile.getPackageName();                               // 46
  var inputFilePath = inputFile.getPathInPackage();                           // 47
  var outputFilePath = inputFilePath;                                         // 48
  var fileOptions = inputFile.getFileOptions();                               // 49
  var toBeAdded = {                                                           // 50
    sourcePath: inputFilePath,                                                // 51
    path: outputFilePath,                                                     // 52
    data: source,                                                             // 53
    hash: inputFile.getSourceHash(),                                          // 54
    sourceMap: null,                                                          // 55
    bare: !! fileOptions.bare                                                 // 56
  };                                                                          // 57
  var cacheDeps = {                                                           // 58
    sourceHash: toBeAdded.hash                                                // 59
  };                                                                          // 60
                                                                              // 61
  // If you need to exclude a specific file within a package from Babel       // 62
  // compilation, pass the { transpile: false } options to api.addFiles       // 63
  // when you add that file.                                                  // 64
  if (fileOptions.transpile !== false &&                                      // 65
      // Bare files should not be transpiled by Babel, because they do not    // 66
      // have access to CommonJS APIs like `require`, `module`, `exports`.    // 67
      ! toBeAdded.bare &&                                                     // 68
      // If you need to exclude a specific file within an app from Babel      // 69
      // compilation, give it the following file extension: .es5.js           // 70
      ! excludedFileExtensionPattern.test(inputFilePath)) {                   // 71
                                                                              // 72
    var extraFeatures = Object.assign({}, this.extraFeatures);                // 73
                                                                              // 74
    if (inputFile.getArch().startsWith("os.")) {                              // 75
      // Start with a much simpler set of Babel presets and plugins if        // 76
      // we're compiling for Node 8.                                          // 77
      extraFeatures.nodeMajorVersion = parseInt(process.versions.node);       // 78
    }                                                                         // 79
                                                                              // 80
    if (! extraFeatures.hasOwnProperty("jscript")) {                          // 81
      // Perform some additional transformations to improve compatibility     // 82
      // in older browsers (e.g. wrapping named function expressions, per     // 83
      // http://kiro.me/blog/nfe_dilemma.html).                               // 84
      extraFeatures.jscript = true;                                           // 85
    }                                                                         // 86
                                                                              // 87
    var babelOptions = Babel.getDefaultOptions(extraFeatures);                // 88
                                                                              // 89
    this.inferExtraBabelOptions(inputFile, babelOptions, cacheDeps);          // 90
                                                                              // 91
    babelOptions.sourceMap = true;                                            // 92
    babelOptions.filename =                                                   // 93
      babelOptions.sourceFileName = packageName                               // 94
      ? "packages/" + packageName + "/" + inputFilePath                       // 95
      : inputFilePath;                                                        // 96
                                                                              // 97
    babelOptions.sourceMapTarget = babelOptions.filename + ".map";            // 98
                                                                              // 99
    try {                                                                     // 100
      var result = profile('Babel.compile', function () {                     // 101
        return Babel.compile(source, babelOptions, cacheDeps);                // 102
      });                                                                     // 103
    } catch (e) {                                                             // 104
      if (e.loc) {                                                            // 105
        inputFile.error({                                                     // 106
          message: e.message,                                                 // 107
          line: e.loc.line,                                                   // 108
          column: e.loc.column,                                               // 109
        });                                                                   // 110
                                                                              // 111
        return null;                                                          // 112
      }                                                                       // 113
                                                                              // 114
      throw e;                                                                // 115
    }                                                                         // 116
                                                                              // 117
    if (isMeteorPre144) {                                                     // 118
      // Versions of meteor-tool earlier than 1.4.4 do not understand that    // 119
      // module.importSync is synonymous with the deprecated module.import    // 120
      // and thus fail to register dependencies for importSync calls.         // 121
      // This string replacement may seem a bit hacky, but it will tide us    // 122
      // over until everyone has updated to Meteor 1.4.4.                     // 123
      // https://github.com/meteor/meteor/issues/8572                         // 124
      result.code = result.code.replace(                                      // 125
        /\bmodule\.importSync\b/g,                                            // 126
        "module.import"                                                       // 127
      );                                                                      // 128
    }                                                                         // 129
                                                                              // 130
    toBeAdded.data = result.code;                                             // 131
    toBeAdded.hash = result.hash;                                             // 132
    toBeAdded.sourceMap = result.map;                                         // 133
  }                                                                           // 134
                                                                              // 135
  return toBeAdded;                                                           // 136
};                                                                            // 137
                                                                              // 138
BCp.setDiskCacheDirectory = function (cacheDir) {                             // 139
  Babel.setCacheDir(cacheDir);                                                // 140
};                                                                            // 141
                                                                              // 142
function profile(name, func) {                                                // 143
  if (typeof Profile !== 'undefined') {                                       // 144
    return Profile.time(name, func);                                          // 145
  } else {                                                                    // 146
    return func();                                                            // 147
  }                                                                           // 148
};                                                                            // 149
                                                                              // 150
BCp.inferExtraBabelOptions = function (inputFile, babelOptions, cacheDeps) {  // 151
  if (! inputFile.require ||                                                  // 152
      ! inputFile.findControlFile ||                                          // 153
      ! inputFile.readAndWatchFile) {                                         // 154
    return false;                                                             // 155
  }                                                                           // 156
                                                                              // 157
  return (                                                                    // 158
    // If a .babelrc exists, it takes precedence over package.json.           // 159
    this._inferFromBabelRc(inputFile, babelOptions, cacheDeps) ||             // 160
    this._inferFromPackageJson(inputFile, babelOptions, cacheDeps)            // 161
  );                                                                          // 162
};                                                                            // 163
                                                                              // 164
BCp._inferFromBabelRc = function (inputFile, babelOptions, cacheDeps) {       // 165
  var babelrcPath = inputFile.findControlFile(".babelrc");                    // 166
  if (babelrcPath) {                                                          // 167
    if (! hasOwn.call(this._babelrcCache, babelrcPath)) {                     // 168
      try {                                                                   // 169
        this._babelrcCache[babelrcPath] =                                     // 170
          JSON.parse(inputFile.readAndWatchFile(babelrcPath));                // 171
      } catch (e) {                                                           // 172
        if (e instanceof SyntaxError) {                                       // 173
          e.message = ".babelrc is not a valid JSON file: " + e.message;      // 174
        }                                                                     // 175
                                                                              // 176
        throw e;                                                              // 177
      }                                                                       // 178
    }                                                                         // 179
                                                                              // 180
    return this._inferHelper(                                                 // 181
      inputFile,                                                              // 182
      babelOptions,                                                           // 183
      babelrcPath,                                                            // 184
      this._babelrcCache[babelrcPath],                                        // 185
      cacheDeps                                                               // 186
    );                                                                        // 187
  }                                                                           // 188
};                                                                            // 189
                                                                              // 190
BCp._inferFromPackageJson = function (inputFile, babelOptions, cacheDeps) {   // 191
  var pkgJsonPath = inputFile.findControlFile("package.json");                // 192
  if (pkgJsonPath) {                                                          // 193
    if (! hasOwn.call(this._babelrcCache, pkgJsonPath)) {                     // 194
      this._babelrcCache[pkgJsonPath] = JSON.parse(                           // 195
        inputFile.readAndWatchFile(pkgJsonPath)                               // 196
      ).babel || null;                                                        // 197
    }                                                                         // 198
                                                                              // 199
    return this._inferHelper(                                                 // 200
      inputFile,                                                              // 201
      babelOptions,                                                           // 202
      pkgJsonPath,                                                            // 203
      this._babelrcCache[pkgJsonPath],                                        // 204
      cacheDeps                                                               // 205
    );                                                                        // 206
  }                                                                           // 207
};                                                                            // 208
                                                                              // 209
BCp._inferHelper = function (                                                 // 210
  inputFile,                                                                  // 211
  babelOptions,                                                               // 212
  controlFilePath,                                                            // 213
  babelrc,                                                                    // 214
  cacheDeps                                                                   // 215
) {                                                                           // 216
  if (! babelrc) {                                                            // 217
    return false;                                                             // 218
  }                                                                           // 219
                                                                              // 220
  var compiler = this;                                                        // 221
                                                                              // 222
  function walkBabelRC(obj, path) {                                           // 223
    if (obj && typeof obj === "object") {                                     // 224
      path = path || [];                                                      // 225
      var index = path.push("presets") - 1;                                   // 226
      walkHelper(obj.presets, path);                                          // 227
      path[index] = "plugins";                                                // 228
      walkHelper(obj.plugins, path);                                          // 229
      path.pop();                                                             // 230
    }                                                                         // 231
  }                                                                           // 232
                                                                              // 233
  function walkHelper(list, path) {                                           // 234
    if (list) {                                                               // 235
      // Empty the list and then refill it with resolved values.              // 236
      list.splice(0).forEach(function (pluginOrPreset) {                      // 237
        var res = resolveHelper(pluginOrPreset, path);                        // 238
        if (res) {                                                            // 239
          list.push(res);                                                     // 240
        }                                                                     // 241
      });                                                                     // 242
    }                                                                         // 243
  }                                                                           // 244
                                                                              // 245
  function resolveHelper(value, path) {                                       // 246
    if (value) {                                                              // 247
      if (typeof value === "function") {                                      // 248
        // The value has already been resolved to a plugin function.          // 249
        return value;                                                         // 250
      }                                                                       // 251
                                                                              // 252
      if (Array.isArray(value)) {                                             // 253
        // The value is a [plugin, options] pair.                             // 254
        var res = value[0] = resolveHelper(value[0], path);                   // 255
        if (res) {                                                            // 256
          return value;                                                       // 257
        }                                                                     // 258
                                                                              // 259
      } else if (typeof value === "string") {                                 // 260
        // The value is a string that we need to require.                     // 261
        var result = requireWithPath(value, path);                            // 262
        if (result && result.module) {                                        // 263
          cacheDeps[result.name] = result.version;                            // 264
          walkBabelRC(result.module, path);                                   // 265
          return result.module;                                               // 266
        }                                                                     // 267
                                                                              // 268
      } else if (typeof value === "object") {                                 // 269
        // The value is a { presets?, plugins? } preset object.               // 270
        walkBabelRC(value, path);                                             // 271
        return value;                                                         // 272
      }                                                                       // 273
    }                                                                         // 274
                                                                              // 275
    return null;                                                              // 276
  }                                                                           // 277
                                                                              // 278
  function requireWithPath(id, path) {                                        // 279
    var prefix;                                                               // 280
    var lastInPath = path[path.length - 1];                                   // 281
    if (lastInPath === "presets") {                                           // 282
      prefix = "babel-preset-";                                               // 283
    } else if (lastInPath === "plugins") {                                    // 284
      prefix = "babel-plugin-";                                               // 285
    }                                                                         // 286
                                                                              // 287
    try {                                                                     // 288
      return requireWithPrefix(inputFile, id, prefix, controlFilePath);       // 289
    } catch (e) {                                                             // 290
      if (e.code !== "MODULE_NOT_FOUND") {                                    // 291
        throw e;                                                              // 292
      }                                                                       // 293
                                                                              // 294
      if (! hasOwn.call(compiler._babelrcWarnings, id)) {                     // 295
        compiler._babelrcWarnings[id] = controlFilePath;                      // 296
                                                                              // 297
        console.error(                                                        // 298
          "Warning: unable to resolve " +                                     // 299
            JSON.stringify(id) +                                              // 300
            " in " + path.join(".") +                                         // 301
            " of " + controlFilePath                                          // 302
        );                                                                    // 303
      }                                                                       // 304
                                                                              // 305
      return null;                                                            // 306
    }                                                                         // 307
  }                                                                           // 308
                                                                              // 309
  babelrc = JSON.parse(JSON.stringify(babelrc));                              // 310
                                                                              // 311
  walkBabelRC(babelrc);                                                       // 312
                                                                              // 313
  merge(babelOptions, babelrc, "presets");                                    // 314
  merge(babelOptions, babelrc, "plugins");                                    // 315
                                                                              // 316
  const babelEnv = (process.env.BABEL_ENV ||                                  // 317
                    process.env.NODE_ENV ||                                   // 318
                    "development");                                           // 319
  if (babelrc && babelrc.env && babelrc.env[babelEnv]) {                      // 320
    const env = babelrc.env[babelEnv];                                        // 321
    walkBabelRC(env);                                                         // 322
    merge(babelOptions, env, "presets");                                      // 323
    merge(babelOptions, env, "plugins");                                      // 324
  }                                                                           // 325
                                                                              // 326
  return !! (babelrc.presets ||                                               // 327
             babelrc.plugins);                                                // 328
};                                                                            // 329
                                                                              // 330
function merge(babelOptions, babelrc, name) {                                 // 331
  if (babelrc[name]) {                                                        // 332
    var list = babelOptions[name] || [];                                      // 333
    babelOptions[name] = list;                                                // 334
    list.push.apply(list, babelrc[name]);                                     // 335
  }                                                                           // 336
}                                                                             // 337
                                                                              // 338
function requireWithPrefix(inputFile, id, prefix, controlFilePath) {          // 339
  var isTopLevel = "./".indexOf(id.charAt(0)) < 0;                            // 340
  var presetOrPlugin;                                                         // 341
  var presetOrPluginMeta;                                                     // 342
                                                                              // 343
  if (isTopLevel) {                                                           // 344
    if (! prefix) {                                                           // 345
      throw new Error("missing babelrc prefix");                              // 346
    }                                                                         // 347
                                                                              // 348
    try {                                                                     // 349
      // If the identifier is top-level, try to prefix it with                // 350
      // "babel-plugin-" or "babel-preset-".                                  // 351
      presetOrPlugin = inputFile.require(prefix + id);                        // 352
      presetOrPluginMeta = inputFile.require(                                 // 353
        packageNameFromTopLevelModuleId(prefix + id) + '/package.json');      // 354
    } catch (e) {                                                             // 355
      if (e.code !== "MODULE_NOT_FOUND") {                                    // 356
        throw e;                                                              // 357
      }                                                                       // 358
      // Fall back to requiring the plugin as-is if the prefix failed.        // 359
      presetOrPlugin = inputFile.require(id);                                 // 360
      presetOrPluginMeta = inputFile.require(                                 // 361
        packageNameFromTopLevelModuleId(id) + '/package.json');               // 362
    }                                                                         // 363
                                                                              // 364
  } else {                                                                    // 365
    // If the identifier is not top-level, but relative or absolute,          // 366
    // then it will be required as-is, so that you can implement your         // 367
    // own Babel plugins locally, rather than always using plugins            // 368
    // installed from npm.                                                    // 369
    presetOrPlugin = inputFile.require(id, controlFilePath);                  // 370
                                                                              // 371
    // Note that inputFile.readAndWatchFileWithHash converts module           // 372
    // identifers to OS-specific paths if necessary.                          // 373
    var absId = inputFile.resolve(id, controlFilePath);                       // 374
    var info = inputFile.readAndWatchFileWithHash(absId);                     // 375
                                                                              // 376
    presetOrPluginMeta = {                                                    // 377
      name: absId,                                                            // 378
      version: info.hash                                                      // 379
    };                                                                        // 380
  }                                                                           // 381
                                                                              // 382
  return {                                                                    // 383
    name: presetOrPluginMeta.name,                                            // 384
    version: presetOrPluginMeta.version,                                      // 385
    module: presetOrPlugin.__esModule                                         // 386
      ? presetOrPlugin.default                                                // 387
      : presetOrPlugin                                                        // 388
  };                                                                          // 389
}                                                                             // 390
                                                                              // 391
// 'react-hot-loader/babel' => 'react-hot-loader'                             // 392
function packageNameFromTopLevelModuleId(id) {                                // 393
  return id.split("/", 1)[0];                                                 // 394
}                                                                             // 395
                                                                              // 396
////////////////////////////////////////////////////////////////////////////////

}).call(this);
