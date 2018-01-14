(function(){

////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                            //
// packages/email/email.js                                                                                    //
//                                                                                                            //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                              //
var Future = Npm.require('fibers/future');                                                                    // 1
var urlModule = Npm.require('url');                                                                           // 2
var nodemailer = Npm.require('node4mailer');                                                                  // 3
                                                                                                              // 4
Email = {};                                                                                                   // 5
EmailTest = {};                                                                                               // 6
                                                                                                              // 7
EmailInternals = {                                                                                            // 8
  NpmModules: {                                                                                               // 9
    mailcomposer: {                                                                                           // 10
      version: Npm.require('node4mailer/package.json').version,                                               // 11
      module: Npm.require('node4mailer/lib/mail-composer')                                                    // 12
    },                                                                                                        // 13
    nodemailer: {                                                                                             // 14
      version: Npm.require('node4mailer/package.json').version,                                               // 15
      module: Npm.require('node4mailer')                                                                      // 16
    }                                                                                                         // 17
  }                                                                                                           // 18
};                                                                                                            // 19
                                                                                                              // 20
var MailComposer = EmailInternals.NpmModules.mailcomposer.module;                                             // 21
                                                                                                              // 22
var makeTransport = function (mailUrlString) {                                                                // 23
  var mailUrl = urlModule.parse(mailUrlString, true);                                                         // 24
                                                                                                              // 25
  if (mailUrl.protocol !== 'smtp:' && mailUrl.protocol !== 'smtps:') {                                        // 26
    throw new Error("Email protocol in $MAIL_URL (" +                                                         // 27
                    mailUrlString + ") must be 'smtp' or 'smtps'");                                           // 28
  }                                                                                                           // 29
                                                                                                              // 30
  if (mailUrl.protocol === 'smtp:' && mailUrl.port === '465') {                                               // 31
    Meteor._debug("The $MAIL_URL is 'smtp://...:465'.  " +                                                    // 32
                  "You probably want 'smtps://' (The 's' enables TLS/SSL) " +                                 // 33
                  "since '465' is typically a secure port.");                                                 // 34
  }                                                                                                           // 35
                                                                                                              // 36
  // Allow overriding pool setting, but default to true.                                                      // 37
  if (!mailUrl.query) {                                                                                       // 38
    mailUrl.query = {};                                                                                       // 39
  }                                                                                                           // 40
                                                                                                              // 41
  if (!mailUrl.query.pool) {                                                                                  // 42
    mailUrl.query.pool = 'true';                                                                              // 43
  }                                                                                                           // 44
                                                                                                              // 45
  var transport = nodemailer.createTransport(                                                                 // 46
    urlModule.format(mailUrl));                                                                               // 47
                                                                                                              // 48
  transport._syncSendMail = Meteor.wrapAsync(transport.sendMail, transport);                                  // 49
  return transport;                                                                                           // 50
};                                                                                                            // 51
                                                                                                              // 52
var getTransport = function() {                                                                               // 53
  // We delay this check until the first call to Email.send, in case someone                                  // 54
  // set process.env.MAIL_URL in startup code. Then we store in a cache until                                 // 55
  // process.env.MAIL_URL changes.                                                                            // 56
  var url = process.env.MAIL_URL;                                                                             // 57
  if (this.cacheKey === undefined || this.cacheKey !== url) {                                                 // 58
    this.cacheKey = url;                                                                                      // 59
    this.cache = url ? makeTransport(url) : null;                                                             // 60
  }                                                                                                           // 61
  return this.cache;                                                                                          // 62
}                                                                                                             // 63
                                                                                                              // 64
var nextDevModeMailId = 0;                                                                                    // 65
var output_stream = process.stdout;                                                                           // 66
                                                                                                              // 67
// Testing hooks                                                                                              // 68
EmailTest.overrideOutputStream = function (stream) {                                                          // 69
  nextDevModeMailId = 0;                                                                                      // 70
  output_stream = stream;                                                                                     // 71
};                                                                                                            // 72
                                                                                                              // 73
EmailTest.restoreOutputStream = function () {                                                                 // 74
  output_stream = process.stdout;                                                                             // 75
};                                                                                                            // 76
                                                                                                              // 77
var devModeSend = function (mail) {                                                                           // 78
  var devModeMailId = nextDevModeMailId++;                                                                    // 79
                                                                                                              // 80
  var stream = output_stream;                                                                                 // 81
                                                                                                              // 82
  // This approach does not prevent other writers to stdout from interleaving.                                // 83
  stream.write("====== BEGIN MAIL #" + devModeMailId + " ======\n");                                          // 84
  stream.write("(Mail not sent; to enable sending, set the MAIL_URL " +                                       // 85
               "environment variable.)\n");                                                                   // 86
  var readStream = new MailComposer(mail).compile().createReadStream();                                       // 87
  readStream.pipe(stream, {end: false});                                                                      // 88
  var future = new Future;                                                                                    // 89
  readStream.on('end', function () {                                                                          // 90
    stream.write("====== END MAIL #" + devModeMailId + " ======\n");                                          // 91
    future.return();                                                                                          // 92
  });                                                                                                         // 93
  future.wait();                                                                                              // 94
};                                                                                                            // 95
                                                                                                              // 96
var smtpSend = function (transport, mail) {                                                                   // 97
  transport._syncSendMail(mail);                                                                              // 98
};                                                                                                            // 99
                                                                                                              // 100
/**                                                                                                           // 101
 * Mock out email sending (eg, during a test.) This is private for now.                                       // 102
 *                                                                                                            // 103
 * f receives the arguments to Email.send and should return true to go                                        // 104
 * ahead and send the email (or at least, try subsequent hooks), or                                           // 105
 * false to skip sending.                                                                                     // 106
 */                                                                                                           // 107
var sendHooks = [];                                                                                           // 108
EmailTest.hookSend = function (f) {                                                                           // 109
  sendHooks.push(f);                                                                                          // 110
};                                                                                                            // 111
                                                                                                              // 112
/**                                                                                                           // 113
 * @summary Send an email. Throws an `Error` on failure to contact mail server                                // 114
 * or if mail server returns an error. All fields should match                                                // 115
 * [RFC5322](http://tools.ietf.org/html/rfc5322) specification.                                               // 116
 *                                                                                                            // 117
 * If the `MAIL_URL` environment variable is set, actually sends the email.                                   // 118
 * Otherwise, prints the contents of the email to standard out.                                               // 119
 *                                                                                                            // 120
 * Note that this package is based on **mailcomposer 4**, so make sure to refer to                            // 121
 * [the documentation](https://github.com/nodemailer/mailcomposer/blob/v4.0.1/README.md)                      // 122
 * for that version when using the `attachments` or `mailComposer` options.                                   // 123
 *                                                                                                            // 124
 * @locus Server                                                                                              // 125
 * @param {Object} options                                                                                    // 126
 * @param {String} [options.from] "From:" address (required)                                                  // 127
 * @param {String|String[]} options.to,cc,bcc,replyTo                                                         // 128
 *   "To:", "Cc:", "Bcc:", and "Reply-To:" addresses                                                          // 129
 * @param {String} [options.inReplyTo] Message-ID this message is replying to                                 // 130
 * @param {String|String[]} [options.references] Array (or space-separated string) of Message-IDs to refer to
 * @param {String} [options.messageId] Message-ID for this message; otherwise, will be set to a random value  // 132
 * @param {String} [options.subject]  "Subject:" line                                                         // 133
 * @param {String} [options.text|html] Mail body (in plain text and/or HTML)                                  // 134
 * @param {String} [options.watchHtml] Mail body in HTML specific for Apple Watch                             // 135
 * @param {String} [options.icalEvent] iCalendar event attachment                                             // 136
 * @param {Object} [options.headers] Dictionary of custom headers                                             // 137
 * @param {Object[]} [options.attachments] Array of attachment objects, as                                    // 138
 * described in the [mailcomposer documentation](https://github.com/nodemailer/mailcomposer/blob/v4.0.1/README.md#attachments).
 * @param {MailComposer} [options.mailComposer] A [MailComposer](https://nodemailer.com/extras/mailcomposer/#e-mail-message-fields)
 * object representing the message to be sent.  Overrides all other options.                                  // 141
 * You can create a `MailComposer` object via                                                                 // 142
 * `new EmailInternals.NpmModules.mailcomposer.module`.                                                       // 143
 */                                                                                                           // 144
Email.send = function (options) {                                                                             // 145
  for (var i = 0; i < sendHooks.length; i++)                                                                  // 146
    if (! sendHooks[i](options))                                                                              // 147
      return;                                                                                                 // 148
                                                                                                              // 149
  if (options.mailComposer) {                                                                                 // 150
    options = options.mailComposer.mail;                                                                      // 151
  }                                                                                                           // 152
                                                                                                              // 153
  var transport = getTransport();                                                                             // 154
  if (transport) {                                                                                            // 155
    smtpSend(transport, options);                                                                             // 156
  } else {                                                                                                    // 157
    devModeSend(options);                                                                                     // 158
  }                                                                                                           // 159
};                                                                                                            // 160
                                                                                                              // 161
////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
