(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                             //
// packages/twitter-oauth/twitter_common.js                                                    //
//                                                                                             //
/////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                               //
Twitter = {};                                                                                  // 1
                                                                                               // 2
Twitter.validParamsAuthenticate = [                                                            // 3
  'force_login',                                                                               // 4
  'screen_name'                                                                                // 5
];                                                                                             // 6
                                                                                               // 7
/////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                             //
// packages/twitter-oauth/twitter_server.js                                                    //
//                                                                                             //
/////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                               //
var urls = {                                                                                   // 1
  requestToken: "https://api.twitter.com/oauth/request_token",                                 // 2
  authorize: "https://api.twitter.com/oauth/authorize",                                        // 3
  accessToken: "https://api.twitter.com/oauth/access_token",                                   // 4
  authenticate: function (oauthBinding, params) {                                              // 5
    return OAuth._queryParamsWithAuthTokenUrl(                                                 // 6
      "https://api.twitter.com/oauth/authenticate",                                            // 7
      oauthBinding,                                                                            // 8
      params,                                                                                  // 9
      Twitter.validParamsAuthenticate                                                          // 10
    );                                                                                         // 11
  }                                                                                            // 12
};                                                                                             // 13
                                                                                               // 14
// https://dev.twitter.com/docs/api/1.1/get/account/verify_credentials                         // 15
Twitter.whitelistedFields = ['profile_image_url', 'profile_image_url_https', 'lang', 'email'];
                                                                                               // 17
OAuth.registerService('twitter', 1, urls, function(oauthBinding) {                             // 18
  var identity = oauthBinding.get('https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true').data;
                                                                                               // 20
  var serviceData = {                                                                          // 21
    id: identity.id_str,                                                                       // 22
    screenName: identity.screen_name,                                                          // 23
    accessToken: OAuth.sealSecret(oauthBinding.accessToken),                                   // 24
    accessTokenSecret: OAuth.sealSecret(oauthBinding.accessTokenSecret)                        // 25
  };                                                                                           // 26
                                                                                               // 27
  // include helpful fields from twitter                                                       // 28
  var fields = _.pick(identity, Twitter.whitelistedFields);                                    // 29
  _.extend(serviceData, fields);                                                               // 30
                                                                                               // 31
  return {                                                                                     // 32
    serviceData: serviceData,                                                                  // 33
    options: {                                                                                 // 34
      profile: {                                                                               // 35
        name: identity.name                                                                    // 36
      }                                                                                        // 37
    }                                                                                          // 38
  };                                                                                           // 39
});                                                                                            // 40
                                                                                               // 41
                                                                                               // 42
Twitter.retrieveCredential = function(credentialToken, credentialSecret) {                     // 43
  return OAuth.retrieveCredential(credentialToken, credentialSecret);                          // 44
};                                                                                             // 45
                                                                                               // 46
/////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
