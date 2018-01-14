(function(){

//////////////////////////////////////////////////////////////////////////////////
//                                                                              //
// packages/rate-limit/rate-limit.js                                            //
//                                                                              //
//////////////////////////////////////////////////////////////////////////////////
                                                                                //
// Default time interval (in milliseconds) to reset rate limit counters         // 1
var DEFAULT_INTERVAL_TIME_IN_MILLISECONDS = 1000;                               // 2
// Default number of events allowed per time interval                           // 3
var DEFAULT_REQUESTS_PER_INTERVAL = 10;                                         // 4
                                                                                // 5
// A rule is defined by an options object that contains two fields,             // 6
// `numRequestsAllowed` which is the number of events allowed per interval, and
// an `intervalTime` which is the amount of time in milliseconds before the     // 8
// rate limit restarts its internal counters, and by a matchers object. A       // 9
// matchers object is a POJO that contains a set of keys with values that       // 10
// define the entire set of inputs that match for each key. The values can      // 11
// either be null (optional), a primitive or a function that returns a boolean  // 12
// of whether the provided input's value matches for this key.                  // 13
//                                                                              // 14
// Rules are uniquely assigned an `id` and they store a dictionary of counters,
// which are records used to keep track of inputs that match the rule. If a     // 16
// counter reaches the `numRequestsAllowed` within a given `intervalTime`, a    // 17
// rate limit is reached and future inputs that map to that counter will        // 18
// result in errors being returned to the client.                               // 19
var Rule = function (options, matchers) {                                       // 20
  var self = this;                                                              // 21
                                                                                // 22
  self.id = Random.id();                                                        // 23
                                                                                // 24
  self.options = options;                                                       // 25
                                                                                // 26
  self._matchers = matchers;                                                    // 27
                                                                                // 28
  self._lastResetTime = new Date().getTime();                                   // 29
                                                                                // 30
  // Dictionary of input keys to counters                                       // 31
  self.counters = {};                                                           // 32
};                                                                              // 33
                                                                                // 34
_.extend(Rule.prototype, {                                                      // 35
  // Determine if this rule applies to the given input by comparing all         // 36
  // rule.matchers. If the match fails, search short circuits instead of        // 37
  // iterating through all matchers.                                            // 38
  match: function (input) {                                                     // 39
    var self = this;                                                            // 40
    var ruleMatches = true;                                                     // 41
    return _.every(self._matchers, function (matcher, key) {                    // 42
      if (matcher !== null) {                                                   // 43
        if (!(_.has(input,key))) {                                              // 44
          return false;                                                         // 45
        } else {                                                                // 46
          if (typeof matcher === 'function') {                                  // 47
            if (!(matcher(input[key]))) {                                       // 48
              return false;                                                     // 49
            }                                                                   // 50
          } else {                                                              // 51
            if (matcher !== input[key]) {                                       // 52
              return false;                                                     // 53
            }                                                                   // 54
          }                                                                     // 55
        }                                                                       // 56
      }                                                                         // 57
      return true;                                                              // 58
    });                                                                         // 59
  },                                                                            // 60
                                                                                // 61
  // Generates unique key string for provided input by concatenating all the    // 62
  // keys in the matcher with the corresponding values in the input.            // 63
  // Only called if rule matches input.                                         // 64
  _generateKeyString: function (input) {                                        // 65
    var self = this;                                                            // 66
    var returnString = "";                                                      // 67
    _.each(self._matchers, function (matcher, key) {                            // 68
      if (matcher !== null) {                                                   // 69
        if (typeof matcher === 'function') {                                    // 70
          if (matcher(input[key])) {                                            // 71
            returnString += key + input[key];                                   // 72
          }                                                                     // 73
        } else {                                                                // 74
          returnString += key + input[key];                                     // 75
        }                                                                       // 76
      }                                                                         // 77
    });                                                                         // 78
    return returnString;                                                        // 79
  },                                                                            // 80
                                                                                // 81
  // Applies the provided input and returns the key string, time since counters
  // were last reset and time to next reset.                                    // 83
  apply: function (input) {                                                     // 84
    var self = this;                                                            // 85
    var keyString = self._generateKeyString(input);                             // 86
    var timeSinceLastReset = new Date().getTime() - self._lastResetTime;        // 87
    var timeToNextReset = self.options.intervalTime - timeSinceLastReset;       // 88
    return {                                                                    // 89
      key: keyString,                                                           // 90
      timeSinceLastReset: timeSinceLastReset,                                   // 91
      timeToNextReset: timeToNextReset                                          // 92
    };                                                                          // 93
  },                                                                            // 94
  // Reset counter dictionary for this specific rule. Called once the           // 95
  // timeSinceLastReset has exceeded the intervalTime. _lastResetTime is        // 96
  // set to be the current time in milliseconds.                                // 97
  resetCounter: function () {                                                   // 98
    var self = this;                                                            // 99
                                                                                // 100
    // Delete the old counters dictionary to allow for garbage collection       // 101
    self.counters = {};                                                         // 102
    self._lastResetTime = new Date().getTime();                                 // 103
  },                                                                            // 104
  _executeCallback: function (reply, ruleInput) {                               // 105
    try {                                                                       // 106
      if (this.options.callback) {                                              // 107
        this.options.callback(reply, ruleInput);                                // 108
      }                                                                         // 109
    } catch (e) {                                                               // 110
      // Do not throw error here                                                // 111
      console.error(e);                                                         // 112
    }                                                                           // 113
  },                                                                            // 114
});                                                                             // 115
                                                                                // 116
// Initialize rules to be an empty dictionary.                                  // 117
RateLimiter = function () {                                                     // 118
  var self = this;                                                              // 119
                                                                                // 120
  // Dictionary of all rules associated with this RateLimiter, keyed by their   // 121
  // id. Each rule object stores the rule pattern, number of events allowed,    // 122
  // last reset time and the rule reset interval in milliseconds.               // 123
  self.rules = {};                                                              // 124
};                                                                              // 125
                                                                                // 126
/**                                                                             // 127
 * Checks if this input has exceeded any rate limits.                           // 128
 * @param  {object} input dictionary containing key-value pairs of attributes   // 129
 * that match to rules                                                          // 130
 * @return {object} Returns object of following structure                       // 131
 * { 'allowed': boolean - is this input allowed                                 // 132
 *   'timeToReset': integer | Infinity - returns time until counters are reset  // 133
 *                   in milliseconds                                            // 134
 *   'numInvocationsLeft': integer | Infinity - returns number of calls left    // 135
 *   before limit is reached                                                    // 136
 * }                                                                            // 137
 * If multiple rules match, the least number of invocations left is returned.   // 138
 * If the rate limit has been reached, the longest timeToReset is returned.     // 139
 */                                                                             // 140
RateLimiter.prototype.check = function (input) {                                // 141
  var self = this;                                                              // 142
  var reply = {                                                                 // 143
    allowed: true,                                                              // 144
    timeToReset: 0,                                                             // 145
    numInvocationsLeft: Infinity,                                               // 146
  };                                                                            // 147
                                                                                // 148
  var matchedRules = self._findAllMatchingRules(input);                         // 149
  _.each(matchedRules, function (rule) {                                        // 150
    var ruleResult = rule.apply(input);                                         // 151
    var numInvocations = rule.counters[ruleResult.key];                         // 152
                                                                                // 153
    if (ruleResult.timeToNextReset < 0) {                                       // 154
      // Reset all the counters since the rule has reset                        // 155
      rule.resetCounter();                                                      // 156
      ruleResult.timeSinceLastReset = new Date().getTime() -                    // 157
        rule._lastResetTime;                                                    // 158
      ruleResult.timeToNextReset = rule.options.intervalTime;                   // 159
      numInvocations = 0;                                                       // 160
    }                                                                           // 161
                                                                                // 162
    if (numInvocations > rule.options.numRequestsAllowed) {                     // 163
      // Only update timeToReset if the new time would be longer than the       // 164
      // previously set time. This is to ensure that if this input triggers     // 165
      // multiple rules, we return the longest period of time until they can    // 166
      // successfully make another call                                         // 167
      if (reply.timeToReset < ruleResult.timeToNextReset) {                     // 168
        reply.timeToReset = ruleResult.timeToNextReset;                         // 169
      };                                                                        // 170
      reply.allowed = false;                                                    // 171
      reply.numInvocationsLeft = 0;                                             // 172
      rule._executeCallback(reply, input);                                      // 173
    } else {                                                                    // 174
      // If this is an allowed attempt and we haven't failed on any of the      // 175
      // other rules that match, update the reply field.                        // 176
      if (rule.options.numRequestsAllowed - numInvocations <                    // 177
        reply.numInvocationsLeft && reply.allowed) {                            // 178
        reply.timeToReset = ruleResult.timeToNextReset;                         // 179
        reply.numInvocationsLeft = rule.options.numRequestsAllowed -            // 180
          numInvocations;                                                       // 181
      }                                                                         // 182
      rule._executeCallback(reply, input);                                      // 183
    }                                                                           // 184
  });                                                                           // 185
  return reply;                                                                 // 186
};                                                                              // 187
                                                                                // 188
/**                                                                             // 189
 * Adds a rule to dictionary of rules that are checked against on every call.   // 190
 * Only inputs that pass all of the rules will be allowed. Returns unique rule  // 191
 * id that can be passed to `removeRule`.                                       // 192
 * @param {object} rule    Input dictionary defining certain attributes and     // 193
 * rules associated with them.                                                  // 194
 * Each attribute's value can either be a value, a function or null. All        // 195
 * functions must return a boolean of whether the input is matched by that      // 196
 * attribute's rule or not                                                      // 197
 * @param {integer} numRequestsAllowed Optional. Number of events allowed per   // 198
 * interval. Default = 10.                                                      // 199
 * @param {integer} intervalTime Optional. Number of milliseconds before        // 200
 * rule's counters are reset. Default = 1000.                                   // 201
 * @param {function} callback Optional. Function to be called after a           // 202
 * rule is executed. Two objects will be passed to this function.               // 203
 * The first one is the result of RateLimiter.prototype.check                   // 204
 * The second is the input object of the rule, it has the following structure:  // 205
 * {                                                                            // 206
 *   'type': string - either 'method' or 'subscription'                         // 207
 *   'name': string - the name of the method or subscription being called       // 208
 *   'userId': string - the user ID attempting the method or subscription       // 209
 *   'connectionId': string - a string representing the user's DDP connection   // 210
 *   'clientAddress': string - the IP address of the user                       // 211
 * }                                                                            // 212
 * @return {string} Returns unique rule id                                      // 213
 */                                                                             // 214
RateLimiter.prototype.addRule = function (rule, numRequestsAllowed,             // 215
  intervalTime, callback) {                                                     // 216
  var self = this;                                                              // 217
                                                                                // 218
  var options = {                                                               // 219
    numRequestsAllowed: numRequestsAllowed || DEFAULT_REQUESTS_PER_INTERVAL,    // 220
    intervalTime: intervalTime || DEFAULT_INTERVAL_TIME_IN_MILLISECONDS,        // 221
    callback: callback && Meteor.bindEnvironment(callback),                     // 222
  };                                                                            // 223
                                                                                // 224
  var newRule = new Rule(options, rule);                                        // 225
  this.rules[newRule.id] = newRule;                                             // 226
  return newRule.id;                                                            // 227
};                                                                              // 228
                                                                                // 229
/**                                                                             // 230
 * Increment counters in every rule that match to this input                    // 231
 * @param  {object} input Dictionary object containing attributes that may      // 232
 * match to rules                                                               // 233
 */                                                                             // 234
RateLimiter.prototype.increment = function (input) {                            // 235
  var self = this;                                                              // 236
                                                                                // 237
  // Only increment rule counters that match this input                         // 238
  var matchedRules = self._findAllMatchingRules(input);                         // 239
  _.each(matchedRules, function (rule) {                                        // 240
    var ruleResult = rule.apply(input);                                         // 241
                                                                                // 242
    if (ruleResult.timeSinceLastReset > rule.options.intervalTime) {            // 243
      // Reset all the counters since the rule has reset                        // 244
      rule.resetCounter();                                                      // 245
    }                                                                           // 246
                                                                                // 247
    // Check whether the key exists, incrementing it if so or otherwise         // 248
    // adding the key and setting its value to 1                                // 249
    if (_.has(rule.counters, ruleResult.key))                                   // 250
      rule.counters[ruleResult.key]++;                                          // 251
    else                                                                        // 252
      rule.counters[ruleResult.key] = 1;                                        // 253
  });                                                                           // 254
};                                                                              // 255
                                                                                // 256
// Returns an array of all rules that apply to provided input                   // 257
RateLimiter.prototype._findAllMatchingRules = function (input) {                // 258
  var self = this;                                                              // 259
                                                                                // 260
  return _.filter(self.rules, function(rule) {                                  // 261
    return rule.match(input);                                                   // 262
  });                                                                           // 263
};                                                                              // 264
/**                                                                             // 265
 * Provides a mechanism to remove rules from the rate limiter. Returns boolean  // 266
 * about success.                                                               // 267
 * @param  {string} id Rule id returned from #addRule                           // 268
 * @return {boolean} Returns true if rule was found and deleted, else false.    // 269
 */                                                                             // 270
RateLimiter.prototype.removeRule = function (id) {                              // 271
  var self = this;                                                              // 272
  if (self.rules[id]) {                                                         // 273
    delete self.rules[id];                                                      // 274
    return true;                                                                // 275
  } else {                                                                      // 276
    return false;                                                               // 277
  }                                                                             // 278
};                                                                              // 279
                                                                                // 280
//////////////////////////////////////////////////////////////////////////////////

}).call(this);
