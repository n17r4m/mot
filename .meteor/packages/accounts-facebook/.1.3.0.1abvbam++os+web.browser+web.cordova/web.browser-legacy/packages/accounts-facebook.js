(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-facebook/notice.js                                                                //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
if (Package['accounts-ui']                                                                             // 1
    && !Package['service-configuration']                                                               // 2
    && !Package.hasOwnProperty('facebook-config-ui')) {                                                // 3
  console.warn(                                                                                        // 4
    "Note: You're using accounts-ui and accounts-facebook,\n" +                                        // 5
    "but didn't install the configuration UI for the Facebook\n" +                                     // 6
    "OAuth. You can install it with:\n" +                                                              // 7
    "\n" +                                                                                             // 8
    "    meteor add facebook-config-ui" +                                                              // 9
    "\n"                                                                                               // 10
  );                                                                                                   // 11
}                                                                                                      // 12
                                                                                                       // 13
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-facebook/facebook.js                                                              //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
Accounts.oauth.registerService('facebook');                                                            // 1
                                                                                                       // 2
if (Meteor.isClient) {                                                                                 // 3
  const loginWithFacebook = function(options, callback) {                                              // 4
    // support a callback without options                                                              // 5
    if (! callback && typeof options === "function") {                                                 // 6
      callback = options;                                                                              // 7
      options = null;                                                                                  // 8
    }                                                                                                  // 9
                                                                                                       // 10
    var credentialRequestCompleteCallback = Accounts.oauth.credentialRequestCompleteHandler(callback);
    Facebook.requestCredential(options, credentialRequestCompleteCallback);                            // 12
  };                                                                                                   // 13
  Accounts.registerClientLoginFunction('facebook', loginWithFacebook);                                 // 14
  Meteor.loginWithFacebook = function () {                                                             // 15
    return Accounts.applyLoginFunction('facebook', arguments);                                         // 16
  };                                                                                                   // 17
} else {                                                                                               // 18
  Accounts.addAutopublishFields({                                                                      // 19
    // publish all fields including access token, which can legitimately                               // 20
    // be used from the client (if transmitted over ssl or on                                          // 21
    // localhost). https://developers.facebook.com/docs/concepts/login/access-tokens-and-types/,       // 22
    // "Sharing of Access Tokens"                                                                      // 23
    forLoggedInUser: ['services.facebook'],                                                            // 24
    forOtherUsers: [                                                                                   // 25
      // https://www.facebook.com/help/167709519956542                                                 // 26
      'services.facebook.id', 'services.facebook.username', 'services.facebook.gender'                 // 27
    ]                                                                                                  // 28
  });                                                                                                  // 29
}                                                                                                      // 30
                                                                                                       // 31
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
