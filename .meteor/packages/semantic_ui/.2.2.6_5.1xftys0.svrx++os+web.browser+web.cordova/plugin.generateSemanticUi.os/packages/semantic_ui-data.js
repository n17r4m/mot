(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var global = Package.meteor.global;
var meteorEnv = Package.meteor.meteorEnv;

/* Package-scope variables */
var semanticUiDataPackage;

(function(){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/semantic_ui-data/semantic-ui-data.js                     //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
var fs = Npm.require('fs');

semanticUiDataPackage = {};

semanticUiDataPackage.getTextFile = function (filePath) {
  return Assets.getText(filePath);
};

semanticUiDataPackage.getBinaryFile = function (filePath) {
  return Assets.getBinary(filePath);
};

///////////////////////////////////////////////////////////////////////

}).call(this);


/* Exports */
if (typeof Package === 'undefined') Package = {};
(function (pkg, symbols) {
  for (var s in symbols)
    (s in pkg) || (pkg[s] = symbols[s]);
})(Package['semantic:ui-data'] = {}, {
  semanticUiDataPackage: semanticUiDataPackage
});

})();
