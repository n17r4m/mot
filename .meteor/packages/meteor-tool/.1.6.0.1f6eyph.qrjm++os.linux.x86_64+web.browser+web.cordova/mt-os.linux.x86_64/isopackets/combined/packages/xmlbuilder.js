(function () {

/* Imports */
var Meteor = Package.meteor.Meteor;
var global = Package.meteor.global;
var meteorEnv = Package.meteor.meteorEnv;

/* Package-scope variables */
var XmlBuilder;

(function(){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/xmlbuilder/xmlbuilder.js                                 //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
XmlBuilder = Npm.require('xmlbuilder');


///////////////////////////////////////////////////////////////////////

}).call(this);


/* Exports */
if (typeof Package === 'undefined') Package = {};
(function (pkg, symbols) {
  for (var s in symbols)
    (s in pkg) || (pkg[s] = symbols[s]);
})(Package.xmlbuilder = {}, {
  XmlBuilder: XmlBuilder
});

})();
