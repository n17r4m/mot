(function(){

///////////////////////////////////////////////////////////////////////
//                                                                   //
// packages/oauth2/oauth2_server.js                                  //
//                                                                   //
///////////////////////////////////////////////////////////////////////
                                                                     //
// connect middleware                                                // 1
OAuth._requestHandlers['2'] = function (service, query, res) {       // 2
  // check if user authorized access                                 // 3
  if (!query.error) {                                                // 4
    // Prepare the login results before returning.                   // 5
                                                                     // 6
    // Run service-specific handler.                                 // 7
    var oauthResult = service.handleOauthRequest(query);             // 8
    var credentialSecret = Random.secret();                          // 9
                                                                     // 10
    var credentialToken = OAuth._credentialTokenFromQuery(query);    // 11
                                                                     // 12
    // Store the login result so it can be retrieved in another      // 13
    // browser tab by the result handler                             // 14
    OAuth._storePendingCredential(credentialToken, {                 // 15
      serviceName: service.serviceName,                              // 16
      serviceData: oauthResult.serviceData,                          // 17
      options: oauthResult.options                                   // 18
    }, credentialSecret);                                            // 19
  }                                                                  // 20
                                                                     // 21
  // Either close the window, redirect, or render nothing            // 22
  // if all else fails                                               // 23
  OAuth._renderOauthResults(res, query, credentialSecret);           // 24
};                                                                   // 25
                                                                     // 26
///////////////////////////////////////////////////////////////////////

}).call(this);
