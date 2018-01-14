(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                   //
// packages/minifier-css/minification.js                                                                             //
//                                                                                                                   //
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                     //
// http://stackoverflow.com/questions/9906794/internet-explorers-css-rules-limits                                    // 1
var LIMIT = 4095;                                                                                                    // 2
                                                                                                                     // 3
// Stringifier based on css-stringify                                                                                // 4
var emit = function (str) {                                                                                          // 5
  return str.toString();                                                                                             // 6
};                                                                                                                   // 7
                                                                                                                     // 8
var visit = function (node, last) {                                                                                  // 9
  return traverse[node.type](node, last);                                                                            // 10
};                                                                                                                   // 11
                                                                                                                     // 12
var mapVisit = function (nodes) {                                                                                    // 13
  var buf = "";                                                                                                      // 14
                                                                                                                     // 15
  for (var i = 0, length = nodes.length; i < length; i++) {                                                          // 16
    buf += visit(nodes[i], i === length - 1);                                                                        // 17
  }                                                                                                                  // 18
                                                                                                                     // 19
  return buf;                                                                                                        // 20
};                                                                                                                   // 21
                                                                                                                     // 22
// returns a list of strings                                                                                         // 23
MinifyAst = function(node) {                                                                                         // 24
  // the approach is taken from BlessCSS                                                                             // 25
                                                                                                                     // 26
  var newAsts = [];                                                                                                  // 27
  var current = {                                                                                                    // 28
    selectors: 0,                                                                                                    // 29
    nodes: []                                                                                                        // 30
  };                                                                                                                 // 31
                                                                                                                     // 32
  var startNewAst = function () {                                                                                    // 33
    newAsts.push({                                                                                                   // 34
      type: 'stylesheet',                                                                                            // 35
      stylesheet: {                                                                                                  // 36
        rules: current.nodes                                                                                         // 37
      }                                                                                                              // 38
    });                                                                                                              // 39
                                                                                                                     // 40
    current.nodes = [];                                                                                              // 41
    current.selectors = 0;                                                                                           // 42
  };                                                                                                                 // 43
                                                                                                                     // 44
  _.each(node.stylesheet.rules, function (rule) {                                                                    // 45
    switch (rule.type) {                                                                                             // 46
      case 'rule':                                                                                                   // 47
        if (current.selectors + rule.selectors.length > LIMIT) {                                                     // 48
          startNewAst();                                                                                             // 49
        }                                                                                                            // 50
                                                                                                                     // 51
        current.selectors += rule.selectors.length;                                                                  // 52
        current.nodes.push(rule);                                                                                    // 53
        break;                                                                                                       // 54
      case 'comment':                                                                                                // 55
        // no-op                                                                                                     // 56
        break;                                                                                                       // 57
      default:                                                                                                       // 58
        // nested rules                                                                                              // 59
        var nested = 0;                                                                                              // 60
        _.each(rule.rules, function (nestedRule) {                                                                   // 61
          if (nestedRule.selectors) {                                                                                // 62
            nested += nestedRule.selectors.length;                                                                   // 63
          }                                                                                                          // 64
        });                                                                                                          // 65
                                                                                                                     // 66
        if (current.selectors + nested > LIMIT) {                                                                    // 67
          startNewAst();                                                                                             // 68
        }                                                                                                            // 69
                                                                                                                     // 70
        current.selectors += nested;                                                                                 // 71
        current.nodes.push(rule);                                                                                    // 72
        break;                                                                                                       // 73
    }                                                                                                                // 74
  });                                                                                                                // 75
                                                                                                                     // 76
  // push the left-over                                                                                              // 77
  if (current.nodes.length > 0) {                                                                                    // 78
    startNewAst();                                                                                                   // 79
  }                                                                                                                  // 80
                                                                                                                     // 81
  var stringifyAst = function (node) {                                                                               // 82
    return node.stylesheet                                                                                           // 83
      .rules.map(function (rule) { return visit(rule); })                                                            // 84
      .join('');                                                                                                     // 85
  };                                                                                                                 // 86
                                                                                                                     // 87
  return newAsts.map(stringifyAst);                                                                                  // 88
};                                                                                                                   // 89
                                                                                                                     // 90
var traverse = {};                                                                                                   // 91
                                                                                                                     // 92
traverse.comment = function(node) {                                                                                  // 93
  return emit('', node.position);                                                                                    // 94
};                                                                                                                   // 95
                                                                                                                     // 96
traverse.import = function(node) {                                                                                   // 97
  return emit('@import ' + node.import + ';', node.position);                                                        // 98
};                                                                                                                   // 99
                                                                                                                     // 100
traverse.media = function(node) {                                                                                    // 101
  return emit('@media ' + node.media, node.position, true)                                                           // 102
    + emit('{')                                                                                                      // 103
    + mapVisit(node.rules)                                                                                           // 104
    + emit('}');                                                                                                     // 105
};                                                                                                                   // 106
                                                                                                                     // 107
traverse.document = function(node) {                                                                                 // 108
  var doc = '@' + (node.vendor || '') + 'document ' + node.document;                                                 // 109
                                                                                                                     // 110
  return emit(doc, node.position, true)                                                                              // 111
    + emit('{')                                                                                                      // 112
    + mapVisit(node.rules)                                                                                           // 113
    + emit('}');                                                                                                     // 114
};                                                                                                                   // 115
                                                                                                                     // 116
traverse.charset = function(node) {                                                                                  // 117
  return emit('@charset ' + node.charset + ';', node.position);                                                      // 118
};                                                                                                                   // 119
                                                                                                                     // 120
traverse.namespace = function(node) {                                                                                // 121
  return emit('@namespace ' + node.namespace + ';', node.position);                                                  // 122
};                                                                                                                   // 123
                                                                                                                     // 124
traverse.supports = function(node){                                                                                  // 125
  return emit('@supports ' + node.supports, node.position, true)                                                     // 126
    + emit('{')                                                                                                      // 127
    + mapVisit(node.rules)                                                                                           // 128
    + emit('}');                                                                                                     // 129
};                                                                                                                   // 130
                                                                                                                     // 131
traverse.keyframes = function(node) {                                                                                // 132
  return emit('@'                                                                                                    // 133
    + (node.vendor || '')                                                                                            // 134
    + 'keyframes '                                                                                                   // 135
    + node.name, node.position, true)                                                                                // 136
    + emit('{')                                                                                                      // 137
    + mapVisit(node.keyframes)                                                                                       // 138
    + emit('}');                                                                                                     // 139
};                                                                                                                   // 140
                                                                                                                     // 141
traverse.keyframe = function(node) {                                                                                 // 142
  var decls = node.declarations;                                                                                     // 143
                                                                                                                     // 144
  return emit(node.values.join(','), node.position, true)                                                            // 145
    + emit('{')                                                                                                      // 146
    + mapVisit(decls)                                                                                                // 147
    + emit('}');                                                                                                     // 148
};                                                                                                                   // 149
                                                                                                                     // 150
traverse.page = function(node) {                                                                                     // 151
  var sel = node.selectors.length                                                                                    // 152
    ? node.selectors.join(', ')                                                                                      // 153
    : '';                                                                                                            // 154
                                                                                                                     // 155
  return emit('@page ' + sel, node.position, true)                                                                   // 156
    + emit('{')                                                                                                      // 157
    + mapVisit(node.declarations)                                                                                    // 158
    + emit('}');                                                                                                     // 159
};                                                                                                                   // 160
                                                                                                                     // 161
traverse['font-face'] = function(node){                                                                              // 162
  return emit('@font-face', node.position, true)                                                                     // 163
    + emit('{')                                                                                                      // 164
    + mapVisit(node.declarations)                                                                                    // 165
    + emit('}');                                                                                                     // 166
};                                                                                                                   // 167
                                                                                                                     // 168
traverse.rule = function(node) {                                                                                     // 169
  var decls = node.declarations;                                                                                     // 170
  if (!decls.length) return '';                                                                                      // 171
                                                                                                                     // 172
  var selectors = node.selectors.map(function (selector) {                                                           // 173
    // removes universal selectors like *.class => .class                                                            // 174
    // removes optional whitespace around '>' and '+'                                                                // 175
    return selector.replace(/\*\./, '.')                                                                             // 176
                   .replace(/\s*>\s*/g, '>')                                                                         // 177
                   .replace(/\s*\+\s*/g, '+');                                                                       // 178
  });                                                                                                                // 179
  return emit(selectors.join(','), node.position, true)                                                              // 180
    + emit('{')                                                                                                      // 181
    + mapVisit(decls)                                                                                                // 182
    + emit('}');                                                                                                     // 183
};                                                                                                                   // 184
                                                                                                                     // 185
traverse.declaration = function(node, last) {                                                                        // 186
  var value = node.value;                                                                                            // 187
                                                                                                                     // 188
  // remove optional quotes around font name                                                                         // 189
  if (node.property === 'font') {                                                                                    // 190
    value = value.replace(/\'[^\']+\'/g, function (m) {                                                              // 191
      if (m.indexOf(' ') !== -1)                                                                                     // 192
        return m;                                                                                                    // 193
      return m.replace(/\'/g, '');                                                                                   // 194
    });                                                                                                              // 195
    value = value.replace(/\"[^\"]+\"/g, function (m) {                                                              // 196
      if (m.indexOf(' ') !== -1)                                                                                     // 197
        return m;                                                                                                    // 198
      return m.replace(/\"/g, '');                                                                                   // 199
    });                                                                                                              // 200
  }                                                                                                                  // 201
  // remove url quotes if possible                                                                                   // 202
  // in case it is the last declaration, we can omit the semicolon                                                   // 203
  return emit(node.property + ':' + value, node.position)                                                            // 204
         + (last ? '' : emit(';'));                                                                                  // 205
};                                                                                                                   // 206
                                                                                                                     // 207
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                   //
// packages/minifier-css/minifier.js                                                                                 //
//                                                                                                                   //
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                     //
var cssParse = Npm.require('css-parse');                                                                             // 1
var cssStringify = Npm.require('css-stringify');                                                                     // 2
var url = Npm.require('url');                                                                                        // 3
var path = Npm.require('path');                                                                                      // 4
                                                                                                                     // 5
CssTools = {                                                                                                         // 6
  parseCss: cssParse,                                                                                                // 7
  stringifyCss: cssStringify,                                                                                        // 8
  minifyCss: function (cssText) {                                                                                    // 9
    return CssTools.minifyCssAst(cssParse(cssText));                                                                 // 10
  },                                                                                                                 // 11
  minifyCssAst: function (cssAst) {                                                                                  // 12
    return MinifyAst(cssAst);                                                                                        // 13
  },                                                                                                                 // 14
  mergeCssAsts: function (cssAsts, warnCb) {                                                                         // 15
    var rulesPredicate = function (rules) {                                                                          // 16
      if (! _.isArray(rules))                                                                                        // 17
        rules = [rules];                                                                                             // 18
      return function (node) {                                                                                       // 19
        return _.contains(rules, node.type);                                                                         // 20
      }                                                                                                              // 21
    };                                                                                                               // 22
                                                                                                                     // 23
    // Simple concatenation of CSS files would break @import rules                                                   // 24
    // located in the beginning of a file. Before concatenation, pull them to                                        // 25
    // the beginning of a new syntax tree so they always precede other rules.                                        // 26
    var newAst = {                                                                                                   // 27
      type: 'stylesheet',                                                                                            // 28
      stylesheet: { rules: [] }                                                                                      // 29
    };                                                                                                               // 30
                                                                                                                     // 31
    _.each(cssAsts, function (ast) {                                                                                 // 32
      // Pick only the imports from the beginning of file ignoring @charset                                          // 33
      // rules as every file is assumed to be in UTF-8.                                                              // 34
      var charsetRules = _.filter(ast.stylesheet.rules,                                                              // 35
                                  rulesPredicate("charset"));                                                        // 36
                                                                                                                     // 37
      if (_.any(charsetRules, function (rule) {                                                                      // 38
        // According to MDN, only 'UTF-8' and "UTF-8" are the correct encoding                                       // 39
        // directives representing UTF-8.                                                                            // 40
        return ! /^(['"])UTF-8\1$/.test(rule.charset);                                                               // 41
      })) {                                                                                                          // 42
        warnCb(ast.filename, "@charset rules in this file will be ignored as UTF-8 is the only encoding supported");
      }                                                                                                              // 44
                                                                                                                     // 45
      ast.stylesheet.rules = _.reject(ast.stylesheet.rules,                                                          // 46
                                      rulesPredicate("charset"));                                                    // 47
      var importCount = 0;                                                                                           // 48
      for (var i = 0; i < ast.stylesheet.rules.length; i++)                                                          // 49
        if (! rulesPredicate(["import", "comment"])(ast.stylesheet.rules[i])) {                                      // 50
          importCount = i;                                                                                           // 51
          break;                                                                                                     // 52
        }                                                                                                            // 53
                                                                                                                     // 54
      CssTools.rewriteCssUrls(ast);                                                                                  // 55
                                                                                                                     // 56
      var imports = ast.stylesheet.rules.splice(0, importCount);                                                     // 57
      newAst.stylesheet.rules = newAst.stylesheet.rules.concat(imports);                                             // 58
                                                                                                                     // 59
      // if there are imports left in the middle of file, warn user as it might                                      // 60
      // be a potential bug (imports are valid only in the beginning of file).                                       // 61
      if (_.any(ast.stylesheet.rules, rulesPredicate("import"))) {                                                   // 62
        // XXX make this an error?                                                                                   // 63
        warnCb(ast.filename, "there are some @import rules those are not taking effect as they are required to be in the beginning of the file");
      }                                                                                                              // 65
                                                                                                                     // 66
    });                                                                                                              // 67
                                                                                                                     // 68
    // Now we can put the rest of CSS rules into new AST                                                             // 69
    _.each(cssAsts, function (ast) {                                                                                 // 70
      newAst.stylesheet.rules =                                                                                      // 71
        newAst.stylesheet.rules.concat(ast.stylesheet.rules);                                                        // 72
    });                                                                                                              // 73
                                                                                                                     // 74
    return newAst;                                                                                                   // 75
  },                                                                                                                 // 76
                                                                                                                     // 77
  // We are looking for all relative urls defined with the `url()` functional                                        // 78
  // notation and rewriting them to the equivalent absolute url using the                                            // 79
  // `position.source` path provided by css-parse                                                                    // 80
  // For performance reasons this function acts by side effect by modifying the                                      // 81
  // given AST without doing a deep copy.                                                                            // 82
  rewriteCssUrls: function (ast) {                                                                                   // 83
    var mergedCssPath = "/";                                                                                         // 84
    rewriteRules(ast.stylesheet.rules, mergedCssPath);                                                               // 85
  }                                                                                                                  // 86
};                                                                                                                   // 87
                                                                                                                     // 88
if (typeof Profile !== 'undefined') {                                                                                // 89
  _.each(['parseCss', 'stringifyCss', 'minifyCss',                                                                   // 90
          'minifyCssAst', 'mergeCssAsts', 'rewriteCssUrls'],                                                         // 91
         function (funcName) {                                                                                       // 92
           CssTools[funcName] = Profile('CssTools.'+funcName,                                                        // 93
                                        CssTools[funcName]);                                                         // 94
         });                                                                                                         // 95
}                                                                                                                    // 96
                                                                                                                     // 97
var rewriteRules = function (rules, mergedCssPath) {                                                                 // 98
  _.each(rules, function(rule, ruleIndex) {                                                                          // 99
                                                                                                                     // 100
    // Recurse if there are sub-rules. An example:                                                                   // 101
    //     @media (...) {                                                                                            // 102
    //         .rule { url(...); }                                                                                   // 103
    //     }                                                                                                         // 104
    if (_.has(rule, 'rules')) {                                                                                      // 105
      rewriteRules(rule.rules, mergedCssPath);                                                                       // 106
    }                                                                                                                // 107
                                                                                                                     // 108
    var basePath = pathJoin("/", pathDirname(rule.position.source));                                                 // 109
                                                                                                                     // 110
    // Set the correct basePath based on how the linked asset will be served.                                        // 111
    // XXX This is wrong. We are coupling the information about how files will                                       // 112
    // be served by the web server to the information how they were stored                                           // 113
    // originally on the filesystem in the project structure. Ideally, there                                         // 114
    // should be some module that tells us precisely how each asset will be                                          // 115
    // served but for now we are just assuming that everything that comes from                                       // 116
    // a folder starting with "/packages/" is served on the same path as                                             // 117
    // it was on the filesystem and everything else is served on root "/".                                           // 118
    if (! basePath.match(/^\/?packages\//i))                                                                         // 119
        basePath = "/";                                                                                              // 120
                                                                                                                     // 121
    _.each(rule.declarations, function(declaration, declarationIndex) {                                              // 122
      var parts, resource, absolutePath, relativeToMergedCss, quote, oldCssUrl, newCssUrl;                           // 123
      var value = declaration.value;                                                                                 // 124
                                                                                                                     // 125
      // Match css values containing some functional calls to `url(URI)` where                                       // 126
      // URI is optionally quoted.                                                                                   // 127
      // Note that a css value can contains other elements, for instance:                                            // 128
      //   background: top center url("background.png") black;                                                       // 129
      // or even multiple url(), for instance for multiple backgrounds.                                              // 130
      var cssUrlRegex = /url\s*\(\s*(['"]?)(.+?)\1\s*\)/gi;                                                          // 131
      while (parts = cssUrlRegex.exec(value)) {                                                                      // 132
        oldCssUrl = parts[0];                                                                                        // 133
        quote = parts[1];                                                                                            // 134
        resource = url.parse(parts[2]);                                                                              // 135
                                                                                                                     // 136
                                                                                                                     // 137
        // We don't rewrite URLs starting with a protocol definition such as                                         // 138
        // http, https, or data, or those with network-path references                                               // 139
        // i.e. //img.domain.com/cat.gif                                                                             // 140
        if (resource.protocol !== null || resource.href.startsWith('//') || resource.href.startsWith('#')) {         // 141
          continue;                                                                                                  // 142
        }                                                                                                            // 143
                                                                                                                     // 144
        // Rewrite relative paths (that refers to the internal application tree)                                     // 145
        // to absolute paths (addressable from the public build).                                                    // 146
        if (isRelative(resource.path)) {                                                                             // 147
          absolutePath = pathJoin(basePath, resource.path);                                                          // 148
        } else {                                                                                                     // 149
          absolutePath = resource.path;                                                                              // 150
        }                                                                                                            // 151
                                                                                                                     // 152
        if (resource.hash) {                                                                                         // 153
          absolutePath += resource.hash;                                                                             // 154
        }                                                                                                            // 155
                                                                                                                     // 156
        // We used to finish the rewriting process at the absolute path step                                         // 157
        // above. But it didn't work in case the Meteor application was deployed                                     // 158
        // under a sub-path (eg `ROOT_URL=http://localhost:3000/myapp meteor`)                                       // 159
        // in which case the resources linked in the merged CSS file would miss                                      // 160
        // the `myapp/` prefix. Since this path prefix is only known at launch                                       // 161
        // time (rather than build time) we can't use absolute paths to link                                         // 162
        // resources in the generated CSS.                                                                           // 163
        //                                                                                                           // 164
        // Instead we transform absolute paths to make them relative to the                                          // 165
        // merged CSS, leaving to the browser the responsibility to calculate                                        // 166
        // the final resource links (by adding the application deployment                                            // 167
        // prefix, here `myapp/`, if applicable).                                                                    // 168
        relativeToMergedCss = pathRelative(mergedCssPath, absolutePath);                                             // 169
        newCssUrl = "url(" + quote + relativeToMergedCss + quote + ")";                                              // 170
        value = value.replace(oldCssUrl, newCssUrl);                                                                 // 171
      }                                                                                                              // 172
                                                                                                                     // 173
      declaration.value = value;                                                                                     // 174
    });                                                                                                              // 175
  });                                                                                                                // 176
};                                                                                                                   // 177
                                                                                                                     // 178
var isRelative = function(path) {                                                                                    // 179
  return path && path.charAt(0) !== '/';                                                                             // 180
};                                                                                                                   // 181
                                                                                                                     // 182
// These are duplicates of functions in tools/files.js, because we don't have                                        // 183
// a good way of exporting them into packages.                                                                       // 184
// XXX deduplicate files.js into a package at some point so that we can use it                                       // 185
// in core                                                                                                           // 186
var toOSPath = function (p) {                                                                                        // 187
  if (process.platform === 'win32')                                                                                  // 188
    return p.replace(/\//g, '\\');                                                                                   // 189
  return p;                                                                                                          // 190
}                                                                                                                    // 191
                                                                                                                     // 192
var toStandardPath = function (p) {                                                                                  // 193
  if (process.platform === 'win32')                                                                                  // 194
    return p.replace(/\\/g, '/');                                                                                    // 195
  return p;                                                                                                          // 196
};                                                                                                                   // 197
                                                                                                                     // 198
var pathJoin = function (a, b) {                                                                                     // 199
  return toStandardPath(path.join(                                                                                   // 200
    toOSPath(a),                                                                                                     // 201
    toOSPath(b)));                                                                                                   // 202
};                                                                                                                   // 203
                                                                                                                     // 204
var pathDirname = function (p) {                                                                                     // 205
  return toStandardPath(path.dirname(toOSPath(p)));                                                                  // 206
};                                                                                                                   // 207
                                                                                                                     // 208
var pathRelative = function(p1, p2) {                                                                                // 209
  return toStandardPath(path.relative(toOSPath(p1), toOSPath(p2)));                                                  // 210
};                                                                                                                   // 211
                                                                                                                     // 212
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
