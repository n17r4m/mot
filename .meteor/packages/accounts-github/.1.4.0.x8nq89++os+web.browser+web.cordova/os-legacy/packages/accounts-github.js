(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-github/notice.js                                                                  //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
if (Package['accounts-ui']                                                                             // 1
    && !Package['service-configuration']                                                               // 2
    && !Package.hasOwnProperty('github-config-ui')) {                                                  // 3
  console.warn(                                                                                        // 4
    "Note: You're using accounts-ui and accounts-github,\n" +                                          // 5
    "but didn't install the configuration UI for the GitHub\n" +                                       // 6
    "OAuth. You can install it with:\n" +                                                              // 7
    "\n" +                                                                                             // 8
    "    meteor add github-config-ui" +                                                                // 9
    "\n"                                                                                               // 10
  );                                                                                                   // 11
}                                                                                                      // 12
                                                                                                       // 13
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-github/github.js                                                                  //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
Accounts.oauth.registerService('github');                                                              // 1
                                                                                                       // 2
if (Meteor.isClient) {                                                                                 // 3
  const loginWithGithub = function(options, callback) {                                                // 4
    // support a callback without options                                                              // 5
    if (! callback && typeof options === "function") {                                                 // 6
      callback = options;                                                                              // 7
      options = null;                                                                                  // 8
    }                                                                                                  // 9
                                                                                                       // 10
    var credentialRequestCompleteCallback = Accounts.oauth.credentialRequestCompleteHandler(callback);
    Github.requestCredential(options, credentialRequestCompleteCallback);                              // 12
  };                                                                                                   // 13
  Accounts.registerClientLoginFunction('github', loginWithGithub);                                     // 14
  Meteor.loginWithGithub = function () {                                                               // 15
    return Accounts.applyLoginFunction('github', arguments);                                           // 16
  };                                                                                                   // 17
} else {                                                                                               // 18
  Accounts.addAutopublishFields({                                                                      // 19
    // not sure whether the github api can be used from the browser,                                   // 20
    // thus not sure if we should be sending access tokens; but we do it                               // 21
    // for all other oauth2 providers, and it may come in handy.                                       // 22
    forLoggedInUser: ['services.github'],                                                              // 23
    forOtherUsers: ['services.github.username']                                                        // 24
  });                                                                                                  // 25
}                                                                                                      // 26
                                                                                                       // 27
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
