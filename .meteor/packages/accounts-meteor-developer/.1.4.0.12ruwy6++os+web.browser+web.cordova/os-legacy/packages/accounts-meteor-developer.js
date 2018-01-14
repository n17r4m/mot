(function(){

///////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                           //
// packages/accounts-meteor-developer/notice.js                                              //
//                                                                                           //
///////////////////////////////////////////////////////////////////////////////////////////////
                                                                                             //
if (Package['accounts-ui']                                                                   // 1
    && !Package['service-configuration']                                                     // 2
    && !Package.hasOwnProperty('meteor-developer-config-ui')) {                              // 3
  console.warn(                                                                              // 4
    "Note: You're using accounts-ui and accounts-meteor-developer,\n" +                      // 5
    "but didn't install the configuration UI for the Meteor Developer\n" +                   // 6
    "Accounts OAuth. You can install it with:\n" +                                           // 7
    "\n" +                                                                                   // 8
    "    meteor add meteor-developer-config-ui" +                                            // 9
    "\n"                                                                                     // 10
  );                                                                                         // 11
}                                                                                            // 12
                                                                                             // 13
///////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

///////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                           //
// packages/accounts-meteor-developer/meteor-developer.js                                    //
//                                                                                           //
///////////////////////////////////////////////////////////////////////////////////////////////
                                                                                             //
Accounts.oauth.registerService("meteor-developer");                                          // 1
                                                                                             // 2
if (Meteor.isClient) {                                                                       // 3
  const loginWithMeteorDeveloperAccount = function (options, callback) {                     // 4
    // support a callback without options                                                    // 5
    if (! callback && typeof options === "function") {                                       // 6
      callback = options;                                                                    // 7
      options = null;                                                                        // 8
    }                                                                                        // 9
                                                                                             // 10
    var credentialRequestCompleteCallback =                                                  // 11
          Accounts.oauth.credentialRequestCompleteHandler(callback);                         // 12
    MeteorDeveloperAccounts.requestCredential(options, credentialRequestCompleteCallback);   // 13
  };                                                                                         // 14
  Accounts.registerClientLoginFunction('meteor-developer', loginWithMeteorDeveloperAccount);
  Meteor.loginWithMeteorDeveloperAccount = function () {                                     // 16
    return Accounts.applyLoginFunction('meteor-developer', arguments);                       // 17
  };                                                                                         // 18
} else {                                                                                     // 19
  Accounts.addAutopublishFields({                                                            // 20
    // publish all fields including access token, which can legitimately be used             // 21
    // from the client (if transmitted over ssl or on localhost).                            // 22
    forLoggedInUser: ['services.meteor-developer'],                                          // 23
    forOtherUsers: [                                                                         // 24
      'services.meteor-developer.username',                                                  // 25
      'services.meteor-developer.profile',                                                   // 26
      'services.meteor-developer.id'                                                         // 27
    ]                                                                                        // 28
  });                                                                                        // 29
}                                                                                            // 30
                                                                                             // 31
///////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
