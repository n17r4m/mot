(function(){

///////////////////////////////////////////////////////////////////////////////////
//                                                                               //
// packages/browser-policy-content/browser-policy-content.js                     //
//                                                                               //
///////////////////////////////////////////////////////////////////////////////////
                                                                                 //
// By adding this package, you get the following default policy:                 // 1
// No eval or other string-to-code, and content can only be loaded from the      // 2
// same origin as the app (except for XHRs and websocket connections, which can  // 3
// go to any origin). Browsers will also be told not to sniff content types      // 4
// away from declared content types (X-Content-Type-Options: nosniff).           // 5
//                                                                               // 6
// Apps should call BrowserPolicy.content.disallowInlineScripts() if they are    // 7
// not using any inline script tags and are willing to accept an extra round     // 8
// trip on page load.                                                            // 9
//                                                                               // 10
// BrowserPolicy.content functions for tweaking CSP:                             // 11
// allowInlineScripts()                                                          // 12
// disallowInlineScripts(): adds extra round-trip to page load time              // 13
// allowInlineStyles()                                                           // 14
// disallowInlineStyles()                                                        // 15
// allowEval()                                                                   // 16
// disallowEval()                                                                // 17
//                                                                               // 18
// For each type of content (script, object, image, media, font, connect,        // 19
// style, frame, frame-ancestors), there are the following functions:            // 20
// allow<content type>Origin(origin): allows the type of content to be loaded    // 21
// from the given origin                                                         // 22
// allow<content type>DataUrl(): allows the content to be loaded from data: URLs
// allow<content type>SameOrigin(): allows the content to be loaded from the     // 24
// same origin                                                                   // 25
// disallow<content type>(): disallows this type of content all together (can't  // 26
// be called for script)                                                         // 27
//                                                                               // 28
// The following functions allow you to set rules for all types of content at    // 29
// once:                                                                         // 30
// allowAllContentOrigin(origin)                                                 // 31
// allowAllContentDataUrl()                                                      // 32
// allowAllContentSameOrigin()                                                   // 33
// disallowAllContent()                                                          // 34
//                                                                               // 35
// You can allow content type sniffing by calling                                // 36
// `BrowserPolicy.content.allowContentTypeSniffing()`.                           // 37
                                                                                 // 38
var cspSrcs;                                                                     // 39
var cachedCsp; // Avoid constructing the header out of cspSrcs when possible.    // 40
                                                                                 // 41
// CSP keywords have to be single-quoted.                                        // 42
var keywords = {                                                                 // 43
  unsafeInline: "'unsafe-inline'",                                               // 44
  unsafeEval: "'unsafe-eval'",                                                   // 45
  self: "'self'",                                                                // 46
  none: "'none'"                                                                 // 47
};                                                                               // 48
                                                                                 // 49
// If false, we set the X-Content-Type-Options header to 'nosniff'.              // 50
var contentSniffingAllowed = false;                                              // 51
                                                                                 // 52
const BrowserPolicy = require("meteor/browser-policy-common").BrowserPolicy;     // 53
BrowserPolicy.content = {};                                                      // 54
                                                                                 // 55
var parseCsp = function (csp) {                                                  // 56
  var policies = csp.split("; ");                                                // 57
  cspSrcs = {};                                                                  // 58
  _.each(policies, function (policy) {                                           // 59
    if (policy[policy.length - 1] === ";")                                       // 60
      policy = policy.substring(0, policy.length - 1);                           // 61
    var srcs = policy.split(" ");                                                // 62
    var directive = srcs[0];                                                     // 63
    if (_.indexOf(srcs, keywords.none) !== -1)                                   // 64
      cspSrcs[directive] = null;                                                 // 65
    else                                                                         // 66
      cspSrcs[directive] = srcs.slice(1);                                        // 67
  });                                                                            // 68
                                                                                 // 69
  if (cspSrcs["default-src"] === undefined)                                      // 70
    throw new Error("Content Security Policies used with " +                     // 71
                    "browser-policy must specify a default-src.");               // 72
                                                                                 // 73
  // Copy default-src sources to other directives.                               // 74
  _.each(cspSrcs, function (sources, directive) {                                // 75
    cspSrcs[directive] = _.union(sources || [], cspSrcs["default-src"] || []);   // 76
  });                                                                            // 77
};                                                                               // 78
                                                                                 // 79
var removeCspSrc = function (directive, src) {                                   // 80
  cspSrcs[directive] = _.without(cspSrcs[directive] || [], src);                 // 81
};                                                                               // 82
                                                                                 // 83
// Prepare for a change to cspSrcs. Ensure that we have a key in the dictionary  // 84
// and clear any cached CSP.                                                     // 85
var prepareForCspDirective = function (directive) {                              // 86
  cspSrcs = cspSrcs || {};                                                       // 87
  cachedCsp = null;                                                              // 88
  if (! _.has(cspSrcs, directive))                                               // 89
    cspSrcs[directive] = _.clone(cspSrcs["default-src"]);                        // 90
};                                                                               // 91
                                                                                 // 92
// Add `src` to the list of allowed sources for `directive`, with the            // 93
// following modifications if `src` is an origin:                                // 94
// - If `src` does not have a protocol specified, then add both                  // 95
//   http://<src> and https://<src>. This is to mask differing                   // 96
//   cross-browser behavior; some browsers interpret an origin without a         // 97
//   protocol as http://<src> and some interpret it as both http://<src>         // 98
//   and https://<src>                                                           // 99
// - Trim trailing slashes from `src`, since some browsers interpret             // 100
//   "foo.com/" as "foo.com" and some don't.                                     // 101
var addSourceForDirective = function (directive, src) {                          // 102
  if (_.contains(_.values(keywords), src)) {                                     // 103
    cspSrcs[directive].push(src);                                                // 104
  } else {                                                                       // 105
    var toAdd = [];                                                              // 106
                                                                                 // 107
    //Only add single quotes to CSP2 script digests                              // 108
    if (/^(sha(256|384|512)-)/i.test(src)) {                                     // 109
      toAdd.push("'" + src + "'");                                               // 110
    } else {                                                                     // 111
      src = src.toLowerCase();                                                   // 112
                                                                                 // 113
      // Trim trailing slashes.                                                  // 114
      src = src.replace(/\/+$/, '');                                             // 115
                                                                                 // 116
      // If there is no protocol, add both http:// and https://.                 // 117
      if (! /^([a-z0-9.+-]+:)/.test(src)) {                                      // 118
        toAdd.push("http://" + src);                                             // 119
        toAdd.push("https://" + src);                                            // 120
      } else {                                                                   // 121
        toAdd.push(src);                                                         // 122
      }                                                                          // 123
    }                                                                            // 124
                                                                                 // 125
    _.each(toAdd, function (s) {                                                 // 126
      cspSrcs[directive].push(s);                                                // 127
    });                                                                          // 128
  }                                                                              // 129
};                                                                               // 130
                                                                                 // 131
var setDefaultPolicy = function () {                                             // 132
  // By default, unsafe inline scripts and styles are allowed, since we expect   // 133
  // many apps will use them for analytics, etc. Unsafe eval is disallowed, and  // 134
  // the only allowable content source is the same origin or data, except for    // 135
  // connect which allows anything (since meteor.com apps make websocket         // 136
  // connections to a lot of different origins).                                 // 137
  BrowserPolicy.content.setPolicy("default-src 'self'; " +                       // 138
                                  "script-src 'self' 'unsafe-inline'; " +        // 139
                                  "connect-src *; " +                            // 140
                                  "img-src data: 'self'; " +                     // 141
                                  "style-src 'self' 'unsafe-inline';");          // 142
  contentSniffingAllowed = false;                                                // 143
};                                                                               // 144
                                                                                 // 145
var setWebAppInlineScripts = function (value) {                                  // 146
  if (! BrowserPolicy._runningTest())                                            // 147
    WebAppInternals.setInlineScriptsAllowed(value);                              // 148
};                                                                               // 149
                                                                                 // 150
_.extend(BrowserPolicy.content, {                                                // 151
  allowContentTypeSniffing: function () {                                        // 152
    contentSniffingAllowed = true;                                               // 153
  },                                                                             // 154
  // Exported for tests and browser-policy-common.                               // 155
  _constructCsp: function () {                                                   // 156
    if (! cspSrcs || _.isEmpty(cspSrcs))                                         // 157
      return null;                                                               // 158
                                                                                 // 159
    if (cachedCsp)                                                               // 160
      return cachedCsp;                                                          // 161
                                                                                 // 162
    var header = _.map(cspSrcs, function (srcs, directive) {                     // 163
      srcs = srcs || [];                                                         // 164
      if (_.isEmpty(srcs))                                                       // 165
        srcs = [keywords.none];                                                  // 166
      var directiveCsp = _.uniq(srcs).join(" ");                                 // 167
      return directive + " " + directiveCsp + ";";                               // 168
    });                                                                          // 169
                                                                                 // 170
    header = header.join(" ");                                                   // 171
    cachedCsp = header;                                                          // 172
    return header;                                                               // 173
  },                                                                             // 174
  _reset: function () {                                                          // 175
    cachedCsp = null;                                                            // 176
    setDefaultPolicy();                                                          // 177
  },                                                                             // 178
                                                                                 // 179
  setPolicy: function (csp) {                                                    // 180
    cachedCsp = null;                                                            // 181
    parseCsp(csp);                                                               // 182
    setWebAppInlineScripts(                                                      // 183
      BrowserPolicy.content._keywordAllowed("script-src", keywords.unsafeInline)
    );                                                                           // 185
  },                                                                             // 186
                                                                                 // 187
  _keywordAllowed: function (directive, keyword) {                               // 188
    return (cspSrcs[directive] &&                                                // 189
            _.indexOf(cspSrcs[directive], keyword) !== -1);                      // 190
  },                                                                             // 191
                                                                                 // 192
  // Helpers for creating content security policies                              // 193
                                                                                 // 194
  allowInlineScripts: function () {                                              // 195
    prepareForCspDirective("script-src");                                        // 196
    cspSrcs["script-src"].push(keywords.unsafeInline);                           // 197
    setWebAppInlineScripts(true);                                                // 198
  },                                                                             // 199
  disallowInlineScripts: function () {                                           // 200
    prepareForCspDirective("script-src");                                        // 201
    removeCspSrc("script-src", keywords.unsafeInline);                           // 202
    setWebAppInlineScripts(false);                                               // 203
  },                                                                             // 204
  allowEval: function () {                                                       // 205
    prepareForCspDirective("script-src");                                        // 206
    cspSrcs["script-src"].push(keywords.unsafeEval);                             // 207
  },                                                                             // 208
  disallowEval: function () {                                                    // 209
    prepareForCspDirective("script-src");                                        // 210
    removeCspSrc("script-src", keywords.unsafeEval);                             // 211
  },                                                                             // 212
  allowInlineStyles: function () {                                               // 213
    prepareForCspDirective("style-src");                                         // 214
    cspSrcs["style-src"].push(keywords.unsafeInline);                            // 215
  },                                                                             // 216
  disallowInlineStyles: function () {                                            // 217
    prepareForCspDirective("style-src");                                         // 218
    removeCspSrc("style-src", keywords.unsafeInline);                            // 219
  },                                                                             // 220
                                                                                 // 221
  // Functions for setting defaults                                              // 222
  allowSameOriginForAll: function () {                                           // 223
    BrowserPolicy.content.allowOriginForAll(keywords.self);                      // 224
  },                                                                             // 225
  allowDataUrlForAll: function () {                                              // 226
    BrowserPolicy.content.allowOriginForAll("data:");                            // 227
  },                                                                             // 228
  allowOriginForAll: function (origin) {                                         // 229
    prepareForCspDirective("default-src");                                       // 230
    _.each(_.keys(cspSrcs), function (directive) {                               // 231
      addSourceForDirective(directive, origin);                                  // 232
    });                                                                          // 233
  },                                                                             // 234
  disallowAll: function () {                                                     // 235
    cachedCsp = null;                                                            // 236
    cspSrcs = {                                                                  // 237
      "default-src": []                                                          // 238
    };                                                                           // 239
    setWebAppInlineScripts(false);                                               // 240
  },                                                                             // 241
                                                                                 // 242
  _xContentTypeOptions: function () {                                            // 243
    if (! contentSniffingAllowed) {                                              // 244
      return "nosniff";                                                          // 245
    }                                                                            // 246
  }                                                                              // 247
});                                                                              // 248
                                                                                 // 249
// allow<Resource>Origin, allow<Resource>Data, allow<Resource>self, and          // 250
// disallow<Resource> methods for each type of resource.                         // 251
var resources = [                                                                // 252
  { methodResource: "Script", directive: "script-src" },                         // 253
  { methodResource: "Object", directive: "object-src" },                         // 254
  { methodResource: "Image", directive: "img-src" },                             // 255
  { methodResource: "Media", directive: "media-src" },                           // 256
  { methodResource: "Font", directive: "font-src" },                             // 257
  { methodResource: "Connect", directive: "connect-src" },                       // 258
  { methodResource: "Style", directive: "style-src" },                           // 259
  { methodResource: "Frame", directive: "frame-src" },                           // 260
  { methodResource: "FrameAncestors", directive: "frame-ancestors" }             // 261
];                                                                               // 262
_.each(resources,  function (resource) {                                         // 263
  var directive = resource.directive;                                            // 264
  var methodResource = resource.methodResource;                                  // 265
  var allowMethodName = "allow" + methodResource + "Origin";                     // 266
  var disallowMethodName = "disallow" + methodResource;                          // 267
  var allowDataMethodName = "allow" + methodResource + "DataUrl";                // 268
  var allowBlobMethodName = "allow" + methodResource + "BlobUrl";                // 269
  var allowSelfMethodName = "allow" + methodResource + "SameOrigin";             // 270
                                                                                 // 271
  var disallow = function () {                                                   // 272
    cachedCsp = null;                                                            // 273
    cspSrcs[directive] = [];                                                     // 274
  };                                                                             // 275
                                                                                 // 276
  BrowserPolicy.content[allowMethodName] = function (src) {                      // 277
    prepareForCspDirective(directive);                                           // 278
    addSourceForDirective(directive, src);                                       // 279
  };                                                                             // 280
  if (resource === "script") {                                                   // 281
    BrowserPolicy.content[disallowMethodName] = function () {                    // 282
      disallow();                                                                // 283
      setWebAppInlineScripts(false);                                             // 284
    };                                                                           // 285
  } else {                                                                       // 286
    BrowserPolicy.content[disallowMethodName] = disallow;                        // 287
  }                                                                              // 288
  BrowserPolicy.content[allowDataMethodName] = function () {                     // 289
    prepareForCspDirective(directive);                                           // 290
    cspSrcs[directive].push("data:");                                            // 291
  };                                                                             // 292
  BrowserPolicy.content[allowBlobMethodName] = function () {                     // 293
    prepareForCspDirective(directive);                                           // 294
    cspSrcs[directive].push("blob:");                                            // 295
  };                                                                             // 296
  BrowserPolicy.content[allowSelfMethodName] = function () {                     // 297
    prepareForCspDirective(directive);                                           // 298
    cspSrcs[directive].push(keywords.self);                                      // 299
  };                                                                             // 300
});                                                                              // 301
                                                                                 // 302
setDefaultPolicy();                                                              // 303
                                                                                 // 304
exports.BrowserPolicy = BrowserPolicy;                                           // 305
                                                                                 // 306
///////////////////////////////////////////////////////////////////////////////////

}).call(this);
