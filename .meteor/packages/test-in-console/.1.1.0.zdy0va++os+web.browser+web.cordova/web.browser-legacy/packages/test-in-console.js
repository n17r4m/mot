(function(){

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                              //
// packages/test-in-console/driver.js                                                                           //
//                                                                                                              //
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                //
// Global flag for phantomjs (or other browser) to eval to see if we're done.                                   // 1
DONE = false;                                                                                                   // 2
// Failure count for phantomjs exit code                                                                        // 3
FAILURES = null;                                                                                                // 4
                                                                                                                // 5
TEST_STATUS = {                                                                                                 // 6
  DONE: false,                                                                                                  // 7
  FAILURES: null                                                                                                // 8
};                                                                                                              // 9
                                                                                                                // 10
// xUnit format uses XML output                                                                                 // 11
var XML_CHAR_MAP = {                                                                                            // 12
  '<': '&lt;',                                                                                                  // 13
  '>': '&gt;',                                                                                                  // 14
  '&': '&amp;',                                                                                                 // 15
  '"': '&quot;',                                                                                                // 16
  "'": '&apos;'                                                                                                 // 17
};                                                                                                              // 18
                                                                                                                // 19
// Escapes a string for insertion into XML                                                                      // 20
var escapeXml = function (s) {                                                                                  // 21
  return s.replace(/[<>&"']/g, function (c) {                                                                   // 22
    return XML_CHAR_MAP[c];                                                                                     // 23
  });                                                                                                           // 24
}                                                                                                               // 25
                                                                                                                // 26
// Returns a human name for a test                                                                              // 27
var getName = function (result) {                                                                               // 28
  return (result.server ? "S: " : "C: ") +                                                                      // 29
    result.groupPath.join(" - ") + " - " + result.test;                                                         // 30
};                                                                                                              // 31
                                                                                                                // 32
// Calls console.log, but returns silently if console.log is not available                                      // 33
var log = function (/*arguments*/) {                                                                            // 34
  if (typeof console !== 'undefined') {                                                                         // 35
    console.log.apply(console, arguments);                                                                      // 36
  }                                                                                                             // 37
};                                                                                                              // 38
                                                                                                                // 39
var MAGIC_PREFIX = '##_meteor_magic##';                                                                         // 40
// Write output so that other tools can read it                                                                 // 41
// Output is sent to console.log, prefixed with the magic prefix and then the facility                          // 42
// By grepping for the prefix, other tools can get the 'special' output                                         // 43
var logMagic = function (facility, s) {                                                                         // 44
  log(MAGIC_PREFIX + facility + ': ' + s);                                                                      // 45
};                                                                                                              // 46
                                                                                                                // 47
// Logs xUnit output, if xunit output is enabled                                                                // 48
// This uses logMagic with a facility of xunit                                                                  // 49
var xunit = function (s) {                                                                                      // 50
  if (xunitEnabled) {                                                                                           // 51
    logMagic('xunit', s);                                                                                       // 52
  }                                                                                                             // 53
};                                                                                                              // 54
                                                                                                                // 55
var passed = 0;                                                                                                 // 56
var failed = 0;                                                                                                 // 57
var expected = 0;                                                                                               // 58
var resultSet = {};                                                                                             // 59
var toReport = [];                                                                                              // 60
                                                                                                                // 61
var hrefPath = window.location.href.split("/");                                                                 // 62
var platform = decodeURIComponent(hrefPath.length && hrefPath[hrefPath.length - 1]);                            // 63
if (!platform)                                                                                                  // 64
  platform = "local";                                                                                           // 65
                                                                                                                // 66
// We enable xUnit output when platform is xunit                                                                // 67
var xunitEnabled = (platform == 'xunit');                                                                       // 68
                                                                                                                // 69
var doReport = Meteor &&                                                                                        // 70
      Meteor.settings &&                                                                                        // 71
      Meteor.settings.public &&                                                                                 // 72
      Meteor.settings.public.runId;                                                                             // 73
var report = function (name, last) {                                                                            // 74
  if (doReport) {                                                                                               // 75
    var data = {                                                                                                // 76
      run_id: Meteor.settings.public.runId,                                                                     // 77
      testPath: resultSet[name].testPath,                                                                       // 78
      status: resultSet[name].status,                                                                           // 79
      platform: platform,                                                                                       // 80
      server: resultSet[name].server,                                                                           // 81
      fullName: name.substr(3)                                                                                  // 82
    };                                                                                                          // 83
    if ((data.status === "FAIL" || data.status === "EXPECTED") &&                                               // 84
        !_.isEmpty(resultSet[name].events)) {                                                                   // 85
      // only send events when bad things happen                                                                // 86
      data.events = resultSet[name].events;                                                                     // 87
    }                                                                                                           // 88
    if (last)                                                                                                   // 89
      data.end = new Date();                                                                                    // 90
    else                                                                                                        // 91
      data.start = new Date();                                                                                  // 92
    toReport.push(EJSON.toJSONValue(data));                                                                     // 93
  }                                                                                                             // 94
};                                                                                                              // 95
var sendReports = function (callback) {                                                                         // 96
  var reports = toReport;                                                                                       // 97
  if (!callback)                                                                                                // 98
    callback = function () {};                                                                                  // 99
  toReport = [];                                                                                                // 100
  if (doReport)                                                                                                 // 101
    Meteor.call("report", reports, callback);                                                                   // 102
  else                                                                                                          // 103
    callback();                                                                                                 // 104
};                                                                                                              // 105
                                                                                                                // 106
runTests = function () {                                                                                        // 107
  setTimeout(sendReports, 500);                                                                                 // 108
  setInterval(sendReports, 2000);                                                                               // 109
                                                                                                                // 110
  Tinytest._runTestsEverywhere(                                                                                 // 111
    function (results) {                                                                                        // 112
      var name = getName(results);                                                                              // 113
      if (!_.has(resultSet, name)) {                                                                            // 114
        var testPath = EJSON.clone(results.groupPath);                                                          // 115
        testPath.push(results.test);                                                                            // 116
        resultSet[name] = {                                                                                     // 117
          name: name,                                                                                           // 118
          status: "PENDING",                                                                                    // 119
          events: [],                                                                                           // 120
          server: !!results.server,                                                                             // 121
          testPath: testPath,                                                                                   // 122
          test: results.test                                                                                    // 123
        };                                                                                                      // 124
        report(name, false);                                                                                    // 125
      }                                                                                                         // 126
      // Loop through events, and record status for each test                                                   // 127
      // Also log result if test has finished                                                                   // 128
      _.each(results.events, function (event) {                                                                 // 129
        resultSet[name].events.push(event);                                                                     // 130
        switch (event.type) {                                                                                   // 131
        case "ok":                                                                                              // 132
          break;                                                                                                // 133
        case "expected_fail":                                                                                   // 134
          if (resultSet[name].status !== "FAIL")                                                                // 135
            resultSet[name].status = "EXPECTED";                                                                // 136
          break;                                                                                                // 137
        case "exception":                                                                                       // 138
          log(name, ":", "!!!!!!!!! FAIL !!!!!!!!!!!");                                                         // 139
          if (event.details && event.details.stack)                                                             // 140
            log(event.details.stack);                                                                           // 141
          else                                                                                                  // 142
            log("Test failed with exception");                                                                  // 143
          failed++;                                                                                             // 144
          break;                                                                                                // 145
        case "finish":                                                                                          // 146
          switch (resultSet[name].status) {                                                                     // 147
          case "OK":                                                                                            // 148
            break;                                                                                              // 149
          case "PENDING":                                                                                       // 150
            resultSet[name].status = "OK";                                                                      // 151
            report(name, true);                                                                                 // 152
            log(name, ":", "OK");                                                                               // 153
            passed++;                                                                                           // 154
            break;                                                                                              // 155
          case "EXPECTED":                                                                                      // 156
            report(name, true);                                                                                 // 157
            log(name, ":", "EXPECTED FAILURE");                                                                 // 158
            expected++;                                                                                         // 159
            break;                                                                                              // 160
          case "FAIL":                                                                                          // 161
            failed++;                                                                                           // 162
            report(name, true);                                                                                 // 163
            log(name, ":", "!!!!!!!!! FAIL !!!!!!!!!!!");                                                       // 164
            log(JSON.stringify(resultSet[name].info));                                                          // 165
            break;                                                                                              // 166
          default:                                                                                              // 167
            log(name, ": unknown state for the test to be in");                                                 // 168
          }                                                                                                     // 169
          break;                                                                                                // 170
        default:                                                                                                // 171
          resultSet[name].status = "FAIL";                                                                      // 172
          resultSet[name].info = results;                                                                       // 173
          break;                                                                                                // 174
        }                                                                                                       // 175
      });                                                                                                       // 176
    },                                                                                                          // 177
                                                                                                                // 178
    // After test completion, log a quick summary                                                               // 179
    function () {                                                                                               // 180
      if (failed > 0) {                                                                                         // 181
        log("~~~~~~~ THERE ARE FAILURES ~~~~~~~");                                                              // 182
      }                                                                                                         // 183
      log("passed/expected/failed/total", passed, "/", expected, "/", failed, "/", _.size(resultSet));          // 184
      sendReports(function () {                                                                                 // 185
        if (doReport) {                                                                                         // 186
          log("Waiting 3s for any last reports to get sent out");                                               // 187
          setTimeout(function () {                                                                              // 188
            TEST_STATUS.FAILURES = FAILURES = failed;                                                           // 189
            TEST_STATUS.DONE = DONE = true;                                                                     // 190
          }, 3000);                                                                                             // 191
        } else {                                                                                                // 192
          TEST_STATUS.FAILURES = FAILURES = failed;                                                             // 193
          TEST_STATUS.DONE = DONE = true;                                                                       // 194
        }                                                                                                       // 195
      });                                                                                                       // 196
                                                                                                                // 197
      // Also log xUnit output                                                                                  // 198
      xunit('<testsuite errors="" failures="" name="meteor" skips="" tests="" time="">');                       // 199
      _.each(resultSet, function (result, name) {                                                               // 200
        var classname = result.testPath.join('.').replace(/ /g, '-') + (result.server ? "-server" : "-client");
        var name = result.test.replace(/ /g, '-') + (result.server ? "-server" : "-client");                    // 202
        var time = "";                                                                                          // 203
        var error = "";                                                                                         // 204
        _.each(result.events, function (event) {                                                                // 205
          switch (event.type) {                                                                                 // 206
            case "finish":                                                                                      // 207
              var timeMs = event.timeMs;                                                                        // 208
              if (timeMs !== undefined) {                                                                       // 209
                time = (timeMs / 1000) + "";                                                                    // 210
              }                                                                                                 // 211
              break;                                                                                            // 212
            case "exception":                                                                                   // 213
              var details = event.details || {};                                                                // 214
              error = (details.message || '?') + " filename=" + (details.filename || '?') + " line=" + (details.line || '?');
              break;                                                                                            // 216
          }                                                                                                     // 217
        });                                                                                                     // 218
        switch (result.status) {                                                                                // 219
          case "FAIL":                                                                                          // 220
            error = error || '?';                                                                               // 221
            break;                                                                                              // 222
          case "EXPECTED":                                                                                      // 223
            error = null;                                                                                       // 224
            break;                                                                                              // 225
        }                                                                                                       // 226
                                                                                                                // 227
        xunit('<testcase classname="' + escapeXml(classname) + '" name="' + escapeXml(name) + '" time="' + time + '">');
        if (error) {                                                                                            // 229
          xunit('  <failure message="test failure">' + escapeXml(error) + '</failure>');                        // 230
        }                                                                                                       // 231
        xunit('</testcase>');                                                                                   // 232
      });                                                                                                       // 233
      xunit('</testsuite>');                                                                                    // 234
      logMagic('state', 'done');                                                                                // 235
    },                                                                                                          // 236
    ["tinytest"]);                                                                                              // 237
}                                                                                                               // 238
                                                                                                                // 239
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
