(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                 //
// packages/meetup-oauth/meetup_server.js                                                          //
//                                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                   //
Meetup = {};                                                                                       // 1
                                                                                                   // 2
OAuth.registerService('meetup', 2, null, function(query) {                                         // 3
                                                                                                   // 4
  var response = getAccessToken(query);                                                            // 5
  var accessToken = response.access_token;                                                         // 6
  var expiresAt = (+new Date) + (1000 * response.expires_in);                                      // 7
  var identity = getIdentity(accessToken);                                                         // 8
                                                                                                   // 9
  return {                                                                                         // 10
    serviceData: {                                                                                 // 11
      id: identity.id,                                                                             // 12
      accessToken: accessToken,                                                                    // 13
      expiresAt: expiresAt                                                                         // 14
    },                                                                                             // 15
    options: {profile: {name: identity.name}}                                                      // 16
  };                                                                                               // 17
});                                                                                                // 18
                                                                                                   // 19
var getAccessToken = function (query) {                                                            // 20
  var config = ServiceConfiguration.configurations.findOne({service: 'meetup'});                   // 21
  if (!config)                                                                                     // 22
    throw new ServiceConfiguration.ConfigError();                                                  // 23
                                                                                                   // 24
  var response;                                                                                    // 25
  try {                                                                                            // 26
    response = HTTP.post(                                                                          // 27
      "https://secure.meetup.com/oauth2/access", {headers: {Accept: 'application/json'}, params: {
        code: query.code,                                                                          // 29
        client_id: config.clientId,                                                                // 30
        client_secret: OAuth.openSecret(config.secret),                                            // 31
        grant_type: 'authorization_code',                                                          // 32
        redirect_uri: OAuth._redirectUri('meetup', config),                                        // 33
        state: query.state                                                                         // 34
      }});                                                                                         // 35
  } catch (err) {                                                                                  // 36
    throw _.extend(new Error("Failed to complete OAuth handshake with Meetup. " + err.message),    // 37
                   {response: err.response});                                                      // 38
  }                                                                                                // 39
                                                                                                   // 40
  if (response.data.error) { // if the http response was a json object with an error attribute     // 41
    throw new Error("Failed to complete OAuth handshake with Meetup. " + response.data.error);     // 42
  } else {                                                                                         // 43
    return response.data;                                                                          // 44
  }                                                                                                // 45
};                                                                                                 // 46
                                                                                                   // 47
var getIdentity = function (accessToken) {                                                         // 48
  try {                                                                                            // 49
    var response = HTTP.get(                                                                       // 50
      "https://api.meetup.com/2/members",                                                          // 51
      {params: {member_id: 'self', access_token: accessToken}});                                   // 52
    return response.data.results && response.data.results[0];                                      // 53
  } catch (err) {                                                                                  // 54
    throw _.extend(new Error("Failed to fetch identity from Meetup. " + err.message),              // 55
                   {response: err.response});                                                      // 56
  }                                                                                                // 57
};                                                                                                 // 58
                                                                                                   // 59
                                                                                                   // 60
Meetup.retrieveCredential = function(credentialToken, credentialSecret) {                          // 61
  return OAuth.retrieveCredential(credentialToken, credentialSecret);                              // 62
};                                                                                                 // 63
                                                                                                   // 64
/////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
