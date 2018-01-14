(function(){

//////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                  //
// packages/meteor-developer-oauth/meteor_developer_common.js                                       //
//                                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                    //
MeteorDeveloperAccounts = {};                                                                       // 1
                                                                                                    // 2
MeteorDeveloperAccounts._server = "https://www.meteor.com";                                         // 3
                                                                                                    // 4
// Options are:                                                                                     // 5
//  - developerAccountsServer: defaults to "https://www.meteor.com"                                 // 6
MeteorDeveloperAccounts._config = function (options) {                                              // 7
  if (options.developerAccountsServer) {                                                            // 8
    MeteorDeveloperAccounts._server = options.developerAccountsServer;                              // 9
  }                                                                                                 // 10
};                                                                                                  // 11
                                                                                                    // 12
//////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

//////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                  //
// packages/meteor-developer-oauth/meteor_developer_client.js                                       //
//                                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                    //
// Request Meteor developer account credentials for the user                                        // 1
// @param credentialRequestCompleteCallback {Function} Callback function to call on                 // 2
//   completion. Takes one argument, credentialToken on success, or Error on                        // 3
//   error.                                                                                         // 4
var requestCredential = function (options, credentialRequestCompleteCallback) {                     // 5
  // support a callback without options                                                             // 6
  if (! credentialRequestCompleteCallback && typeof options === "function") {                       // 7
    credentialRequestCompleteCallback = options;                                                    // 8
    options = null;                                                                                 // 9
  }                                                                                                 // 10
                                                                                                    // 11
  var config = ServiceConfiguration.configurations.findOne({                                        // 12
    service: 'meteor-developer'                                                                     // 13
  });                                                                                               // 14
  if (!config) {                                                                                    // 15
    credentialRequestCompleteCallback &&                                                            // 16
      credentialRequestCompleteCallback(new ServiceConfiguration.ConfigError());                    // 17
    return;                                                                                         // 18
  }                                                                                                 // 19
                                                                                                    // 20
  var credentialToken = Random.secret();                                                            // 21
                                                                                                    // 22
  var loginStyle = OAuth._loginStyle('meteor-developer', config, options);                          // 23
                                                                                                    // 24
  var loginUrl =                                                                                    // 25
        MeteorDeveloperAccounts._server +                                                           // 26
        "/oauth2/authorize?" +                                                                      // 27
        "state=" + OAuth._stateParam(loginStyle, credentialToken, options && options.redirectUrl) +
        "&response_type=code&" +                                                                    // 29
        "client_id=" + config.clientId;                                                             // 30
                                                                                                    // 31
  /**                                                                                               // 32
   * @deprecated in 1.3.0                                                                           // 33
   */                                                                                               // 34
  if (options && options.userEmail && !options.loginHint) {                                         // 35
    options.loginHint = options.userEmail;                                                          // 36
    delete options.userEmail;                                                                       // 37
  }                                                                                                 // 38
                                                                                                    // 39
  if (options && options.loginHint) {                                                               // 40
    loginUrl += '&user_email=' + encodeURIComponent(options.loginHint);                             // 41
  }                                                                                                 // 42
                                                                                                    // 43
  loginUrl += "&redirect_uri=" + OAuth._redirectUri('meteor-developer', config);                    // 44
                                                                                                    // 45
  OAuth.launchLogin({                                                                               // 46
    loginService: "meteor-developer",                                                               // 47
    loginStyle: loginStyle,                                                                         // 48
    loginUrl: loginUrl,                                                                             // 49
    credentialRequestCompleteCallback: credentialRequestCompleteCallback,                           // 50
    credentialToken: credentialToken,                                                               // 51
    popupOptions: {width: 470, height: 490}                                                         // 52
  });                                                                                               // 53
};                                                                                                  // 54
                                                                                                    // 55
MeteorDeveloperAccounts.requestCredential = requestCredential;                                      // 56
                                                                                                    // 57
//////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
