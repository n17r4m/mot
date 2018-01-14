(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/datatypes.js                                                    //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
ConstraintSolver = {};                                                                        // 1
                                                                                              // 2
var PV = PackageVersion;                                                                      // 3
var CS = ConstraintSolver;                                                                    // 4
                                                                                              // 5
////////// PackageAndVersion                                                                  // 6
                                                                                              // 7
// An ordered pair of (package, version).                                                     // 8
CS.PackageAndVersion = function (pkg, version) {                                              // 9
  check(pkg, String);                                                                         // 10
  check(version, String);                                                                     // 11
                                                                                              // 12
  this.package = pkg;                                                                         // 13
  this.version = version;                                                                     // 14
};                                                                                            // 15
                                                                                              // 16
// The string form of a PackageAndVersion is "package version",                               // 17
// for example "foo 1.0.1".  The reason we don't use an "@" is                                // 18
// it would look too much like a PackageConstraint.                                           // 19
CS.PackageAndVersion.prototype.toString = function () {                                       // 20
  return this.package + " " + this.version;                                                   // 21
};                                                                                            // 22
                                                                                              // 23
CS.PackageAndVersion.fromString = function (str) {                                            // 24
  var parts = str.split(' ');                                                                 // 25
  if (parts.length === 2 && parts[0] && parts[1]) {                                           // 26
    return new CS.PackageAndVersion(parts[0], parts[1]);                                      // 27
  } else {                                                                                    // 28
    throw new Error("Malformed PackageAndVersion: " + str);                                   // 29
  }                                                                                           // 30
};                                                                                            // 31
                                                                                              // 32
////////// Dependency                                                                         // 33
                                                                                              // 34
// A Dependency consists of a PackageConstraint (like "foo@=1.2.3")                           // 35
// and flags, like "isWeak".                                                                  // 36
                                                                                              // 37
CS.Dependency = function (packageConstraint, flags) {                                         // 38
  if (typeof packageConstraint !== 'string') {                                                // 39
    // this `if` is because Match.OneOf is really, really slow when it fails                  // 40
    check(packageConstraint, Match.OneOf(PV.PackageConstraint, String));                      // 41
  }                                                                                           // 42
  if (typeof packageConstraint === 'string') {                                                // 43
    packageConstraint = PV.parsePackageConstraint(packageConstraint);                         // 44
  }                                                                                           // 45
  if (flags) {                                                                                // 46
    check(flags, Object);                                                                     // 47
  }                                                                                           // 48
                                                                                              // 49
  this.packageConstraint = packageConstraint;                                                 // 50
  this.isWeak = false;                                                                        // 51
                                                                                              // 52
  if (flags) {                                                                                // 53
    if (flags.isWeak) {                                                                       // 54
      this.isWeak = true;                                                                     // 55
    }                                                                                         // 56
  }                                                                                           // 57
};                                                                                            // 58
                                                                                              // 59
// The string form of a Dependency is `?foo@1.0.0` for a weak                                 // 60
// reference to package "foo" with VersionConstraint "1.0.0".                                 // 61
CS.Dependency.prototype.toString = function () {                                              // 62
  var ret = this.packageConstraint.toString();                                                // 63
  if (this.isWeak) {                                                                          // 64
    ret = '?' + ret;                                                                          // 65
  }                                                                                           // 66
  return ret;                                                                                 // 67
};                                                                                            // 68
                                                                                              // 69
CS.Dependency.fromString = function (str) {                                                   // 70
  var isWeak = false;                                                                         // 71
                                                                                              // 72
  if (str.charAt(0) === '?') {                                                                // 73
    isWeak = true;                                                                            // 74
    str = str.slice(1);                                                                       // 75
  }                                                                                           // 76
                                                                                              // 77
  var flags = isWeak ? { isWeak: true } : null;                                               // 78
                                                                                              // 79
  return new CS.Dependency(str, flags);                                                       // 80
};                                                                                            // 81
                                                                                              // 82
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/catalog-cache.js                                                //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
var CS = ConstraintSolver;                                                                    // 1
var PV = PackageVersion;                                                                      // 2
                                                                                              // 3
var pvkey = function (pkg, version) {                                                         // 4
  return pkg + " " + version;                                                                 // 5
};                                                                                            // 6
                                                                                              // 7
// Stores the Dependencies for each known PackageAndVersion.                                  // 8
CS.CatalogCache = function () {                                                               // 9
  // String(PackageAndVersion) -> String -> Dependency.                                       // 10
  // For example, "foo 1.0.0" -> "bar" -> Dependency.fromString("?bar@1.0.2").                // 11
  this._dependencies = {};                                                                    // 12
  // A map derived from the keys of _dependencies, for ease of iteration.                     // 13
  // "foo" -> ["1.0.0", ...]                                                                  // 14
  // Versions in the array are unique but not sorted, unless the `.sorted`                    // 15
  // property is set on the array.  The array is never empty.                                 // 16
  this._versions = {};                                                                        // 17
};                                                                                            // 18
                                                                                              // 19
CS.CatalogCache.prototype.hasPackageVersion = function (pkg, version) {                       // 20
  return _.has(this._dependencies, pvkey(pkg, version));                                      // 21
};                                                                                            // 22
                                                                                              // 23
CS.CatalogCache.prototype.addPackageVersion = function (p, v, deps) {                         // 24
  check(p, String);                                                                           // 25
  check(v, String);                                                                           // 26
  // `deps` must not have any duplicate values of `.packageConstraint.package`                // 27
  check(deps, [CS.Dependency]);                                                               // 28
                                                                                              // 29
  var key = pvkey(p, v);                                                                      // 30
  if (_.has(this._dependencies, key)) {                                                       // 31
    throw new Error("Already have an entry for " + key);                                      // 32
  }                                                                                           // 33
                                                                                              // 34
  if (! _.has(this._versions, p)) {                                                           // 35
    this._versions[p] = [];                                                                   // 36
  }                                                                                           // 37
  this._versions[p].push(v);                                                                  // 38
  this._versions[p].sorted = false;                                                           // 39
                                                                                              // 40
  var depsByPackage = {};                                                                     // 41
  this._dependencies[key] = depsByPackage;                                                    // 42
  _.each(deps, function (d) {                                                                 // 43
    var p2 = d.packageConstraint.package;                                                     // 44
    if (_.has(depsByPackage, p2)) {                                                           // 45
      throw new Error("Can't have two dependencies on " + p2 +                                // 46
                      " in " + key);                                                          // 47
    }                                                                                         // 48
    depsByPackage[p2] = d;                                                                    // 49
  });                                                                                         // 50
};                                                                                            // 51
                                                                                              // 52
// Returns the dependencies of a (package, version), stored in a map.                         // 53
// The values are Dependency objects; the key for `d` is                                      // 54
// `d.packageConstraint.package`.  (Don't mutate the map.)                                    // 55
CS.CatalogCache.prototype.getDependencyMap = function (p, v) {                                // 56
  var key = pvkey(p, v);                                                                      // 57
  if (! _.has(this._dependencies, key)) {                                                     // 58
    throw new Error("No entry for " + key);                                                   // 59
  }                                                                                           // 60
  return this._dependencies[key];                                                             // 61
};                                                                                            // 62
                                                                                              // 63
// Returns an array of version strings, sorted, possibly empty.                               // 64
// (Don't mutate the result.)                                                                 // 65
CS.CatalogCache.prototype.getPackageVersions = function (pkg) {                               // 66
  var result = (_.has(this._versions, pkg) ?                                                  // 67
                this._versions[pkg] : []);                                                    // 68
  if ((!result.length) || result.sorted) {                                                    // 69
    return result;                                                                            // 70
  } else {                                                                                    // 71
    // sort in place, and record so that we don't sort redundantly                            // 72
    // (we'll sort again if more versions are pushed onto the array)                          // 73
    var pvParse = _.memoize(PV.parse);                                                        // 74
    result.sort(function (a, b) {                                                             // 75
      return PV.compare(pvParse(a), pvParse(b));                                              // 76
    });                                                                                       // 77
    result.sorted = true;                                                                     // 78
    return result;                                                                            // 79
  }                                                                                           // 80
};                                                                                            // 81
                                                                                              // 82
CS.CatalogCache.prototype.hasPackage = function (pkg) {                                       // 83
  return _.has(this._versions, pkg);                                                          // 84
};                                                                                            // 85
                                                                                              // 86
CS.CatalogCache.prototype.toJSONable = function () {                                          // 87
  var self = this;                                                                            // 88
  var data = {};                                                                              // 89
  _.each(self._dependencies, function (depsByPackage, key) {                                  // 90
    // depsByPackage is a map of String -> Dependency.                                        // 91
    // Map over the values to get an array of String.                                         // 92
    data[key] = _.map(depsByPackage, function (dep) {                                         // 93
      return dep.toString();                                                                  // 94
    });                                                                                       // 95
  });                                                                                         // 96
  return { data: data };                                                                      // 97
};                                                                                            // 98
                                                                                              // 99
CS.CatalogCache.fromJSONable = function (obj) {                                               // 100
  check(obj, { data: Object });                                                               // 101
                                                                                              // 102
  var cache = new CS.CatalogCache();                                                          // 103
  _.each(obj.data, function (depsArray, pv) {                                                 // 104
    check(depsArray, [String]);                                                               // 105
    pv = CS.PackageAndVersion.fromString(pv);                                                 // 106
    cache.addPackageVersion(                                                                  // 107
      pv.package, pv.version,                                                                 // 108
      _.map(depsArray, function (str) {                                                       // 109
        return CS.Dependency.fromString(str);                                                 // 110
      }));                                                                                    // 111
  });                                                                                         // 112
  return cache;                                                                               // 113
};                                                                                            // 114
                                                                                              // 115
// Calls `iter` on each PackageAndVersion, with the second argument being                     // 116
// a map from package name to Dependency.  If `iter` returns true,                            // 117
// iteration is stopped.  There's no particular order to the iteration.                       // 118
CS.CatalogCache.prototype.eachPackageVersion = function (iter) {                              // 119
  var self = this;                                                                            // 120
  _.find(self._dependencies, function (value, key) {                                          // 121
    var stop = iter(CS.PackageAndVersion.fromString(key), value);                             // 122
    return stop;                                                                              // 123
  });                                                                                         // 124
};                                                                                            // 125
                                                                                              // 126
// Calls `iter` on each package name, with the second argument being                          // 127
// a list of versions present for that package (unique and sorted).                           // 128
// If `iter` returns true, iteration is stopped.                                              // 129
ConstraintSolver.CatalogCache.prototype.eachPackage = function (iter) {                       // 130
  var self = this;                                                                            // 131
  _.find(_.keys(self._versions), function (key) {                                             // 132
    var stop = iter(key, self.getPackageVersions(key));                                       // 133
    return stop;                                                                              // 134
  });                                                                                         // 135
};                                                                                            // 136
                                                                                              // 137
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/catalog-loader.js                                               //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
var PV = PackageVersion;                                                                      // 1
var CS = ConstraintSolver;                                                                    // 2
                                                                                              // 3
// A CatalogLoader does the work of populating a CatalogCache from the                        // 4
// Catalog.  When you run a unit test with canned Catalog data, there is                      // 5
// a CatalogCache but no CatalogLoader.                                                       // 6
//                                                                                            // 7
// CatalogLoader acts as a minor cache layer between CatalogCache and                         // 8
// the Catalog, because going to the Catalog generally means going to                         // 9
// SQLite, i.e. disk, while caching a version in the CatalogCache means                       // 10
// that it is available to the solver.  CatalogLoader's private cache                         // 11
// allows it to over-read from the Catalog so that it can mediate                             // 12
// between the granularity provided by the Catalog and the versions                           // 13
// requested by the solver.                                                                   // 14
//                                                                                            // 15
// We rely on the following `catalog` methods:                                                // 16
//                                                                                            // 17
// * getSortedVersionRecords(packageName) ->                                                  // 18
//     [{packageName, version, dependencies}]                                                 // 19
//                                                                                            // 20
//   Where `dependencies` is a map from packageName to                                        // 21
//   an object of the form `{ constraint: String|null,                                        // 22
//   references: [{arch: String, optional "weak": true}] }`.                                  // 23
//                                                                                            // 24
// * getVersion(packageName, version) ->                                                      // 25
//   {packageName, version, dependencies}                                                     // 26
                                                                                              // 27
CS.CatalogLoader = function (fromCatalog, toCatalogCache) {                                   // 28
  var self = this;                                                                            // 29
                                                                                              // 30
  self.catalog = fromCatalog;                                                                 // 31
  self.catalogCache = toCatalogCache;                                                         // 32
                                                                                              // 33
  self._sortedVersionRecordsCache = {};                                                       // 34
};                                                                                            // 35
                                                                                              // 36
var convertDeps = function (catalogDeps) {                                                    // 37
  return _.map(catalogDeps, function (dep, pkg) {                                             // 38
    // The dependency is strong if any of its "references"                                    // 39
    // (for different architectures) are strong.                                              // 40
    var isStrong = _.any(dep.references, function (ref) {                                     // 41
      return !ref.weak;                                                                       // 42
    });                                                                                       // 43
                                                                                              // 44
    var constraint = (dep.constraint || null);                                                // 45
                                                                                              // 46
    return new CS.Dependency(new PV.PackageConstraint(pkg, constraint),                       // 47
                             isStrong ? null : {isWeak: true});                               // 48
  });                                                                                         // 49
};                                                                                            // 50
                                                                                              // 51
// Since we don't fetch different versions of a package independently                         // 52
// at the moment, this helper is where we get our data.                                       // 53
CS.CatalogLoader.prototype._getSortedVersionRecords = function (pkg) {                        // 54
  if (! _.has(this._sortedVersionRecordsCache, pkg)) {                                        // 55
    this._sortedVersionRecordsCache[pkg] =                                                    // 56
      this.catalog.getSortedVersionRecords(pkg);                                              // 57
  }                                                                                           // 58
                                                                                              // 59
  return this._sortedVersionRecordsCache[pkg];                                                // 60
};                                                                                            // 61
                                                                                              // 62
CS.CatalogLoader.prototype.loadSingleVersion = function (pkg, version) {                      // 63
  var self = this;                                                                            // 64
  var cache = self.catalogCache;                                                              // 65
  if (! cache.hasPackageVersion(pkg, version)) {                                              // 66
    var rec;                                                                                  // 67
    if (_.has(self._sortedVersionRecordsCache, pkg)) {                                        // 68
      rec = _.find(self._sortedVersionRecordsCache[pkg],                                      // 69
                   function (r) {                                                             // 70
                     return r.version === version;                                            // 71
                   });                                                                        // 72
    } else {                                                                                  // 73
      rec = self.catalog.getVersion(pkg, version);                                            // 74
    }                                                                                         // 75
    if (rec) {                                                                                // 76
      var deps = convertDeps(rec.dependencies);                                               // 77
      cache.addPackageVersion(pkg, version, deps);                                            // 78
    }                                                                                         // 79
  }                                                                                           // 80
};                                                                                            // 81
                                                                                              // 82
CS.CatalogLoader.prototype.loadAllVersions = function (pkg) {                                 // 83
  var self = this;                                                                            // 84
  var cache = self.catalogCache;                                                              // 85
  var versionRecs = self._getSortedVersionRecords(pkg);                                       // 86
  _.each(versionRecs, function (rec) {                                                        // 87
    var version = rec.version;                                                                // 88
    if (! cache.hasPackageVersion(pkg, version)) {                                            // 89
      var deps = convertDeps(rec.dependencies);                                               // 90
      cache.addPackageVersion(pkg, version, deps);                                            // 91
    }                                                                                         // 92
  });                                                                                         // 93
};                                                                                            // 94
                                                                                              // 95
// Takes an array of package names.  Loads all versions of them and their                     // 96
// (strong) dependencies.                                                                     // 97
CS.CatalogLoader.prototype.loadAllVersionsRecursive = function (packageList) {                // 98
  var self = this;                                                                            // 99
                                                                                              // 100
  // Within a call to loadAllVersionsRecursive, we only visit each package                    // 101
  // at most once.  If we visit a package we've already loaded, it will                       // 102
  // lead to a quick scan through the versions in our cache to make sure                      // 103
  // they have been loaded into the CatalogCache.                                             // 104
  var loadQueue = [];                                                                         // 105
  var packagesEverEnqueued = {};                                                              // 106
                                                                                              // 107
  var enqueue = function (pkg) {                                                              // 108
    if (! _.has(packagesEverEnqueued, pkg)) {                                                 // 109
      packagesEverEnqueued[pkg] = true;                                                       // 110
      loadQueue.push(pkg);                                                                    // 111
    }                                                                                         // 112
  };                                                                                          // 113
                                                                                              // 114
  _.each(packageList, enqueue);                                                               // 115
                                                                                              // 116
  while (loadQueue.length) {                                                                  // 117
    var pkg = loadQueue.pop();                                                                // 118
    self.loadAllVersions(pkg);                                                                // 119
    _.each(self.catalogCache.getPackageVersions(pkg), function (v) {                          // 120
      var depMap = self.catalogCache.getDependencyMap(pkg, v);                                // 121
      _.each(depMap, function (dep, package2) {                                               // 122
        enqueue(package2);                                                                    // 123
      });                                                                                     // 124
    });                                                                                       // 125
  }                                                                                           // 126
};                                                                                            // 127
                                                                                              // 128
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/constraint-solver-input.js                                      //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
var PV = PackageVersion;                                                                      // 1
var CS = ConstraintSolver;                                                                    // 2
                                                                                              // 3
// `check` can be really slow, so this line is a valve that makes it                          // 4
// easy to turn off when debugging performance problems.                                      // 5
var _check = check;                                                                           // 6
                                                                                              // 7
// The "Input" object completely specifies the input to the resolver,                         // 8
// and it holds the data loaded from the Catalog as well.  It can be                          // 9
// serialized to JSON and read back in for testing purposes.                                  // 10
CS.Input = function (dependencies, constraints, catalogCache, options) {                      // 11
  var self = this;                                                                            // 12
  options = options || {};                                                                    // 13
                                                                                              // 14
  // PackageConstraints passed in from the tool to us (where we are a                         // 15
  // uniloaded package) will have constructors that we don't recognize                        // 16
  // because they come from a different copy of package-version-parser!                       // 17
  // Convert them to our PackageConstraint class if necessary.  (This is                      // 18
  // just top-level constraints from .meteor/packages or running from                         // 19
  // checkout, so it's not a lot of data.)                                                    // 20
  constraints = _.map(constraints, function (c) {                                             // 21
    if (c instanceof PV.PackageConstraint) {                                                  // 22
      return c;                                                                               // 23
    } else {                                                                                  // 24
      return PV.parsePackageConstraint(c.package, c.constraintString);                        // 25
    }                                                                                         // 26
  });                                                                                         // 27
                                                                                              // 28
  // Note that `dependencies` and `constraints` are required (you can't                       // 29
  // omit them or pass null), while the other properties have defaults.                       // 30
  self.dependencies = dependencies;                                                           // 31
  self.constraints = constraints;                                                             // 32
  // If you add a property, make sure you add it to:                                          // 33
  // - The `check` statements below                                                           // 34
  // - toJSONable (this file)                                                                 // 35
  // - fromJSONable (this file)                                                               // 36
  // - the "input serialization" test in constraint-solver-tests.js                           // 37
  // If it's an option passed in from the tool, you'll also have to                           // 38
  // add it to CS.PackagesResolver#resolve.                                                   // 39
  self.upgrade = options.upgrade || [];                                                       // 40
  self.anticipatedPrereleases = options.anticipatedPrereleases || {};                         // 41
  self.previousSolution = options.previousSolution || null;                                   // 42
  self.allowIncompatibleUpdate = options.allowIncompatibleUpdate || false;                    // 43
  self.upgradeIndirectDepPatchVersions =                                                      // 44
    options.upgradeIndirectDepPatchVersions || false;                                         // 45
                                                                                              // 46
  _check(self.dependencies, [String]);                                                        // 47
  _check(self.constraints, [PV.PackageConstraint]);                                           // 48
  _check(self.upgrade, [String]);                                                             // 49
  _check(self.anticipatedPrereleases,                                                         // 50
        Match.ObjectWithValues(Match.ObjectWithValues(Boolean)));                             // 51
  _check(self.previousSolution, Match.OneOf(Object, null));                                   // 52
  _check(self.allowIncompatibleUpdate, Boolean);                                              // 53
  _check(self.upgradeIndirectDepPatchVersions, Boolean);                                      // 54
                                                                                              // 55
  self.catalogCache = catalogCache;                                                           // 56
  _check(self.catalogCache, CS.CatalogCache);                                                 // 57
  // The catalog presumably has valid package names in it, but make sure                      // 58
  // there aren't any characters in there somehow that will trip us up                        // 59
  // with creating valid variable strings.                                                    // 60
  self.catalogCache.eachPackage(function (packageName) {                                      // 61
    validatePackageName(packageName);                                                         // 62
  });                                                                                         // 63
  self.catalogCache.eachPackageVersion(function (packageName, depsMap) {                      // 64
    _.each(depsMap, function (deps, depPackageName) {                                         // 65
      validatePackageName(depPackageName);                                                    // 66
    });                                                                                       // 67
  });                                                                                         // 68
                                                                                              // 69
  _.each(self.dependencies, validatePackageName);                                             // 70
  _.each(self.upgrade, validatePackageName);                                                  // 71
  _.each(self.constraints, function (c) {                                                     // 72
    validatePackageName(c.package);                                                           // 73
  });                                                                                         // 74
  if (self.previousSolution) {                                                                // 75
    _.each(_.keys(self.previousSolution),                                                     // 76
           validatePackageName);                                                              // 77
  }                                                                                           // 78
                                                                                              // 79
  self._dependencySet = {}; // package name -> true                                           // 80
  _.each(self.dependencies, function (d) {                                                    // 81
    self._dependencySet[d] = true;                                                            // 82
  });                                                                                         // 83
  self._upgradeSet = {};                                                                      // 84
  _.each(self.upgrade, function (u) {                                                         // 85
    self._upgradeSet[u] = true;                                                               // 86
  });                                                                                         // 87
};                                                                                            // 88
                                                                                              // 89
validatePackageName = function (name) {                                                       // 90
  PV.validatePackageName(name);                                                               // 91
  // We have some hard requirements of our own so that packages can be                        // 92
  // used as solver variables.  PV.validatePackageName should already                         // 93
  // enforce these requirements and more, so these checks are just a                          // 94
  // backstop in case it changes under us somehow.                                            // 95
  if ((name.charAt(0) === '$') || (name.charAt(0) === '-')) {                                 // 96
    throw new Error("First character of package name cannot be: " +                           // 97
                    name.charAt(0));                                                          // 98
  }                                                                                           // 99
  if (/ /.test(name)) {                                                                       // 100
    throw new Error("No space allowed in package name");                                      // 101
  }                                                                                           // 102
};                                                                                            // 103
                                                                                              // 104
CS.Input.prototype.isKnownPackage = function (p) {                                            // 105
  return this.catalogCache.hasPackage(p);                                                     // 106
};                                                                                            // 107
                                                                                              // 108
CS.Input.prototype.isRootDependency = function (p) {                                          // 109
  return _.has(this._dependencySet, p);                                                       // 110
};                                                                                            // 111
                                                                                              // 112
CS.Input.prototype.isUpgrading = function (p) {                                               // 113
  return _.has(this._upgradeSet, p);                                                          // 114
};                                                                                            // 115
                                                                                              // 116
CS.Input.prototype.isInPreviousSolution = function (p) {                                      // 117
  return !! (this.previousSolution && _.has(this.previousSolution, p));                       // 118
};                                                                                            // 119
                                                                                              // 120
function getMentionedPackages(input) {                                                        // 121
  var packages = {}; // package -> true                                                       // 122
                                                                                              // 123
  _.each(input.dependencies, function (pkg) {                                                 // 124
    packages[pkg] = true;                                                                     // 125
  });                                                                                         // 126
  _.each(input.constraints, function (constraint) {                                           // 127
    packages[constraint.package] = true;                                                      // 128
  });                                                                                         // 129
  if (input.previousSolution) {                                                               // 130
    _.each(input.previousSolution, function (version, pkg) {                                  // 131
      packages[pkg] = true;                                                                   // 132
    });                                                                                       // 133
  }                                                                                           // 134
                                                                                              // 135
  return _.keys(packages);                                                                    // 136
}                                                                                             // 137
                                                                                              // 138
CS.Input.prototype.loadFromCatalog = function (catalogLoader) {                               // 139
  // Load packages into the cache (if they aren't loaded already).                            // 140
  catalogLoader.loadAllVersionsRecursive(getMentionedPackages(this));                         // 141
};                                                                                            // 142
                                                                                              // 143
CS.Input.prototype.loadOnlyPreviousSolution = function (catalogLoader) {                      // 144
  var self = this;                                                                            // 145
                                                                                              // 146
  // load just the exact versions from the previousSolution                                   // 147
  if (self.previousSolution) {                                                                // 148
    _.each(self.previousSolution, function (version, pkg) {                                   // 149
      catalogLoader.loadSingleVersion(pkg, version);                                          // 150
    });                                                                                       // 151
  }                                                                                           // 152
};                                                                                            // 153
                                                                                              // 154
CS.Input.prototype.isEqual = function (otherInput) {                                          // 155
  var a = this;                                                                               // 156
  var b = otherInput;                                                                         // 157
                                                                                              // 158
  // It would be more efficient to compare the fields directly,                               // 159
  // but converting to JSON is much easier to implement.                                      // 160
  // This equality test is also overly sensitive to order,                                    // 161
  // missing opportunities to declare two inputs equal when only                              // 162
  // the order has changed.                                                                   // 163
                                                                                              // 164
  // Omit `catalogCache` -- it's not actually part of the serialized                          // 165
  // input object (it's only in `toJSONable()` for tests).                                    // 166
  //                                                                                          // 167
  // Moreover, catalogCache is populated as-needed so their values for                        // 168
  // `a` and `b` will very likely be different even if they represent                         // 169
  // the same input. So by omitting `catalogCache` we no longer need                          // 170
  // to reload the entire relevant part of the catalog from SQLite on                         // 171
  // every rebuild!                                                                           // 172
  return _.isEqual(                                                                           // 173
    a.toJSONable(true),                                                                       // 174
    b.toJSONable(true)                                                                        // 175
  );                                                                                          // 176
};                                                                                            // 177
                                                                                              // 178
CS.Input.prototype.toJSONable = function (omitCatalogCache) {                                 // 179
  var self = this;                                                                            // 180
  var obj = {                                                                                 // 181
    dependencies: self.dependencies,                                                          // 182
    constraints: _.map(self.constraints, function (c) {                                       // 183
      return c.toString();                                                                    // 184
    })                                                                                        // 185
  };                                                                                          // 186
                                                                                              // 187
  if (! omitCatalogCache) {                                                                   // 188
    obj.catalogCache = self.catalogCache.toJSONable();                                        // 189
  }                                                                                           // 190
                                                                                              // 191
  // For readability of the resulting JSON, only include optional                             // 192
  // properties that aren't the default.                                                      // 193
  if (self.upgrade.length) {                                                                  // 194
    obj.upgrade = self.upgrade;                                                               // 195
  }                                                                                           // 196
  if (! _.isEmpty(self.anticipatedPrereleases)) {                                             // 197
    obj.anticipatedPrereleases = self.anticipatedPrereleases;                                 // 198
  }                                                                                           // 199
  if (self.previousSolution !== null) {                                                       // 200
    obj.previousSolution = self.previousSolution;                                             // 201
  }                                                                                           // 202
  if (self.allowIncompatibleUpdate) {                                                         // 203
    obj.allowIncompatibleUpdate = true;                                                       // 204
  }                                                                                           // 205
  if (self.upgradeIndirectDepPatchVersions) {                                                 // 206
    obj.upgradeIndirectDepPatchVersions = true;                                               // 207
  }                                                                                           // 208
                                                                                              // 209
  return obj;                                                                                 // 210
};                                                                                            // 211
                                                                                              // 212
CS.Input.fromJSONable = function (obj) {                                                      // 213
  _check(obj, {                                                                               // 214
    dependencies: [String],                                                                   // 215
    constraints: [String],                                                                    // 216
    catalogCache: Object,                                                                     // 217
    anticipatedPrereleases: Match.Optional(                                                   // 218
      Match.ObjectWithValues(Match.ObjectWithValues(Boolean))),                               // 219
    previousSolution: Match.Optional(Match.OneOf(Object, null)),                              // 220
    upgrade: Match.Optional([String]),                                                        // 221
    allowIncompatibleUpdate: Match.Optional(Boolean),                                         // 222
    upgradeIndirectDepPatchVersions: Match.Optional(Boolean)                                  // 223
  });                                                                                         // 224
                                                                                              // 225
  return new CS.Input(                                                                        // 226
    obj.dependencies,                                                                         // 227
    _.map(obj.constraints, function (cstr) {                                                  // 228
      return PV.parsePackageConstraint(cstr);                                                 // 229
    }),                                                                                       // 230
    CS.CatalogCache.fromJSONable(obj.catalogCache),                                           // 231
    {                                                                                         // 232
      upgrade: obj.upgrade,                                                                   // 233
      anticipatedPrereleases: obj.anticipatedPrereleases,                                     // 234
      previousSolution: obj.previousSolution,                                                 // 235
      allowIncompatibleUpdate: obj.allowIncompatibleUpdate,                                   // 236
      upgradeIndirectDepPatchVersions: obj.upgradeIndirectDepPatchVersions                    // 237
    });                                                                                       // 238
};                                                                                            // 239
                                                                                              // 240
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/version-pricer.js                                               //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
var CS = ConstraintSolver;                                                                    // 1
var PV = PackageVersion;                                                                      // 2
                                                                                              // 3
CS.VersionPricer = function () {                                                              // 4
  var self = this;                                                                            // 5
                                                                                              // 6
  // self.getVersionInfo(versionString) returns an object                                     // 7
  // that contains at least { major, minor, patch }.                                          // 8
  //                                                                                          // 9
  // The VersionPricer instance stores a memoization table for                                // 10
  // efficiency.                                                                              // 11
  self.getVersionInfo = _.memoize(PV.parse);                                                  // 12
};                                                                                            // 13
                                                                                              // 14
CS.VersionPricer.MODE_UPDATE = 1;                                                             // 15
CS.VersionPricer.MODE_GRAVITY = 2;                                                            // 16
CS.VersionPricer.MODE_GRAVITY_WITH_PATCHES = 3;                                               // 17
                                                                                              // 18
// priceVersions(versions, mode, options) calculates small integer                            // 19
// costs for each version, based on whether each part of the version                          // 20
// is low or high relative to the other versions with the same higher                         // 21
// parts.                                                                                     // 22
//                                                                                            // 23
// For example, if "1.2.0" and "1.2.1" are the only 1.2.x versions                            // 24
// in the versions array, they will be assigned PATCH costs of                                // 25
// 1 and 0 in UPDATE mode (penalizing the older version), or 0 and 1                          // 26
// in GRAVITY mode (penalizing the newer version).  When optimizing,                          // 27
// the solver will prioritizing minimizing MAJOR costs, then MINOR                            // 28
// costs, then PATCH costs, and then "REST" costs (which penalizing                           // 29
// being old or new within versions that have the same major, minor,                          // 30
// AND patch).                                                                                // 31
//                                                                                            // 32
// - `versions` - Array of version strings in sorted order                                    // 33
// - `mode` - A MODE constant                                                                 // 34
// - `options`:                                                                               // 35
//   - `versionAfter` - if provided, the next newer version not in the                        // 36
//     array but that would come next.                                                        // 37
//   - `versionBefore` - if provided, the next older version not in the                       // 38
//     the array but that would come before it.                                               // 39
//                                                                                            // 40
// Returns: an array of 4 arrays, each of length versions.length,                             // 41
// containing the MAJOR, MINOR, PATCH, and REST costs corresponding                           // 42
// to the versions.                                                                           // 43
//                                                                                            // 44
// MODE_UPDATE penalizes versions for being old (because we want                              // 45
// them to be new), while the MODE_GRAVITY penalizes versions for                             // 46
// being new (because we are trying to apply "version gravity" and                            // 47
// prefer older versions).  MODE_GRAVITY_WITH_PATCHES applies gravity                         // 48
// to the major and minor parts of the version, but prefers updates                           // 49
// to the patch and rest of the version.                                                      // 50
//                                                                                            // 51
// Use `versionAfter` when scanning a partial array of versions                               // 52
// if you want the newest version in the array to have a non-zero                             // 53
// weight in MODE_UPDATE.  For example, the versions                                          // 54
// `["1.0.0", "1.0.1"]` will be considered to have an out-of-date                             // 55
// version if versionAfter is `"2.0.0"`.  The costs returned                                  // 56
// won't be the same as if the whole array was scanned at once,                               // 57
// but this option is useful in order to apply MODE_UPDATE to some                            // 58
// versions and MODE_GRAVITY to others, for example.                                          // 59
//                                                                                            // 60
// `versionBefore` is used in an analogous way with the GRAVITY modes.                        // 61
//                                                                                            // 62
// The easiest way to implement this function would be to partition                           // 63
// `versions` into subarrays of versions with the same major part,                            // 64
// and then partition those arrays based on the minor parts, and                              // 65
// so on.  However, that's a lot of array allocations -- O(N) or                              // 66
// thereabouts.  So instead we use a linear scan backwards through                            // 67
// the versions array.                                                                        // 68
CS.VersionPricer.prototype.priceVersions = function (versions, mode, options) {               // 69
  var self = this;                                                                            // 70
                                                                                              // 71
  var getMajorMinorPatch = function (v) {                                                     // 72
    var vInfo = self.getVersionInfo(v);                                                       // 73
    return [vInfo.major, vInfo.minor, vInfo.patch];                                           // 74
  };                                                                                          // 75
                                                                                              // 76
  var MAJOR = 0, MINOR = 1, PATCH = 2, REST = 3;                                              // 77
  var gravity; // array of MAJOR, MINOR, PATCH, REST                                          // 78
                                                                                              // 79
  switch (mode) {                                                                             // 80
  case CS.VersionPricer.MODE_UPDATE:                                                          // 81
    gravity = [false, false, false, false];                                                   // 82
    break;                                                                                    // 83
  case CS.VersionPricer.MODE_GRAVITY:                                                         // 84
    gravity = [true, true, true, true];                                                       // 85
    break;                                                                                    // 86
  case CS.VersionPricer.MODE_GRAVITY_WITH_PATCHES:                                            // 87
    gravity = [true, true, false, false];                                                     // 88
    break;                                                                                    // 89
  default:                                                                                    // 90
    throw new Error("Bad mode: " + mode);                                                     // 91
  }                                                                                           // 92
                                                                                              // 93
  var lastMajorMinorPatch = null;                                                             // 94
  if (options && options.versionAfter) {                                                      // 95
    lastMajorMinorPatch = getMajorMinorPatch(options.versionAfter);                           // 96
  }                                                                                           // 97
  // `costs` contains arrays of whole numbers, each of which will                             // 98
  // have a length of versions.length.  This is what we will return.                          // 99
  var costs = [[], [], [], []]; // MAJOR, MINOR, PATCH, REST                                  // 100
  // How many in a row of the same MAJOR, MINOR, or PATCH have we seen?                       // 101
  var countOfSame = [0, 0, 0];                                                                // 102
                                                                                              // 103
  // Track how old each part of versions[i] is, in terms of how many                          // 104
  // greater values there are for that part among versions with the                           // 105
  // same higher parts.  For example, oldness[REST] counts the number                         // 106
  // of versions after versions[i] with the same MAJOR, MINOR, and REST.                      // 107
  // oldness[PATCH] counts the number of *different* higher values for                        // 108
  // for PATCH among later versions with the same MAJOR and MINOR parts.                      // 109
  var oldness = [0, 0, 0, 0];                                                                 // 110
                                                                                              // 111
  // Walk the array backwards                                                                 // 112
  for (var i = versions.length - 1; i >= 0; i--) {                                            // 113
    var v = versions[i];                                                                      // 114
    var majorMinorPatch = getMajorMinorPatch(v);                                              // 115
    if (lastMajorMinorPatch) {                                                                // 116
      for (var k = MAJOR; k <= REST; k++) {                                                   // 117
        if (k === REST || majorMinorPatch[k] !== lastMajorMinorPatch[k]) {                    // 118
          // For the highest part that changed, bumped the oldness                            // 119
          // and clear the lower oldnesses.                                                   // 120
          oldness[k]++;                                                                       // 121
          for (var m = k+1; m <= REST; m++) {                                                 // 122
            if (gravity[m]) {                                                                 // 123
              // if we should actually be counting "newness" instead of                       // 124
              // oldness, flip the count.  Instead of [0, 1, 1, 2, 3],                        // 125
              // for example, make it [3, 2, 2, 1, 0].  This is the place                     // 126
              // to do it, because we have just "closed out" a run.                           // 127
              flipLastN(costs[m], countOfSame[m-1], oldness[m]);                              // 128
            }                                                                                 // 129
            countOfSame[m-1] = 0;                                                             // 130
            oldness[m] = 0;                                                                   // 131
          }                                                                                   // 132
          break;                                                                              // 133
        }                                                                                     // 134
      }                                                                                       // 135
    }                                                                                         // 136
    for (var k = MAJOR; k <= REST; k++) {                                                     // 137
      costs[k].push(oldness[k]);                                                              // 138
      if (k !== REST) {                                                                       // 139
        countOfSame[k]++;                                                                     // 140
      }                                                                                       // 141
    }                                                                                         // 142
    lastMajorMinorPatch = majorMinorPatch;                                                    // 143
  }                                                                                           // 144
  if (options && options.versionBefore && versions.length) {                                  // 145
    // bump the appropriate value of oldness, as if we ran the loop                           // 146
    // one more time                                                                          // 147
    majorMinorPatch = getMajorMinorPatch(options.versionBefore);                              // 148
    for (var k = MAJOR; k <= REST; k++) {                                                     // 149
      if (k === REST || majorMinorPatch[k] !== lastMajorMinorPatch[k]) {                      // 150
        oldness[k]++;                                                                         // 151
        break;                                                                                // 152
      }                                                                                       // 153
    }                                                                                         // 154
  }                                                                                           // 155
                                                                                              // 156
  // Flip the MAJOR costs if we have MAJOR gravity -- subtracting them                        // 157
  // all from oldness[MAJOR] -- and likewise for other parts if countOfSame                   // 158
  // is > 0 for the next highest part (meaning we didn't get a chance to                      // 159
  // flip some of the costs because the loop ended).                                          // 160
  for (var k = MAJOR; k <= REST; k++) {                                                       // 161
    if (gravity[k]) {                                                                         // 162
      flipLastN(costs[k], k === MAJOR ? costs[k].length : countOfSame[k-1],                   // 163
                oldness[k]);                                                                  // 164
    }                                                                                         // 165
  }                                                                                           // 166
                                                                                              // 167
  // We pushed costs onto the arrays in reverse order.  Reverse the cost                      // 168
  // arrays in place before returning them.                                                   // 169
  return [costs[MAJOR].reverse(),                                                             // 170
          costs[MINOR].reverse(),                                                             // 171
          costs[PATCH].reverse(),                                                             // 172
          costs[REST].reverse()];                                                             // 173
};                                                                                            // 174
                                                                                              // 175
// "Flip" the last N elements of array in place by subtracting each                           // 176
// one from `max`.  For example, if `a` is `[3,0,1,1,2]`, then calling                        // 177
// `flipLastN(a, 4, 2)` mutates `a` into `[3,2,1,1,0]`.                                       // 178
var flipLastN = function (array, N, max) {                                                    // 179
  var len = array.length;                                                                     // 180
  for (var i = 0; i < N; i++) {                                                               // 181
    var j = len - 1 - i;                                                                      // 182
    array[j] = max - array[j];                                                                // 183
  }                                                                                           // 184
};                                                                                            // 185
                                                                                              // 186
// Partition a sorted array of versions into three arrays, containing                         // 187
// the versions that are `older` than the `target` version,                                   // 188
// `compatible` with it, or have a `higherMajor` version.                                     // 189
//                                                                                            // 190
// For example, `["1.0.0", "2.5.0", "2.6.1", "3.0.0"]` with a target of                       // 191
// `"2.5.0"` returns `{ older: ["1.0.0"], compatible: ["2.5.0", "2.6.1"],                     // 192
// higherMajor: ["3.0.0"] }`.                                                                 // 193
CS.VersionPricer.prototype.partitionVersions = function (versions, target) {                  // 194
  var self = this;                                                                            // 195
  var firstGteIndex = versions.length;                                                        // 196
  var higherMajorIndex = versions.length;                                                     // 197
  var targetVInfo = self.getVersionInfo(target);                                              // 198
  for (var i = 0; i < versions.length; i++) {                                                 // 199
    var v = versions[i];                                                                      // 200
    var vInfo = self.getVersionInfo(v);                                                       // 201
    if (firstGteIndex === versions.length &&                                                  // 202
        ! PV.lessThan(vInfo, targetVInfo)) {                                                  // 203
      firstGteIndex = i;                                                                      // 204
    }                                                                                         // 205
    if (vInfo.major > targetVInfo.major) {                                                    // 206
      higherMajorIndex = i;                                                                   // 207
      break;                                                                                  // 208
    }                                                                                         // 209
  }                                                                                           // 210
  return { older: versions.slice(0, firstGteIndex),                                           // 211
           compatible: versions.slice(firstGteIndex, higherMajorIndex),                       // 212
           higherMajor: versions.slice(higherMajorIndex) };                                   // 213
};                                                                                            // 214
                                                                                              // 215
// Use a combination of calls to priceVersions with different modes in order                  // 216
// to generate costs for versions relative to a "previous solution" version                   // 217
// (called the "target" here).                                                                // 218
CS.VersionPricer.prototype.priceVersionsWithPrevious = function (                             // 219
  versions, target, takePatches) {                                                            // 220
                                                                                              // 221
  var self = this;                                                                            // 222
  var parts = self.partitionVersions(versions, target);                                       // 223
                                                                                              // 224
  var result1 = self.priceVersions(parts.older, CS.VersionPricer.MODE_UPDATE,                 // 225
                                   { versionAfter: target });                                 // 226
  // Usually, it's better to remain as close as possible to the target                        // 227
  // version, but prefer higher patch versions (and wrapNums, etc.) if                        // 228
  // we were passed `takePatches`.                                                            // 229
  var result2 = self.priceVersions(parts.compatible,                                          // 230
                                   (takePatches ?                                             // 231
                                    CS.VersionPricer.MODE_GRAVITY_WITH_PATCHES :              // 232
                                    CS.VersionPricer.MODE_GRAVITY));                          // 233
  // If we're already bumping the major version, might as well take patches.                  // 234
  var result3 = self.priceVersions(parts.higherMajor,                                         // 235
                                   CS.VersionPricer.MODE_GRAVITY_WITH_PATCHES,                // 236
                                   // not actually the version right before, but              // 237
                                   // gives the `major` cost the bump it needs                // 238
                                   { versionBefore: target });                                // 239
                                                                                              // 240
  // Generate a fifth array, incompat, which has a 1 for each incompatible                    // 241
  // version and a 0 for each compatible version.                                             // 242
  var incompat = [];                                                                          // 243
  var i;                                                                                      // 244
  for (i = 0; i < parts.older.length; i++) {                                                  // 245
    incompat.push(1);                                                                         // 246
  }                                                                                           // 247
  for (i = 0; i < parts.compatible.length; i++) {                                             // 248
    incompat.push(0);                                                                         // 249
  }                                                                                           // 250
  for (i = 0; i < parts.higherMajor.length; i++) {                                            // 251
    incompat.push(1);                                                                         // 252
  }                                                                                           // 253
                                                                                              // 254
  return [                                                                                    // 255
    incompat,                                                                                 // 256
    result1[0].concat(result2[0], result3[0]),                                                // 257
    result1[1].concat(result2[1], result3[1]),                                                // 258
    result1[2].concat(result2[2], result3[2]),                                                // 259
    result1[3].concat(result2[3], result3[3])                                                 // 260
  ];                                                                                          // 261
};                                                                                            // 262
                                                                                              // 263
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/solver.js                                                       //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
var CS = ConstraintSolver;                                                                    // 1
var PV = PackageVersion;                                                                      // 2
                                                                                              // 3
var pvVar = function (p, v) {                                                                 // 4
  return p + ' ' + v;                                                                         // 5
};                                                                                            // 6
                                                                                              // 7
// The "inner solver".  You construct it with a ConstraintSolver.Input object                 // 8
// (which specifies the problem) and then call .getAnswer() on it.                            // 9
                                                                                              // 10
CS.Solver = function (input, options) {                                                       // 11
  var self = this;                                                                            // 12
  check(input, CS.Input);                                                                     // 13
                                                                                              // 14
  self.input = input;                                                                         // 15
  self.errors = []; // [String]                                                               // 16
                                                                                              // 17
  self.pricer = new CS.VersionPricer();                                                       // 18
  self.getConstraintFormula = _.memoize(_getConstraintFormula,                                // 19
                                         function (p, vConstraint) {                          // 20
                                           return p + "@" + vConstraint.raw;                  // 21
                                         });                                                  // 22
                                                                                              // 23
  self.options = options || {};                                                               // 24
  self.Profile = (self.options.Profile || CS.DummyProfile);                                   // 25
                                                                                              // 26
  self.steps = [];                                                                            // 27
  self.stepsByName = {};                                                                      // 28
                                                                                              // 29
  self.analysis = {};                                                                         // 30
                                                                                              // 31
  self.Profile.time("Solver#analyze", function () {                                           // 32
    self.analyze();                                                                           // 33
  });                                                                                         // 34
                                                                                              // 35
  self.logic = null; // Logic.Solver, initialized later                                       // 36
};                                                                                            // 37
                                                                                              // 38
CS.Solver.prototype.throwAnyErrors = function () {                                            // 39
  if (this.errors.length) {                                                                   // 40
    var multiline = _.any(this.errors, function (e) {                                         // 41
      return /\n/.test(e);                                                                    // 42
    });                                                                                       // 43
    CS.throwConstraintSolverError(this.errors.join(                                           // 44
      multiline ? '\n\n' : '\n'));                                                            // 45
  }                                                                                           // 46
};                                                                                            // 47
                                                                                              // 48
CS.Solver.prototype.getVersions = function (pkg) {                                            // 49
  var self = this;                                                                            // 50
  if (_.has(self.analysis.allowedVersions, pkg)) {                                            // 51
    return self.analysis.allowedVersions[pkg];                                                // 52
  } else {                                                                                    // 53
    return self.input.catalogCache.getPackageVersions(pkg);                                   // 54
  }                                                                                           // 55
};                                                                                            // 56
                                                                                              // 57
// Populates `self.analysis` with various data structures derived from the                    // 58
// input.  May also throw errors, and may call methods that rely on                           // 59
// analysis once that particular analysis is done (e.g. `self.getVersions`                    // 60
// which relies on `self.analysis.allowedVersions`.                                           // 61
CS.Solver.prototype.analyze = function () {                                                   // 62
  var self = this;                                                                            // 63
  var analysis = self.analysis;                                                               // 64
  var input = self.input;                                                                     // 65
  var cache = input.catalogCache;                                                             // 66
  var Profile = self.Profile;                                                                 // 67
                                                                                              // 68
  ////////// ANALYZE ALLOWED VERSIONS                                                         // 69
  // (An "allowed version" is one that isn't ruled out by a top-level                         // 70
  // constraint.)                                                                             // 71
                                                                                              // 72
  // package -> array of version strings.  If a package has an entry in                       // 73
  // this map, then only the versions in the array are allowed for                            // 74
  // consideration.                                                                           // 75
  analysis.allowedVersions = {};                                                              // 76
  analysis.packagesWithNoAllowedVersions = {}; // package -> [constraints]                    // 77
                                                                                              // 78
  // Process top-level constraints, applying them right now by                                // 79
  // limiting what package versions we even consider.  This speeds up                         // 80
  // solving, especially given the equality constraints on core                               // 81
  // packages.  For versions we don't allow, we get to avoid generating                       // 82
  // Constraint objects for their constraints, which saves us both                            // 83
  // clause generation time and solver work up through the point where we                     // 84
  // determine there are no conflicts between constraints.                                    // 85
  //                                                                                          // 86
  // we can't throw any errors yet, because `input.constraints`                               // 87
  // doesn't establish any dependencies (so we don't know if it's a                           // 88
  // problem that some package has no legal versions), but we can                             // 89
  // track such packages in packagesWithNoAllowedVersions so that we                          // 90
  // throw a good error later.                                                                // 91
  Profile.time("analyze allowed versions", function () {                                      // 92
    _.each(_.groupBy(input.constraints, 'package'), function (cs, p) {                        // 93
      var versions = cache.getPackageVersions(p);                                             // 94
      if (! versions.length) {                                                                // 95
        // deal with wholly unknown packages later                                            // 96
        return;                                                                               // 97
      }                                                                                       // 98
      _.each(cs, function (constr) {                                                          // 99
        versions = _.filter(versions, function (v) {                                          // 100
          return CS.isConstraintSatisfied(p, constr.versionConstraint, v);                    // 101
        });                                                                                   // 102
      });                                                                                     // 103
      if (! versions.length) {                                                                // 104
        analysis.packagesWithNoAllowedVersions[p] = _.filter(cs, function (c) {               // 105
          return !! c.constraintString;                                                       // 106
        });                                                                                   // 107
      }                                                                                       // 108
      analysis.allowedVersions[p] = versions;                                                 // 109
    });                                                                                       // 110
  });                                                                                         // 111
                                                                                              // 112
  ////////// ANALYZE ROOT DEPENDENCIES                                                        // 113
                                                                                              // 114
  // Collect root dependencies that we've never heard of.                                     // 115
  analysis.unknownRootDeps = [];                                                              // 116
  // Collect "previous solution" versions of root dependencies.                               // 117
  analysis.previousRootDepVersions = [];                                                      // 118
                                                                                              // 119
  Profile.time("analyze root dependencies", function () {                                     // 120
    _.each(input.dependencies, function (p) {                                                 // 121
      if (! input.isKnownPackage(p)) {                                                        // 122
        analysis.unknownRootDeps.push(p);                                                     // 123
      } else if (input.isInPreviousSolution(p) &&                                             // 124
                 ! input.isUpgrading(p)) {                                                    // 125
        analysis.previousRootDepVersions.push(new CS.PackageAndVersion(                       // 126
          p, input.previousSolution[p]));                                                     // 127
      }                                                                                       // 128
    });                                                                                       // 129
                                                                                              // 130
    // throw if there are unknown packages in root deps                                       // 131
    if (analysis.unknownRootDeps.length) {                                                    // 132
      _.each(analysis.unknownRootDeps, function (p) {                                         // 133
        if (CS.isIsobuildFeaturePackage(p)) {                                                 // 134
          self.errors.push(                                                                   // 135
            'unsupported Isobuild feature "' + p +                                            // 136
            '" in top-level dependencies; see ' +                                             // 137
            'https://github.com/meteor/meteor/wiki/Isobuild-Feature-Packages ' +              // 138
            'for a list of features and the minimum Meteor release required'                  // 139
          );                                                                                  // 140
        } else {                                                                              // 141
          self.errors.push('unknown package in top-level dependencies: ' + p);                // 142
        }                                                                                     // 143
      });                                                                                     // 144
      self.throwAnyErrors();                                                                  // 145
    }                                                                                         // 146
  });                                                                                         // 147
                                                                                              // 148
  ////////// ANALYZE REACHABILITY                                                             // 149
                                                                                              // 150
  // A "reachable" package is one that is either a root dependency or                         // 151
  // a strong dependency of any "allowed" version of a reachable package.                     // 152
  // In other words, we walk all strong dependencies starting                                 // 153
  // with the root dependencies, and visiting all allowed versions of each                    // 154
  // package.                                                                                 // 155
  //                                                                                          // 156
  // This analysis is mainly done for performance, because if there are                       // 157
  // extraneous packages in the CatalogCache (for whatever reason) we                         // 158
  // want to spend as little time on them as possible.  It also establishes                   // 159
  // the universe of possible "known" and "unknown" packages we might                         // 160
  // come across.                                                                             // 161
  //                                                                                          // 162
  // A more nuanced reachability analysis that takes versions into account                    // 163
  // is probably possible.                                                                    // 164
                                                                                              // 165
  // package name -> true                                                                     // 166
  analysis.reachablePackages = {};                                                            // 167
  // package name -> package versions asking for it (in pvVar form)                           // 168
  analysis.unknownPackages = {};                                                              // 169
                                                                                              // 170
  var markReachable = function (p) {                                                          // 171
    analysis.reachablePackages[p] = true;                                                     // 172
                                                                                              // 173
    _.each(self.getVersions(p), function (v) {                                                // 174
      _.each(cache.getDependencyMap(p, v), function (dep) {                                   // 175
        // `dep` is a CS.Dependency                                                           // 176
        var p2 = dep.packageConstraint.package;                                               // 177
        if (! input.isKnownPackage(p2)) {                                                     // 178
          // record this package so we will generate a variable                               // 179
          // for it.  we'll try not to select it, and ultimately                              // 180
          // throw an error if we are forced to.                                              // 181
          if (! _.has(analysis.unknownPackages, p2)) {                                        // 182
            analysis.unknownPackages[p2] = [];                                                // 183
          }                                                                                   // 184
          analysis.unknownPackages[p2].push(pvVar(p, v));                                     // 185
        } else {                                                                              // 186
          if (! dep.isWeak) {                                                                 // 187
            if (! _.has(analysis.reachablePackages, p2)) {                                    // 188
              markReachable(p2);                                                              // 189
            }                                                                                 // 190
          }                                                                                   // 191
        }                                                                                     // 192
      });                                                                                     // 193
    });                                                                                       // 194
  };                                                                                          // 195
                                                                                              // 196
  Profile.time("analyze reachability", function () {                                          // 197
    _.each(input.dependencies, markReachable);                                                // 198
  });                                                                                         // 199
                                                                                              // 200
  ////////// ANALYZE CONSTRAINTS                                                              // 201
                                                                                              // 202
  // Array of CS.Solver.Constraint                                                            // 203
  analysis.constraints = [];                                                                  // 204
  // packages `foo` such that there's a simple top-level equality                             // 205
  // constraint about `foo`.  package name -> true.                                           // 206
  analysis.topLevelEqualityConstrainedPackages = {};                                          // 207
                                                                                              // 208
  Profile.time("analyze constraints", function () {                                           // 209
    // top-level constraints                                                                  // 210
    _.each(input.constraints, function (c) {                                                  // 211
      if (c.constraintString) {                                                               // 212
        analysis.constraints.push(new CS.Solver.Constraint(                                   // 213
          null, c.package, c.versionConstraint,                                               // 214
          "constraint#" + analysis.constraints.length));                                      // 215
                                                                                              // 216
        if (c.versionConstraint.alternatives.length === 1 &&                                  // 217
            c.versionConstraint.alternatives[0].type === 'exactly') {                         // 218
          analysis.topLevelEqualityConstrainedPackages[c.package] = true;                     // 219
        }                                                                                     // 220
      }                                                                                       // 221
    });                                                                                       // 222
                                                                                              // 223
    // constraints specified in package dependencies                                          // 224
    _.each(_.keys(analysis.reachablePackages), function (p) {                                 // 225
      _.each(self.getVersions(p), function (v) {                                              // 226
        var pv = pvVar(p, v);                                                                 // 227
        _.each(cache.getDependencyMap(p, v), function (dep) {                                 // 228
          // `dep` is a CS.Dependency                                                         // 229
          var p2 = dep.packageConstraint.package;                                             // 230
          if (input.isKnownPackage(p2) &&                                                     // 231
              dep.packageConstraint.constraintString) {                                       // 232
            analysis.constraints.push(new CS.Solver.Constraint(                               // 233
              pv, p2, dep.packageConstraint.versionConstraint,                                // 234
              "constraint#" + analysis.constraints.length));                                  // 235
          }                                                                                   // 236
        });                                                                                   // 237
      });                                                                                     // 238
    });                                                                                       // 239
  });                                                                                         // 240
                                                                                              // 241
  ////////// ANALYZE PRE-RELEASES                                                             // 242
                                                                                              // 243
  Profile.time("analyze pre-releases", function () {                                          // 244
    var unanticipatedPrereleases = [];                                                        // 245
    _.each(_.keys(analysis.reachablePackages), function (p) {                                 // 246
      var anticipatedPrereleases = input.anticipatedPrereleases[p];                           // 247
      _.each(self.getVersions(p), function (v) {                                              // 248
        if (/-/.test(v) && ! (anticipatedPrereleases &&                                       // 249
                              _.has(anticipatedPrereleases, v))) {                            // 250
          unanticipatedPrereleases.push(pvVar(p, v));                                         // 251
        }                                                                                     // 252
      });                                                                                     // 253
    });                                                                                       // 254
    analysis.unanticipatedPrereleases = unanticipatedPrereleases;                             // 255
  });                                                                                         // 256
};                                                                                            // 257
                                                                                              // 258
var WholeNumber = Match.Where(Logic.isWholeNumber);                                           // 259
                                                                                              // 260
// A Step consists of a name, an array of terms, and an array of weights.                     // 261
// Steps are optimized one by one.  Optimizing a Step means to find                           // 262
// the minimum whole number value for the weighted sum of the terms,                          // 263
// and then to enforce in the solver that the weighted sum be that number.                    // 264
// Thus, when the Steps are optimized in sequence, earlier Steps take                         // 265
// precedence and will stay minimized while later Steps are optimized.                        // 266
//                                                                                            // 267
// A term can be a package name, a package version, or any other variable                     // 268
// name or Logic formula.                                                                     // 269
//                                                                                            // 270
// A weight is a non-negative integer.  The weights array can be a single                     // 271
// weight (which is used for all terms).                                                      // 272
//                                                                                            // 273
// The terms and weights arguments each default to [].  You can add terms                     // 274
// with weights using addTerm.                                                                // 275
//                                                                                            // 276
// options is optional.                                                                       // 277
CS.Solver.Step = function (name, terms, weights) {                                            // 278
  check(name, String);                                                                        // 279
  terms = terms || [];                                                                        // 280
  check(terms, [String]);                                                                     // 281
  weights = (weights == null ? [] : weights);                                                 // 282
  check(weights, Match.OneOf([WholeNumber], WholeNumber));                                    // 283
                                                                                              // 284
  this.name = name;                                                                           // 285
                                                                                              // 286
  // mutable:                                                                                 // 287
  this.terms = terms;                                                                         // 288
  this.weights = weights;                                                                     // 289
  this.optimum = null; // set when optimized                                                  // 290
};                                                                                            // 291
                                                                                              // 292
// If weights is a single number, you can omit the weight argument.                           // 293
// Adds a term.  If weight is 0, addTerm may skip it.                                         // 294
CS.Solver.Step.prototype.addTerm = function (term, weight) {                                  // 295
  if (weight == null) {                                                                       // 296
    if (typeof this.weights !== 'number') {                                                   // 297
      throw new Error("Must specify a weight");                                               // 298
    }                                                                                         // 299
    weight = this.weights;                                                                    // 300
  }                                                                                           // 301
  check(weight, WholeNumber);                                                                 // 302
  if (weight !== 0) {                                                                         // 303
    this.terms.push(term);                                                                    // 304
    if (typeof this.weights === 'number') {                                                   // 305
      if (weight !== this.weights) {                                                          // 306
        throw new Error("Can't specify a different weight now: " +                            // 307
                        weight + " != " + this.weights);                                      // 308
      }                                                                                       // 309
    } else {                                                                                  // 310
      this.weights.push(weight);                                                              // 311
    }                                                                                         // 312
  }                                                                                           // 313
};                                                                                            // 314
                                                                                              // 315
var DEBUG = false;                                                                            // 316
                                                                                              // 317
// Call as one of:                                                                            // 318
// * minimize(step, options)                                                                  // 319
// * minimize([step1, step2, ...], options)                                                   // 320
// * minimize(stepName, costTerms, costWeights, options)                                      // 321
CS.Solver.prototype.minimize = function (step, options) {                                     // 322
  var self = this;                                                                            // 323
                                                                                              // 324
  if (_.isArray(step)) {                                                                      // 325
    // minimize([steps...], options)                                                          // 326
    _.each(step, function (st) {                                                              // 327
      self.minimize(st, options);                                                             // 328
    });                                                                                       // 329
    return;                                                                                   // 330
  }                                                                                           // 331
                                                                                              // 332
  if (typeof step === 'string') {                                                             // 333
    // minimize(stepName, costTerms, costWeights, options)                                    // 334
    var stepName_ = arguments[0];                                                             // 335
    var costTerms_ = arguments[1];                                                            // 336
    var costWeights_ = arguments[2];                                                          // 337
    var options_ = arguments[3];                                                              // 338
    if (costWeights_ && typeof costWeights_ === 'object' &&                                   // 339
        ! _.isArray(costWeights_)) {                                                          // 340
      options_ = costWeights_;                                                                // 341
      costWeights_ = null;                                                                    // 342
    }                                                                                         // 343
    var theStep = new CS.Solver.Step(                                                         // 344
      stepName_, costTerms_, (costWeights_ == null ? 1 : costWeights_));                      // 345
    self.minimize(theStep, options_);                                                         // 346
    return;                                                                                   // 347
  }                                                                                           // 348
                                                                                              // 349
  // minimize(step, options);                                                                 // 350
                                                                                              // 351
  self.Profile.time("minimize " + step.name, function () {                                    // 352
                                                                                              // 353
    var logic = self.logic;                                                                   // 354
                                                                                              // 355
    self.steps.push(step);                                                                    // 356
    self.stepsByName[step.name] = step;                                                       // 357
                                                                                              // 358
    if (DEBUG) {                                                                              // 359
      console.log("--- MINIMIZING " + step.name);                                             // 360
    }                                                                                         // 361
                                                                                              // 362
    var costWeights = step.weights;                                                           // 363
    var costTerms = step.terms;                                                               // 364
                                                                                              // 365
    var optimized = groupMutuallyExclusiveTerms(costTerms, costWeights);                      // 366
                                                                                              // 367
    self.setSolution(logic.minimizeWeightedSum(                                               // 368
      self.solution, optimized.costTerms, optimized.costWeights, {                            // 369
        progress: function (status, cost) {                                                   // 370
          if (self.options.nudge) {                                                           // 371
            self.options.nudge();                                                             // 372
          }                                                                                   // 373
          if (DEBUG) {                                                                        // 374
            if (status === 'improving') {                                                     // 375
              console.log(cost + " ... trying to improve ...");                               // 376
            } else if (status === 'trying') {                                                 // 377
              console.log("... trying " + cost + " ... ");                                    // 378
            }                                                                                 // 379
          }                                                                                   // 380
        },                                                                                    // 381
        strategy: (options && options.strategy)                                               // 382
      }));                                                                                    // 383
                                                                                              // 384
    step.optimum = self.solution.getWeightedSum(costTerms, costWeights);                      // 385
    if (DEBUG) {                                                                              // 386
      console.log(step.optimum + " is optimal");                                              // 387
                                                                                              // 388
      if (step.optimum) {                                                                     // 389
        _.each(costTerms, function (t, i) {                                                   // 390
          var w = (typeof costWeights === 'number' ? costWeights :                            // 391
                   costWeights[i]);                                                           // 392
          if (w && self.solution.evaluate(t)) {                                               // 393
            console.log("    " + w + ": " + t);                                               // 394
          }                                                                                   // 395
        });                                                                                   // 396
      }                                                                                       // 397
    }                                                                                         // 398
  });                                                                                         // 399
};                                                                                            // 400
                                                                                              // 401
// This is a correctness-preserving performance optimization.                                 // 402
//                                                                                            // 403
// Cost functions often have many terms where both the package name                           // 404
// and the weight are the same.  For example, when optimizing major                           // 405
// version, we might have `(foo 3.0.0)*2 + (foo 3.0.1)*2 ...`.  It's                          // 406
// more efficient to give the solver `((foo 3.0.0) OR (foo 3.0.1) OR                          // 407
// ...)*2 + ...`, because it separates the question of whether to use                         // 408
// ANY `foo 3.x.x` variable from the question of which one.  Other                            // 409
// constraints already enforce the fact that `foo 3.0.0` and `foo 3.0.1`                      // 410
// are mutually exclusive variables.  We can use that fact to "relax"                         // 411
// that relationship for the purposes of the weighted sum.                                    // 412
//                                                                                            // 413
// Note that shuffling up the order of terms unnecessarily seems to                           // 414
// impact performance, so it's significant that we group by package                           // 415
// first, then weight, rather than vice versa.                                                // 416
var groupMutuallyExclusiveTerms = function (costTerms, costWeights) {                         // 417
  // Return a key for a term, such that terms with the same key are                           // 418
  // guaranteed to be mutually exclusive.  We assume each term is                             // 419
  // a variable representing either a package or a package version.                           // 420
  // We take a prefix of the variable name up to and including the                            // 421
  // first space.  So "foo 1.0.0" becomes "foo " and "foo" stays "foo".                       // 422
  var getTermKey = function (t) {                                                             // 423
    var firstSpace = t.indexOf(' ');                                                          // 424
    return firstSpace < 0 ? t : t.slice(0, firstSpace+1);                                     // 425
  };                                                                                          // 426
                                                                                              // 427
  // costWeights, as usual, may be a number or an array                                       // 428
  if (typeof costWeights === 'number') {                                                      // 429
    return {                                                                                  // 430
      costTerms: _.map(_.groupBy(costTerms, getTermKey), function (group) {                   // 431
        return Logic.or(group);                                                               // 432
      }),                                                                                     // 433
      costWeights: costWeights                                                                // 434
    };                                                                                        // 435
  } else if (! costTerms.length) {                                                            // 436
    return { costTerms: costTerms, costWeights: costWeights };                                // 437
  } else {                                                                                    // 438
    var weightedTerms = _.zip(costWeights, costTerms);                                        // 439
    var newWeightedTerms = _.map(_.groupBy(weightedTerms, function (wt) {                     // 440
      // construct a string from the weight and term key, for grouping                        // 441
      // purposes.  since the weight comes first, there's no ambiguity                        // 442
      // and the separator char could be pretty much anything.                                // 443
      return wt[0] + ' ' + getTermKey(wt[1]);                                                 // 444
    }), function (wts) {                                                                      // 445
      return [wts[0][0], Logic.or(_.pluck(wts, 1))];                                          // 446
    });                                                                                       // 447
    return {                                                                                  // 448
      costTerms: _.pluck(newWeightedTerms, 1),                                                // 449
      costWeights: _.pluck(newWeightedTerms, 0)                                               // 450
    };                                                                                        // 451
  }                                                                                           // 452
                                                                                              // 453
};                                                                                            // 454
                                                                                              // 455
// Determine the non-zero contributions to the cost function in `step`                        // 456
// based on the current solution, returning a map from term (usually                          // 457
// the name of a package or package version) to positive integer cost.                        // 458
CS.Solver.prototype.getStepContributions = function (step) {                                  // 459
  var self = this;                                                                            // 460
  var solution = self.solution;                                                               // 461
  var contributions = {};                                                                     // 462
  var weights = step.weights;                                                                 // 463
  _.each(step.terms, function (t, i) {                                                        // 464
    var w = (typeof weights === 'number' ? weights : weights[i]);                             // 465
    if (w && self.solution.evaluate(t)) {                                                     // 466
      contributions[t] = w;                                                                   // 467
    }                                                                                         // 468
  });                                                                                         // 469
  return contributions;                                                                       // 470
};                                                                                            // 471
                                                                                              // 472
var addCostsToSteps = function (pkg, versions, costs, steps) {                                // 473
  var pvs = _.map(versions, function (v) {                                                    // 474
    return pvVar(pkg, v);                                                                     // 475
  });                                                                                         // 476
  for (var j = 0; j < steps.length; j++) {                                                    // 477
    var step = steps[j];                                                                      // 478
    var costList = costs[j];                                                                  // 479
    if (costList.length !== versions.length) {                                                // 480
      throw new Error("Assertion failure: Bad lengths in addCostsToSteps");                   // 481
    }                                                                                         // 482
    for (var i = 0; i < versions.length; i++) {                                               // 483
      step.addTerm(pvs[i], costList[i]);                                                      // 484
    }                                                                                         // 485
  }                                                                                           // 486
};                                                                                            // 487
                                                                                              // 488
// Get an array of "Steps" that, when minimized in order, optimizes                           // 489
// the package version costs of `packages` (an array of String package                        // 490
// names) according to `pricerMode`, which may be                                             // 491
// `CS.VersionPricer.MODE_UPDATE` or a similar mode constant.                                 // 492
// Wraps `VersionPricer#priceVersions`, which is tasked with calculating                      // 493
// the cost of every version of every package.  This function iterates                        // 494
// over `packages` and puts the result into `Step` objects.                                   // 495
CS.Solver.prototype.getVersionCostSteps = function (stepBaseName, packages,                   // 496
                                                    pricerMode) {                             // 497
  var self = this;                                                                            // 498
  var major = new CS.Solver.Step(stepBaseName + '_major');                                    // 499
  var minor = new CS.Solver.Step(stepBaseName + '_minor');                                    // 500
  var patch = new CS.Solver.Step(stepBaseName + '_patch');                                    // 501
  var rest = new CS.Solver.Step(stepBaseName + '_rest');                                      // 502
                                                                                              // 503
  self.Profile.time(                                                                          // 504
    "calculate " + stepBaseName + " version costs",                                           // 505
    function () {                                                                             // 506
      _.each(packages, function (p) {                                                         // 507
        var versions = self.getVersions(p);                                                   // 508
        if (versions.length >= 2) {                                                           // 509
          var costs = self.pricer.priceVersions(versions, pricerMode);                        // 510
          addCostsToSteps(p, versions, costs, [major, minor, patch, rest]);                   // 511
        }                                                                                     // 512
      });                                                                                     // 513
    });                                                                                       // 514
                                                                                              // 515
  return [major, minor, patch, rest];                                                         // 516
};                                                                                            // 517
                                                                                              // 518
// Like `getVersionCostSteps`, but wraps                                                      // 519
// `VersionPricer#priceVersionsWithPrevious` instead of `#priceVersions`.                     // 520
// The cost function is "distance" from the previous versions passed in                       // 521
// as `packageAndVersion`.  (Actually it's a complicated function of the                      // 522
// previous and new version.)                                                                 // 523
CS.Solver.prototype.getVersionDistanceSteps = function (stepBaseName,                         // 524
                                                        packageAndVersions,                   // 525
                                                        takePatches) {                        // 526
  var self = this;                                                                            // 527
                                                                                              // 528
  var incompat = new CS.Solver.Step(stepBaseName + '_incompat');                              // 529
  var major = new CS.Solver.Step(stepBaseName + '_major');                                    // 530
  var minor = new CS.Solver.Step(stepBaseName + '_minor');                                    // 531
  var patch = new CS.Solver.Step(stepBaseName + '_patch');                                    // 532
  var rest = new CS.Solver.Step(stepBaseName + '_rest');                                      // 533
                                                                                              // 534
  self.Profile.time(                                                                          // 535
    "calculate " + stepBaseName + " distance costs",                                          // 536
    function () {                                                                             // 537
      _.each(packageAndVersions, function (pvArg) {                                           // 538
        var pkg = pvArg.package;                                                              // 539
        var previousVersion = pvArg.version;                                                  // 540
        var versions = self.getVersions(pkg);                                                 // 541
        if (versions.length >= 2) {                                                           // 542
          var costs = self.pricer.priceVersionsWithPrevious(                                  // 543
            versions, previousVersion, takePatches);                                          // 544
          addCostsToSteps(pkg, versions, costs,                                               // 545
                          [incompat, major, minor, patch, rest]);                             // 546
        }                                                                                     // 547
      });                                                                                     // 548
    });                                                                                       // 549
                                                                                              // 550
  return [incompat, major, minor, patch, rest];                                               // 551
};                                                                                            // 552
                                                                                              // 553
CS.Solver.prototype.currentVersionMap = function () {                                         // 554
  var self = this;                                                                            // 555
  var pvs = [];                                                                               // 556
  _.each(self.solution.getTrueVars(), function (x) {                                          // 557
    if (x.indexOf(' ') >= 0) {                                                                // 558
      // all variables with spaces in them are PackageAndVersions                             // 559
      var pv = CS.PackageAndVersion.fromString(x);                                            // 560
      pvs.push(pv);                                                                           // 561
    }                                                                                         // 562
  });                                                                                         // 563
                                                                                              // 564
  var versionMap = {};                                                                        // 565
  _.each(pvs, function (pv) {                                                                 // 566
    if (_.has(versionMap, pv.package)) {                                                      // 567
      throw new Error("Assertion failure: Selected two versions of " +                        // 568
                      pv.package + ", " +versionMap[pv.package] +                             // 569
                      " and " + pv.version);                                                  // 570
    }                                                                                         // 571
    versionMap[pv.package] = pv.version;                                                      // 572
  });                                                                                         // 573
                                                                                              // 574
  return versionMap;                                                                          // 575
};                                                                                            // 576
                                                                                              // 577
// Called to re-assign `self.solution` after a call to `self.logic.solve()`,                  // 578
// `solveAssuming`, or `minimize`.                                                            // 579
CS.Solver.prototype.setSolution = function (solution) {                                       // 580
  var self = this;                                                                            // 581
  self.solution = solution;                                                                   // 582
  if (! self.solution) {                                                                      // 583
    throw new Error("Unexpected unsatisfiability");                                           // 584
  }                                                                                           // 585
  // When we query a Solution, we always want to treat unknown variables                      // 586
  // as "false".  Logic Solver normally throws an error if you ask it                         // 587
  // to evaluate a formula containing a variable that isn't found in any                      // 588
  // constraints, as a courtesy to help catch bugs, but we treat                              // 589
  // variables as an open class of predicates ("foo" means package foo                        // 590
  // is selected, for example), and we don't ensure that every package                        // 591
  // or package version we might ask about is registered with the Solver.                     // 592
  // For example, when we go to explain a conflict or generate an error                       // 593
  // about an unknown package, we may ask about packages that were                            // 594
  // forbidden in an early analysis of the problem and never entered                          // 595
  // into the Solver.                                                                         // 596
  self.solution.ignoreUnknownVariables();                                                     // 597
};                                                                                            // 598
                                                                                              // 599
CS.Solver.prototype.getAnswer = function (options) {                                          // 600
  var self = this;                                                                            // 601
  return self.Profile.time("Solver#getAnswer", function () {                                  // 602
    return self._getAnswer(options);                                                          // 603
  });                                                                                         // 604
};                                                                                            // 605
                                                                                              // 606
CS.Solver.prototype._getAnswer = function (options) {                                         // 607
  var self = this;                                                                            // 608
  var input = self.input;                                                                     // 609
  var analysis = self.analysis;                                                               // 610
  var cache = input.catalogCache;                                                             // 611
  var allAnswers = (options && options.allAnswers); // for tests                              // 612
  var Profile = self.Profile;                                                                 // 613
                                                                                              // 614
  var logic;                                                                                  // 615
  Profile.time("new Logic.Solver (MiniSat start-up)", function () {                           // 616
    logic = self.logic = new Logic.Solver();                                                  // 617
  });                                                                                         // 618
                                                                                              // 619
  // require root dependencies                                                                // 620
  Profile.time("require root dependencies", function () {                                     // 621
    _.each(input.dependencies, function (p) {                                                 // 622
      logic.require(p);                                                                       // 623
    });                                                                                       // 624
  });                                                                                         // 625
                                                                                              // 626
  // generate package version variables for known, reachable packages                         // 627
  Profile.time("generate package variables", function () {                                    // 628
    _.each(_.keys(analysis.reachablePackages), function (p) {                                 // 629
      if (! _.has(analysis.packagesWithNoAllowedVersions, p)) {                               // 630
        var versionVars = _.map(self.getVersions(p),                                          // 631
                                function (v) {                                                // 632
                                  return pvVar(p, v);                                         // 633
                                });                                                           // 634
        // At most one of ["foo 1.0.0", "foo 1.0.1", ...] is true.                            // 635
        logic.require(Logic.atMostOne(versionVars));                                          // 636
        // The variable "foo" is true if and only if at least one of the                      // 637
        // variables ["foo 1.0.0", "foo 1.0.1", ...] is true.                                 // 638
        logic.require(Logic.equiv(p, Logic.or(versionVars)));                                 // 639
      }                                                                                       // 640
    });                                                                                       // 641
  });                                                                                         // 642
                                                                                              // 643
  // generate strong dependency requirements                                                  // 644
  Profile.time("generate dependency requirements", function () {                              // 645
    _.each(_.keys(analysis.reachablePackages), function (p) {                                 // 646
      _.each(self.getVersions(p), function (v) {                                              // 647
        _.each(cache.getDependencyMap(p, v), function (dep) {                                 // 648
          // `dep` is a CS.Dependency                                                         // 649
          if (! dep.isWeak) {                                                                 // 650
            var p2 = dep.packageConstraint.package;                                           // 651
            logic.require(Logic.implies(pvVar(p, v), p2));                                    // 652
          }                                                                                   // 653
        });                                                                                   // 654
      });                                                                                     // 655
    });                                                                                       // 656
  });                                                                                         // 657
                                                                                              // 658
  // generate constraints -- but technically don't enforce them, because                      // 659
  // we haven't forced the conflictVars to be false                                           // 660
  Profile.time("generate constraints", function () {                                          // 661
    _.each(analysis.constraints, function (c) {                                               // 662
      // We logically require that EITHER a constraint is marked as a                         // 663
      // conflict OR it comes from a package version that is not selected                     // 664
      // OR its constraint formula must be true.                                              // 665
      // (The constraint formula says that if toPackage is selected,                          // 666
      // then a version of it that satisfies our constraint must be true.)                    // 667
      logic.require(                                                                          // 668
        Logic.or(c.conflictVar,                                                               // 669
                 c.fromVar ? Logic.not(c.fromVar) : [],                                       // 670
                 self.getConstraintFormula(c.toPackage, c.vConstraint)));                     // 671
    });                                                                                       // 672
  });                                                                                         // 673
                                                                                              // 674
  // Establish the invariant of self.solution being a valid solution.                         // 675
  // From now on, if we add some new logical requirement to the solver                        // 676
  // that isn't necessarily true of `self.solution`, we must                                  // 677
  // recalculate `self.solution` and pass the new value to                                    // 678
  // self.setSolution.  It is our job to obtain the new solution in a                         // 679
  // way that ensures the solution exists and doesn't put the solver                          // 680
  // in an unsatisfiable state.  There are several ways to do this:                           // 681
  //                                                                                          // 682
  // * Calling `logic.solve()` and immediately throwing a fatal error                         // 683
  //   if there's no solution (not calling `setSolution` at all)                              // 684
  // * Calling `logic.solve()` in a situation where we know we have                           // 685
  //   not made the problem unsatisfiable                                                     // 686
  // * Calling `logic.solveAssuming(...)` and checking the result, only                       // 687
  //   using the solution if it exists                                                        // 688
  // * Calling `minimize()`, which always maintains satisfiability                            // 689
                                                                                              // 690
  Profile.time("pre-solve", function () {                                                     // 691
    self.setSolution(logic.solve());                                                          // 692
  });                                                                                         // 693
  // There is always a solution at this point, namely,                                        // 694
  // select all packages (including unknown packages), select                                 // 695
  // any version of each known package (excluding packages with                               // 696
  // "no allowed versions"), and set all conflictVars                                         // 697
  // to true.                                                                                 // 698
                                                                                              // 699
  // Forbid packages with no versions allowed by top-level constraints,                       // 700
  // which we didn't do earlier because we needed to establish an                             // 701
  // initial solution before asking the solver if it's possible to                            // 702
  // not use these packages.                                                                  // 703
  Profile.time("forbid packages with no matching versions", function () {                     // 704
    _.each(analysis.packagesWithNoAllowedVersions, function (constrs, p) {                    // 705
      var newSolution = logic.solveAssuming(Logic.not(p));                                    // 706
      if (newSolution) {                                                                      // 707
        self.setSolution(newSolution);                                                        // 708
        logic.forbid(p);                                                                      // 709
      } else {                                                                                // 710
        var error =                                                                           // 711
          'No version of ' + p + ' satisfies all constraints: ' +                             // 712
            _.map(constrs, function (constr) {                                                // 713
              return '@' + constr.constraintString;                                           // 714
            }).join(', ');                                                                    // 715
        error += '\n' + self.listConstraintsOnPackage(p);                                     // 716
        self.errors.push(error);                                                              // 717
      }                                                                                       // 718
    });                                                                                       // 719
    self.throwAnyErrors();                                                                    // 720
  });                                                                                         // 721
                                                                                              // 722
  // try not to use any unknown packages.  If the minimum is greater                          // 723
  // than 0, we'll throw an error later, after we apply the constraints                       // 724
  // and the cost function, so that we can explain the problem to the                         // 725
  // user in a convincing way.                                                                // 726
  self.minimize('unknown_packages', _.keys(analysis.unknownPackages));                        // 727
                                                                                              // 728
  // try not to set the conflictVar on any constraint.  If the minimum                        // 729
  // is greater than 0, we'll throw an error later, after we've run the                       // 730
  // cost function, so we can show a better error.                                            // 731
  // If there are conflicts, this minimization can be time-consuming                          // 732
  // (several seconds or more).  The strategy 'bottom-up' helps by                            // 733
  // looking for solutions with few conflicts first.                                          // 734
  self.minimize('conflicts', _.pluck(analysis.constraints, 'conflictVar'),                    // 735
                { strategy: 'bottom-up' });                                                   // 736
                                                                                              // 737
  // Try not to use "unanticipated" prerelease versions                                       // 738
  self.minimize('unanticipated_prereleases',                                                  // 739
                analysis.unanticipatedPrereleases);                                           // 740
                                                                                              // 741
  var previousRootSteps = self.getVersionDistanceSteps(                                       // 742
    'previous_root', analysis.previousRootDepVersions);                                       // 743
  // the "previous_root_incompat" step                                                        // 744
  var previousRootIncompat = previousRootSteps[0];                                            // 745
  // the "previous_root_major", "previous_root_minor", etc. steps                             // 746
  var previousRootVersionParts = previousRootSteps.slice(1);                                  // 747
                                                                                              // 748
  var toUpdate = _.filter(input.upgrade, function (p) {                                       // 749
    return analysis.reachablePackages[p] === true;                                            // 750
  });                                                                                         // 751
                                                                                              // 752
  // make sure packages that are being updated can still count as                             // 753
  // a previous_root for the purposes of previous_root_incompat                               // 754
  Profile.time("add terms to previous_root_incompat", function () {                           // 755
    _.each(toUpdate, function (p) {                                                           // 756
      if (input.isRootDependency(p) && input.isInPreviousSolution(p)) {                       // 757
        var parts = self.pricer.partitionVersions(                                            // 758
          self.getVersions(p), input.previousSolution[p]);                                    // 759
        _.each(parts.older.concat(parts.higherMajor), function (v) {                          // 760
          previousRootIncompat.addTerm(pvVar(p, v), 1);                                       // 761
        });                                                                                   // 762
      }                                                                                       // 763
    });                                                                                       // 764
  });                                                                                         // 765
                                                                                              // 766
  if (! input.allowIncompatibleUpdate) {                                                      // 767
    // Enforce that we don't make breaking changes to your root dependencies,                 // 768
    // unless you pass --allow-incompatible-update.  It will actually be enforced             // 769
    // farther down, but for now, we want to apply this constraint before handling            // 770
    // updates.                                                                               // 771
    self.minimize(previousRootIncompat);                                                      // 772
  }                                                                                           // 773
                                                                                              // 774
  self.minimize(self.getVersionCostSteps(                                                     // 775
    'update', toUpdate, CS.VersionPricer.MODE_UPDATE));                                       // 776
                                                                                              // 777
  if (input.allowIncompatibleUpdate) {                                                        // 778
    // If you pass `--allow-incompatible-update`, we will still try to minimize               // 779
    // version changes to root deps that break compatibility, but with a lower                // 780
    // priority than taking as-new-as-possible versions for `meteor update`.                  // 781
    self.minimize(previousRootIncompat);                                                      // 782
  }                                                                                           // 783
                                                                                              // 784
  self.minimize(previousRootVersionParts);                                                    // 785
                                                                                              // 786
  var otherPrevious = _.filter(_.map(input.previousSolution, function (v, p) {                // 787
    return new CS.PackageAndVersion(p, v);                                                    // 788
  }), function (pv) {                                                                         // 789
    var p = pv.package;                                                                       // 790
    return analysis.reachablePackages[p] === true &&                                          // 791
      ! input.isRootDependency(p);                                                            // 792
  });                                                                                         // 793
                                                                                              // 794
  self.minimize(self.getVersionDistanceSteps(                                                 // 795
    'previous_indirect', otherPrevious,                                                       // 796
    input.upgradeIndirectDepPatchVersions));                                                  // 797
                                                                                              // 798
  var newRootDeps = _.filter(input.dependencies, function (p) {                               // 799
    return ! input.isInPreviousSolution(p);                                                   // 800
  });                                                                                         // 801
                                                                                              // 802
  self.minimize(self.getVersionCostSteps(                                                     // 803
    'new_root', newRootDeps, CS.VersionPricer.MODE_UPDATE));                                  // 804
                                                                                              // 805
  // Lock down versions of all root, previous, and updating packages that                     // 806
  // are currently selected.  The reason to do this is to save the solver                     // 807
  // a bunch of work (i.e. improve performance) by not asking it to                           // 808
  // optimize the "unimportant" packages while also twiddling the versions                    // 809
  // of the "important" packages, which would just multiply the search space.                 // 810
  //                                                                                          // 811
  // The important packages are root deps, packages in the previous solution,                 // 812
  // and packages being upgraded.  At this point, we either have unique                       // 813
  // versions for them, or else there is some kind of trade-off, like a                       // 814
  // situation where raising the version of one package and lowering the                      // 815
  // version of another produces the same cost -- a tie between two solutions.                // 816
  // If we have a tie, it probably won't be broken by the unimportant                         // 817
  // packages, so we'll end up going with whatever we picked anyway.  (Note                   // 818
  // that we have already taken the unimportant packages into account in that                 // 819
  // we are only considering solutions where SOME versions can be chosen for                  // 820
  // them.)  Even if optimizing the unimportant packages (coming up next)                     // 821
  // was able to break a tie in the important packages, we care so little                     // 822
  // about the versions of the unimportant packages that it's a very weak                     // 823
  // signal.  In other words, the user might be better off with some tie-breaker              // 824
  // that looks only at the important packages anyway.                                        // 825
  Profile.time("lock down important versions", function () {                                  // 826
    _.each(self.currentVersionMap(), function (v, pkg) {                                      // 827
      if (input.isRootDependency(pkg) ||                                                      // 828
          input.isInPreviousSolution(pkg) ||                                                  // 829
          input.isUpgrading(pkg)) {                                                           // 830
        logic.require(Logic.implies(pkg, pvVar(pkg, v)));                                     // 831
      }                                                                                       // 832
    });                                                                                       // 833
  });                                                                                         // 834
                                                                                              // 835
  // new, indirect packages are the lowest priority                                           // 836
  var otherPackages = [];                                                                     // 837
  _.each(_.keys(analysis.reachablePackages), function (p) {                                   // 838
    if (! (input.isRootDependency(p) ||                                                       // 839
           input.isInPreviousSolution(p) ||                                                   // 840
           input.isUpgrading(p))) {                                                           // 841
      otherPackages.push(p);                                                                  // 842
    }                                                                                         // 843
  });                                                                                         // 844
                                                                                              // 845
  self.minimize(self.getVersionCostSteps(                                                     // 846
    'new_indirect', otherPackages,                                                            // 847
    CS.VersionPricer.MODE_GRAVITY_WITH_PATCHES));                                             // 848
                                                                                              // 849
  self.minimize('total_packages', _.keys(analysis.reachablePackages));                        // 850
                                                                                              // 851
  // throw errors about unknown packages                                                      // 852
  if (self.stepsByName['unknown_packages'].optimum > 0) {                                     // 853
    Profile.time("generate error for unknown packages", function () {                         // 854
      var unknownPackages = _.keys(analysis.unknownPackages);                                 // 855
      var unknownPackagesNeeded = _.filter(unknownPackages, function (p) {                    // 856
        return self.solution.evaluate(p);                                                     // 857
      });                                                                                     // 858
      _.each(unknownPackagesNeeded, function (p) {                                            // 859
        var requirers = _.filter(analysis.unknownPackages[p], function (pv) {                 // 860
          return self.solution.evaluate(pv);                                                  // 861
        });                                                                                   // 862
        var errorStr;                                                                         // 863
        if (CS.isIsobuildFeaturePackage(p)) {                                                 // 864
          errorStr = 'unsupported Isobuild feature "' + p + '"; see ' +                       // 865
            'https://github.com/meteor/meteor/wiki/Isobuild-Feature-Packages ' +              // 866
            'for a list of features and the minimum Meteor release required';                 // 867
        } else {                                                                              // 868
          errorStr = 'unknown package: ' + p;                                                 // 869
        }                                                                                     // 870
        _.each(requirers, function (pv) {                                                     // 871
          errorStr += '\nRequired by: ' + pv;                                                 // 872
        });                                                                                   // 873
        self.errors.push(errorStr);                                                           // 874
      });                                                                                     // 875
    });                                                                                       // 876
    self.throwAnyErrors();                                                                    // 877
  }                                                                                           // 878
                                                                                              // 879
  // throw errors about conflicts                                                             // 880
  if (self.stepsByName['conflicts'].optimum > 0) {                                            // 881
    self.throwConflicts();                                                                    // 882
  }                                                                                           // 883
                                                                                              // 884
  if ((! input.allowIncompatibleUpdate) &&                                                    // 885
      self.stepsByName['previous_root_incompat'].optimum > 0) {                               // 886
    // we have some "incompatible root changes", where we needed to change a                  // 887
    // version of a root dependency to a new version incompatible with the                    // 888
    // original, but --allow-incompatible-update hasn't been passed in.                       // 889
    // these are in the form of PackageAndVersion strings that we need.                       // 890
    var incompatRootChanges = _.keys(self.getStepContributions(                               // 891
      self.stepsByName['previous_root_incompat']));                                           // 892
                                                                                              // 893
    Profile.time("generate errors for incompatible root change", function () {                // 894
      var numActualErrors = 0;                                                                // 895
      _.each(incompatRootChanges, function (pvStr) {                                          // 896
        var pv = CS.PackageAndVersion.fromString(pvStr);                                      // 897
        // exclude packages with top-level equality constraints (added by user                // 898
        // or by the tool pinning a version)                                                  // 899
        if (! _.has(analysis.topLevelEqualityConstrainedPackages, pv.package)) {              // 900
          var prevVersion = input.previousSolution[pv.package];                               // 901
          self.errors.push(                                                                   // 902
            'Potentially incompatible change required to ' +                                  // 903
              'top-level dependency: ' +                                                      // 904
              pvStr + ', was ' + prevVersion + '.\n' +                                        // 905
              self.listConstraintsOnPackage(pv.package));                                     // 906
          numActualErrors++;                                                                  // 907
        }                                                                                     // 908
      });                                                                                     // 909
      if (numActualErrors) {                                                                  // 910
        self.errors.push(                                                                     // 911
          'To allow potentially incompatible changes to top-level ' +                         // 912
            'dependencies, you must pass --allow-incompatible-update ' +                      // 913
            'on the command line.');                                                          // 914
      }                                                                                       // 915
    });                                                                                       // 916
    self.throwAnyErrors();                                                                    // 917
  }                                                                                           // 918
                                                                                              // 919
  var result = {                                                                              // 920
    neededToUseUnanticipatedPrereleases: (                                                    // 921
      self.stepsByName['unanticipated_prereleases'].optimum > 0),                             // 922
    answer: Profile.time("generate version map", function () {                                // 923
      return self.currentVersionMap();                                                        // 924
    })                                                                                        // 925
  };                                                                                          // 926
                                                                                              // 927
  if (allAnswers) {                                                                           // 928
    Profile.time("generate all answers", function () {                                        // 929
      var allAnswersList = [result.answer];                                                   // 930
      var nextAnswer = function () {                                                          // 931
        var formula = self.solution.getFormula();                                             // 932
        var newSolution = logic.solveAssuming(Logic.not(formula));                            // 933
        if (newSolution) {                                                                    // 934
          self.setSolution(newSolution);                                                      // 935
          logic.forbid(formula);                                                              // 936
        }                                                                                     // 937
        return newSolution;                                                                   // 938
      };                                                                                      // 939
      while (nextAnswer()) {                                                                  // 940
        allAnswersList.push(self.currentVersionMap());                                        // 941
      }                                                                                       // 942
      result.allAnswers = allAnswersList;                                                     // 943
    });                                                                                       // 944
  };                                                                                          // 945
                                                                                              // 946
  return result;                                                                              // 947
};                                                                                            // 948
                                                                                              // 949
// Get a list of package-version variables that satisfy a given constraint.                   // 950
var getOkVersions = function (toPackage, vConstraint, targetVersions) {                       // 951
  return _.compact(_.map(targetVersions, function (v) {                                       // 952
    if (CS.isConstraintSatisfied(toPackage, vConstraint, v)) {                                // 953
      return pvVar(toPackage, v);                                                             // 954
    } else {                                                                                  // 955
      return null;                                                                            // 956
    }                                                                                         // 957
  }));                                                                                        // 958
};                                                                                            // 959
                                                                                              // 960
// The CS.Solver constructor turns this into a memoized method.                               // 961
// Memoizing the Formula object reduces clause generation a lot.                              // 962
var _getConstraintFormula = function (toPackage, vConstraint) {                               // 963
  var self = this;                                                                            // 964
                                                                                              // 965
  var targetVersions = self.getVersions(toPackage);                                           // 966
  var okVersions = getOkVersions(toPackage, vConstraint, targetVersions);                     // 967
                                                                                              // 968
  if (okVersions.length === targetVersions.length) {                                          // 969
    return Logic.TRUE;                                                                        // 970
  } else {                                                                                    // 971
    return Logic.or(Logic.not(toPackage), okVersions);                                        // 972
  }                                                                                           // 973
};                                                                                            // 974
                                                                                              // 975
CS.Solver.prototype.listConstraintsOnPackage = function (pkg) {                               // 976
  var self = this;                                                                            // 977
  var constraints = self.analysis.constraints;                                                // 978
                                                                                              // 979
  var result = 'Constraints on package "' + pkg + '":';                                       // 980
                                                                                              // 981
  _.each(constraints, function (c) {                                                          // 982
    if (c.toPackage === pkg) {                                                                // 983
      var paths;                                                                              // 984
      if (c.fromVar) {                                                                        // 985
        paths = self.getPathsToPackageVersion(                                                // 986
          CS.PackageAndVersion.fromString(c.fromVar));                                        // 987
      } else {                                                                                // 988
        paths = [['top level']];                                                              // 989
      }                                                                                       // 990
      _.each(paths, function (path) {                                                         // 991
        result += '\n* ' + (new PV.PackageConstraint(                                         // 992
          pkg, c.vConstraint.raw)) + ' <- ' + path.join(' <- ');                              // 993
      });                                                                                     // 994
    }                                                                                         // 995
  });                                                                                         // 996
                                                                                              // 997
  return result;                                                                              // 998
};                                                                                            // 999
                                                                                              // 1000
CS.Solver.prototype.throwConflicts = function () {                                            // 1001
  var self = this;                                                                            // 1002
                                                                                              // 1003
  var solution = self.solution;                                                               // 1004
  var constraints = self.analysis.constraints;                                                // 1005
                                                                                              // 1006
  self.Profile.time("generate error about conflicts", function () {                           // 1007
    _.each(constraints, function (c) {                                                        // 1008
      // c is a CS.Solver.Constraint                                                          // 1009
      if (solution.evaluate(c.conflictVar)) {                                                 // 1010
        // skipped this constraint                                                            // 1011
        var possibleVersions = self.getVersions(c.toPackage);                                 // 1012
        var chosenVersion = _.find(possibleVersions, function (v) {                           // 1013
          return solution.evaluate(pvVar(c.toPackage, v));                                    // 1014
        });                                                                                   // 1015
        if (! chosenVersion) {                                                                // 1016
          // this can't happen, because for a constraint to be a problem,                     // 1017
          // we must have chosen some version of the package it applies to!                   // 1018
          throw new Error("Internal error: Version not found");                               // 1019
        }                                                                                     // 1020
        var error = (                                                                         // 1021
          'Conflict: Constraint ' + (new PV.PackageConstraint(                                // 1022
            c.toPackage, c.vConstraint)) +                                                    // 1023
            ' is not satisfied by ' + c.toPackage + ' ' + chosenVersion + '.');               // 1024
                                                                                              // 1025
        error += '\n' + self.listConstraintsOnPackage(c.toPackage);                           // 1026
                                                                                              // 1027
        // Avoid printing exactly the same error twice.  eg, if we have two                   // 1028
        // different packages which have the same unsatisfiable constraint.                   // 1029
        if (self.errors.indexOf(error) === -1) {                                              // 1030
          self.errors.push(error);                                                            // 1031
        }                                                                                     // 1032
      }                                                                                       // 1033
    });                                                                                       // 1034
  });                                                                                         // 1035
                                                                                              // 1036
  // always throws, never returns                                                             // 1037
  self.throwAnyErrors();                                                                      // 1038
                                                                                              // 1039
  throw new Error("Internal error: conflicts could not be explained");                        // 1040
};                                                                                            // 1041
                                                                                              // 1042
// Takes a PackageVersion and returns an array of arrays of PackageVersions.                  // 1043
// If the `packageVersion` is not selected in `self.solution`, returns                        // 1044
// an empty array.  Otherwise, returns an array of all paths from                             // 1045
// root dependencies to the package, in reverse order.  In other words,                       // 1046
// the first element of each path is `packageVersion`,                                        // 1047
// and the last element is the selected version of a root dependency.                         // 1048
//                                                                                            // 1049
// Ok, it isn't all paths.  Because that would be crazy (combinatorial                        // 1050
// explosion).  It stops at root dependencies and tries to filter out                         // 1051
// ones that are definitely longer than another.                                              // 1052
CS.Solver.prototype.getPathsToPackageVersion = function (packageAndVersion) {                 // 1053
  check(packageAndVersion, CS.PackageAndVersion);                                             // 1054
  var self = this;                                                                            // 1055
  var input = self.input;                                                                     // 1056
  var cache = input.catalogCache;                                                             // 1057
  var solution = self.solution;                                                               // 1058
                                                                                              // 1059
  var versionMap = self.currentVersionMap();                                                  // 1060
  var hasDep = function (p1, p2) {                                                            // 1061
    // Include weak dependencies, because their constraints matter.                           // 1062
    return _.has(cache.getDependencyMap(p1, versionMap[p1]), p2);                             // 1063
  };                                                                                          // 1064
  var allPackages = _.keys(versionMap);                                                       // 1065
                                                                                              // 1066
  var getPaths = function (pv, _ignorePackageSet) {                                           // 1067
    if (! solution.evaluate(pv.toString())) {                                                 // 1068
      return [];                                                                              // 1069
    }                                                                                         // 1070
    var pkg = pv.package;                                                                     // 1071
                                                                                              // 1072
    if (input.isRootDependency(pkg)) {                                                        // 1073
      return [[pv]];                                                                          // 1074
    }                                                                                         // 1075
                                                                                              // 1076
    var newIgnorePackageSet = _.clone(_ignorePackageSet);                                     // 1077
    newIgnorePackageSet[pkg] = true;                                                          // 1078
                                                                                              // 1079
    var paths = [];                                                                           // 1080
    var shortestLength = null;                                                                // 1081
                                                                                              // 1082
    _.each(allPackages, function (p) {                                                        // 1083
      if ((! _.has(newIgnorePackageSet, p)) &&                                                // 1084
          solution.evaluate(p) &&                                                             // 1085
          hasDep(p, pkg)) {                                                                   // 1086
        var newPV = new CS.PackageAndVersion(p, versionMap[p]);                               // 1087
        _.each(getPaths(newPV, newIgnorePackageSet), function (path) {                        // 1088
          var newPath = [pv].concat(path);                                                    // 1089
          if ((! paths.length) || newPath.length < shortestLength) {                          // 1090
            paths.push(newPath);                                                              // 1091
            shortestLength = newPath.length;                                                  // 1092
          }                                                                                   // 1093
        });                                                                                   // 1094
      }                                                                                       // 1095
    });                                                                                       // 1096
                                                                                              // 1097
    return paths;                                                                             // 1098
  };                                                                                          // 1099
                                                                                              // 1100
  return getPaths(packageAndVersion, {});                                                     // 1101
};                                                                                            // 1102
                                                                                              // 1103
                                                                                              // 1104
CS.Solver.Constraint = function (fromVar, toPackage, vConstraint, conflictVar) {              // 1105
  this.fromVar = fromVar;                                                                     // 1106
  this.toPackage = toPackage;                                                                 // 1107
  this.vConstraint = vConstraint;                                                             // 1108
  this.conflictVar = conflictVar;                                                             // 1109
                                                                                              // 1110
  // this.fromVar is a return value of pvVar(p, v), or null for a                             // 1111
  // top-level constraint                                                                     // 1112
  check(this.fromVar, Match.OneOf(String, null));                                             // 1113
  check(this.toPackage, String); // package name                                              // 1114
  check(this.vConstraint, PV.VersionConstraint);                                              // 1115
  check(this.conflictVar, String);                                                            // 1116
};                                                                                            // 1117
                                                                                              // 1118
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                            //
// packages/constraint-solver/constraint-solver.js                                            //
//                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                              //
var PV = PackageVersion;                                                                      // 1
var CS = ConstraintSolver;                                                                    // 2
                                                                                              // 3
// This is the entry point for the constraint-solver package.  The tool                       // 4
// creates a ConstraintSolver.PackagesResolver and calls .resolve on it.                      // 5
                                                                                              // 6
CS.PackagesResolver = function (catalog, options) {                                           // 7
  var self = this;                                                                            // 8
                                                                                              // 9
  self.catalog = catalog;                                                                     // 10
  self.catalogCache = new CS.CatalogCache();                                                  // 11
  self.catalogLoader = new CS.CatalogLoader(self.catalog, self.catalogCache);                 // 12
                                                                                              // 13
  self._options = {                                                                           // 14
    nudge: options && options.nudge,                                                          // 15
    Profile: options && options.Profile,                                                      // 16
    // For resultCache, pass in an empty object `{}`, and PackagesResolver                    // 17
    // will put data on it.  Pass in the same object again to allow reusing                   // 18
    // the result from the previous run.                                                      // 19
    resultCache: options && options.resultCache                                               // 20
  };                                                                                          // 21
};                                                                                            // 22
                                                                                              // 23
// dependencies - an array of string names of packages (not slices)                           // 24
// constraints - an array of PV.PackageConstraints                                            // 25
// options:                                                                                   // 26
//  - upgrade - list of dependencies for which upgrade is prioritized higher                  // 27
//    than keeping the old version                                                            // 28
//  - previousSolution - mapping from package name to a version that was used in              // 29
//    the previous constraint solver run                                                      // 30
//  - anticipatedPrereleases: mapping from package name to version to true;                   // 31
//    included versions are the only pre-releases that are allowed to match                   // 32
//    constraints that don't specifically name them during the "try not to                    // 33
//    use unanticipated pre-releases" pass                                                    // 34
//  - allowIncompatibleUpdate: allows choosing versions of                                    // 35
//    root dependencies that are incompatible with the previous solution,                     // 36
//    if necessary to satisfy all constraints                                                 // 37
//  - upgradeIndirectDepPatchVersions: also upgrade indirect dependencies                     // 38
//    to newer patch versions, proactively                                                    // 39
//  - missingPreviousVersionIsError - throw an error if a package version in                  // 40
//    previousSolution is not found in the catalog                                            // 41
//  - supportedIsobuildFeaturePackages - map from package name to list of                     // 42
//    version strings of isobuild feature packages that are available in the                  // 43
//    catalog                                                                                 // 44
CS.PackagesResolver.prototype.resolve = function (dependencies, constraints,                  // 45
                                                  options) {                                  // 46
  var self = this;                                                                            // 47
  options = options || {};                                                                    // 48
  var Profile = (self._options.Profile || CS.DummyProfile);                                   // 49
                                                                                              // 50
  var input;                                                                                  // 51
  Profile.time("new CS.Input", function () {                                                  // 52
    input = new CS.Input(dependencies, constraints, self.catalogCache,                        // 53
                         _.pick(options,                                                      // 54
                                'upgrade',                                                    // 55
                                'anticipatedPrereleases',                                     // 56
                                'previousSolution',                                           // 57
                                'allowIncompatibleUpdate',                                    // 58
                                'upgradeIndirectDepPatchVersions'));                          // 59
  });                                                                                         // 60
                                                                                              // 61
  var resultCache = self._options.resultCache;                                                // 62
  if (resultCache &&                                                                          // 63
      resultCache.lastInput &&                                                                // 64
      _.isEqual(resultCache.lastInput,                                                        // 65
                input.toJSONable(true))) {                                                    // 66
    return resultCache.lastOutput;                                                            // 67
  }                                                                                           // 68
                                                                                              // 69
  if (options.supportedIsobuildFeaturePackages) {                                             // 70
    _.each(options.supportedIsobuildFeaturePackages, function (versions, pkg) {               // 71
      _.each(versions, function (version) {                                                   // 72
        input.catalogCache.addPackageVersion(pkg, version, []);                               // 73
      });                                                                                     // 74
    });                                                                                       // 75
  }                                                                                           // 76
                                                                                              // 77
  Profile.time(                                                                               // 78
    "Input#loadOnlyPreviousSolution",                                                         // 79
    function () {                                                                             // 80
      input.loadOnlyPreviousSolution(self.catalogLoader);                                     // 81
    });                                                                                       // 82
                                                                                              // 83
  if (options.previousSolution && options.missingPreviousVersionIsError) {                    // 84
    // see comment where missingPreviousVersionIsError is passed in                           // 85
    Profile.time("check for previous versions in catalog", function () {                      // 86
      _.each(options.previousSolution, function (version, pkg) {                              // 87
        if (! input.catalogCache.hasPackageVersion(pkg, version)) {                           // 88
          CS.throwConstraintSolverError(                                                      // 89
            "Package version not in catalog: " + pkg + " " + version);                        // 90
        }                                                                                     // 91
      });                                                                                     // 92
    });                                                                                       // 93
  }                                                                                           // 94
                                                                                              // 95
  var resolveOptions = {                                                                      // 96
    nudge: self._options.nudge,                                                               // 97
    Profile: self._options.Profile                                                            // 98
  };                                                                                          // 99
                                                                                              // 100
  var output = null;                                                                          // 101
  if (options.previousSolution && !input.upgrade && !input.upgradeIndirectDepPatchVersions) {
    // Try solving first with just the versions from previousSolution in                      // 103
    // the catalogCache, so that we don't have to solve the big problem                       // 104
    // if we don't have to. But don't do this if we're attempting to upgrade                  // 105
    // packages, because that would always result in just using the current                   // 106
    // version, hence disabling upgrades.                                                     // 107
    try {                                                                                     // 108
      output = CS.PackagesResolver._resolveWithInput(input, resolveOptions);                  // 109
    } catch (e) {                                                                             // 110
      if (e.constraintSolverError) {                                                          // 111
        output = null;                                                                        // 112
      } else {                                                                                // 113
        throw e;                                                                              // 114
      }                                                                                       // 115
    }                                                                                         // 116
  }                                                                                           // 117
                                                                                              // 118
  if (! output) {                                                                             // 119
    // do a solve with all package versions available in the catalog.                         // 120
    Profile.time(                                                                             // 121
      "Input#loadFromCatalog",                                                                // 122
      function () {                                                                           // 123
        input.loadFromCatalog(self.catalogLoader);                                            // 124
      });                                                                                     // 125
                                                                                              // 126
    // if we fail to find a solution this time, this will throw.                              // 127
    output = CS.PackagesResolver._resolveWithInput(input, resolveOptions);                    // 128
  }                                                                                           // 129
                                                                                              // 130
  if (resultCache) {                                                                          // 131
    resultCache.lastInput = input.toJSONable(true);                                           // 132
    resultCache.lastOutput = output;                                                          // 133
  }                                                                                           // 134
                                                                                              // 135
  return output;                                                                              // 136
};                                                                                            // 137
                                                                                              // 138
// Exposed for tests.                                                                         // 139
//                                                                                            // 140
// Options (all optional):                                                                    // 141
// - nudge (function to be called when possible to "nudge" the progress spinner)              // 142
// - allAnswers (for testing, calculate all possible answers and put an extra                 // 143
//   property named "allAnswers" on the result)                                               // 144
// - Profile (the profiler interface in `tools/profile.js`)                                   // 145
CS.PackagesResolver._resolveWithInput = function (input, options) {                           // 146
  options = options || {};                                                                    // 147
                                                                                              // 148
  if (Meteor.isServer &&                                                                      // 149
      process.env['METEOR_PRINT_CONSTRAINT_SOLVER_INPUT']) {                                  // 150
    console.log("CONSTRAINT_SOLVER_INPUT = ");                                                // 151
    console.log(JSON.stringify(input.toJSONable(), null, 2));                                 // 152
  }                                                                                           // 153
                                                                                              // 154
  var solver;                                                                                 // 155
  (options.Profile || CS.DummyProfile).time("new CS.Solver", function () {                    // 156
    solver = new CS.Solver(input, {                                                           // 157
      nudge: options.nudge,                                                                   // 158
      Profile: options.Profile                                                                // 159
    });                                                                                       // 160
  });                                                                                         // 161
                                                                                              // 162
  // Disable runtime type checks (they slow things down a bunch)                              // 163
  return Logic.disablingAssertions(function () {                                              // 164
    var result = solver.getAnswer({                                                           // 165
      allAnswers: options.allAnswers                                                          // 166
    });                                                                                       // 167
    // if we're here, no conflicts were found (or an error would have                         // 168
    // been thrown)                                                                           // 169
    return result;                                                                            // 170
  });                                                                                         // 171
};                                                                                            // 172
                                                                                              // 173
                                                                                              // 174
// - package: String package name                                                             // 175
// - vConstraint: a PackageVersion.VersionConstraint, or an object                            // 176
//   with an `alternatives` property lifted from one.                                         // 177
// - version: version String                                                                  // 178
CS.isConstraintSatisfied = function (pkg, vConstraint, version) {                             // 179
  return _.some(vConstraint.alternatives, function (simpleConstraint) {                       // 180
    var type = simpleConstraint.type;                                                         // 181
                                                                                              // 182
    if (type === "any-reasonable") {                                                          // 183
      return true;                                                                            // 184
    } else if (type === "exactly") {                                                          // 185
      var cVersion = simpleConstraint.versionString;                                          // 186
      return (cVersion === version);                                                          // 187
    } else if (type === 'compatible-with') {                                                  // 188
      var cv = PV.parse(simpleConstraint.versionString);                                      // 189
      var v = PV.parse(version);                                                              // 190
                                                                                              // 191
      // If the candidate version is less than the version named in the                       // 192
      // constraint, we are not satisfied.                                                    // 193
      if (PV.lessThan(v, cv)) {                                                               // 194
        return false;                                                                         // 195
      }                                                                                       // 196
                                                                                              // 197
      // To be compatible, the two versions must have the same major version                  // 198
      // number.                                                                              // 199
      if (v.major !== cv.major) {                                                             // 200
        return false;                                                                         // 201
      }                                                                                       // 202
                                                                                              // 203
      return true;                                                                            // 204
    } else {                                                                                  // 205
      throw Error("Unknown constraint type: " + type);                                        // 206
    }                                                                                         // 207
  });                                                                                         // 208
};                                                                                            // 209
                                                                                              // 210
CS.throwConstraintSolverError = function (message) {                                          // 211
  var e = new Error(message);                                                                 // 212
  e.constraintSolverError = true;                                                             // 213
  throw e;                                                                                    // 214
};                                                                                            // 215
                                                                                              // 216
// This function is duplicated in tools/compiler.js.                                          // 217
CS.isIsobuildFeaturePackage = function (packageName) {                                        // 218
  return /^isobuild:/.test(packageName);                                                      // 219
};                                                                                            // 220
                                                                                              // 221
                                                                                              // 222
// Implements the Profile interface (as we use it) but doesn't do                             // 223
// anything.                                                                                  // 224
CS.DummyProfile = function (bucket, f) {                                                      // 225
  return f;                                                                                   // 226
};                                                                                            // 227
CS.DummyProfile.time = function (bucket, f) {                                                 // 228
  return f();                                                                                 // 229
};                                                                                            // 230
                                                                                              // 231
////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
