(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var global = Package.meteor.global;
var meteorEnv = Package.meteor.meteorEnv;
var ECMAScript = Package.ecmascript.ECMAScript;
var Random = Package.random.Random;
var meteorInstall = Package.modules.meteorInstall;
var meteorBabelHelpers = Package['babel-runtime'].meteorBabelHelpers;
var Promise = Package.promise.Promise;

/* Package-scope variables */
var CachingCompilerBase, CachingCompiler, MultiFileCachingCompiler;

var require = meteorInstall({"node_modules":{"meteor":{"caching-compiler":{"caching-compiler.js":function(require){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                //
// packages/caching-compiler/caching-compiler.js                                                                  //
//                                                                                                                //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                  //
const fs = Plugin.fs;
const path = Plugin.path;

const createHash = Npm.require('crypto').createHash;

const assert = Npm.require('assert');

const Future = Npm.require('fibers/future');

const LRU = Npm.require('lru-cache');

const async = Npm.require('async'); // Base class for CachingCompiler and MultiFileCachingCompiler.


CachingCompilerBase = class CachingCompilerBase {
  constructor({
    compilerName,
    defaultCacheSize,
    maxParallelism = 20
  }) {
    this._compilerName = compilerName;
    this._maxParallelism = maxParallelism;
    const envVarPrefix = 'METEOR_' + compilerName.toUpperCase() + '_CACHE_';
    const debugEnvVar = envVarPrefix + 'DEBUG';
    this._cacheDebugEnabled = !!process.env[debugEnvVar];
    const cacheSizeEnvVar = envVarPrefix + 'SIZE';
    this._cacheSize = +process.env[cacheSizeEnvVar] || defaultCacheSize;
    this._diskCache = null; // For testing.

    this._callCount = 0;
  } // Your subclass must override this method to define the key used to identify
  // a particular version of an InputFile.
  //
  // Given an InputFile (the data type passed to processFilesForTarget as part
  // of the Plugin.registerCompiler API), returns a cache key that represents
  // it. This cache key can be any JSON value (it will be converted internally
  // into a hash).  This should reflect any aspect of the InputFile that affects
  // the output of `compileOneFile`. Typically you'll want to include
  // `inputFile.getDeclaredExports()`, and perhaps
  // `inputFile.getPathInPackage()` or `inputFile.getDeclaredExports` if
  // `compileOneFile` pays attention to them.
  //
  // Note that for MultiFileCachingCompiler, your cache key doesn't need to
  // include the file's path, because that is automatically taken into account
  // by the implementation. CachingCompiler subclasses can choose whether or not
  // to include the file's path in the cache key.


  getCacheKey(inputFile) {
    throw Error('CachingCompiler subclass should implement getCacheKey!');
  } // Your subclass must override this method to define how a CompileResult
  // translates into adding assets to the bundle.
  //
  // This method is given an InputFile (the data type passed to
  // processFilesForTarget as part of the Plugin.registerCompiler API) and a
  // CompileResult (either returned directly from compileOneFile or read from
  // the cache).  It should call methods like `inputFile.addJavaScript`
  // and `inputFile.error`.


  addCompileResult(inputFile, compileResult) {
    throw Error('CachingCompiler subclass should implement addCompileResult!');
  } // Your subclass must override this method to define the size of a
  // CompilerResult (used by the in-memory cache to limit the total amount of
  // data cached).


  compileResultSize(compileResult) {
    throw Error('CachingCompiler subclass should implement compileResultSize!');
  } // Your subclass may override this method to define an alternate way of
  // stringifying CompilerResults.  Takes a CompileResult and returns a string.


  stringifyCompileResult(compileResult) {
    return JSON.stringify(compileResult);
  } // Your subclass may override this method to define an alternate way of
  // parsing CompilerResults from string.  Takes a string and returns a
  // CompileResult.  If the string doesn't represent a valid CompileResult, you
  // may want to return null instead of throwing, which will make
  // CachingCompiler ignore the cache.


  parseCompileResult(stringifiedCompileResult) {
    return this._parseJSONOrNull(stringifiedCompileResult);
  }

  _parseJSONOrNull(json) {
    try {
      return JSON.parse(json);
    } catch (e) {
      if (e instanceof SyntaxError) return null;
      throw e;
    }
  }

  _cacheDebug(message) {
    if (!this._cacheDebugEnabled) return;
    console.log(`CACHE(${this._compilerName}): ${message}`);
  }

  setDiskCacheDirectory(diskCache) {
    if (this._diskCache) throw Error('setDiskCacheDirectory called twice?');
    this._diskCache = diskCache;
  } // Since so many compilers will need to calculate the size of a SourceMap in
  // their compileResultSize, this method is provided.


  sourceMapSize(sm) {
    if (!sm) return 0; // sum the length of sources and the mappings, the size of
    // metadata is ignored, but it is not a big deal

    return sm.mappings.length + (sm.sourcesContent || []).reduce(function (soFar, current) {
      return soFar + (current ? current.length : 0);
    }, 0);
  } // Borrowed from another MIT-licensed project that benjamn wrote:
  // https://github.com/reactjs/commoner/blob/235d54a12c/lib/util.js#L136-L168


  _deepHash(val) {
    const hash = createHash('sha1');
    let type = typeof val;

    if (val === null) {
      type = 'null';
    }

    hash.update(type + '\0');

    switch (type) {
      case 'object':
        const keys = Object.keys(val); // Array keys will already be sorted.

        if (!Array.isArray(val)) {
          keys.sort();
        }

        keys.forEach(key => {
          if (typeof val[key] === 'function') {
            // Silently ignore nested methods, but nevertheless complain below
            // if the root value is a function.
            return;
          }

          hash.update(key + '\0').update(this._deepHash(val[key]));
        });
        break;

      case 'function':
        assert.ok(false, 'cannot hash function objects');
        break;

      default:
        hash.update('' + val);
        break;
    }

    return hash.digest('hex');
  } // We want to write the file atomically. But we also don't want to block
  // processing on the file write.


  _writeFileAsync(filename, contents) {
    const tempFilename = filename + '.tmp.' + Random.id();

    if (this._cacheDebugEnabled) {
      // Write cache file synchronously when cache debugging enabled.
      try {
        fs.writeFileSync(tempFilename, contents);
        fs.renameSync(tempFilename, filename);
      } catch (e) {// ignore errors, it's just a cache
      }
    } else {
      fs.writeFile(tempFilename, contents, err => {
        // ignore errors, it's just a cache
        if (!err) {
          fs.rename(tempFilename, filename, err => {});
        }
      });
    }
  } // Helper function. Returns the body of the file as a string, or null if it
  // doesn't exist.


  _readFileOrNull(filename) {
    try {
      return fs.readFileSync(filename, 'utf8');
    } catch (e) {
      if (e && e.code === 'ENOENT') return null;
      throw e;
    }
  }

}; // CachingCompiler is a class designed to be used with Plugin.registerCompiler
// which implements in-memory and on-disk caches for the files that it
// processes.  You should subclass CachingCompiler and define the following
// methods: getCacheKey, compileOneFile, addCompileResult, and
// compileResultSize.
//
// CachingCompiler assumes that files are processed independently of each other;
// there is no 'import' directive allowing one file to reference another.  That
// is, editing one file should only require that file to be rebuilt, not other
// files.
//
// The data that is cached for each file is of a type that is (implicitly)
// defined by your subclass. CachingCompiler refers to this type as
// `CompileResult`, but this isn't a single type: it's up to your subclass to
// decide what type of data this is.  You should document what your subclass's
// CompileResult type is.
//
// Your subclass's compiler should call the superclass compiler specifying the
// compiler name (used to generate environment variables for debugging and
// tweaking in-memory cache size) and the default cache size.
//
// By default, CachingCompiler processes each file in "parallel". That is, if it
// needs to yield to read from the disk cache, or if getCacheKey,
// compileOneFile, or addCompileResult yields, it will start processing the next
// few files. To set how many files can be processed in parallel (including
// setting it to 1 if your subclass doesn't support any parallelism), pass the
// maxParallelism option to the superclass constructor.
//
// For example (using ES2015 via the ecmascript package):
//
//   class AwesomeCompiler extends CachingCompiler {
//     constructor() {
//       super({
//         compilerName: 'awesome',
//         defaultCacheSize: 1024*1024*10,
//       });
//     }
//     // ... define the other methods
//   }
//   Plugin.registerCompile({
//     extensions: ['awesome'],
//   }, () => new AwesomeCompiler());
//
// XXX maybe compileResultSize and stringifyCompileResult should just be methods
// on CompileResult? Sort of hard to do that with parseCompileResult.

CachingCompiler = class CachingCompiler extends CachingCompilerBase {
  constructor({
    compilerName,
    defaultCacheSize,
    maxParallelism = 20
  }) {
    super({
      compilerName,
      defaultCacheSize,
      maxParallelism
    }); // Maps from a hashed cache key to a compileResult.

    this._cache = new LRU({
      max: this._cacheSize,
      length: value => this.compileResultSize(value)
    });
  } // Your subclass must override this method to define the transformation from
  // InputFile to its cacheable CompileResult).
  //
  // Given an InputFile (the data type passed to processFilesForTarget as part
  // of the Plugin.registerCompiler API), compiles the file and returns a
  // CompileResult (the cacheable data type specific to your subclass).
  //
  // This method is not called on files when a valid cache entry exists in
  // memory or on disk.
  //
  // On a compile error, you should call `inputFile.error` appropriately and
  // return null; this will not be cached.
  //
  // This method should not call `inputFile.addJavaScript` and similar files!
  // That's what addCompileResult is for.


  compileOneFile(inputFile) {
    throw Error('CachingCompiler subclass should implement compileOneFile!');
  } // The processFilesForTarget method from the Plugin.registerCompiler API. If
  // you have processing you want to perform at the beginning or end of a
  // processing phase, you may want to override this method and call the
  // superclass implementation from within your method.


  processFilesForTarget(inputFiles) {
    const cacheMisses = [];
    const future = new Future();
    async.eachLimit(inputFiles, this._maxParallelism, (inputFile, cb) => {
      let error = null;

      try {
        const cacheKey = this._deepHash(this.getCacheKey(inputFile));

        let compileResult = this._cache.get(cacheKey);

        if (!compileResult) {
          compileResult = this._readCache(cacheKey);

          if (compileResult) {
            this._cacheDebug(`Loaded ${inputFile.getDisplayPath()}`);
          }
        }

        if (!compileResult) {
          cacheMisses.push(inputFile.getDisplayPath());
          compileResult = this.compileOneFile(inputFile);

          if (!compileResult) {
            // compileOneFile should have called inputFile.error.
            //  We don't cache failures for now.
            return;
          } // Save what we've compiled.


          this._cache.set(cacheKey, compileResult);

          this._writeCacheAsync(cacheKey, compileResult);
        }

        this.addCompileResult(inputFile, compileResult);
      } catch (e) {
        error = e;
      } finally {
        cb(error);
      }
    }, future.resolver());
    future.wait();

    if (this._cacheDebugEnabled) {
      cacheMisses.sort();

      this._cacheDebug(`Ran (#${++this._callCount}) on: ${JSON.stringify(cacheMisses)}`);
    }
  }

  _cacheFilename(cacheKey) {
    // We want cacheKeys to be hex so that they work on any FS and never end in
    // .cache.
    if (!/^[a-f0-9]+$/.test(cacheKey)) {
      throw Error('bad cacheKey: ' + cacheKey);
    }

    return path.join(this._diskCache, cacheKey + '.cache');
  } // Load a cache entry from disk. Returns the compileResult object
  // and loads it into the in-memory cache too.


  _readCache(cacheKey) {
    if (!this._diskCache) {
      return null;
    }

    const cacheFilename = this._cacheFilename(cacheKey);

    const compileResult = this._readAndParseCompileResultOrNull(cacheFilename);

    if (!compileResult) {
      return null;
    }

    this._cache.set(cacheKey, compileResult);

    return compileResult;
  }

  _writeCacheAsync(cacheKey, compileResult) {
    if (!this._diskCache) return;

    const cacheFilename = this._cacheFilename(cacheKey);

    const cacheContents = this.stringifyCompileResult(compileResult);

    this._writeFileAsync(cacheFilename, cacheContents);
  } // Returns null if the file does not exist or can't be parsed; otherwise
  // returns the parsed compileResult in the file.


  _readAndParseCompileResultOrNull(filename) {
    const raw = this._readFileOrNull(filename);

    return this.parseCompileResult(raw);
  }

};
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

},"multi-file-caching-compiler.js":function(require){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                //
// packages/caching-compiler/multi-file-caching-compiler.js                                                       //
//                                                                                                                //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                  //
const path = Plugin.path;

const Future = Npm.require('fibers/future');

const LRU = Npm.require('lru-cache');

const async = Npm.require('async'); // MultiFileCachingCompiler is like CachingCompiler, but for implementing
// languages which allow files to reference each other, such as CSS
// preprocessors with `@import` directives.
//
// Like CachingCompiler, you should subclass MultiFileCachingCompiler and define
// the following methods: getCacheKey, compileOneFile, addCompileResult, and
// compileResultSize.  compileOneFile gets an additional allFiles argument and
// returns an array of referenced import paths in addition to the CompileResult.
// You may also override isRoot and getAbsoluteImportPath to customize
// MultiFileCachingCompiler further.


MultiFileCachingCompiler = class MultiFileCachingCompiler extends CachingCompilerBase {
  constructor({
    compilerName,
    defaultCacheSize,
    maxParallelism
  }) {
    super({
      compilerName,
      defaultCacheSize,
      maxParallelism
    }); // Maps from absolute import path to { compileResult, cacheKeys }, where
    // cacheKeys is an object mapping from absolute import path to hashed
    // cacheKey for each file referenced by this file (including itself).

    this._cache = new LRU({
      max: this._cacheSize,
      // We ignore the size of cacheKeys here.
      length: value => this.compileResultSize(value.compileResult)
    });
  } // Your subclass must override this method to define the transformation from
  // InputFile to its cacheable CompileResult).
  //
  // Arguments:
  //   - inputFile is the InputFile to process
  //   - allFiles is a a Map mapping from absolute import path to InputFile of
  //     all files being processed in the target
  // Returns an object with keys:
  //   - compileResult: the CompileResult (the cacheable data type specific to
  //     your subclass).
  //   - referencedImportPaths: an array of absolute import paths of files
  //     which were refererenced by the current file.  The current file
  //     is included implicitly.
  //
  // This method is not called on files when a valid cache entry exists in
  // memory or on disk.
  //
  // On a compile error, you should call `inputFile.error` appropriately and
  // return null; this will not be cached.
  //
  // This method should not call `inputFile.addJavaScript` and similar files!
  // That's what addCompileResult is for.


  compileOneFile(inputFile, allFiles) {
    throw Error('MultiFileCachingCompiler subclass should implement compileOneFile!');
  } // Your subclass may override this to declare that a file is not a "root" ---
  // ie, it can be included from other files but is not processed on its own. In
  // this case, MultiFileCachingCompiler won't waste time trying to look for a
  // cache for its compilation on disk.


  isRoot(inputFile) {
    return true;
  } // Returns the absolute import path for an InputFile. By default, this is a
  // path is a path of the form "{package}/path/to/file" for files in packages
  // and "{}/path/to/file" for files in apps. Your subclass may override and/or
  // call this method.


  getAbsoluteImportPath(inputFile) {
    if (inputFile.getPackageName() === null) {
      return '{}/' + inputFile.getPathInPackage();
    }

    return '{' + inputFile.getPackageName() + '}/' + inputFile.getPathInPackage();
  } // The processFilesForTarget method from the Plugin.registerCompiler API.


  processFilesForTarget(inputFiles) {
    const allFiles = new Map();
    const cacheKeyMap = new Map();
    const cacheMisses = [];
    inputFiles.forEach(inputFile => {
      const importPath = this.getAbsoluteImportPath(inputFile);
      allFiles.set(importPath, inputFile);
      cacheKeyMap.set(importPath, this._deepHash(this.getCacheKey(inputFile)));
    });
    const allProcessedFuture = new Future();
    async.eachLimit(inputFiles, this._maxParallelism, (inputFile, cb) => {
      let error = null;

      try {
        // If this isn't a root, skip it (and definitely don't waste time
        // looking for a cache file that won't be there).
        if (!this.isRoot(inputFile)) {
          return;
        }

        const absoluteImportPath = this.getAbsoluteImportPath(inputFile);

        let cacheEntry = this._cache.get(absoluteImportPath);

        if (!cacheEntry) {
          cacheEntry = this._readCache(absoluteImportPath);

          if (cacheEntry) {
            this._cacheDebug(`Loaded ${absoluteImportPath}`);
          }
        }

        if (!(cacheEntry && this._cacheEntryValid(cacheEntry, cacheKeyMap))) {
          cacheMisses.push(inputFile.getDisplayPath());
          const compileOneFileReturn = this.compileOneFile(inputFile, allFiles);

          if (!compileOneFileReturn) {
            // compileOneFile should have called inputFile.error.
            //  We don't cache failures for now.
            return;
          }

          const {
            compileResult,
            referencedImportPaths
          } = compileOneFileReturn;
          cacheEntry = {
            compileResult,
            cacheKeys: {
              // Include the hashed cache key of the file itself...
              [absoluteImportPath]: cacheKeyMap.get(absoluteImportPath)
            }
          }; // ... and of the other referenced files.

          referencedImportPaths.forEach(path => {
            if (!cacheKeyMap.has(path)) {
              throw Error(`Unknown absolute import path ${path}`);
            }

            cacheEntry.cacheKeys[path] = cacheKeyMap.get(path);
          }); // Save the cache entry.

          this._cache.set(absoluteImportPath, cacheEntry);

          this._writeCacheAsync(absoluteImportPath, cacheEntry);
        }

        this.addCompileResult(inputFile, cacheEntry.compileResult);
      } catch (e) {
        error = e;
      } finally {
        cb(error);
      }
    }, allProcessedFuture.resolver());
    allProcessedFuture.wait();

    if (this._cacheDebugEnabled) {
      cacheMisses.sort();

      this._cacheDebug(`Ran (#${++this._callCount}) on: ${JSON.stringify(cacheMisses)}`);
    }
  }

  _cacheEntryValid(cacheEntry, cacheKeyMap) {
    return Object.keys(cacheEntry.cacheKeys).every(path => cacheEntry.cacheKeys[path] === cacheKeyMap.get(path));
  } // The format of a cache file on disk is the JSON-stringified cacheKeys
  // object, a newline, followed by the CompileResult as returned from
  // this.stringifyCompileResult.


  _cacheFilename(absoluteImportPath) {
    return path.join(this._diskCache, this._deepHash(absoluteImportPath) + '.cache');
  } // Loads a {compileResult, cacheKeys} cache entry from disk. Returns the whole
  // cache entry and loads it into the in-memory cache too.


  _readCache(absoluteImportPath) {
    if (!this._diskCache) {
      return null;
    }

    const cacheFilename = this._cacheFilename(absoluteImportPath);

    const raw = this._readFileOrNull(cacheFilename);

    if (!raw) {
      return null;
    } // Split on newline.


    const newlineIndex = raw.indexOf('\n');

    if (newlineIndex === -1) {
      return null;
    }

    const cacheKeysString = raw.substring(0, newlineIndex);
    const compileResultString = raw.substring(newlineIndex + 1);

    const cacheKeys = this._parseJSONOrNull(cacheKeysString);

    if (!cacheKeys) {
      return null;
    }

    const compileResult = this.parseCompileResult(compileResultString);

    if (!compileResult) {
      return null;
    }

    const cacheEntry = {
      compileResult,
      cacheKeys
    };

    this._cache.set(absoluteImportPath, cacheEntry);

    return cacheEntry;
  }

  _writeCacheAsync(absoluteImportPath, cacheEntry) {
    if (!this._diskCache) {
      return null;
    }

    const cacheFilename = this._cacheFilename(absoluteImportPath);

    const cacheContents = JSON.stringify(cacheEntry.cacheKeys) + '\n' + this.stringifyCompileResult(cacheEntry.compileResult);

    this._writeFileAsync(cacheFilename, cacheContents);
  }

};
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}}}}},{
  "extensions": [
    ".js",
    ".json"
  ]
});
require("./node_modules/meteor/caching-compiler/caching-compiler.js");
require("./node_modules/meteor/caching-compiler/multi-file-caching-compiler.js");

/* Exports */
if (typeof Package === 'undefined') Package = {};
(function (pkg, symbols) {
  for (var s in symbols)
    (s in pkg) || (pkg[s] = symbols[s]);
})(Package['caching-compiler'] = {}, {
  CachingCompiler: CachingCompiler,
  MultiFileCachingCompiler: MultiFileCachingCompiler
});

})();




//# sourceURL=meteor://💻app/packages/caching-compiler.js


//# sourceMappingURL=caching-compiler.js.map
