(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-meetup/notice.js                                                                  //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
if (Package['accounts-ui']                                                                             // 1
    && !Package['service-configuration']                                                               // 2
    && !Package.hasOwnProperty('meetup-config-ui')) {                                                  // 3
  console.warn(                                                                                        // 4
    "Note: You're using accounts-ui and accounts-meetup,\n" +                                          // 5
    "but didn't install the configuration UI for the Meetup\n" +                                       // 6
    "OAuth. You can install it with:\n" +                                                              // 7
    "\n" +                                                                                             // 8
    "    meteor add meetup-config-ui" +                                                                // 9
    "\n"                                                                                               // 10
  );                                                                                                   // 11
}                                                                                                      // 12
                                                                                                       // 13
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                     //
// packages/accounts-meetup/meetup.js                                                                  //
//                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                       //
Accounts.oauth.registerService('meetup');                                                              // 1
                                                                                                       // 2
if (Meteor.isClient) {                                                                                 // 3
  const loginWithMeetup = function(options, callback) {                                                // 4
    // support a callback without options                                                              // 5
    if (! callback && typeof options === "function") {                                                 // 6
      callback = options;                                                                              // 7
      options = null;                                                                                  // 8
    }                                                                                                  // 9
                                                                                                       // 10
    var credentialRequestCompleteCallback = Accounts.oauth.credentialRequestCompleteHandler(callback);
    Meetup.requestCredential(options, credentialRequestCompleteCallback);                              // 12
  };                                                                                                   // 13
  Accounts.registerClientLoginFunction('meetup', loginWithMeetup);                                     // 14
  Meteor.loginWithMeetup = function () {                                                               // 15
    return Accounts.applyLoginFunction('meetup', arguments);                                           // 16
  };                                                                                                   // 17
} else {                                                                                               // 18
  Accounts.addAutopublishFields({                                                                      // 19
    // publish all fields including access token, which can legitimately                               // 20
    // be used from the client (if transmitted over ssl or on                                          // 21
    // localhost). http://www.meetup.com/meetup_api/auth/#oauth2implicit                               // 22
    forLoggedInUser: ['services.meetup'],                                                              // 23
    forOtherUsers: ['services.meetup.id']                                                              // 24
  });                                                                                                  // 25
}                                                                                                      // 26
                                                                                                       // 27
/////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
