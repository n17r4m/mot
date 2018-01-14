(function(){

////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                    //
// packages/twitter-oauth/twitter_common.js                                                           //
//                                                                                                    //
////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                      //
Twitter = {};                                                                                         // 1
                                                                                                      // 2
Twitter.validParamsAuthenticate = [                                                                   // 3
  'force_login',                                                                                      // 4
  'screen_name'                                                                                       // 5
];                                                                                                    // 6
                                                                                                      // 7
////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                    //
// packages/twitter-oauth/twitter_client.js                                                           //
//                                                                                                    //
////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                      //
// Request Twitter credentials for the user                                                           // 1
// @param options {optional}  XXX support options.requestPermissions                                  // 2
// @param credentialRequestCompleteCallback {Function} Callback function to call on                   // 3
//   completion. Takes one argument, credentialToken on success, or Error on                          // 4
//   error.                                                                                           // 5
Twitter.requestCredential = function (options, credentialRequestCompleteCallback) {                   // 6
  // support both (options, callback) and (callback).                                                 // 7
  if (!credentialRequestCompleteCallback && typeof options === 'function') {                          // 8
    credentialRequestCompleteCallback = options;                                                      // 9
    options = {};                                                                                     // 10
  }                                                                                                   // 11
                                                                                                      // 12
  var config = ServiceConfiguration.configurations.findOne({service: 'twitter'});                     // 13
  if (!config) {                                                                                      // 14
    credentialRequestCompleteCallback && credentialRequestCompleteCallback(                           // 15
      new ServiceConfiguration.ConfigError());                                                        // 16
    return;                                                                                           // 17
  }                                                                                                   // 18
                                                                                                      // 19
  var credentialToken = Random.secret();                                                              // 20
  // We need to keep credentialToken across the next two 'steps' so we're adding                      // 21
  // a credentialToken parameter to the url and the callback url that we'll be returned               // 22
  // to by oauth provider                                                                             // 23
                                                                                                      // 24
  var loginStyle = OAuth._loginStyle('twitter', config, options);                                     // 25
                                                                                                      // 26
  // url to app, enters "step 1" as described in                                                      // 27
  // packages/accounts-oauth1-helper/oauth1_server.js                                                 // 28
  var loginPath = '_oauth/twitter/?requestTokenAndRedirect=true'                                      // 29
        + '&state=' + OAuth._stateParam(loginStyle, credentialToken, options && options.redirectUrl);
                                                                                                      // 31
  if (Meteor.isCordova) {                                                                             // 32
    loginPath = loginPath + "&cordova=true";                                                          // 33
    if (/Android/i.test(navigator.userAgent)) {                                                       // 34
      loginPath = loginPath + "&android=true";                                                        // 35
    }                                                                                                 // 36
  }                                                                                                   // 37
                                                                                                      // 38
  // Support additional, permitted parameters                                                         // 39
  if (options) {                                                                                      // 40
    var hasOwn = Object.prototype.hasOwnProperty;                                                     // 41
    Twitter.validParamsAuthenticate.forEach(function (param) {                                        // 42
      if (hasOwn.call(options, param)) {                                                              // 43
        loginPath += "&" + param + "=" + encodeURIComponent(options[param]);                          // 44
      }                                                                                               // 45
    });                                                                                               // 46
  }                                                                                                   // 47
                                                                                                      // 48
  var loginUrl = Meteor.absoluteUrl(loginPath);                                                       // 49
                                                                                                      // 50
  OAuth.launchLogin({                                                                                 // 51
    loginService: "twitter",                                                                          // 52
    loginStyle: loginStyle,                                                                           // 53
    loginUrl: loginUrl,                                                                               // 54
    credentialRequestCompleteCallback: credentialRequestCompleteCallback,                             // 55
    credentialToken: credentialToken                                                                  // 56
  });                                                                                                 // 57
};                                                                                                    // 58
                                                                                                      // 59
////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
