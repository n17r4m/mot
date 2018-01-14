(function(){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                //
// packages/logging/logging.js                                                                                    //
//                                                                                                                //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                  //
Log = function () {                                                                                               // 1
  return Log.info.apply(this, arguments);                                                                         // 2
};                                                                                                                // 3
                                                                                                                  // 4
/// FOR TESTING                                                                                                   // 5
var intercept = 0;                                                                                                // 6
var interceptedLines = [];                                                                                        // 7
var suppress = 0;                                                                                                 // 8
                                                                                                                  // 9
// Intercept the next 'count' calls to a Log function. The actual                                                 // 10
// lines printed to the console can be cleared and read by calling                                                // 11
// Log._intercepted().                                                                                            // 12
Log._intercept = function (count) {                                                                               // 13
  intercept += count;                                                                                             // 14
};                                                                                                                // 15
                                                                                                                  // 16
// Suppress the next 'count' calls to a Log function. Use this to stop                                            // 17
// tests from spamming the console, especially with red errors that                                               // 18
// might look like a failing test.                                                                                // 19
Log._suppress = function (count) {                                                                                // 20
  suppress += count;                                                                                              // 21
};                                                                                                                // 22
                                                                                                                  // 23
// Returns intercepted lines and resets the intercept counter.                                                    // 24
Log._intercepted = function () {                                                                                  // 25
  var lines = interceptedLines;                                                                                   // 26
  interceptedLines = [];                                                                                          // 27
  intercept = 0;                                                                                                  // 28
  return lines;                                                                                                   // 29
};                                                                                                                // 30
                                                                                                                  // 31
// Either 'json' or 'colored-text'.                                                                               // 32
//                                                                                                                // 33
// When this is set to 'json', print JSON documents that are parsed by another                                    // 34
// process ('satellite' or 'meteor run'). This other process should call                                          // 35
// 'Log.format' for nice output.                                                                                  // 36
//                                                                                                                // 37
// When this is set to 'colored-text', call 'Log.format' before printing.                                         // 38
// This should be used for logging from within satellite, since there is no                                       // 39
// other process that will be reading its standard output.                                                        // 40
Log.outputFormat = 'json';                                                                                        // 41
                                                                                                                  // 42
var LEVEL_COLORS = {                                                                                              // 43
  debug: 'green',                                                                                                 // 44
  // leave info as the default color                                                                              // 45
  warn: 'magenta',                                                                                                // 46
  error: 'red'                                                                                                    // 47
};                                                                                                                // 48
                                                                                                                  // 49
var META_COLOR = 'blue';                                                                                          // 50
                                                                                                                  // 51
// Default colors cause readability problems on Windows Powershell,                                               // 52
// switch to bright variants. While still capable of millions of                                                  // 53
// operations per second, the benchmark showed a 25%+ increase in                                                 // 54
// ops per second (on Node 8) by caching "process.platform".                                                      // 55
var isWin32 = typeof process === 'object' && process.platform === 'win32';                                        // 56
var platformColor = function (color) {                                                                            // 57
  if (isWin32 && typeof color === 'string' && color.slice(-6) !== 'Bright') {                                     // 58
    return color + 'Bright';                                                                                      // 59
  }                                                                                                               // 60
  return color;                                                                                                   // 61
};                                                                                                                // 62
                                                                                                                  // 63
// XXX package                                                                                                    // 64
var RESTRICTED_KEYS = ['time', 'timeInexact', 'level', 'file', 'line',                                            // 65
                        'program', 'originApp', 'satellite', 'stderr'];                                           // 66
                                                                                                                  // 67
var FORMATTED_KEYS = RESTRICTED_KEYS.concat(['app', 'message']);                                                  // 68
                                                                                                                  // 69
var logInBrowser = function (obj) {                                                                               // 70
  var str = Log.format(obj);                                                                                      // 71
                                                                                                                  // 72
  // XXX Some levels should be probably be sent to the server                                                     // 73
  var level = obj.level;                                                                                          // 74
                                                                                                                  // 75
  if ((typeof console !== 'undefined') && console[level]) {                                                       // 76
    console[level](str);                                                                                          // 77
  } else {                                                                                                        // 78
    // XXX Uses of Meteor._debug should probably be replaced by Log.debug or                                      // 79
    //     Log.info, and we should have another name for "do your best to                                         // 80
    //     call call console.log".                                                                                // 81
    Meteor._debug(str);                                                                                           // 82
  }                                                                                                               // 83
};                                                                                                                // 84
                                                                                                                  // 85
// @returns {Object: { line: Number, file: String }}                                                              // 86
Log._getCallerDetails = function () {                                                                             // 87
  var getStack = function () {                                                                                    // 88
    // We do NOT use Error.prepareStackTrace here (a V8 extension that gets us a                                  // 89
    // pre-parsed stack) since it's impossible to compose it with the use of                                      // 90
    // Error.prepareStackTrace used on the server for source maps.                                                // 91
    var err = new Error;                                                                                          // 92
    var stack = err.stack;                                                                                        // 93
    return stack;                                                                                                 // 94
  };                                                                                                              // 95
                                                                                                                  // 96
  var stack = getStack();                                                                                         // 97
                                                                                                                  // 98
  if (!stack) return {};                                                                                          // 99
                                                                                                                  // 100
  var lines = stack.split('\n');                                                                                  // 101
                                                                                                                  // 102
  // looking for the first line outside the logging package (or an                                                // 103
  // eval if we find that first)                                                                                  // 104
  var line;                                                                                                       // 105
  for (var i = 1; i < lines.length; ++i) {                                                                        // 106
    line = lines[i];                                                                                              // 107
    if (line.match(/^\s*at eval \(eval/)) {                                                                       // 108
      return {file: "eval"};                                                                                      // 109
    }                                                                                                             // 110
                                                                                                                  // 111
    if (!line.match(/packages\/(?:local-test[:_])?logging(?:\/|\.js)/))                                           // 112
      break;                                                                                                      // 113
  }                                                                                                               // 114
                                                                                                                  // 115
  var details = {};                                                                                               // 116
                                                                                                                  // 117
  // The format for FF is 'functionName@filePath:lineNumber'                                                      // 118
  // The format for V8 is 'functionName (packages/logging/logging.js:81)' or                                      // 119
  //                      'packages/logging/logging.js:81'                                                        // 120
  var match = /(?:[@(]| at )([^(]+?):([0-9:]+)(?:\)|$)/.exec(line);                                               // 121
  if (!match)                                                                                                     // 122
    return details;                                                                                               // 123
  // in case the matched block here is line:column                                                                // 124
  details.line = match[2].split(':')[0];                                                                          // 125
                                                                                                                  // 126
  // Possible format: https://foo.bar.com/scripts/file.js?random=foobar                                           // 127
  // XXX: if you can write the following in better way, please do it                                              // 128
  // XXX: what about evals?                                                                                       // 129
  details.file = match[1].split('/').slice(-1)[0].split('?')[0];                                                  // 130
                                                                                                                  // 131
  return details;                                                                                                 // 132
};                                                                                                                // 133
                                                                                                                  // 134
_.each(['debug', 'info', 'warn', 'error'], function (level) {                                                     // 135
  // @param arg {String|Object}                                                                                   // 136
  Log[level] = function (arg) {                                                                                   // 137
    if (suppress) {                                                                                               // 138
      suppress--;                                                                                                 // 139
      return;                                                                                                     // 140
    }                                                                                                             // 141
                                                                                                                  // 142
    var intercepted = false;                                                                                      // 143
    if (intercept) {                                                                                              // 144
      intercept--;                                                                                                // 145
      intercepted = true;                                                                                         // 146
    }                                                                                                             // 147
                                                                                                                  // 148
    var obj = (_.isObject(arg) && !_.isRegExp(arg) && !_.isDate(arg) ) ?                                          // 149
              arg : {message: new String(arg).toString() };                                                       // 150
                                                                                                                  // 151
    _.each(RESTRICTED_KEYS, function (key) {                                                                      // 152
      if (obj[key])                                                                                               // 153
        throw new Error("Can't set '" + key + "' in log message");                                                // 154
    });                                                                                                           // 155
                                                                                                                  // 156
    if (_.has(obj, 'message') && !_.isString(obj.message))                                                        // 157
      throw new Error("The 'message' field in log objects must be a string");                                     // 158
    if (!obj.omitCallerDetails)                                                                                   // 159
      obj = _.extend(Log._getCallerDetails(), obj);                                                               // 160
    obj.time = new Date();                                                                                        // 161
    obj.level = level;                                                                                            // 162
                                                                                                                  // 163
    // XXX allow you to enable 'debug', probably per-package                                                      // 164
    if (level === 'debug')                                                                                        // 165
      return;                                                                                                     // 166
                                                                                                                  // 167
    if (intercepted) {                                                                                            // 168
      interceptedLines.push(EJSON.stringify(obj));                                                                // 169
    } else if (Meteor.isServer) {                                                                                 // 170
      if (Log.outputFormat === 'colored-text') {                                                                  // 171
        console.log(Log.format(obj, {color: true}));                                                              // 172
      } else if (Log.outputFormat === 'json') {                                                                   // 173
        console.log(EJSON.stringify(obj));                                                                        // 174
      } else {                                                                                                    // 175
        throw new Error("Unknown logging output format: " + Log.outputFormat);                                    // 176
      }                                                                                                           // 177
    } else {                                                                                                      // 178
      logInBrowser(obj);                                                                                          // 179
    }                                                                                                             // 180
  };                                                                                                              // 181
});                                                                                                               // 182
                                                                                                                  // 183
// tries to parse line as EJSON. returns object if parse is successful, or null if not                            // 184
Log.parse = function (line) {                                                                                     // 185
  var obj = null;                                                                                                 // 186
  if (line && line.charAt(0) === '{') { // might be json generated from calling 'Log'                             // 187
    try { obj = EJSON.parse(line); } catch (e) {}                                                                 // 188
  }                                                                                                               // 189
                                                                                                                  // 190
  // XXX should probably check fields other than 'time'                                                           // 191
  if (obj && obj.time && (obj.time instanceof Date))                                                              // 192
    return obj;                                                                                                   // 193
  else                                                                                                            // 194
    return null;                                                                                                  // 195
};                                                                                                                // 196
                                                                                                                  // 197
// formats a log object into colored human and machine-readable text                                              // 198
Log.format = function (obj, options) {                                                                            // 199
  obj = EJSON.clone(obj); // don't mutate the argument                                                            // 200
  options = options || {};                                                                                        // 201
                                                                                                                  // 202
  var time = obj.time;                                                                                            // 203
  if (!(time instanceof Date))                                                                                    // 204
    throw new Error("'time' must be a Date object");                                                              // 205
  var timeInexact = obj.timeInexact;                                                                              // 206
                                                                                                                  // 207
  // store fields that are in FORMATTED_KEYS since we strip them                                                  // 208
  var level = obj.level || 'info';                                                                                // 209
  var file = obj.file;                                                                                            // 210
  var lineNumber = obj.line;                                                                                      // 211
  var appName = obj.app || '';                                                                                    // 212
  var originApp = obj.originApp;                                                                                  // 213
  var message = obj.message || '';                                                                                // 214
  var program = obj.program || '';                                                                                // 215
  var satellite = obj.satellite;                                                                                  // 216
  var stderr = obj.stderr || '';                                                                                  // 217
                                                                                                                  // 218
  _.each(FORMATTED_KEYS, function(key) {                                                                          // 219
    delete obj[key];                                                                                              // 220
  });                                                                                                             // 221
                                                                                                                  // 222
  if (!_.isEmpty(obj)) {                                                                                          // 223
    if (message) message += " ";                                                                                  // 224
    message += EJSON.stringify(obj);                                                                              // 225
  }                                                                                                               // 226
                                                                                                                  // 227
  var pad2 = function(n) { return n < 10 ? '0' + n : n.toString(); };                                             // 228
  var pad3 = function(n) { return n < 100 ? '0' + pad2(n) : n.toString(); };                                      // 229
                                                                                                                  // 230
  var dateStamp = time.getFullYear().toString() +                                                                 // 231
    pad2(time.getMonth() + 1 /*0-based*/) +                                                                       // 232
    pad2(time.getDate());                                                                                         // 233
  var timeStamp = pad2(time.getHours()) +                                                                         // 234
        ':' +                                                                                                     // 235
        pad2(time.getMinutes()) +                                                                                 // 236
        ':' +                                                                                                     // 237
        pad2(time.getSeconds()) +                                                                                 // 238
        '.' +                                                                                                     // 239
        pad3(time.getMilliseconds());                                                                             // 240
                                                                                                                  // 241
  // eg in San Francisco in June this will be '(-7)'                                                              // 242
  var utcOffsetStr = '(' + (-(new Date().getTimezoneOffset() / 60)) + ')';                                        // 243
                                                                                                                  // 244
  var appInfo = '';                                                                                               // 245
  if (appName) appInfo += appName;                                                                                // 246
  if (originApp && originApp !== appName) appInfo += ' via ' + originApp;                                         // 247
  if (appInfo) appInfo = '[' + appInfo + '] ';                                                                    // 248
                                                                                                                  // 249
  var sourceInfoParts = [];                                                                                       // 250
  if (program) sourceInfoParts.push(program);                                                                     // 251
  if (file) sourceInfoParts.push(file);                                                                           // 252
  if (lineNumber) sourceInfoParts.push(lineNumber);                                                               // 253
  var sourceInfo = _.isEmpty(sourceInfoParts) ?                                                                   // 254
    '' : '(' + sourceInfoParts.join(':') + ') ';                                                                  // 255
                                                                                                                  // 256
  if (satellite)                                                                                                  // 257
    sourceInfo += ['[', satellite, ']'].join('');                                                                 // 258
                                                                                                                  // 259
  var stderrIndicator = stderr ? '(STDERR) ' : '';                                                                // 260
                                                                                                                  // 261
  var metaPrefix = [                                                                                              // 262
    level.charAt(0).toUpperCase(),                                                                                // 263
    dateStamp,                                                                                                    // 264
    '-',                                                                                                          // 265
    timeStamp,                                                                                                    // 266
    utcOffsetStr,                                                                                                 // 267
    timeInexact ? '? ' : ' ',                                                                                     // 268
    appInfo,                                                                                                      // 269
    sourceInfo,                                                                                                   // 270
    stderrIndicator].join('');                                                                                    // 271
                                                                                                                  // 272
  var prettify = function (line, color) {                                                                         // 273
    return (options.color && Meteor.isServer && color) ?                                                          // 274
      require('cli-color')[color](line) : line;                                                                   // 275
  };                                                                                                              // 276
                                                                                                                  // 277
  return prettify(metaPrefix, platformColor(options.metaColor || META_COLOR)) +                                   // 278
    prettify(message, platformColor(LEVEL_COLORS[level]));                                                        // 279
};                                                                                                                // 280
                                                                                                                  // 281
// Turn a line of text into a loggable object.                                                                    // 282
// @param line {String}                                                                                           // 283
// @param override {Object}                                                                                       // 284
Log.objFromText = function (line, override) {                                                                     // 285
  var obj = {message: line, level: "info", time: new Date(), timeInexact: true};                                  // 286
  return _.extend(obj, override);                                                                                 // 287
};                                                                                                                // 288
                                                                                                                  // 289
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                //
// packages/logging/logging_cordova.js                                                                            //
//                                                                                                                //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                  //
// Log all uncaught errors so they can be printed to the developer.                                               // 1
// But since Android's adb catlog already prints the uncaught exceptions, we                                      // 2
// can disable it for Android.                                                                                    // 3
if (! /Android/i.test(navigator.userAgent)) {                                                                     // 4
  window.onerror = function (msg, url, line) {                                                                    // 5
    // Cut off the url prefix, the meaningful part always starts at 'www/' in                                     // 6
    // Cordova apps.                                                                                              // 7
    url = url.replace(/^.*?\/www\//, '');                                                                         // 8
    console.log('Uncaught Error: ' + msg + ':' + line + ':' + url);                                               // 9
  };                                                                                                              // 10
}                                                                                                                 // 11
                                                                                                                  // 12
                                                                                                                  // 13
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                //
// packages/logging/logging_test.js                                                                               //
//                                                                                                                //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                  //
Tinytest.add("logging - _getCallerDetails", function (test) {                                                     // 1
  var details = Log._getCallerDetails();                                                                          // 2
  // Ignore this test for Opera, IE, Safari since this test would work only                                       // 3
  // in Chrome and Firefox, other browsers don't give us an ability to get                                        // 4
  // stacktrace.                                                                                                  // 5
  if ((new Error).stack) {                                                                                        // 6
    if (Meteor.isServer) {                                                                                        // 7
      test.equal(details.file, 'tinytest.js');                                                                    // 8
    } else {                                                                                                      // 9
      // Note that we want this to work in --production too, so we need to allow                                  // 10
      // for the minified filename.                                                                               // 11
      test.matches(details.file,                                                                                  // 12
                   /^(?:tinytest\.js|[a-f0-9]{40}\.js)$/);                                                        // 13
    }                                                                                                             // 14
                                                                                                                  // 15
    // evaled statements shouldn't crash                                                                          // 16
    var code = "Log._getCallerDetails().file";                                                                    // 17
    // Note that we want this to work in --production too, so we need to allow                                    // 18
    // for the minified filename                                                                                  // 19
    test.matches(eval(code),                                                                                      // 20
                 /^(?:eval|local-test_logging\.js|[a-f0-9]{40}\.js)/);                                            // 21
  }                                                                                                               // 22
});                                                                                                               // 23
                                                                                                                  // 24
Tinytest.add("logging - log", function (test) {                                                                   // 25
  var logBothMessageAndObject = function (log, level) {                                                           // 26
    Log._intercept(3);                                                                                            // 27
                                                                                                                  // 28
    // Tests for correctness                                                                                      // 29
    log("message");                                                                                               // 30
    log({property1: "foo", property2: "bar"});                                                                    // 31
    log({message: "mixed", property1: "foo", property2: "bar"});                                                  // 32
                                                                                                                  // 33
    var intercepted = Log._intercepted();                                                                         // 34
    test.equal(intercepted.length, 3);                                                                            // 35
                                                                                                                  // 36
    var obj1 = EJSON.parse(intercepted[0]);                                                                       // 37
    test.equal(obj1.message, "message");                                                                          // 38
    test.equal(obj1.level, level);                                                                                // 39
    test.instanceOf(obj1.time, Date);                                                                             // 40
                                                                                                                  // 41
    var obj2 = EJSON.parse(intercepted[1]);                                                                       // 42
    test.isFalse(obj2.message);                                                                                   // 43
    test.equal(obj2.property1, "foo");                                                                            // 44
    test.equal(obj2.property2, "bar");                                                                            // 45
    test.equal(obj2.level, level);                                                                                // 46
    test.instanceOf(obj2.time, Date);                                                                             // 47
                                                                                                                  // 48
    var obj3 = EJSON.parse(intercepted[2]);                                                                       // 49
    test.equal(obj3.message, "mixed");                                                                            // 50
    test.equal(obj3.property1, "foo");                                                                            // 51
    test.equal(obj3.property2, "bar");                                                                            // 52
    test.equal(obj3.level, level);                                                                                // 53
    test.instanceOf(obj3.time, Date);                                                                             // 54
                                                                                                                  // 55
    // Test logging falsy values, as well as single digits                                                        // 56
    // and some other non-stringy things                                                                          // 57
    // In a format of testcase, expected result, name of the test.                                                // 58
    var testcases = [                                                                                             // 59
          [1, "1", "single digit"],                                                                               // 60
          [0, "0", "falsy - 0"],                                                                                  // 61
          [null, "null", "falsy - null"],                                                                         // 62
          [undefined, "undefined", "falsy - undefined"],                                                          // 63
          [new Date("2013-06-13T01:15:16.000Z"), new Date("2013-06-13T01:15:16.000Z"), "date"],                   // 64
          [/[^regexp]{0,1}/g, "/[^regexp]{0,1}/g", "regexp"],                                                     // 65
          [true, "true", "boolean - true"],                                                                       // 66
          [false, "false", "boolean - false"],                                                                    // 67
          [-Infinity, "-Infinity", "number - -Infinity"]];                                                        // 68
                                                                                                                  // 69
    Log._intercept(testcases.length);                                                                             // 70
    _.each(testcases, function (testcase) {                                                                       // 71
      log(testcase[0]);                                                                                           // 72
    });                                                                                                           // 73
                                                                                                                  // 74
    intercepted = Log._intercepted();                                                                             // 75
                                                                                                                  // 76
    test.equal(intercepted.length, testcases.length);                                                             // 77
                                                                                                                  // 78
    _.each(testcases, function (testcase, index) {                                                                // 79
      var expected = testcase[1];                                                                                 // 80
      var testName = testcase[2];                                                                                 // 81
      var recieved = intercepted[index];                                                                          // 82
      var obj = EJSON.parse(recieved);                                                                            // 83
                                                                                                                  // 84
      // IE8 and old Safari don't support this date format. Skip it.                                              // 85
      if (expected && expected.toString &&                                                                        // 86
          (expected.toString() === "NaN" ||                                                                       // 87
           expected.toString() === "Invalid Date"))                                                               // 88
        return;                                                                                                   // 89
                                                                                                                  // 90
      if (_.isDate(testcase[0]))                                                                                  // 91
        obj.message = new Date(obj.message);                                                                      // 92
      test.equal(obj.message, expected, 'Logging ' + testName);                                                   // 93
    });                                                                                                           // 94
                                                                                                                  // 95
    // Tests for correct exceptions                                                                               // 96
    Log._intercept(6);                                                                                            // 97
                                                                                                                  // 98
    test.throws(function () {                                                                                     // 99
      log({time: 'not the right time'});                                                                          // 100
    });                                                                                                           // 101
    test.throws(function () {                                                                                     // 102
      log({level: 'not the right level'});                                                                        // 103
    });                                                                                                           // 104
    _.each(['file', 'line', 'program', 'originApp', 'satellite'],                                                 // 105
      function (restrictedKey) {                                                                                  // 106
      test.throws(function () {                                                                                   // 107
        var obj = {};                                                                                             // 108
        obj[restrictedKey] = 'usage of restricted key';                                                           // 109
        log(obj);                                                                                                 // 110
      });                                                                                                         // 111
    });                                                                                                           // 112
                                                                                                                  // 113
    // Can't pass numbers, objects, arrays, regexps or functions as message                                       // 114
    var throwingTestcases = [1, NaN, {foo:"bar"}, ["a", "r", "r"], null,                                          // 115
                             undefined, new Date, function () { return 42; },                                     // 116
                             /[regexp]/ ];                                                                        // 117
    Log._intercept(throwingTestcases.length);                                                                     // 118
    _.each(throwingTestcases, function (testcase) {                                                               // 119
      test.throws(function () {                                                                                   // 120
        log({ message: testcase });                                                                               // 121
      });                                                                                                         // 122
    });                                                                                                           // 123
                                                                                                                  // 124
    // Since all tests above should throw, nothing should be printed.                                             // 125
    // This call will set the logging interception to the clean state as well.                                    // 126
    test.equal(Log._intercepted().length, 0);                                                                     // 127
  };                                                                                                              // 128
                                                                                                                  // 129
  logBothMessageAndObject(Log, 'info');                                                                           // 130
  _.each(['info', 'warn', 'error'], function (level) {                                                            // 131
    logBothMessageAndObject(Log[level], level);                                                                   // 132
  });                                                                                                             // 133
});                                                                                                               // 134
                                                                                                                  // 135
Tinytest.add("logging - parse", function (test) {                                                                 // 136
  test.equal(Log.parse("message"), null);                                                                         // 137
  test.equal(Log.parse('{"foo": "bar"}'), null);                                                                  // 138
  var time = new Date;                                                                                            // 139
  test.equal(Log.parse('{"foo": "bar", "time": ' + EJSON.stringify(time) + '}'),                                  // 140
                        { foo: "bar", time: time });                                                              // 141
  test.equal(Log.parse('{"foo": not json "bar"}'), null);                                                         // 142
  test.equal(Log.parse('{"time": "not a date object"}'), null);                                                   // 143
});                                                                                                               // 144
                                                                                                                  // 145
Tinytest.add("logging - format", function (test) {                                                                // 146
  var time = new Date(2012, 9 - 1/*0-based*/, 8, 7, 6, 5, 4);                                                     // 147
  var utcOffsetStr = '(' + (-(new Date().getTimezoneOffset() / 60)) + ')';                                        // 148
                                                                                                                  // 149
  _.each(['debug', 'info', 'warn', 'error'], function (level) {                                                   // 150
    test.equal(                                                                                                   // 151
      Log.format({message: "message", time: time, level: level}),                                                 // 152
      level.charAt(0).toUpperCase() + "20120908-07:06:05.004" + utcOffsetStr + " message");                       // 153
                                                                                                                  // 154
    test.equal(                                                                                                   // 155
      Log.format({message: "message", time: time, timeInexact: true, level: level}),                              // 156
      level.charAt(0).toUpperCase() + "20120908-07:06:05.004" + utcOffsetStr + "? message");                      // 157
                                                                                                                  // 158
    test.equal(                                                                                                   // 159
      Log.format({foo1: "bar1", foo2: "bar2", time: time, level: level}),                                         // 160
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' {"foo1":"bar1","foo2":"bar2"}');
                                                                                                                  // 162
    test.equal(                                                                                                   // 163
      Log.format({message: "message", foo: "bar", time: time, level: level}),                                     // 164
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' message {"foo":"bar"}');         // 165
                                                                                                                  // 166
    // Has everything except stderr field                                                                         // 167
    test.equal(                                                                                                   // 168
      Log.format({message: "message", foo: "bar", time: time, level: level, file: "app.js", line:42, app: "myApp", originApp: "proxy", program: "server"}),
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' [myApp via proxy] (server:app.js:42) message {\"foo\":\"bar\"}');
                                                                                                                  // 171
    // stderr                                                                                                     // 172
    test.equal(                                                                                                   // 173
      Log.format({message: "message from stderr", time: time, level: level, stderr: true}),                       // 174
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' (STDERR) message from stderr');  // 175
                                                                                                                  // 176
    // app/originApp                                                                                              // 177
    test.equal(                                                                                                   // 178
      Log.format({message: "message", time: time, level: level, app: "app", originApp: "app"}),                   // 179
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' [app] message');                 // 180
    test.equal(                                                                                                   // 181
      Log.format({message: "message", time: time, level: level, app: "app", originApp: "proxy"}),                 // 182
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' [app via proxy] message');       // 183
                                                                                                                  // 184
    // source info                                                                                                // 185
    test.equal(                                                                                                   // 186
      Log.format({message: "message", time: time, level: level, file: "app.js", line: 42, program: "server"}),    // 187
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' (server:app.js:42) message');    // 188
    test.equal(                                                                                                   // 189
      Log.format({message: "message", time: time, level: level, file: "app.js", line: 42}),                       // 190
      level.charAt(0).toUpperCase() + '20120908-07:06:05.004' + utcOffsetStr + ' (app.js:42) message');           // 191
  });                                                                                                             // 192
                                                                                                                  // 193
  test.matches(Log.format({                                                                                       // 194
    message: "oyez",                                                                                              // 195
    time: new Date,                                                                                               // 196
    level: "error"                                                                                                // 197
  }, {                                                                                                            // 198
    color: true                                                                                                   // 199
  }), /oyez/);                                                                                                    // 200
});                                                                                                               // 201
                                                                                                                  // 202
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
