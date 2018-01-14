(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                   //
// packages/check/match.js                                                                                           //
//                                                                                                                   //
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                     //
// XXX docs                                                                                                          // 1
                                                                                                                     // 2
// Things we explicitly do NOT support:                                                                              // 3
//    - heterogenous arrays                                                                                          // 4
                                                                                                                     // 5
var currentArgumentChecker = new Meteor.EnvironmentVariable;                                                         // 6
var isPlainObject = require("./isPlainObject.js").isPlainObject;                                                     // 7
                                                                                                                     // 8
/**                                                                                                                  // 9
 * @summary Check that a value matches a [pattern](#matchpatterns).                                                  // 10
 * If the value does not match the pattern, throw a `Match.Error`.                                                   // 11
 *                                                                                                                   // 12
 * Particularly useful to assert that arguments to a function have the right                                         // 13
 * types and structure.                                                                                              // 14
 * @locus Anywhere                                                                                                   // 15
 * @param {Any} value The value to check                                                                             // 16
 * @param {MatchPattern} pattern The pattern to match                                                                // 17
 * `value` against                                                                                                   // 18
 */                                                                                                                  // 19
var check = exports.check = function (value, pattern) {                                                              // 20
  // Record that check got called, if somebody cared.                                                                // 21
  //                                                                                                                 // 22
  // We use getOrNullIfOutsideFiber so that it's OK to call check()                                                  // 23
  // from non-Fiber server contexts; the downside is that if you forget to                                           // 24
  // bindEnvironment on some random callback in your method/publisher,                                               // 25
  // it might not find the argumentChecker and you'll get an error about                                             // 26
  // not checking an argument that it looks like you're checking (instead                                            // 27
  // of just getting a "Node code must run in a Fiber" error).                                                       // 28
  var argChecker = currentArgumentChecker.getOrNullIfOutsideFiber();                                                 // 29
  if (argChecker)                                                                                                    // 30
    argChecker.checking(value);                                                                                      // 31
  var result = testSubtree(value, pattern);                                                                          // 32
  if (result) {                                                                                                      // 33
    var err = new Match.Error(result.message);                                                                       // 34
    if (result.path) {                                                                                               // 35
      err.message += " in field " + result.path;                                                                     // 36
      err.path = result.path;                                                                                        // 37
    }                                                                                                                // 38
    throw err;                                                                                                       // 39
  }                                                                                                                  // 40
};                                                                                                                   // 41
                                                                                                                     // 42
/**                                                                                                                  // 43
 * @namespace Match                                                                                                  // 44
 * @summary The namespace for all Match types and methods.                                                           // 45
 */                                                                                                                  // 46
var Match = exports.Match = {                                                                                        // 47
  Optional: function (pattern) {                                                                                     // 48
    return new Optional(pattern);                                                                                    // 49
  },                                                                                                                 // 50
  Maybe: function (pattern) {                                                                                        // 51
    return new Maybe(pattern);                                                                                       // 52
  },                                                                                                                 // 53
  OneOf: function (/*arguments*/) {                                                                                  // 54
    return new OneOf(_.toArray(arguments));                                                                          // 55
  },                                                                                                                 // 56
  Any: ['__any__'],                                                                                                  // 57
  Where: function (condition) {                                                                                      // 58
    return new Where(condition);                                                                                     // 59
  },                                                                                                                 // 60
  ObjectIncluding: function (pattern) {                                                                              // 61
    return new ObjectIncluding(pattern);                                                                             // 62
  },                                                                                                                 // 63
  ObjectWithValues: function (pattern) {                                                                             // 64
    return new ObjectWithValues(pattern);                                                                            // 65
  },                                                                                                                 // 66
  // Matches only signed 32-bit integers                                                                             // 67
  Integer: ['__integer__'],                                                                                          // 68
                                                                                                                     // 69
  // XXX matchers should know how to describe themselves for errors                                                  // 70
  Error: Meteor.makeErrorType("Match.Error", function (msg) {                                                        // 71
    this.message = "Match error: " + msg;                                                                            // 72
    // The path of the value that failed to match. Initially empty, this gets                                        // 73
    // populated by catching and rethrowing the exception as it goes back up the                                     // 74
    // stack.                                                                                                        // 75
    // E.g.: "vals[3].entity.created"                                                                                // 76
    this.path = "";                                                                                                  // 77
    // If this gets sent over DDP, don't give full internal details but at least                                     // 78
    // provide something better than 500 Internal server error.                                                      // 79
    this.sanitizedError = new Meteor.Error(400, "Match failed");                                                     // 80
  }),                                                                                                                // 81
                                                                                                                     // 82
  // Tests to see if value matches pattern. Unlike check, it merely returns true                                     // 83
  // or false (unless an error other than Match.Error was thrown). It does not                                       // 84
  // interact with _failIfArgumentsAreNotAllChecked.                                                                 // 85
  // XXX maybe also implement a Match.match which returns more information about                                     // 86
  //     failures but without using exception handling or doing what check()                                         // 87
  //     does with _failIfArgumentsAreNotAllChecked and Meteor.Error conversion                                      // 88
                                                                                                                     // 89
  /**                                                                                                                // 90
   * @summary Returns true if the value matches the pattern.                                                         // 91
   * @locus Anywhere                                                                                                 // 92
   * @param {Any} value The value to check                                                                           // 93
   * @param {MatchPattern} pattern The pattern to match `value` against                                              // 94
   */                                                                                                                // 95
  test: function (value, pattern) {                                                                                  // 96
    return !testSubtree(value, pattern);                                                                             // 97
  },                                                                                                                 // 98
                                                                                                                     // 99
  // Runs `f.apply(context, args)`. If check() is not called on every element of                                     // 100
  // `args` (either directly or in the first level of an array), throws an error                                     // 101
  // (using `description` in the message).                                                                           // 102
  //                                                                                                                 // 103
  _failIfArgumentsAreNotAllChecked: function (f, context, args, description) {                                       // 104
    var argChecker = new ArgumentChecker(args, description);                                                         // 105
    var result = currentArgumentChecker.withValue(argChecker, function () {                                          // 106
      return f.apply(context, args);                                                                                 // 107
    });                                                                                                              // 108
    // If f didn't itself throw, make sure it checked all of its arguments.                                          // 109
    argChecker.throwUnlessAllArgumentsHaveBeenChecked();                                                             // 110
    return result;                                                                                                   // 111
  }                                                                                                                  // 112
};                                                                                                                   // 113
                                                                                                                     // 114
var Optional = function (pattern) {                                                                                  // 115
  this.pattern = pattern;                                                                                            // 116
};                                                                                                                   // 117
                                                                                                                     // 118
var Maybe = function (pattern) {                                                                                     // 119
  this.pattern = pattern;                                                                                            // 120
};                                                                                                                   // 121
                                                                                                                     // 122
var OneOf = function (choices) {                                                                                     // 123
  if (_.isEmpty(choices))                                                                                            // 124
    throw new Error("Must provide at least one choice to Match.OneOf");                                              // 125
  this.choices = choices;                                                                                            // 126
};                                                                                                                   // 127
                                                                                                                     // 128
var Where = function (condition) {                                                                                   // 129
  this.condition = condition;                                                                                        // 130
};                                                                                                                   // 131
                                                                                                                     // 132
var ObjectIncluding = function (pattern) {                                                                           // 133
  this.pattern = pattern;                                                                                            // 134
};                                                                                                                   // 135
                                                                                                                     // 136
var ObjectWithValues = function (pattern) {                                                                          // 137
  this.pattern = pattern;                                                                                            // 138
};                                                                                                                   // 139
                                                                                                                     // 140
var stringForErrorMessage = function (value, options) {                                                              // 141
  options = options || {};                                                                                           // 142
                                                                                                                     // 143
  if ( value === null ) return "null";                                                                               // 144
                                                                                                                     // 145
  if ( options.onlyShowType ) {                                                                                      // 146
    return typeof value;                                                                                             // 147
  }                                                                                                                  // 148
                                                                                                                     // 149
  // Your average non-object things.  Saves from doing the try/catch below for.                                      // 150
  if ( typeof value !== "object" ) {                                                                                 // 151
    return EJSON.stringify(value)                                                                                    // 152
  }                                                                                                                  // 153
                                                                                                                     // 154
  try {                                                                                                              // 155
    // Find objects with circular references since EJSON doesn't support them yet (Issue #4778 + Unaccepted PR)      // 156
    // If the native stringify is going to choke, EJSON.stringify is going to choke too.                             // 157
    JSON.stringify(value);                                                                                           // 158
  } catch (stringifyError) {                                                                                         // 159
    if ( stringifyError.name === "TypeError" ) {                                                                     // 160
      return typeof value;                                                                                           // 161
    }                                                                                                                // 162
  }                                                                                                                  // 163
                                                                                                                     // 164
  return EJSON.stringify(value);                                                                                     // 165
};                                                                                                                   // 166
                                                                                                                     // 167
var typeofChecks = [                                                                                                 // 168
  [String, "string"],                                                                                                // 169
  [Number, "number"],                                                                                                // 170
  [Boolean, "boolean"],                                                                                              // 171
  // While we don't allow undefined/function in EJSON, this is good for optional                                     // 172
  // arguments with OneOf.                                                                                           // 173
  [Function, "function"],                                                                                            // 174
  [undefined, "undefined"]                                                                                           // 175
];                                                                                                                   // 176
                                                                                                                     // 177
// Return `false` if it matches. Otherwise, return an object with a `message` and a `path` field.                    // 178
var testSubtree = function (value, pattern) {                                                                        // 179
  // Match anything!                                                                                                 // 180
  if (pattern === Match.Any)                                                                                         // 181
    return false;                                                                                                    // 182
                                                                                                                     // 183
  // Basic atomic types.                                                                                             // 184
  // Do not match boxed objects (e.g. String, Boolean)                                                               // 185
  for (var i = 0; i < typeofChecks.length; ++i) {                                                                    // 186
    if (pattern === typeofChecks[i][0]) {                                                                            // 187
      if (typeof value === typeofChecks[i][1])                                                                       // 188
        return false;                                                                                                // 189
      return {                                                                                                       // 190
        message: "Expected " + typeofChecks[i][1] + ", got " + stringForErrorMessage(value, { onlyShowType: true }),
        path: ""                                                                                                     // 192
      };                                                                                                             // 193
    }                                                                                                                // 194
  }                                                                                                                  // 195
                                                                                                                     // 196
  if (pattern === null) {                                                                                            // 197
    if (value === null) {                                                                                            // 198
      return false;                                                                                                  // 199
    }                                                                                                                // 200
    return {                                                                                                         // 201
      message: "Expected null, got " + stringForErrorMessage(value),                                                 // 202
      path: ""                                                                                                       // 203
    };                                                                                                               // 204
  }                                                                                                                  // 205
                                                                                                                     // 206
  // Strings, numbers, and booleans match literally. Goes well with Match.OneOf.                                     // 207
  if (typeof pattern === "string" || typeof pattern === "number" || typeof pattern === "boolean") {                  // 208
    if (value === pattern)                                                                                           // 209
      return false;                                                                                                  // 210
    return {                                                                                                         // 211
      message: "Expected " + pattern + ", got " + stringForErrorMessage(value),                                      // 212
      path: ""                                                                                                       // 213
    };                                                                                                               // 214
  }                                                                                                                  // 215
                                                                                                                     // 216
  // Match.Integer is special type encoded with array                                                                // 217
  if (pattern === Match.Integer) {                                                                                   // 218
    // There is no consistent and reliable way to check if variable is a 64-bit                                      // 219
    // integer. One of the popular solutions is to get reminder of division by 1                                     // 220
    // but this method fails on really large floats with big precision.                                              // 221
    // E.g.: 1.348192308491824e+23 % 1 === 0 in V8                                                                   // 222
    // Bitwise operators work consistantly but always cast variable to 32-bit                                        // 223
    // signed integer according to JavaScript specs.                                                                 // 224
    if (typeof value === "number" && (value | 0) === value)                                                          // 225
      return false;                                                                                                  // 226
    return {                                                                                                         // 227
      message: "Expected Integer, got " + stringForErrorMessage(value),                                              // 228
      path: ""                                                                                                       // 229
    };                                                                                                               // 230
  }                                                                                                                  // 231
                                                                                                                     // 232
  // "Object" is shorthand for Match.ObjectIncluding({});                                                            // 233
  if (pattern === Object)                                                                                            // 234
    pattern = Match.ObjectIncluding({});                                                                             // 235
                                                                                                                     // 236
  // Array (checked AFTER Any, which is implemented as an Array).                                                    // 237
  if (pattern instanceof Array) {                                                                                    // 238
    if (pattern.length !== 1) {                                                                                      // 239
      return {                                                                                                       // 240
        message: "Bad pattern: arrays must have one type element" + stringForErrorMessage(pattern),                  // 241
        path: ""                                                                                                     // 242
      };                                                                                                             // 243
    }                                                                                                                // 244
    if (!_.isArray(value) && !_.isArguments(value)) {                                                                // 245
      return {                                                                                                       // 246
        message: "Expected array, got " + stringForErrorMessage(value),                                              // 247
        path: ""                                                                                                     // 248
      };                                                                                                             // 249
    }                                                                                                                // 250
                                                                                                                     // 251
    for (var i = 0, length = value.length; i < length; i++) {                                                        // 252
      var result = testSubtree(value[i], pattern[0]);                                                                // 253
      if (result) {                                                                                                  // 254
        result.path = _prependPath(i, result.path);                                                                  // 255
        return result;                                                                                               // 256
      }                                                                                                              // 257
    }                                                                                                                // 258
    return false;                                                                                                    // 259
  }                                                                                                                  // 260
                                                                                                                     // 261
  // Arbitrary validation checks. The condition can return false or throw a                                          // 262
  // Match.Error (ie, it can internally use check()) to fail.                                                        // 263
  if (pattern instanceof Where) {                                                                                    // 264
    var result;                                                                                                      // 265
    try {                                                                                                            // 266
      result = pattern.condition(value);                                                                             // 267
    } catch (err) {                                                                                                  // 268
      if (!(err instanceof Match.Error))                                                                             // 269
        throw err;                                                                                                   // 270
      return {                                                                                                       // 271
        message: err.message,                                                                                        // 272
        path: err.path                                                                                               // 273
      };                                                                                                             // 274
    }                                                                                                                // 275
    if (result)                                                                                                      // 276
      return false;                                                                                                  // 277
    // XXX this error is terrible                                                                                    // 278
    return {                                                                                                         // 279
      message: "Failed Match.Where validation",                                                                      // 280
      path: ""                                                                                                       // 281
    };                                                                                                               // 282
  }                                                                                                                  // 283
                                                                                                                     // 284
                                                                                                                     // 285
  if (pattern instanceof Maybe) {                                                                                    // 286
    pattern = Match.OneOf(undefined, null, pattern.pattern);                                                         // 287
  }                                                                                                                  // 288
  else if (pattern instanceof Optional) {                                                                            // 289
    pattern = Match.OneOf(undefined, pattern.pattern);                                                               // 290
  }                                                                                                                  // 291
                                                                                                                     // 292
  if (pattern instanceof OneOf) {                                                                                    // 293
    for (var i = 0; i < pattern.choices.length; ++i) {                                                               // 294
      var result = testSubtree(value, pattern.choices[i]);                                                           // 295
      if (!result) {                                                                                                 // 296
        // No error? Yay, return.                                                                                    // 297
        return false;                                                                                                // 298
      }                                                                                                              // 299
      // Match errors just mean try another choice.                                                                  // 300
    }                                                                                                                // 301
    // XXX this error is terrible                                                                                    // 302
    return {                                                                                                         // 303
      message: "Failed Match.OneOf, Match.Maybe or Match.Optional validation",                                       // 304
      path: ""                                                                                                       // 305
    };                                                                                                               // 306
  }                                                                                                                  // 307
                                                                                                                     // 308
  // A function that isn't something we special-case is assumed to be a                                              // 309
  // constructor.                                                                                                    // 310
  if (pattern instanceof Function) {                                                                                 // 311
    if (value instanceof pattern)                                                                                    // 312
      return false;                                                                                                  // 313
    return {                                                                                                         // 314
      message: "Expected " + (pattern.name ||"particular constructor"),                                              // 315
      path: ""                                                                                                       // 316
    };                                                                                                               // 317
  }                                                                                                                  // 318
                                                                                                                     // 319
  var unknownKeysAllowed = false;                                                                                    // 320
  var unknownKeyPattern;                                                                                             // 321
  if (pattern instanceof ObjectIncluding) {                                                                          // 322
    unknownKeysAllowed = true;                                                                                       // 323
    pattern = pattern.pattern;                                                                                       // 324
  }                                                                                                                  // 325
  if (pattern instanceof ObjectWithValues) {                                                                         // 326
    unknownKeysAllowed = true;                                                                                       // 327
    unknownKeyPattern = [pattern.pattern];                                                                           // 328
    pattern = {};  // no required keys                                                                               // 329
  }                                                                                                                  // 330
                                                                                                                     // 331
  if (typeof pattern !== "object") {                                                                                 // 332
    return {                                                                                                         // 333
      message: "Bad pattern: unknown pattern type",                                                                  // 334
      path: ""                                                                                                       // 335
    };                                                                                                               // 336
  }                                                                                                                  // 337
                                                                                                                     // 338
  // An object, with required and optional keys. Note that this does NOT do                                          // 339
  // structural matches against objects of special types that happen to match                                        // 340
  // the pattern: this really needs to be a plain old {Object}!                                                      // 341
  if (typeof value !== 'object') {                                                                                   // 342
    return {                                                                                                         // 343
      message: "Expected object, got " + typeof value,                                                               // 344
      path: ""                                                                                                       // 345
    };                                                                                                               // 346
  }                                                                                                                  // 347
  if (value === null) {                                                                                              // 348
    return {                                                                                                         // 349
      message: "Expected object, got null",                                                                          // 350
      path: ""                                                                                                       // 351
    };                                                                                                               // 352
  }                                                                                                                  // 353
  if (! isPlainObject(value)) {                                                                                      // 354
    return {                                                                                                         // 355
      message: "Expected plain object",                                                                              // 356
      path: ""                                                                                                       // 357
    };                                                                                                               // 358
  }                                                                                                                  // 359
                                                                                                                     // 360
  var requiredPatterns = {};                                                                                         // 361
  var optionalPatterns = {};                                                                                         // 362
  _.each(pattern, function (subPattern, key) {                                                                       // 363
    if (subPattern instanceof Optional || subPattern instanceof Maybe)                                               // 364
      optionalPatterns[key] = subPattern.pattern;                                                                    // 365
    else                                                                                                             // 366
      requiredPatterns[key] = subPattern;                                                                            // 367
  });                                                                                                                // 368
                                                                                                                     // 369
  //XXX: replace with underscore's _.allKeys if Meteor updates underscore to 1.8+ (or lodash)                        // 370
  var allKeys = function(obj){                                                                                       // 371
    var keys = [];                                                                                                   // 372
    if (_.isObject(obj)){                                                                                            // 373
      for (var key in obj) keys.push(key);                                                                           // 374
    }                                                                                                                // 375
    return keys;                                                                                                     // 376
  }                                                                                                                  // 377
                                                                                                                     // 378
  for (var keys = allKeys(value), i = 0, length = keys.length; i < length; i++) {                                    // 379
    var key = keys[i];                                                                                               // 380
    var subValue = value[key];                                                                                       // 381
    if (_.has(requiredPatterns, key)) {                                                                              // 382
      var result = testSubtree(subValue, requiredPatterns[key]);                                                     // 383
      if (result) {                                                                                                  // 384
        result.path = _prependPath(key, result.path);                                                                // 385
        return result;                                                                                               // 386
      }                                                                                                              // 387
      delete requiredPatterns[key];                                                                                  // 388
    } else if (_.has(optionalPatterns, key)) {                                                                       // 389
      var result = testSubtree(subValue, optionalPatterns[key]);                                                     // 390
      if (result) {                                                                                                  // 391
        result.path = _prependPath(key, result.path);                                                                // 392
        return result;                                                                                               // 393
      }                                                                                                              // 394
    } else {                                                                                                         // 395
      if (!unknownKeysAllowed) {                                                                                     // 396
        return {                                                                                                     // 397
          message: "Unknown key",                                                                                    // 398
          path: key                                                                                                  // 399
        };                                                                                                           // 400
      }                                                                                                              // 401
      if (unknownKeyPattern) {                                                                                       // 402
        var result = testSubtree(subValue, unknownKeyPattern[0]);                                                    // 403
        if (result) {                                                                                                // 404
          result.path = _prependPath(key, result.path);                                                              // 405
          return result;                                                                                             // 406
        }                                                                                                            // 407
      }                                                                                                              // 408
    }                                                                                                                // 409
  }                                                                                                                  // 410
                                                                                                                     // 411
  var keys = _.keys(requiredPatterns);                                                                               // 412
  if (keys.length) {                                                                                                 // 413
    return {                                                                                                         // 414
      message: "Missing key '" + keys[0] + "'",                                                                      // 415
      path: ""                                                                                                       // 416
    };                                                                                                               // 417
  }                                                                                                                  // 418
};                                                                                                                   // 419
                                                                                                                     // 420
var ArgumentChecker = function (args, description) {                                                                 // 421
  var self = this;                                                                                                   // 422
  // Make a SHALLOW copy of the arguments. (We'll be doing identity checks                                           // 423
  // against its contents.)                                                                                          // 424
  self.args = _.clone(args);                                                                                         // 425
  // Since the common case will be to check arguments in order, and we splice                                        // 426
  // out arguments when we check them, make it so we splice out from the end                                         // 427
  // rather than the beginning.                                                                                      // 428
  self.args.reverse();                                                                                               // 429
  self.description = description;                                                                                    // 430
};                                                                                                                   // 431
                                                                                                                     // 432
_.extend(ArgumentChecker.prototype, {                                                                                // 433
  checking: function (value) {                                                                                       // 434
    var self = this;                                                                                                 // 435
    if (self._checkingOneValue(value))                                                                               // 436
      return;                                                                                                        // 437
    // Allow check(arguments, [String]) or check(arguments.slice(1), [String])                                       // 438
    // or check([foo, bar], [String]) to count... but only if value wasn't                                           // 439
    // itself an argument.                                                                                           // 440
    if (_.isArray(value) || _.isArguments(value)) {                                                                  // 441
      _.each(value, _.bind(self._checkingOneValue, self));                                                           // 442
    }                                                                                                                // 443
  },                                                                                                                 // 444
  _checkingOneValue: function (value) {                                                                              // 445
    var self = this;                                                                                                 // 446
    for (var i = 0; i < self.args.length; ++i) {                                                                     // 447
      // Is this value one of the arguments? (This can have a false positive if                                      // 448
      // the argument is an interned primitive, but it's still a good enough                                         // 449
      // check.)                                                                                                     // 450
      // (NaN is not === to itself, so we have to check specially.)                                                  // 451
      if (value === self.args[i] || (_.isNaN(value) && _.isNaN(self.args[i]))) {                                     // 452
        self.args.splice(i, 1);                                                                                      // 453
        return true;                                                                                                 // 454
      }                                                                                                              // 455
    }                                                                                                                // 456
    return false;                                                                                                    // 457
  },                                                                                                                 // 458
  throwUnlessAllArgumentsHaveBeenChecked: function () {                                                              // 459
    var self = this;                                                                                                 // 460
    if (!_.isEmpty(self.args))                                                                                       // 461
      throw new Error("Did not check() all arguments during " +                                                      // 462
                      self.description);                                                                             // 463
  }                                                                                                                  // 464
});                                                                                                                  // 465
                                                                                                                     // 466
var _jsKeywords = ["do", "if", "in", "for", "let", "new", "try", "var", "case",                                      // 467
  "else", "enum", "eval", "false", "null", "this", "true", "void", "with",                                           // 468
  "break", "catch", "class", "const", "super", "throw", "while", "yield",                                            // 469
  "delete", "export", "import", "public", "return", "static", "switch",                                              // 470
  "typeof", "default", "extends", "finally", "package", "private", "continue",                                       // 471
  "debugger", "function", "arguments", "interface", "protected", "implements",                                       // 472
  "instanceof"];                                                                                                     // 473
                                                                                                                     // 474
// Assumes the base of path is already escaped properly                                                              // 475
// returns key + base                                                                                                // 476
var _prependPath = function (key, base) {                                                                            // 477
  if ((typeof key) === "number" || key.match(/^[0-9]+$/))                                                            // 478
    key = "[" + key + "]";                                                                                           // 479
  else if (!key.match(/^[a-z_$][0-9a-z_$]*$/i) || _.contains(_jsKeywords, key))                                      // 480
    key = JSON.stringify([key]);                                                                                     // 481
                                                                                                                     // 482
  if (base && base[0] !== "[")                                                                                       // 483
    return key + '.' + base;                                                                                         // 484
  return key + base;                                                                                                 // 485
};                                                                                                                   // 486
                                                                                                                     // 487
                                                                                                                     // 488
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                   //
// packages/check/isPlainObject.js                                                                                   //
//                                                                                                                   //
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                     //
// Copy of jQuery.isPlainObject for the server side from jQuery v3.1.1.                                              // 1
                                                                                                                     // 2
var class2type = {};                                                                                                 // 3
                                                                                                                     // 4
var toString = class2type.toString;                                                                                  // 5
                                                                                                                     // 6
var hasOwn = class2type.hasOwnProperty;                                                                              // 7
                                                                                                                     // 8
var fnToString = hasOwn.toString;                                                                                    // 9
                                                                                                                     // 10
var ObjectFunctionString = fnToString.call(Object);                                                                  // 11
                                                                                                                     // 12
var getProto = Object.getPrototypeOf;                                                                                // 13
                                                                                                                     // 14
exports.isPlainObject = function( obj ) {                                                                            // 15
  var proto,                                                                                                         // 16
    Ctor;                                                                                                            // 17
                                                                                                                     // 18
  // Detect obvious negatives                                                                                        // 19
  // Use toString instead of jQuery.type to catch host objects                                                       // 20
  if (!obj || toString.call(obj) !== "[object Object]") {                                                            // 21
    return false;                                                                                                    // 22
  }                                                                                                                  // 23
                                                                                                                     // 24
  proto = getProto(obj);                                                                                             // 25
                                                                                                                     // 26
  // Objects with no prototype (e.g., `Object.create( null )`) are plain                                             // 27
  if (!proto) {                                                                                                      // 28
    return true;                                                                                                     // 29
  }                                                                                                                  // 30
                                                                                                                     // 31
  // Objects with prototype are plain iff they were constructed by a global Object function                          // 32
  Ctor = hasOwn.call(proto, "constructor") && proto.constructor;                                                     // 33
  return typeof Ctor === "function" && fnToString.call(Ctor) === ObjectFunctionString;                               // 34
};                                                                                                                   // 35
                                                                                                                     // 36
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                   //
// packages/check/match_test.js                                                                                      //
//                                                                                                                   //
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                     //
Tinytest.add("check - check", function (test) {                                                                      // 1
  var matches = function (value, pattern) {                                                                          // 2
    var error;                                                                                                       // 3
    try {                                                                                                            // 4
      check(value, pattern);                                                                                         // 5
    } catch (e) {                                                                                                    // 6
      error = e;                                                                                                     // 7
    }                                                                                                                // 8
    test.isFalse(error);                                                                                             // 9
    test.isTrue(Match.test(value, pattern));                                                                         // 10
  };                                                                                                                 // 11
  var fails = function (value, pattern) {                                                                            // 12
    var error;                                                                                                       // 13
    try {                                                                                                            // 14
      check(value, pattern);                                                                                         // 15
    } catch (e) {                                                                                                    // 16
      error = e;                                                                                                     // 17
    }                                                                                                                // 18
    test.isTrue(error);                                                                                              // 19
    test.instanceOf(error, Match.Error);                                                                             // 20
    test.isFalse(Match.test(value, pattern));                                                                        // 21
  };                                                                                                                 // 22
                                                                                                                     // 23
  // Atoms.                                                                                                          // 24
  var pairs = [                                                                                                      // 25
    ["foo", String],                                                                                                 // 26
    ["", String],                                                                                                    // 27
    [0, Number],                                                                                                     // 28
    [42.59, Number],                                                                                                 // 29
    [NaN, Number],                                                                                                   // 30
    [Infinity, Number],                                                                                              // 31
    [true, Boolean],                                                                                                 // 32
    [false, Boolean],                                                                                                // 33
    [function(){}, Function],                                                                                        // 34
    [undefined, undefined],                                                                                          // 35
    [null, null]                                                                                                     // 36
  ];                                                                                                                 // 37
  _.each(pairs, function (pair) {                                                                                    // 38
    matches(pair[0], Match.Any);                                                                                     // 39
    _.each([String, Number, Boolean, undefined, null], function (type) {                                             // 40
      if (type === pair[1]) {                                                                                        // 41
        matches(pair[0], type);                                                                                      // 42
        matches(pair[0], Match.Optional(type));                                                                      // 43
        matches(undefined, Match.Optional(type));                                                                    // 44
        matches(pair[0], Match.Maybe(type));                                                                         // 45
        matches(undefined, Match.Maybe(type));                                                                       // 46
        matches(null, Match.Maybe(type));                                                                            // 47
        matches(pair[0], Match.Where(function () {                                                                   // 48
          check(pair[0], type);                                                                                      // 49
          return true;                                                                                               // 50
        }));                                                                                                         // 51
        matches(pair[0], Match.Where(function () {                                                                   // 52
          try {                                                                                                      // 53
            check(pair[0], type);                                                                                    // 54
            return true;                                                                                             // 55
          } catch (e) {                                                                                              // 56
            return false;                                                                                            // 57
          }                                                                                                          // 58
        }));                                                                                                         // 59
      } else {                                                                                                       // 60
        fails(pair[0], type);                                                                                        // 61
        matches(pair[0], Match.OneOf(type, pair[1]));                                                                // 62
        matches(pair[0], Match.OneOf(pair[1], type));                                                                // 63
        fails(pair[0], Match.Where(function () {                                                                     // 64
          check(pair[0], type);                                                                                      // 65
          return true;                                                                                               // 66
        }));                                                                                                         // 67
        fails(pair[0], Match.Where(function () {                                                                     // 68
          try {                                                                                                      // 69
            check(pair[0], type);                                                                                    // 70
            return true;                                                                                             // 71
          } catch (e) {                                                                                              // 72
            return false;                                                                                            // 73
          }                                                                                                          // 74
        }));                                                                                                         // 75
      }                                                                                                              // 76
      if ( type !== null ) fails(null, Match.Optional(type)); // Optional doesn't allow null, but does match on null type
      fails(pair[0], [type]);                                                                                        // 78
      fails(pair[0], Object);                                                                                        // 79
    });                                                                                                              // 80
  });                                                                                                                // 81
  fails(true, Match.OneOf(String, Number, undefined, null, [Boolean]));                                              // 82
  fails(new String("foo"), String);                                                                                  // 83
  fails(new Boolean(true), Boolean);                                                                                 // 84
  fails(new Number(123), Number);                                                                                    // 85
                                                                                                                     // 86
  matches([1, 2, 3], [Number]);                                                                                      // 87
  matches([], [Number]);                                                                                             // 88
  fails([1, 2, 3, "4"], [Number]);                                                                                   // 89
  fails([1, 2, 3, [4]], [Number]);                                                                                   // 90
  matches([1, 2, 3, "4"], [Match.OneOf(Number, String)]);                                                            // 91
                                                                                                                     // 92
  matches({}, Object);                                                                                               // 93
  matches({}, {});                                                                                                   // 94
  matches({foo: 42}, Object);                                                                                        // 95
  fails({foo: 42}, {});                                                                                              // 96
  matches({a: 1, b:2}, {b: Number, a: Number});                                                                      // 97
  fails({a: 1, b:2}, {b: Number});                                                                                   // 98
  matches({a: 1, b:2}, Match.ObjectIncluding({b: Number}));                                                          // 99
  fails({a: 1, b:2}, Match.ObjectIncluding({b: String}));                                                            // 100
  fails({a: 1, b:2}, Match.ObjectIncluding({c: String}));                                                            // 101
  fails({}, {a: Number});                                                                                            // 102
  matches({nodeType: 1}, {nodeType: Match.Any});                                                                     // 103
  matches({nodeType: 1}, Match.ObjectIncluding({nodeType: Match.Any}));                                              // 104
  fails({nodeType: 1}, {nodeType: String});                                                                          // 105
  fails({}, Match.ObjectIncluding({nodeType: Match.Any}));                                                           // 106
                                                                                                                     // 107
  // Match.Optional does not match on a null value, unless the allowed type is itself "null"                         // 108
  fails(null, Match.Optional(String));                                                                               // 109
  fails(null, Match.Optional(undefined));                                                                            // 110
  matches(null, Match.Optional(null));                                                                               // 111
                                                                                                                     // 112
  // on the other hand, undefined, works fine for all of them                                                        // 113
  matches(undefined, Match.Optional(String));                                                                        // 114
  matches(undefined, Match.Optional(undefined));                                                                     // 115
  matches(undefined, Match.Optional(null));                                                                          // 116
                                                                                                                     // 117
  fails(true, Match.Optional(String)); // different should still fail                                                // 118
  matches("String", Match.Optional(String)); // same should pass                                                     // 119
                                                                                                                     // 120
  matches({}, {a: Match.Optional(Number)});                                                                          // 121
  matches({a: 1}, {a: Match.Optional(Number)});                                                                      // 122
  fails({a: true}, {a: Match.Optional(Number)});                                                                     // 123
  fails({a: undefined}, {a: Match.Optional(Number)});                                                                // 124
                                                                                                                     // 125
  // .Maybe requires undefined, null or the allowed type in order to match                                           // 126
  matches(null, Match.Maybe(String));                                                                                // 127
  matches(null, Match.Maybe(undefined));                                                                             // 128
  matches(null, Match.Maybe(null));                                                                                  // 129
                                                                                                                     // 130
  matches(undefined, Match.Maybe(String));                                                                           // 131
  matches(undefined, Match.Maybe(undefined));                                                                        // 132
  matches(undefined, Match.Maybe(null));                                                                             // 133
                                                                                                                     // 134
  fails(true, Match.Maybe(String)); // different should still fail                                                   // 135
  matches("String", Match.Maybe(String)); // same should pass                                                        // 136
                                                                                                                     // 137
  matches({}, {a: Match.Maybe(Number)});                                                                             // 138
  matches({a: 1}, {a: Match.Maybe(Number)});                                                                         // 139
  fails({a: true}, {a: Match.Maybe(Number)});                                                                        // 140
  // Match.Optional means "or undefined" at the top level but "or absent" in                                         // 141
  // objects.                                                                                                        // 142
  // Match.Maybe should behave the same as Match.Optional in objects                                                 // 143
  // including handling nulls                                                                                        // 144
  fails({a: undefined}, {a: Match.Maybe(Number)});                                                                   // 145
  fails({a: null}, {a: Match.Maybe(Number)});                                                                        // 146
  var F = function () {                                                                                              // 147
    this.x = 123;                                                                                                    // 148
  };                                                                                                                 // 149
  fails(new F, { x: 123 });                                                                                          // 150
                                                                                                                     // 151
  matches({}, Match.ObjectWithValues(Number));                                                                       // 152
  matches({x: 1}, Match.ObjectWithValues(Number));                                                                   // 153
  matches({x: 1, y: 2}, Match.ObjectWithValues(Number));                                                             // 154
  fails({x: 1, y: "2"}, Match.ObjectWithValues(Number));                                                             // 155
                                                                                                                     // 156
  matches("asdf", "asdf");                                                                                           // 157
  fails("asdf", "monkey");                                                                                           // 158
  matches(123, 123);                                                                                                 // 159
  fails(123, 456);                                                                                                   // 160
  fails("123", 123);                                                                                                 // 161
  fails(123, "123");                                                                                                 // 162
  matches(true, true);                                                                                               // 163
  matches(false, false);                                                                                             // 164
  fails(true, false);                                                                                                // 165
  fails(true, "true");                                                                                               // 166
  fails("false", false);                                                                                             // 167
                                                                                                                     // 168
  matches(/foo/, RegExp);                                                                                            // 169
  fails(/foo/, String);                                                                                              // 170
  matches(new Date, Date);                                                                                           // 171
  fails(new Date, Number);                                                                                           // 172
  matches(EJSON.newBinary(42), Match.Where(EJSON.isBinary));                                                         // 173
  fails([], Match.Where(EJSON.isBinary));                                                                            // 174
                                                                                                                     // 175
  matches(42, Match.Where(function (x) { return x % 2 === 0; }));                                                    // 176
  fails(43, Match.Where(function (x) { return x % 2 === 0; }));                                                      // 177
                                                                                                                     // 178
  matches({                                                                                                          // 179
    a: "something",                                                                                                  // 180
    b: [                                                                                                             // 181
      {x: 42, k: null},                                                                                              // 182
      {x: 43, k: true, p: ["yay"]}                                                                                   // 183
    ]                                                                                                                // 184
  }, {a: String, b: [Match.ObjectIncluding({                                                                         // 185
    x: Number,                                                                                                       // 186
    k: Match.OneOf(null, Boolean)})]});                                                                              // 187
                                                                                                                     // 188
                                                                                                                     // 189
  // Match.Integer                                                                                                   // 190
  matches(-1, Match.Integer);                                                                                        // 191
  matches(0, Match.Integer);                                                                                         // 192
  matches(1, Match.Integer);                                                                                         // 193
  matches(-2147483648, Match.Integer); // INT_MIN                                                                    // 194
  matches(2147483647, Match.Integer); // INT_MAX                                                                     // 195
  fails(123.33, Match.Integer);                                                                                      // 196
  fails(.33, Match.Integer);                                                                                         // 197
  fails(1.348192308491824e+23, Match.Integer);                                                                       // 198
  fails(NaN, Match.Integer);                                                                                         // 199
  fails(Infinity, Match.Integer);                                                                                    // 200
  fails(-Infinity, Match.Integer);                                                                                   // 201
  fails({}, Match.Integer);                                                                                          // 202
  fails([], Match.Integer);                                                                                          // 203
  fails(function () {}, Match.Integer);                                                                              // 204
  fails(new Date, Match.Integer);                                                                                    // 205
                                                                                                                     // 206
                                                                                                                     // 207
  // Test non-plain objects.                                                                                         // 208
  var parentObj = {foo: "bar"};                                                                                      // 209
  var childObj = Object.assign(Object.create(parentObj), {bar: "foo"});                                              // 210
  matches(parentObj, Object);                                                                                        // 211
  fails(parentObj, {foo: String, bar: String});                                                                      // 212
  fails(parentObj, {bar: String});                                                                                   // 213
  matches(parentObj, {foo: String});                                                                                 // 214
  fails(childObj, Object);                                                                                           // 215
  fails(childObj, {foo: String, bar: String});                                                                       // 216
  fails(childObj, {bar: String});                                                                                    // 217
  fails(childObj, {foo: String});                                                                                    // 218
                                                                                                                     // 219
  // Functions                                                                                                       // 220
  var testFunction = function () {};                                                                                 // 221
  matches(testFunction, Function);                                                                                   // 222
  fails(5, Function);                                                                                                // 223
                                                                                                                     // 224
  // Circular Reference "Classes"                                                                                    // 225
                                                                                                                     // 226
  var TestInstanceChild = function () {};                                                                            // 227
  var TestInstanceParent = function (child) {                                                                        // 228
    child._parent = this;                                                                                            // 229
    this.child = child;                                                                                              // 230
  };                                                                                                                 // 231
                                                                                                                     // 232
  var testInstanceChild = new TestInstanceChild()                                                                    // 233
  var testInstanceParent = new TestInstanceParent(testInstanceChild);                                                // 234
                                                                                                                     // 235
  matches(TestInstanceParent, Function);                                                                             // 236
  matches(testInstanceParent, TestInstanceParent);                                                                   // 237
  fails(testInstanceChild, TestInstanceParent);                                                                      // 238
                                                                                                                     // 239
  matches(testInstanceParent, Match.Optional(TestInstanceParent));                                                   // 240
  matches(testInstanceParent, Match.Maybe(TestInstanceParent));                                                      // 241
                                                                                                                     // 242
  // Circular Reference Objects                                                                                      // 243
                                                                                                                     // 244
  var circleFoo = {};                                                                                                // 245
  var circleBar = {};                                                                                                // 246
  circleFoo.bar = circleBar;                                                                                         // 247
  circleBar.foo = circleFoo;                                                                                         // 248
  fails(circleFoo, null);                                                                                            // 249
                                                                                                                     // 250
  // Test that "arguments" is treated like an array.                                                                 // 251
  var argumentsMatches = function () {                                                                               // 252
    matches(arguments, [Number]);                                                                                    // 253
  };                                                                                                                 // 254
  argumentsMatches();                                                                                                // 255
  argumentsMatches(1);                                                                                               // 256
  argumentsMatches(1, 2);                                                                                            // 257
  var argumentsFails = function () {                                                                                 // 258
    fails(arguments, [Number]);                                                                                      // 259
  };                                                                                                                 // 260
  argumentsFails("123");                                                                                             // 261
  argumentsFails(1, "23");                                                                                           // 262
});                                                                                                                  // 263
                                                                                                                     // 264
Tinytest.add("check - argument checker", function (test) {                                                           // 265
  var checksAllArguments = function (f /*arguments*/) {                                                              // 266
    Match._failIfArgumentsAreNotAllChecked(                                                                          // 267
      f, {}, _.toArray(arguments).slice(1), "test");                                                                 // 268
  };                                                                                                                 // 269
  checksAllArguments(function () {});                                                                                // 270
  checksAllArguments(function (x) {check(x, Match.Any);}, undefined);                                                // 271
  checksAllArguments(function (x) {check(x, Match.Any);}, null);                                                     // 272
  checksAllArguments(function (x) {check(x, Match.Any);}, false);                                                    // 273
  checksAllArguments(function (x) {check(x, Match.Any);}, true);                                                     // 274
  checksAllArguments(function (x) {check(x, Match.Any);}, 0);                                                        // 275
  checksAllArguments(function (a, b, c) {                                                                            // 276
    check(a, String);                                                                                                // 277
    check(b, Boolean);                                                                                               // 278
    check(c, Match.Optional(Number));                                                                                // 279
  }, "foo", true);                                                                                                   // 280
  checksAllArguments(function () {                                                                                   // 281
    check(arguments, [Number]);                                                                                      // 282
  }, 1, 2, 4);                                                                                                       // 283
  checksAllArguments(function(x) {                                                                                   // 284
    check(x, Number);                                                                                                // 285
    check(_.toArray(arguments).slice(1), [String]);                                                                  // 286
  }, 1, "foo", "bar", "baz");                                                                                        // 287
  // NaN values                                                                                                      // 288
  checksAllArguments(function (x) {                                                                                  // 289
    check(x, Number);                                                                                                // 290
  }, NaN);                                                                                                           // 291
                                                                                                                     // 292
  var doesntCheckAllArguments = function (f /*arguments*/) {                                                         // 293
    try {                                                                                                            // 294
      Match._failIfArgumentsAreNotAllChecked(                                                                        // 295
        f, {}, _.toArray(arguments).slice(1), "test");                                                               // 296
      test.fail({message: "expected _failIfArgumentsAreNotAllChecked to throw"});                                    // 297
    } catch (e) {                                                                                                    // 298
      test.equal(e.message, "Did not check() all arguments during test");                                            // 299
    }                                                                                                                // 300
  };                                                                                                                 // 301
                                                                                                                     // 302
  doesntCheckAllArguments(function () {}, undefined);                                                                // 303
  doesntCheckAllArguments(function () {}, null);                                                                     // 304
  doesntCheckAllArguments(function () {}, 1);                                                                        // 305
  doesntCheckAllArguments(function () {                                                                              // 306
    check(_.toArray(arguments).slice(1), [String]);                                                                  // 307
  }, 1, "asdf", "foo");                                                                                              // 308
  doesntCheckAllArguments(function (x, y) {                                                                          // 309
    check(x, Boolean);                                                                                               // 310
  }, true, false);                                                                                                   // 311
  // One "true" check doesn't count for all.                                                                         // 312
  doesntCheckAllArguments(function (x, y) {                                                                          // 313
    check(x, Boolean);                                                                                               // 314
  }, true, true);                                                                                                    // 315
  // For non-primitives, we really do require that each arg gets checked.                                            // 316
  doesntCheckAllArguments(function (x, y) {                                                                          // 317
    check(x, [Boolean]);                                                                                             // 318
    check(x, [Boolean]);                                                                                             // 319
  }, [true], [true]);                                                                                                // 320
                                                                                                                     // 321
                                                                                                                     // 322
  // In an ideal world this test would fail, but we currently can't                                                  // 323
  // differentiate between "two calls to check x, both of which are true" and                                        // 324
  // "check x and check y, both of which are true" (for any interned primitive                                       // 325
  // type).                                                                                                          // 326
  checksAllArguments(function (x, y) {                                                                               // 327
    check(x, Boolean);                                                                                               // 328
    check(x, Boolean);                                                                                               // 329
  }, true, true);                                                                                                    // 330
});                                                                                                                  // 331
                                                                                                                     // 332
Tinytest.add("check - Match error path", function (test) {                                                           // 333
  var match = function (value, pattern, expectedPath) {                                                              // 334
    try {                                                                                                            // 335
      check(value, pattern);                                                                                         // 336
    } catch (err) {                                                                                                  // 337
      // XXX just for FF 3.6, its JSON stringification prefers "\u000a" to "\n"                                      // 338
      err.path = err.path.replace(/\\u000a/, "\\n");                                                                 // 339
      if (err.path != expectedPath)                                                                                  // 340
        test.fail({                                                                                                  // 341
          type: "match-error-path",                                                                                  // 342
          message: "The path of Match.Error doesn't match.",                                                         // 343
          pattern: JSON.stringify(pattern),                                                                          // 344
          value: JSON.stringify(value),                                                                              // 345
          path: err.path,                                                                                            // 346
          expectedPath: expectedPath                                                                                 // 347
        });                                                                                                          // 348
    }                                                                                                                // 349
  };                                                                                                                 // 350
                                                                                                                     // 351
  match({ foo: [ { bar: 3 }, {bar: "something"} ] }, { foo: [ { bar: Number } ] }, "foo[1].bar");                    // 352
  // Complicated case with arrays, $, whitespace and quotes!                                                         // 353
  match([{ $FoO: { "bar baz\n\"'": 3 } }], [{ $FoO: { "bar baz\n\"'": String } }], "[0].$FoO[\"bar baz\\n\\\"'\"]");
  // Numbers only, can be accessed w/o quotes                                                                        // 355
  match({ "1231": 123 }, { "1231": String }, "[1231]");                                                              // 356
  match({ "1234abcd": 123 }, { "1234abcd": String }, "[\"1234abcd\"]");                                              // 357
  match({ $set: { people: "nice" } }, { $set: { people: [String] } }, "$set.people");                                // 358
  match({ _underscore: "should work" }, { _underscore: Number }, "_underscore");                                     // 359
  // Nested array looks nice                                                                                         // 360
  match([[["something", "here"], []], [["string", 123]]], [[[String]]], "[1][0][1]");                                // 361
  // Object nested in arrays should look nice, too!                                                                  // 362
  match([[[{ foo: "something" }, { foo: "here"}],                                                                    // 363
          [{ foo: "asdf" }]],                                                                                        // 364
         [[{ foo: 123 }]]],                                                                                          // 365
        [[[{ foo: String }]]], "[1][0][0].foo");                                                                     // 366
                                                                                                                     // 367
  // JS keyword                                                                                                      // 368
  match({ "return": 0 }, { "return": String }, "[\"return\"]");                                                      // 369
});                                                                                                                  // 370
                                                                                                                     // 371
Tinytest.add("check - Match error message", function (test) {                                                        // 372
  var match = function (value, pattern, expectedMessage) {                                                           // 373
    try {                                                                                                            // 374
      check(value, pattern);                                                                                         // 375
    } catch (err) {                                                                                                  // 376
      if (err.message !== "Match error: " + expectedMessage)                                                         // 377
        test.fail({                                                                                                  // 378
          type: "match-error-message",                                                                               // 379
          message: "The message of Match.Error doesn't match.",                                                      // 380
          pattern: JSON.stringify(pattern),                                                                          // 381
          value: JSON.stringify(value),                                                                              // 382
          errorMessage: err.message,                                                                                 // 383
          expectedErrorMessage: expectedMessage                                                                      // 384
        });                                                                                                          // 385
    }                                                                                                                // 386
  };                                                                                                                 // 387
                                                                                                                     // 388
  match(2, String, "Expected string, got number");                                                                   // 389
  match({key: 0}, Number, "Expected number, got object");                                                            // 390
  match(null, Boolean, "Expected boolean, got null");                                                                // 391
  match("string", undefined, "Expected undefined, got string");                                                      // 392
  match(true, null, "Expected null, got true");                                                                      // 393
  match({}, Match.ObjectIncluding({ bar: String }), "Missing key 'bar'");                                            // 394
  match(null, Object, "Expected object, got null");                                                                  // 395
  match(null, Function, "Expected function, got null");                                                              // 396
  match("bar", "foo", "Expected foo, got \"bar\"");                                                                  // 397
  match(3.14, Match.Integer, "Expected Integer, got 3.14");                                                          // 398
  match(false, [Boolean], "Expected array, got false");                                                              // 399
  match([null, null], [String], "Expected string, got null in field [0]");                                           // 400
  match(2, {key: 2}, "Expected object, got number");                                                                 // 401
  match(null, {key: 2}, "Expected object, got null");                                                                // 402
  match(new Date, {key: 2}, "Expected plain object");                                                                // 403
                                                                                                                     // 404
  var TestInstanceChild = function () {};                                                                            // 405
  var TestInstanceParent = function (child) {                                                                        // 406
    child._parent = this;                                                                                            // 407
    this.child = child;                                                                                              // 408
  };                                                                                                                 // 409
                                                                                                                     // 410
  var testInstanceChild = new TestInstanceChild()                                                                    // 411
  var testInstanceParent = new TestInstanceParent(testInstanceChild);                                                // 412
  match(testInstanceChild, TestInstanceParent, "Expected " + (TestInstanceParent.name || "particular constructor"));
                                                                                                                     // 414
  var circleFoo = {};                                                                                                // 415
  var circleBar = {};                                                                                                // 416
  circleFoo.bar = circleBar;                                                                                         // 417
  circleBar.foo = circleFoo;                                                                                         // 418
  match(circleFoo, null, "Expected null, got object");                                                               // 419
                                                                                                                     // 420
});                                                                                                                  // 421
                                                                                                                     // 422
// Regression test for https://github.com/meteor/meteor/issues/2136                                                  // 423
Meteor.isServer && Tinytest.addAsync("check - non-fiber check works", function (test, onComplete) {                  // 424
  var Fiber = Npm.require('fibers');                                                                                 // 425
                                                                                                                     // 426
  // We can only call test.isTrue inside normal Meteor Fibery code, so give us a                                     // 427
  // bindEnvironment way to get back.                                                                                // 428
  var report = Meteor.bindEnvironment(function (success) {                                                           // 429
    test.isTrue(success);                                                                                            // 430
    onComplete();                                                                                                    // 431
  });                                                                                                                // 432
                                                                                                                     // 433
  // Get out of a fiber with process.nextTick and ensure that we can still use                                       // 434
  // check.                                                                                                          // 435
  process.nextTick(function () {                                                                                     // 436
    var success = true;                                                                                              // 437
    if (Fiber.current)                                                                                               // 438
      success = false;                                                                                               // 439
    if (success) {                                                                                                   // 440
      try {                                                                                                          // 441
        check(true, Boolean);                                                                                        // 442
      } catch (e) {                                                                                                  // 443
        success = false;                                                                                             // 444
      }                                                                                                              // 445
    }                                                                                                                // 446
    report(success);                                                                                                 // 447
  });                                                                                                                // 448
});                                                                                                                  // 449
                                                                                                                     // 450
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
