(function(){

//////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                  //
// packages/weibo-oauth/weibo_client.js                                                             //
//                                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                    //
Weibo = {};                                                                                         // 1
                                                                                                    // 2
// Request Weibo credentials for the user                                                           // 3
// @param options {optional}                                                                        // 4
// @param credentialRequestCompleteCallback {Function} Callback function to call on                 // 5
//   completion. Takes one argument, credentialToken on success, or Error on                        // 6
//   error.                                                                                         // 7
Weibo.requestCredential = function (options, credentialRequestCompleteCallback) {                   // 8
  // support both (options, callback) and (callback).                                               // 9
  if (!credentialRequestCompleteCallback && typeof options === 'function') {                        // 10
    credentialRequestCompleteCallback = options;                                                    // 11
    options = {};                                                                                   // 12
  }                                                                                                 // 13
                                                                                                    // 14
  var config = ServiceConfiguration.configurations.findOne({service: 'weibo'});                     // 15
  if (!config) {                                                                                    // 16
    credentialRequestCompleteCallback && credentialRequestCompleteCallback(                         // 17
      new ServiceConfiguration.ConfigError());                                                      // 18
    return;                                                                                         // 19
  }                                                                                                 // 20
                                                                                                    // 21
  var credentialToken = Random.secret();                                                            // 22
                                                                                                    // 23
  var loginStyle = OAuth._loginStyle('weibo', config, options);                                     // 24
                                                                                                    // 25
  // XXX need to support configuring access_type and scope                                          // 26
  var loginUrl =                                                                                    // 27
        'https://api.weibo.com/oauth2/authorize' +                                                  // 28
        '?response_type=code' +                                                                     // 29
        '&client_id=' + config.clientId +                                                           // 30
        '&redirect_uri=' + OAuth._redirectUri('weibo', config, null, {replaceLocalhost: true}) +    // 31
        '&state=' + OAuth._stateParam(loginStyle, credentialToken, options && options.redirectUrl);
                                                                                                    // 33
  OAuth.launchLogin({                                                                               // 34
    loginService: "weibo",                                                                          // 35
    loginStyle: loginStyle,                                                                         // 36
    loginUrl: loginUrl,                                                                             // 37
    credentialRequestCompleteCallback: credentialRequestCompleteCallback,                           // 38
    credentialToken: credentialToken                                                                // 39
  });                                                                                               // 40
};                                                                                                  // 41
                                                                                                    // 42
//////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
