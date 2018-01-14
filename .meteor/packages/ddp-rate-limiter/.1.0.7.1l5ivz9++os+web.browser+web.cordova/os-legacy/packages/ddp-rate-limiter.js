(function(){

/////////////////////////////////////////////////////////////////////////////////////
//                                                                                 //
// packages/ddp-rate-limiter/ddp-rate-limiter.js                                   //
//                                                                                 //
/////////////////////////////////////////////////////////////////////////////////////
                                                                                   //
// Rate Limiter built into DDP with a default error message. See README or         // 1
// online documentation for more details.                                          // 2
DDPRateLimiter = {};                                                               // 3
                                                                                   // 4
var errorMessage = function (rateLimitResult) {                                    // 5
  return "Error, too many requests. Please slow down. You must wait " +            // 6
    Math.ceil(rateLimitResult.timeToReset / 1000) + " seconds before " +           // 7
    "trying again.";                                                               // 8
};                                                                                 // 9
var rateLimiter = new RateLimiter();                                               // 10
                                                                                   // 11
DDPRateLimiter.getErrorMessage = function (rateLimitResult) {                      // 12
  if (typeof errorMessage === 'function')                                          // 13
    return errorMessage(rateLimitResult);                                          // 14
  else                                                                             // 15
    return errorMessage;                                                           // 16
};                                                                                 // 17
                                                                                   // 18
/**                                                                                // 19
 * @summary Set error message text when method or subscription rate limit          // 20
 * exceeded.                                                                       // 21
 * @param {string|function} message Functions are passed in an object with a       // 22
 * `timeToReset` field that specifies the number of milliseconds until the next    // 23
 * method or subscription is allowed to run. The function must return a string     // 24
 * of the error message.                                                           // 25
 * @locus Server                                                                   // 26
 */                                                                                // 27
DDPRateLimiter.setErrorMessage = function (message) {                              // 28
  errorMessage = message;                                                          // 29
};                                                                                 // 30
                                                                                   // 31
/**                                                                                // 32
 * @summary                                                                        // 33
 * Add a rule that matches against a stream of events describing method or         // 34
 * subscription attempts. Each event is an object with the following               // 35
 * properties:                                                                     // 36
 *                                                                                 // 37
 * - `type`: Either "method" or "subscription"                                     // 38
 * - `name`: The name of the method or subscription being called                   // 39
 * - `userId`: The user ID attempting the method or subscription                   // 40
 * - `connectionId`: A string representing the user's DDP connection               // 41
 * - `clientAddress`: The IP address of the user                                   // 42
 *                                                                                 // 43
 * Returns unique `ruleId` that can be passed to `removeRule`.                     // 44
 *                                                                                 // 45
 * @param {Object} matcher                                                         // 46
 *   Matchers specify which events are counted towards a rate limit. A matcher     // 47
 *   is an object that has a subset of the same properties as the event objects    // 48
 *   described above. Each value in a matcher object is one of the following:      // 49
 *                                                                                 // 50
 *   - a string: for the event to satisfy the matcher, this value must be equal    // 51
 *   to the value of the same property in the event object                         // 52
 *                                                                                 // 53
 *   - a function: for the event to satisfy the matcher, the function must         // 54
 *   evaluate to true when passed the value of the same property                   // 55
 *   in the event object                                                           // 56
 *                                                                                 // 57
 * Here's how events are counted: Each event that satisfies the matcher's          // 58
 * filter is mapped to a bucket. Buckets are uniquely determined by the            // 59
 * event object's values for all properties present in both the matcher and        // 60
 * event objects.                                                                  // 61
 *                                                                                 // 62
 * @param {number} numRequests  number of requests allowed per time interval.      // 63
 * Default = 10.                                                                   // 64
 * @param {number} timeInterval time interval in milliseconds after which          // 65
 * rule's counters are reset. Default = 1000.                                      // 66
 * @param {function} callback function to be called after a rule is executed.      // 67
 * @locus Server                                                                   // 68
 */                                                                                // 69
DDPRateLimiter.addRule = function (matcher, numRequests, timeInterval, callback) {
  return rateLimiter.addRule(matcher, numRequests, timeInterval, callback);        // 71
};                                                                                 // 72
                                                                                   // 73
DDPRateLimiter.printRules = function () {                                          // 74
  return rateLimiter.rules;                                                        // 75
};                                                                                 // 76
                                                                                   // 77
/**                                                                                // 78
 * @summary Removes the specified rule from the rate limiter. If rule had          // 79
 * hit a rate limit, that limit is removed as well.                                // 80
 * @param  {string} id 'ruleId' returned from `addRule`                            // 81
 * @return {boolean}    True if a rule was removed.                                // 82
 * @locus Server                                                                   // 83
 */                                                                                // 84
DDPRateLimiter.removeRule = function (id) {                                        // 85
  return rateLimiter.removeRule(id);                                               // 86
};                                                                                 // 87
                                                                                   // 88
// This is accessed inside livedata_server.js, but shouldn't be called by any      // 89
// user.                                                                           // 90
DDPRateLimiter._increment = function (input) {                                     // 91
  rateLimiter.increment(input);                                                    // 92
};                                                                                 // 93
                                                                                   // 94
DDPRateLimiter._check = function (input) {                                         // 95
  return rateLimiter.check(input);                                                 // 96
};                                                                                 // 97
                                                                                   // 98
/////////////////////////////////////////////////////////////////////////////////////

}).call(this);
