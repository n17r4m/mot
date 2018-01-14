(function () {

/* Imports */
var Babel = Package['babel-compiler'].Babel;
var BabelCompiler = Package['babel-compiler'].BabelCompiler;

(function(){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/compile-ecmascript/plugin.js                             //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
Plugin.registerCompiler({
  extensions: ['js', 'jsx'],
}, function () {
  return new BabelCompiler({
    react: true
  });
});

///////////////////////////////////////////////////////////////////////

}).call(this);


/* Exports */
if (typeof Package === 'undefined') Package = {};
Package['compile-ecmascript'] = {};

})();
