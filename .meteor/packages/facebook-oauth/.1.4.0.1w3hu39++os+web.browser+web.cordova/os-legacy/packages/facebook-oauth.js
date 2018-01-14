(function(){

///////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                           //
// packages/facebook-oauth/facebook_server.js                                                                //
//                                                                                                           //
///////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                             //
Facebook = {};                                                                                               // 1
var crypto = Npm.require('crypto');                                                                          // 2
                                                                                                             // 3
Facebook.handleAuthFromAccessToken = function handleAuthFromAccessToken(accessToken, expiresAt) {            // 4
  // include all fields from facebook                                                                        // 5
  // http://developers.facebook.com/docs/reference/login/public-profile-and-friend-list/                     // 6
  var whitelisted = ['id', 'email', 'name', 'first_name',                                                    // 7
      'last_name', 'link', 'gender', 'locale', 'age_range'];                                                 // 8
                                                                                                             // 9
  var identity = getIdentity(accessToken, whitelisted);                                                      // 10
                                                                                                             // 11
  var serviceData = {                                                                                        // 12
    accessToken: accessToken,                                                                                // 13
    expiresAt: expiresAt                                                                                     // 14
  };                                                                                                         // 15
                                                                                                             // 16
  var fields = _.pick(identity, whitelisted);                                                                // 17
  _.extend(serviceData, fields);                                                                             // 18
                                                                                                             // 19
  return {                                                                                                   // 20
    serviceData: serviceData,                                                                                // 21
    options: {profile: {name: identity.name}}                                                                // 22
  };                                                                                                         // 23
};                                                                                                           // 24
                                                                                                             // 25
OAuth.registerService('facebook', 2, null, function(query) {                                                 // 26
  var response = getTokenResponse(query);                                                                    // 27
  var accessToken = response.accessToken;                                                                    // 28
  var expiresIn = response.expiresIn;                                                                        // 29
                                                                                                             // 30
  return Facebook.handleAuthFromAccessToken(accessToken, (+new Date) + (1000 * expiresIn));                  // 31
});                                                                                                          // 32
                                                                                                             // 33
// checks whether a string parses as JSON                                                                    // 34
var isJSON = function (str) {                                                                                // 35
  try {                                                                                                      // 36
    JSON.parse(str);                                                                                         // 37
    return true;                                                                                             // 38
  } catch (e) {                                                                                              // 39
    return false;                                                                                            // 40
  }                                                                                                          // 41
};                                                                                                           // 42
                                                                                                             // 43
// returns an object containing:                                                                             // 44
// - accessToken                                                                                             // 45
// - expiresIn: lifetime of token in seconds                                                                 // 46
var getTokenResponse = function (query) {                                                                    // 47
  var config = ServiceConfiguration.configurations.findOne({service: 'facebook'});                           // 48
  if (!config)                                                                                               // 49
    throw new ServiceConfiguration.ConfigError();                                                            // 50
                                                                                                             // 51
  var responseContent;                                                                                       // 52
  try {                                                                                                      // 53
    // Request an access token                                                                               // 54
    responseContent = HTTP.get(                                                                              // 55
      "https://graph.facebook.com/v2.8/oauth/access_token", {                                                // 56
        params: {                                                                                            // 57
          client_id: config.appId,                                                                           // 58
          redirect_uri: OAuth._redirectUri('facebook', config),                                              // 59
          client_secret: OAuth.openSecret(config.secret),                                                    // 60
          code: query.code                                                                                   // 61
        }                                                                                                    // 62
      }).data;                                                                                               // 63
  } catch (err) {                                                                                            // 64
    throw _.extend(new Error("Failed to complete OAuth handshake with Facebook. " + err.message),            // 65
                   {response: err.response});                                                                // 66
  }                                                                                                          // 67
                                                                                                             // 68
  var fbAccessToken = responseContent.access_token;                                                          // 69
  var fbExpires = responseContent.expires_in;                                                                // 70
                                                                                                             // 71
  if (!fbAccessToken) {                                                                                      // 72
    throw new Error("Failed to complete OAuth handshake with facebook " +                                    // 73
                    "-- can't find access token in HTTP response. " + responseContent);                      // 74
  }                                                                                                          // 75
  return {                                                                                                   // 76
    accessToken: fbAccessToken,                                                                              // 77
    expiresIn: fbExpires                                                                                     // 78
  };                                                                                                         // 79
};                                                                                                           // 80
                                                                                                             // 81
var getIdentity = function (accessToken, fields) {                                                           // 82
  var config = ServiceConfiguration.configurations.findOne({service: 'facebook'});                           // 83
  if (!config)                                                                                               // 84
    throw new ServiceConfiguration.ConfigError();                                                            // 85
                                                                                                             // 86
  // Generate app secret proof that is a sha256 hash of the app access token, with the app secret as the key
  // https://developers.facebook.com/docs/graph-api/securing-requests#appsecret_proof                        // 88
  var hmac = crypto.createHmac('sha256', OAuth.openSecret(config.secret));                                   // 89
  hmac.update(accessToken);                                                                                  // 90
                                                                                                             // 91
  try {                                                                                                      // 92
    return HTTP.get("https://graph.facebook.com/v2.8/me", {                                                  // 93
      params: {                                                                                              // 94
        access_token: accessToken,                                                                           // 95
        appsecret_proof: hmac.digest('hex'),                                                                 // 96
        fields: fields.join(",")                                                                             // 97
      }                                                                                                      // 98
    }).data;                                                                                                 // 99
  } catch (err) {                                                                                            // 100
    throw _.extend(new Error("Failed to fetch identity from Facebook. " + err.message),                      // 101
                   {response: err.response});                                                                // 102
  }                                                                                                          // 103
};                                                                                                           // 104
                                                                                                             // 105
Facebook.retrieveCredential = function(credentialToken, credentialSecret) {                                  // 106
  return OAuth.retrieveCredential(credentialToken, credentialSecret);                                        // 107
};                                                                                                           // 108
                                                                                                             // 109
///////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
