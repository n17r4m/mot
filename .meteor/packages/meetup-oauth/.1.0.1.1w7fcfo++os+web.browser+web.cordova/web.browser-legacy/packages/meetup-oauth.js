(function(){

//////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                  //
// packages/meetup-oauth/meetup_client.js                                                           //
//                                                                                                  //
//////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                    //
Meetup = {};                                                                                        // 1
// Request Meetup credentials for the user                                                          // 2
// @param options {optional}                                                                        // 3
// @param credentialRequestCompleteCallback {Function} Callback function to call on                 // 4
//   completion. Takes one argument, credentialToken on success, or Error on                        // 5
//   error.                                                                                         // 6
Meetup.requestCredential = function (options, credentialRequestCompleteCallback) {                  // 7
  // support both (options, callback) and (callback).                                               // 8
  if (!credentialRequestCompleteCallback && typeof options === 'function') {                        // 9
    credentialRequestCompleteCallback = options;                                                    // 10
    options = {};                                                                                   // 11
  }                                                                                                 // 12
                                                                                                    // 13
  var config = ServiceConfiguration.configurations.findOne({service: 'meetup'});                    // 14
  if (!config) {                                                                                    // 15
    credentialRequestCompleteCallback && credentialRequestCompleteCallback(                         // 16
      new ServiceConfiguration.ConfigError());                                                      // 17
    return;                                                                                         // 18
  }                                                                                                 // 19
                                                                                                    // 20
  // For some reason, meetup converts underscores to spaces in the state                            // 21
  // parameter when redirecting back to the client, so we use                                       // 22
  // `Random.id()` here (alphanumerics) instead of `Random.secret()`                                // 23
  // (base 64 characters).                                                                          // 24
  var credentialToken = Random.id();                                                                // 25
                                                                                                    // 26
  var scope = (options && options.requestPermissions) || [];                                        // 27
  var flatScope = _.map(scope, encodeURIComponent).join('+');                                       // 28
                                                                                                    // 29
  var loginStyle = OAuth._loginStyle('meetup', config, options);                                    // 30
                                                                                                    // 31
  var loginUrl =                                                                                    // 32
        'https://secure.meetup.com/oauth2/authorize' +                                              // 33
        '?client_id=' + config.clientId +                                                           // 34
        '&response_type=code' +                                                                     // 35
        '&scope=' + flatScope +                                                                     // 36
        '&redirect_uri=' + OAuth._redirectUri('meetup', config) +                                   // 37
        '&state=' + OAuth._stateParam(loginStyle, credentialToken, options && options.redirectUrl);
                                                                                                    // 39
  // meetup box gets taller when permissions requested.                                             // 40
  var height = 620;                                                                                 // 41
  if (_.without(scope, 'basic').length)                                                             // 42
    height += 130;                                                                                  // 43
                                                                                                    // 44
  OAuth.launchLogin({                                                                               // 45
    loginService: "meetup",                                                                         // 46
    loginStyle: loginStyle,                                                                         // 47
    loginUrl: loginUrl,                                                                             // 48
    credentialRequestCompleteCallback: credentialRequestCompleteCallback,                           // 49
    credentialToken: credentialToken,                                                               // 50
    popupOptions: {width: 900, height: height}                                                      // 51
  });                                                                                               // 52
};                                                                                                  // 53
                                                                                                    // 54
//////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
