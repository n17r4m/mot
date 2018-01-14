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
  compileForShell: function () {                                     // 2
    function compileForShell(command) {                              // 1
      var babelOptions = Babel.getDefaultOptions();                  // 3
      babelOptions.sourceMap = false;                                // 4
      babelOptions.ast = false;                                      // 5
      return Babel.compile(command, babelOptions).code;              // 6
    }                                                                // 7
                                                                     //
    return compileForShell;                                          // 1
  }()                                                                // 1
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
//# sourceMappingURL=data:application/json;charset=utf8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm1ldGVvcjovL/CfkrthcHAvcGFja2FnZXMvZWNtYXNjcmlwdC9lY21hc2NyaXB0LmpzIl0sIm5hbWVzIjpbIkVDTUFTY3JpcHQiLCJjb21waWxlRm9yU2hlbGwiLCJjb21tYW5kIiwiYmFiZWxPcHRpb25zIiwiQmFiZWwiLCJnZXREZWZhdWx0T3B0aW9ucyIsInNvdXJjZU1hcCIsImFzdCIsImNvbXBpbGUiLCJjb2RlIl0sIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQUFBQSxhQUFhO0FBQ1hDLGlCQURXO0FBQUEsNkJBQ0tDLE9BREwsRUFDYztBQUN2QixVQUFNQyxlQUFlQyxNQUFNQyxpQkFBTixFQUFyQjtBQUNBRixtQkFBYUcsU0FBYixHQUF5QixLQUF6QjtBQUNBSCxtQkFBYUksR0FBYixHQUFtQixLQUFuQjtBQUNBLGFBQU9ILE1BQU1JLE9BQU4sQ0FBY04sT0FBZCxFQUF1QkMsWUFBdkIsRUFBcUNNLElBQTVDO0FBQ0Q7O0FBTlU7QUFBQTtBQUFBLENBQWIsd0UiLCJmaWxlIjoiL3BhY2thZ2VzL2VjbWFzY3JpcHQuanMiLCJzb3VyY2VzQ29udGVudCI6WyJFQ01BU2NyaXB0ID0ge1xuICBjb21waWxlRm9yU2hlbGwoY29tbWFuZCkge1xuICAgIGNvbnN0IGJhYmVsT3B0aW9ucyA9IEJhYmVsLmdldERlZmF1bHRPcHRpb25zKCk7XG4gICAgYmFiZWxPcHRpb25zLnNvdXJjZU1hcCA9IGZhbHNlO1xuICAgIGJhYmVsT3B0aW9ucy5hc3QgPSBmYWxzZTtcbiAgICByZXR1cm4gQmFiZWwuY29tcGlsZShjb21tYW5kLCBiYWJlbE9wdGlvbnMpLmNvZGU7XG4gIH1cbn07XG4iXX0=
