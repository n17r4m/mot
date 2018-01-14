(function(){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/semantic_ui-data/semantic-ui-data.js                     //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
var fs = Npm.require('fs');                                          // 1
                                                                     // 2
semanticUiDataPackage = {};                                          // 3
                                                                     // 4
semanticUiDataPackage.getTextFile = function (filePath) {            // 5
  return Assets.getText(filePath);                                   // 6
};                                                                   // 7
                                                                     // 8
semanticUiDataPackage.getBinaryFile = function (filePath) {          // 9
  return Assets.getBinary(filePath);                                 // 10
};                                                                   // 11
                                                                     // 12
///////////////////////////////////////////////////////////////////////

}).call(this);
