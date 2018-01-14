(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-twitter/notice.js                                                                 //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
if (Package['accounts-ui']                                                                             // 1
    && !Package['service-configuration']                                                               // 2
    && !Package.hasOwnProperty('twitter-config-ui')) {                                                 // 3
  console.warn(                                                                                        // 4
    "Note: You're using accounts-ui and accounts-twitter,\n" +                                         // 5
    "but didn't install the configuration UI for Twitter\n" +                                          // 6
    "OAuth. You can install it with:\n" +                                                              // 7
    "\n" +                                                                                             // 8
    "    meteor add twitter-config-ui" +                                                               // 9
    "\n"                                                                                               // 10
  );                                                                                                   // 11
}                                                                                                      // 12
                                                                                                       // 13
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-twitter/twitter.js                                                                //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
Accounts.oauth.registerService('twitter');                                                             // 1
                                                                                                       // 2
if (Meteor.isClient) {                                                                                 // 3
  const loginWithTwitter = function(options, callback) {                                               // 4
    // support a callback without options                                                              // 5
    if (! callback && typeof options === "function") {                                                 // 6
      callback = options;                                                                              // 7
      options = null;                                                                                  // 8
    }                                                                                                  // 9
                                                                                                       // 10
    var credentialRequestCompleteCallback = Accounts.oauth.credentialRequestCompleteHandler(callback);
    Twitter.requestCredential(options, credentialRequestCompleteCallback);                             // 12
  };                                                                                                   // 13
  Accounts.registerClientLoginFunction('twitter', loginWithTwitter);                                   // 14
  Meteor.loginWithTwitter = function () {                                                              // 15
    return Accounts.applyLoginFunction('twitter', arguments);                                          // 16
  };                                                                                                   // 17
} else {                                                                                               // 18
  var autopublishedFields = _.map(                                                                     // 19
    // don't send access token. https://dev.twitter.com/discussions/5025                               // 20
    Twitter.whitelistedFields.concat(['id', 'screenName']),                                            // 21
    function (subfield) { return 'services.twitter.' + subfield; });                                   // 22
                                                                                                       // 23
  Accounts.addAutopublishFields({                                                                      // 24
    forLoggedInUser: autopublishedFields,                                                              // 25
    forOtherUsers: autopublishedFields                                                                 // 26
  });                                                                                                  // 27
}                                                                                                      // 28
                                                                                                       // 29
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
