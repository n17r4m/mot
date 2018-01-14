(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-weibo/notice.js                                                                   //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
if (Package['accounts-ui']                                                                             // 1
    && !Package['service-configuration']                                                               // 2
    && !Package.hasOwnProperty('weibo-config-ui')) {                                                   // 3
  console.warn(                                                                                        // 4
    "Note: You're using accounts-ui and accounts-weibo,\n" +                                           // 5
    "but didn't install the configuration UI for the Weibo\n" +                                        // 6
    "OAuth. You can install it with:\n" +                                                              // 7
    "\n" +                                                                                             // 8
    "    meteor add weibo-config-ui" +                                                                 // 9
    "\n"                                                                                               // 10
  );                                                                                                   // 11
}                                                                                                      // 12
                                                                                                       // 13
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-weibo/weibo.js                                                                    //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
Accounts.oauth.registerService('weibo');                                                               // 1
                                                                                                       // 2
if (Meteor.isClient) {                                                                                 // 3
  const loginWithWeibo = function(options, callback) {                                                 // 4
    // support a callback without options                                                              // 5
    if (! callback && typeof options === "function") {                                                 // 6
      callback = options;                                                                              // 7
      options = null;                                                                                  // 8
    }                                                                                                  // 9
                                                                                                       // 10
    var credentialRequestCompleteCallback = Accounts.oauth.credentialRequestCompleteHandler(callback);
    Weibo.requestCredential(options, credentialRequestCompleteCallback);                               // 12
  };                                                                                                   // 13
  Accounts.registerClientLoginFunction('weibo', loginWithWeibo);                                       // 14
  Meteor.loginWithWeibo = function () {                                                                // 15
    return Accounts.applyLoginFunction('weibo', arguments);                                            // 16
  };                                                                                                   // 17
} else {                                                                                               // 18
  Accounts.addAutopublishFields({                                                                      // 19
    // publish all fields including access token, which can legitimately                               // 20
    // be used from the client (if transmitted over ssl or on localhost)                               // 21
    forLoggedInUser: ['services.weibo'],                                                               // 22
    forOtherUsers: ['services.weibo.screenName']                                                       // 23
  });                                                                                                  // 24
}                                                                                                      // 25
                                                                                                       // 26
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
