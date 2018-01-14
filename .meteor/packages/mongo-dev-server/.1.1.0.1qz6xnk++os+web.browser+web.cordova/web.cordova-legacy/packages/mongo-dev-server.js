(function(){

////////////////////////////////////////////////////////////////////////
//                                                                    //
// packages/mongo-dev-server/server.js                                //
//                                                                    //
////////////////////////////////////////////////////////////////////////
                                                                      //
if (process.env.MONGO_URL === 'no-mongo-server') {                    // 1
  Meteor._debug('Note: Restart Meteor to start the MongoDB server.');
}                                                                     // 3
                                                                      // 4
////////////////////////////////////////////////////////////////////////

}).call(this);
