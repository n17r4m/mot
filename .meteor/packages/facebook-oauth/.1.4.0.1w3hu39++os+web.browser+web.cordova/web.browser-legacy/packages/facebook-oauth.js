(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                   //
// packages/facebook-oauth/facebook_client.js                                                        //
//                                                                                                   //
///////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                     //
Facebook = {};                                                                                       // 1
                                                                                                     // 2
// Request Facebook credentials for the user                                                         // 3
//                                                                                                   // 4
// @param options {optional}                                                                         // 5
// @param credentialRequestCompleteCallback {Function} Callback function to call on                  // 6
//   completion. Takes one argument, credentialToken on success, or Error on                         // 7
//   error.                                                                                          // 8
Facebook.requestCredential = function (options, credentialRequestCompleteCallback) {                 // 9
  // support both (options, callback) and (callback).                                                // 10
  if (!credentialRequestCompleteCallback && typeof options === 'function') {                         // 11
    credentialRequestCompleteCallback = options;                                                     // 12
    options = {};                                                                                    // 13
  }                                                                                                  // 14
                                                                                                     // 15
  var config = ServiceConfiguration.configurations.findOne({service: 'facebook'});                   // 16
  if (!config) {                                                                                     // 17
    credentialRequestCompleteCallback && credentialRequestCompleteCallback(                          // 18
      new ServiceConfiguration.ConfigError());                                                       // 19
    return;                                                                                          // 20
  }                                                                                                  // 21
                                                                                                     // 22
  var credentialToken = Random.secret();                                                             // 23
  var mobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|Windows Phone/i.test(navigator.userAgent);
  var display = mobile ? 'touch' : 'popup';                                                          // 25
                                                                                                     // 26
  var scope = "email";                                                                               // 27
  if (options && options.requestPermissions)                                                         // 28
    scope = options.requestPermissions.join(',');                                                    // 29
                                                                                                     // 30
  var loginStyle = OAuth._loginStyle('facebook', config, options);                                   // 31
                                                                                                     // 32
  var loginUrl =                                                                                     // 33
        'https://www.facebook.com/v2.9/dialog/oauth?client_id=' + config.appId +                     // 34
        '&redirect_uri=' + OAuth._redirectUri('facebook', config) +                                  // 35
        '&display=' + display + '&scope=' + scope +                                                  // 36
        '&state=' + OAuth._stateParam(loginStyle, credentialToken, options && options.redirectUrl);  // 37
                                                                                                     // 38
  // Handle authentication type (e.g. for force login you need auth_type: "reauthenticate")          // 39
  if (options && options.auth_type) {                                                                // 40
    loginUrl += "&auth_type=" + encodeURIComponent(options.auth_type);                               // 41
  }                                                                                                  // 42
                                                                                                     // 43
  OAuth.launchLogin({                                                                                // 44
    loginService: "facebook",                                                                        // 45
    loginStyle: loginStyle,                                                                          // 46
    loginUrl: loginUrl,                                                                              // 47
    credentialRequestCompleteCallback: credentialRequestCompleteCallback,                            // 48
    credentialToken: credentialToken                                                                 // 49
  });                                                                                                // 50
};                                                                                                   // 51
                                                                                                     // 52
///////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
