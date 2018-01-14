(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var global = Package.meteor.global;
var meteorEnv = Package.meteor.meteorEnv;
var Babel = Package['babel-compiler'].Babel;
var BabelCompiler = Package['babel-compiler'].BabelCompiler;

/* Package-scope variables */
var ECMAScript;

(function(){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/ecmascript/ecmascript.js                                 //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
ECMAScript = {                                                       // 1
  compileForShell: function compileForShell(command) {               // 2
    var babelOptions = Babel.getDefaultOptions();                    // 3
    babelOptions.sourceMap = false;                                  // 4
    babelOptions.ast = false;                                        // 5
    return Babel.compile(command, babelOptions).code;                // 6
  }                                                                  // 7
};                                                                   // 1
///////////////////////////////////////////////////////////////////////

}).call(this);


/* Exports */
if (typeof Package === 'undefined') Package = {};
(function (pkg, symbols) {
  for (var s in symbols)
    (s in pkg) || (pkg[s] = symbols[s]);
})(Package.ecmascript = {}, {
  ECMAScript: ECMAScript
});

})();



//# sourceURL=meteor://💻app/packages/ecmascript.js
//# sourceMappingURL=data:application/json;charset=utf8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvZWNtYXNjcmlwdC9lY21hc2NyaXB0LmpzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQUEsYUFBYTtBQUNYLGlCQURXLDJCQUNLLE9BREwsRUFDYztBQUN2QixRQUFNLGVBQWUsTUFBTSxpQkFBTixFQUFyQjtBQUNBLGlCQUFhLFNBQWIsR0FBeUIsS0FBekI7QUFDQSxpQkFBYSxHQUFiLEdBQW1CLEtBQW5CO0FBQ0EsV0FBTyxNQUFNLE9BQU4sQ0FBYyxPQUFkLEVBQXVCLFlBQXZCLEVBQXFDLElBQTVDO0FBQ0Q7QUFOVSxDQUFiLHdFIiwiZmlsZSI6Ii9wYWNrYWdlcy9lY21hc2NyaXB0LmpzIiwic291cmNlc0NvbnRlbnQiOlsiRUNNQVNjcmlwdCA9IHtcbiAgY29tcGlsZUZvclNoZWxsKGNvbW1hbmQpIHtcbiAgICBjb25zdCBiYWJlbE9wdGlvbnMgPSBCYWJlbC5nZXREZWZhdWx0T3B0aW9ucygpO1xuICAgIGJhYmVsT3B0aW9ucy5zb3VyY2VNYXAgPSBmYWxzZTtcbiAgICBiYWJlbE9wdGlvbnMuYXN0ID0gZmFsc2U7XG4gICAgcmV0dXJuIEJhYmVsLmNvbXBpbGUoY29tbWFuZCwgYmFiZWxPcHRpb25zKS5jb2RlO1xuICB9XG59O1xuIl19
