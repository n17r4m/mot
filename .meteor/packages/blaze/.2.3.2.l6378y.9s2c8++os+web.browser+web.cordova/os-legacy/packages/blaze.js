(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/preamble.js                                                                                          //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
/**                                                                                                                    // 1
 * @namespace Blaze                                                                                                    // 2
 * @summary The namespace for all Blaze-related methods and classes.                                                   // 3
 */                                                                                                                    // 4
Blaze = {};                                                                                                            // 5
                                                                                                                       // 6
// Utility to HTML-escape a string.  Included for legacy reasons.                                                      // 7
// TODO: Should be replaced with _.escape once underscore is upgraded to a newer                                       // 8
//       version which escapes ` (backtick) as well. Underscore 1.5.2 does not.                                        // 9
Blaze._escape = (function() {                                                                                          // 10
  var escape_map = {                                                                                                   // 11
    "<": "&lt;",                                                                                                       // 12
    ">": "&gt;",                                                                                                       // 13
    '"': "&quot;",                                                                                                     // 14
    "'": "&#x27;",                                                                                                     // 15
    "/": "&#x2F;",                                                                                                     // 16
    "`": "&#x60;", /* IE allows backtick-delimited attributes?? */                                                     // 17
    "&": "&amp;"                                                                                                       // 18
  };                                                                                                                   // 19
  var escape_one = function(c) {                                                                                       // 20
    return escape_map[c];                                                                                              // 21
  };                                                                                                                   // 22
                                                                                                                       // 23
  return function (x) {                                                                                                // 24
    return x.replace(/[&<>"'`]/g, escape_one);                                                                         // 25
  };                                                                                                                   // 26
})();                                                                                                                  // 27
                                                                                                                       // 28
Blaze._warn = function (msg) {                                                                                         // 29
  msg = 'Warning: ' + msg;                                                                                             // 30
                                                                                                                       // 31
  if ((typeof console !== 'undefined') && console.warn) {                                                              // 32
    console.warn(msg);                                                                                                 // 33
  }                                                                                                                    // 34
};                                                                                                                     // 35
                                                                                                                       // 36
var nativeBind = Function.prototype.bind;                                                                              // 37
                                                                                                                       // 38
// An implementation of _.bind which allows better optimization.                                                       // 39
// See: https://github.com/petkaantonov/bluebird/wiki/Optimization-killers#3-managing-arguments                        // 40
if (nativeBind) {                                                                                                      // 41
  Blaze._bind = function (func, obj) {                                                                                 // 42
    if (arguments.length === 2) {                                                                                      // 43
      return nativeBind.call(func, obj);                                                                               // 44
    }                                                                                                                  // 45
                                                                                                                       // 46
    // Copy the arguments so this function can be optimized.                                                           // 47
    var args = new Array(arguments.length);                                                                            // 48
    for (var i = 0; i < args.length; i++) {                                                                            // 49
      args[i] = arguments[i];                                                                                          // 50
    }                                                                                                                  // 51
                                                                                                                       // 52
    return nativeBind.apply(func, args.slice(1));                                                                      // 53
  };                                                                                                                   // 54
}                                                                                                                      // 55
else {                                                                                                                 // 56
  // A slower but backwards compatible version.                                                                        // 57
  Blaze._bind = _.bind;                                                                                                // 58
}                                                                                                                      // 59
                                                                                                                       // 60
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/exceptions.js                                                                                        //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
var debugFunc;                                                                                                         // 1
                                                                                                                       // 2
// We call into user code in many places, and it's nice to catch exceptions                                            // 3
// propagated from user code immediately so that the whole system doesn't just                                         // 4
// break.  Catching exceptions is easy; reporting them is hard.  This helper                                           // 5
// reports exceptions.                                                                                                 // 6
//                                                                                                                     // 7
// Usage:                                                                                                              // 8
//                                                                                                                     // 9
// ```                                                                                                                 // 10
// try {                                                                                                               // 11
//   // ... someStuff ...                                                                                              // 12
// } catch (e) {                                                                                                       // 13
//   reportUIException(e);                                                                                             // 14
// }                                                                                                                   // 15
// ```                                                                                                                 // 16
//                                                                                                                     // 17
// An optional second argument overrides the default message.                                                          // 18
                                                                                                                       // 19
// Set this to `true` to cause `reportException` to throw                                                              // 20
// the next exception rather than reporting it.  This is                                                               // 21
// useful in unit tests that test error messages.                                                                      // 22
Blaze._throwNextException = false;                                                                                     // 23
                                                                                                                       // 24
Blaze._reportException = function (e, msg) {                                                                           // 25
  if (Blaze._throwNextException) {                                                                                     // 26
    Blaze._throwNextException = false;                                                                                 // 27
    throw e;                                                                                                           // 28
  }                                                                                                                    // 29
                                                                                                                       // 30
  if (! debugFunc)                                                                                                     // 31
    // adapted from Tracker                                                                                            // 32
    debugFunc = function () {                                                                                          // 33
      return (typeof Meteor !== "undefined" ? Meteor._debug :                                                          // 34
              ((typeof console !== "undefined") && console.log ? console.log :                                         // 35
               function () {}));                                                                                       // 36
    };                                                                                                                 // 37
                                                                                                                       // 38
  // In Chrome, `e.stack` is a multiline string that starts with the message                                           // 39
  // and contains a stack trace.  Furthermore, `console.log` makes it clickable.                                       // 40
  // `console.log` supplies the space between the two arguments.                                                       // 41
  debugFunc()(msg || 'Exception caught in template:', e.stack || e.message || e);                                      // 42
};                                                                                                                     // 43
                                                                                                                       // 44
Blaze._wrapCatchingExceptions = function (f, where) {                                                                  // 45
  if (typeof f !== 'function')                                                                                         // 46
    return f;                                                                                                          // 47
                                                                                                                       // 48
  return function () {                                                                                                 // 49
    try {                                                                                                              // 50
      return f.apply(this, arguments);                                                                                 // 51
    } catch (e) {                                                                                                      // 52
      Blaze._reportException(e, 'Exception in ' + where + ':');                                                        // 53
    }                                                                                                                  // 54
  };                                                                                                                   // 55
};                                                                                                                     // 56
                                                                                                                       // 57
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/view.js                                                                                              //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
/// [new] Blaze.View([name], renderMethod)                                                                             // 1
///                                                                                                                    // 2
/// Blaze.View is the building block of reactive DOM.  Views have                                                      // 3
/// the following features:                                                                                            // 4
///                                                                                                                    // 5
/// * lifecycle callbacks - Views are created, rendered, and destroyed,                                                // 6
///   and callbacks can be registered to fire when these things happen.                                                // 7
///                                                                                                                    // 8
/// * parent pointer - A View points to its parentView, which is the                                                   // 9
///   View that caused it to be rendered.  These pointers form a                                                       // 10
///   hierarchy or tree of Views.                                                                                      // 11
///                                                                                                                    // 12
/// * render() method - A View's render() method specifies the DOM                                                     // 13
///   (or HTML) content of the View.  If the method establishes                                                        // 14
///   reactive dependencies, it may be re-run.                                                                         // 15
///                                                                                                                    // 16
/// * a DOMRange - If a View is rendered to DOM, its position and                                                      // 17
///   extent in the DOM are tracked using a DOMRange object.                                                           // 18
///                                                                                                                    // 19
/// When a View is constructed by calling Blaze.View, the View is                                                      // 20
/// not yet considered "created."  It doesn't have a parentView yet,                                                   // 21
/// and no logic has been run to initialize the View.  All real                                                        // 22
/// work is deferred until at least creation time, when the onViewCreated                                              // 23
/// callbacks are fired, which happens when the View is "used" in                                                      // 24
/// some way that requires it to be rendered.                                                                          // 25
///                                                                                                                    // 26
/// ...more lifecycle stuff                                                                                            // 27
///                                                                                                                    // 28
/// `name` is an optional string tag identifying the View.  The only                                                   // 29
/// time it's used is when looking in the View tree for a View of a                                                    // 30
/// particular name; for example, data contexts are stored on Views                                                    // 31
/// of name "with".  Names are also useful when debugging, so in                                                       // 32
/// general it's good for functions that create Views to set the name.                                                 // 33
/// Views associated with templates have names of the form "Template.foo".                                             // 34
                                                                                                                       // 35
/**                                                                                                                    // 36
 * @class                                                                                                              // 37
 * @summary Constructor for a View, which represents a reactive region of DOM.                                         // 38
 * @locus Client                                                                                                       // 39
 * @param {String} [name] Optional.  A name for this type of View.  See [`view.name`](#view_name).                     // 40
 * @param {Function} renderFunction A function that returns [*renderable content*](#renderable_content).  In this function, `this` is bound to the View.
 */                                                                                                                    // 42
Blaze.View = function (name, render) {                                                                                 // 43
  if (! (this instanceof Blaze.View))                                                                                  // 44
    // called without `new`                                                                                            // 45
    return new Blaze.View(name, render);                                                                               // 46
                                                                                                                       // 47
  if (typeof name === 'function') {                                                                                    // 48
    // omitted "name" argument                                                                                         // 49
    render = name;                                                                                                     // 50
    name = '';                                                                                                         // 51
  }                                                                                                                    // 52
  this.name = name;                                                                                                    // 53
  this._render = render;                                                                                               // 54
                                                                                                                       // 55
  this._callbacks = {                                                                                                  // 56
    created: null,                                                                                                     // 57
    rendered: null,                                                                                                    // 58
    destroyed: null                                                                                                    // 59
  };                                                                                                                   // 60
                                                                                                                       // 61
  // Setting all properties here is good for readability,                                                              // 62
  // and also may help Chrome optimize the code by keeping                                                             // 63
  // the View object from changing shape too much.                                                                     // 64
  this.isCreated = false;                                                                                              // 65
  this._isCreatedForExpansion = false;                                                                                 // 66
  this.isRendered = false;                                                                                             // 67
  this._isAttached = false;                                                                                            // 68
  this.isDestroyed = false;                                                                                            // 69
  this._isInRender = false;                                                                                            // 70
  this.parentView = null;                                                                                              // 71
  this._domrange = null;                                                                                               // 72
  // This flag is normally set to false except for the cases when view's parent                                        // 73
  // was generated as part of expanding some syntactic sugar expressions or                                            // 74
  // methods.                                                                                                          // 75
  // Ex.: Blaze.renderWithData is an equivalent to creating a view with regular                                        // 76
  // Blaze.render and wrapping it into {{#with data}}{{/with}} view. Since the                                         // 77
  // users don't know anything about these generated parent views, Blaze needs                                         // 78
  // this information to be available on views to make smarter decisions. For                                          // 79
  // example: removing the generated parent view with the view on Blaze.remove.                                        // 80
  this._hasGeneratedParent = false;                                                                                    // 81
  // Bindings accessible to children views (via view.lookup('name')) within the                                        // 82
  // closest template view.                                                                                            // 83
  this._scopeBindings = {};                                                                                            // 84
                                                                                                                       // 85
  this.renderCount = 0;                                                                                                // 86
};                                                                                                                     // 87
                                                                                                                       // 88
Blaze.View.prototype._render = function () { return null; };                                                           // 89
                                                                                                                       // 90
Blaze.View.prototype.onViewCreated = function (cb) {                                                                   // 91
  this._callbacks.created = this._callbacks.created || [];                                                             // 92
  this._callbacks.created.push(cb);                                                                                    // 93
};                                                                                                                     // 94
                                                                                                                       // 95
Blaze.View.prototype._onViewRendered = function (cb) {                                                                 // 96
  this._callbacks.rendered = this._callbacks.rendered || [];                                                           // 97
  this._callbacks.rendered.push(cb);                                                                                   // 98
};                                                                                                                     // 99
                                                                                                                       // 100
Blaze.View.prototype.onViewReady = function (cb) {                                                                     // 101
  var self = this;                                                                                                     // 102
  var fire = function () {                                                                                             // 103
    Tracker.afterFlush(function () {                                                                                   // 104
      if (! self.isDestroyed) {                                                                                        // 105
        Blaze._withCurrentView(self, function () {                                                                     // 106
          cb.call(self);                                                                                               // 107
        });                                                                                                            // 108
      }                                                                                                                // 109
    });                                                                                                                // 110
  };                                                                                                                   // 111
  self._onViewRendered(function onViewRendered() {                                                                     // 112
    if (self.isDestroyed)                                                                                              // 113
      return;                                                                                                          // 114
    if (! self._domrange.attached)                                                                                     // 115
      self._domrange.onAttached(fire);                                                                                 // 116
    else                                                                                                               // 117
      fire();                                                                                                          // 118
  });                                                                                                                  // 119
};                                                                                                                     // 120
                                                                                                                       // 121
Blaze.View.prototype.onViewDestroyed = function (cb) {                                                                 // 122
  this._callbacks.destroyed = this._callbacks.destroyed || [];                                                         // 123
  this._callbacks.destroyed.push(cb);                                                                                  // 124
};                                                                                                                     // 125
Blaze.View.prototype.removeViewDestroyedListener = function (cb) {                                                     // 126
  var destroyed = this._callbacks.destroyed;                                                                           // 127
  if (! destroyed)                                                                                                     // 128
    return;                                                                                                            // 129
  var index = _.lastIndexOf(destroyed, cb);                                                                            // 130
  if (index !== -1) {                                                                                                  // 131
    // XXX You'd think the right thing to do would be splice, but _fireCallbacks                                       // 132
    // gets sad if you remove callbacks while iterating over the list.  Should                                         // 133
    // change this to use callback-hook or EventEmitter or something else that                                         // 134
    // properly supports removal.                                                                                      // 135
    destroyed[index] = null;                                                                                           // 136
  }                                                                                                                    // 137
};                                                                                                                     // 138
                                                                                                                       // 139
/// View#autorun(func)                                                                                                 // 140
///                                                                                                                    // 141
/// Sets up a Tracker autorun that is "scoped" to this View in two                                                     // 142
/// important ways: 1) Blaze.currentView is automatically set                                                          // 143
/// on every re-run, and 2) the autorun is stopped when the                                                            // 144
/// View is destroyed.  As with Tracker.autorun, the first run of                                                      // 145
/// the function is immediate, and a Computation object that can                                                       // 146
/// be used to stop the autorun is returned.                                                                           // 147
///                                                                                                                    // 148
/// View#autorun is meant to be called from View callbacks like                                                        // 149
/// onViewCreated, or from outside the rendering process.  It may not                                                  // 150
/// be called before the onViewCreated callbacks are fired (too early),                                                // 151
/// or from a render() method (too confusing).                                                                         // 152
///                                                                                                                    // 153
/// Typically, autoruns that update the state                                                                          // 154
/// of the View (as in Blaze.With) should be started from an onViewCreated                                             // 155
/// callback.  Autoruns that update the DOM should be started                                                          // 156
/// from either onViewCreated (guarded against the absence of                                                          // 157
/// view._domrange), or onViewReady.                                                                                   // 158
Blaze.View.prototype.autorun = function (f, _inViewScope, displayName) {                                               // 159
  var self = this;                                                                                                     // 160
                                                                                                                       // 161
  // The restrictions on when View#autorun can be called are in order                                                  // 162
  // to avoid bad patterns, like creating a Blaze.View and immediately                                                 // 163
  // calling autorun on it.  A freshly created View is not ready to                                                    // 164
  // have logic run on it; it doesn't have a parentView, for example.                                                  // 165
  // It's when the View is materialized or expanded that the onViewCreated                                             // 166
  // handlers are fired and the View starts up.                                                                        // 167
  //                                                                                                                   // 168
  // Letting the render() method call `this.autorun()` is problematic                                                  // 169
  // because of re-render.  The best we can do is to stop the old                                                      // 170
  // autorun and start a new one for each render, but that's a pattern                                                 // 171
  // we try to avoid internally because it leads to helpers being                                                      // 172
  // called extra times, in the case where the autorun causes the                                                      // 173
  // view to re-render (and thus the autorun to be torn down and a                                                     // 174
  // new one established).                                                                                             // 175
  //                                                                                                                   // 176
  // We could lift these restrictions in various ways.  One interesting                                                // 177
  // idea is to allow you to call `view.autorun` after instantiating                                                   // 178
  // `view`, and automatically wrap it in `view.onViewCreated`, deferring                                              // 179
  // the autorun so that it starts at an appropriate time.  However,                                                   // 180
  // then we can't return the Computation object to the caller, because                                                // 181
  // it doesn't exist yet.                                                                                             // 182
  if (! self.isCreated) {                                                                                              // 183
    throw new Error("View#autorun must be called from the created callback at the earliest");                          // 184
  }                                                                                                                    // 185
  if (this._isInRender) {                                                                                              // 186
    throw new Error("Can't call View#autorun from inside render(); try calling it from the created or rendered callback");
  }                                                                                                                    // 188
                                                                                                                       // 189
  var templateInstanceFunc = Blaze.Template._currentTemplateInstanceFunc;                                              // 190
                                                                                                                       // 191
  var func = function viewAutorun(c) {                                                                                 // 192
    return Blaze._withCurrentView(_inViewScope || self, function () {                                                  // 193
      return Blaze.Template._withTemplateInstanceFunc(                                                                 // 194
        templateInstanceFunc, function () {                                                                            // 195
          return f.call(self, c);                                                                                      // 196
        });                                                                                                            // 197
    });                                                                                                                // 198
  };                                                                                                                   // 199
                                                                                                                       // 200
  // Give the autorun function a better name for debugging and profiling.                                              // 201
  // The `displayName` property is not part of the spec but browsers like Chrome                                       // 202
  // and Firefox prefer it in debuggers over the name function was declared by.                                        // 203
  func.displayName =                                                                                                   // 204
    (self.name || 'anonymous') + ':' + (displayName || 'anonymous');                                                   // 205
  var comp = Tracker.autorun(func);                                                                                    // 206
                                                                                                                       // 207
  var stopComputation = function () { comp.stop(); };                                                                  // 208
  self.onViewDestroyed(stopComputation);                                                                               // 209
  comp.onStop(function () {                                                                                            // 210
    self.removeViewDestroyedListener(stopComputation);                                                                 // 211
  });                                                                                                                  // 212
                                                                                                                       // 213
  return comp;                                                                                                         // 214
};                                                                                                                     // 215
                                                                                                                       // 216
Blaze.View.prototype._errorIfShouldntCallSubscribe = function () {                                                     // 217
  var self = this;                                                                                                     // 218
                                                                                                                       // 219
  if (! self.isCreated) {                                                                                              // 220
    throw new Error("View#subscribe must be called from the created callback at the earliest");                        // 221
  }                                                                                                                    // 222
  if (self._isInRender) {                                                                                              // 223
    throw new Error("Can't call View#subscribe from inside render(); try calling it from the created or rendered callback");
  }                                                                                                                    // 225
  if (self.isDestroyed) {                                                                                              // 226
    throw new Error("Can't call View#subscribe from inside the destroyed callback, try calling it inside created or rendered.");
  }                                                                                                                    // 228
};                                                                                                                     // 229
                                                                                                                       // 230
/**                                                                                                                    // 231
 * Just like Blaze.View#autorun, but with Meteor.subscribe instead of                                                  // 232
 * Tracker.autorun. Stop the subscription when the view is destroyed.                                                  // 233
 * @return {SubscriptionHandle} A handle to the subscription so that you can                                           // 234
 * see if it is ready, or stop it manually                                                                             // 235
 */                                                                                                                    // 236
Blaze.View.prototype.subscribe = function (args, options) {                                                            // 237
  var self = this;                                                                                                     // 238
  options = options || {};                                                                                             // 239
                                                                                                                       // 240
  self._errorIfShouldntCallSubscribe();                                                                                // 241
                                                                                                                       // 242
  var subHandle;                                                                                                       // 243
  if (options.connection) {                                                                                            // 244
    subHandle = options.connection.subscribe.apply(options.connection, args);                                          // 245
  } else {                                                                                                             // 246
    subHandle = Meteor.subscribe.apply(Meteor, args);                                                                  // 247
  }                                                                                                                    // 248
                                                                                                                       // 249
  self.onViewDestroyed(function () {                                                                                   // 250
    subHandle.stop();                                                                                                  // 251
  });                                                                                                                  // 252
                                                                                                                       // 253
  return subHandle;                                                                                                    // 254
};                                                                                                                     // 255
                                                                                                                       // 256
Blaze.View.prototype.firstNode = function () {                                                                         // 257
  if (! this._isAttached)                                                                                              // 258
    throw new Error("View must be attached before accessing its DOM");                                                 // 259
                                                                                                                       // 260
  return this._domrange.firstNode();                                                                                   // 261
};                                                                                                                     // 262
                                                                                                                       // 263
Blaze.View.prototype.lastNode = function () {                                                                          // 264
  if (! this._isAttached)                                                                                              // 265
    throw new Error("View must be attached before accessing its DOM");                                                 // 266
                                                                                                                       // 267
  return this._domrange.lastNode();                                                                                    // 268
};                                                                                                                     // 269
                                                                                                                       // 270
Blaze._fireCallbacks = function (view, which) {                                                                        // 271
  Blaze._withCurrentView(view, function () {                                                                           // 272
    Tracker.nonreactive(function fireCallbacks() {                                                                     // 273
      var cbs = view._callbacks[which];                                                                                // 274
      for (var i = 0, N = (cbs && cbs.length); i < N; i++)                                                             // 275
        cbs[i] && cbs[i].call(view);                                                                                   // 276
    });                                                                                                                // 277
  });                                                                                                                  // 278
};                                                                                                                     // 279
                                                                                                                       // 280
Blaze._createView = function (view, parentView, forExpansion) {                                                        // 281
  if (view.isCreated)                                                                                                  // 282
    throw new Error("Can't render the same View twice");                                                               // 283
                                                                                                                       // 284
  view.parentView = (parentView || null);                                                                              // 285
  view.isCreated = true;                                                                                               // 286
  if (forExpansion)                                                                                                    // 287
    view._isCreatedForExpansion = true;                                                                                // 288
                                                                                                                       // 289
  Blaze._fireCallbacks(view, 'created');                                                                               // 290
};                                                                                                                     // 291
                                                                                                                       // 292
var doFirstRender = function (view, initialContent) {                                                                  // 293
  var domrange = new Blaze._DOMRange(initialContent);                                                                  // 294
  view._domrange = domrange;                                                                                           // 295
  domrange.view = view;                                                                                                // 296
  view.isRendered = true;                                                                                              // 297
  Blaze._fireCallbacks(view, 'rendered');                                                                              // 298
                                                                                                                       // 299
  var teardownHook = null;                                                                                             // 300
                                                                                                                       // 301
  domrange.onAttached(function attached(range, element) {                                                              // 302
    view._isAttached = true;                                                                                           // 303
                                                                                                                       // 304
    teardownHook = Blaze._DOMBackend.Teardown.onElementTeardown(                                                       // 305
      element, function teardown() {                                                                                   // 306
        Blaze._destroyView(view, true /* _skipNodes */);                                                               // 307
      });                                                                                                              // 308
  });                                                                                                                  // 309
                                                                                                                       // 310
  // tear down the teardown hook                                                                                       // 311
  view.onViewDestroyed(function () {                                                                                   // 312
    teardownHook && teardownHook.stop();                                                                               // 313
    teardownHook = null;                                                                                               // 314
  });                                                                                                                  // 315
                                                                                                                       // 316
  return domrange;                                                                                                     // 317
};                                                                                                                     // 318
                                                                                                                       // 319
// Take an uncreated View `view` and create and render it to DOM,                                                      // 320
// setting up the autorun that updates the View.  Returns a new                                                        // 321
// DOMRange, which has been associated with the View.                                                                  // 322
//                                                                                                                     // 323
// The private arguments `_workStack` and `_intoArray` are passed in                                                   // 324
// by Blaze._materializeDOM and are only present for recursive calls                                                   // 325
// (when there is some other _materializeView on the stack).  If                                                       // 326
// provided, then we avoid the mutual recursion of calling back into                                                   // 327
// Blaze._materializeDOM so that deep View hierarchies don't blow the                                                  // 328
// stack.  Instead, we push tasks onto workStack for the initial                                                       // 329
// rendering and subsequent setup of the View, and they are done after                                                 // 330
// we return.  When there is a _workStack, we do not return the new                                                    // 331
// DOMRange, but instead push it into _intoArray from a _workStack                                                     // 332
// task.                                                                                                               // 333
Blaze._materializeView = function (view, parentView, _workStack, _intoArray) {                                         // 334
  Blaze._createView(view, parentView);                                                                                 // 335
                                                                                                                       // 336
  var domrange;                                                                                                        // 337
  var lastHtmljs;                                                                                                      // 338
  // We don't expect to be called in a Computation, but just in case,                                                  // 339
  // wrap in Tracker.nonreactive.                                                                                      // 340
  Tracker.nonreactive(function () {                                                                                    // 341
    view.autorun(function doRender(c) {                                                                                // 342
      // `view.autorun` sets the current view.                                                                         // 343
      view.renderCount++;                                                                                              // 344
      view._isInRender = true;                                                                                         // 345
      // Any dependencies that should invalidate this Computation come                                                 // 346
      // from this line:                                                                                               // 347
      var htmljs = view._render();                                                                                     // 348
      view._isInRender = false;                                                                                        // 349
                                                                                                                       // 350
      if (! c.firstRun && ! Blaze._isContentEqual(lastHtmljs, htmljs)) {                                               // 351
        Tracker.nonreactive(function doMaterialize() {                                                                 // 352
          // re-render                                                                                                 // 353
          var rangesAndNodes = Blaze._materializeDOM(htmljs, [], view);                                                // 354
          domrange.setMembers(rangesAndNodes);                                                                         // 355
          Blaze._fireCallbacks(view, 'rendered');                                                                      // 356
        });                                                                                                            // 357
      }                                                                                                                // 358
      lastHtmljs = htmljs;                                                                                             // 359
                                                                                                                       // 360
      // Causes any nested views to stop immediately, not when we call                                                 // 361
      // `setMembers` the next time around the autorun.  Otherwise,                                                    // 362
      // helpers in the DOM tree to be replaced might be scheduled                                                     // 363
      // to re-run before we have a chance to stop them.                                                               // 364
      Tracker.onInvalidate(function () {                                                                               // 365
        if (domrange) {                                                                                                // 366
          domrange.destroyMembers();                                                                                   // 367
        }                                                                                                              // 368
      });                                                                                                              // 369
    }, undefined, 'materialize');                                                                                      // 370
                                                                                                                       // 371
    // first render.  lastHtmljs is the first htmljs.                                                                  // 372
    var initialContents;                                                                                               // 373
    if (! _workStack) {                                                                                                // 374
      initialContents = Blaze._materializeDOM(lastHtmljs, [], view);                                                   // 375
      domrange = doFirstRender(view, initialContents);                                                                 // 376
      initialContents = null; // help GC because we close over this scope a lot                                        // 377
    } else {                                                                                                           // 378
      // We're being called from Blaze._materializeDOM, so to avoid                                                    // 379
      // recursion and save stack space, provide a description of the                                                  // 380
      // work to be done instead of doing it.  Tasks pushed onto                                                       // 381
      // _workStack will be done in LIFO order after we return.                                                        // 382
      // The work will still be done within a Tracker.nonreactive,                                                     // 383
      // because it will be done by some call to Blaze._materializeDOM                                                 // 384
      // (which is always called in a Tracker.nonreactive).                                                            // 385
      initialContents = [];                                                                                            // 386
      // push this function first so that it happens last                                                              // 387
      _workStack.push(function () {                                                                                    // 388
        domrange = doFirstRender(view, initialContents);                                                               // 389
        initialContents = null; // help GC because of all the closures here                                            // 390
        _intoArray.push(domrange);                                                                                     // 391
      });                                                                                                              // 392
      // now push the task that calculates initialContents                                                             // 393
      _workStack.push(Blaze._bind(Blaze._materializeDOM, null,                                                         // 394
                             lastHtmljs, initialContents, view, _workStack));                                          // 395
    }                                                                                                                  // 396
  });                                                                                                                  // 397
                                                                                                                       // 398
  if (! _workStack) {                                                                                                  // 399
    return domrange;                                                                                                   // 400
  } else {                                                                                                             // 401
    return null;                                                                                                       // 402
  }                                                                                                                    // 403
};                                                                                                                     // 404
                                                                                                                       // 405
// Expands a View to HTMLjs, calling `render` recursively on all                                                       // 406
// Views and evaluating any dynamic attributes.  Calls the `created`                                                   // 407
// callback, but not the `materialized` or `rendered` callbacks.                                                       // 408
// Destroys the view immediately, unless called in a Tracker Computation,                                              // 409
// in which case the view will be destroyed when the Computation is                                                    // 410
// invalidated.  If called in a Tracker Computation, the result is a                                                   // 411
// reactive string; that is, the Computation will be invalidated                                                       // 412
// if any changes are made to the view or subviews that might affect                                                   // 413
// the HTML.                                                                                                           // 414
Blaze._expandView = function (view, parentView) {                                                                      // 415
  Blaze._createView(view, parentView, true /*forExpansion*/);                                                          // 416
                                                                                                                       // 417
  view._isInRender = true;                                                                                             // 418
  var htmljs = Blaze._withCurrentView(view, function () {                                                              // 419
    return view._render();                                                                                             // 420
  });                                                                                                                  // 421
  view._isInRender = false;                                                                                            // 422
                                                                                                                       // 423
  var result = Blaze._expand(htmljs, view);                                                                            // 424
                                                                                                                       // 425
  if (Tracker.active) {                                                                                                // 426
    Tracker.onInvalidate(function () {                                                                                 // 427
      Blaze._destroyView(view);                                                                                        // 428
    });                                                                                                                // 429
  } else {                                                                                                             // 430
    Blaze._destroyView(view);                                                                                          // 431
  }                                                                                                                    // 432
                                                                                                                       // 433
  return result;                                                                                                       // 434
};                                                                                                                     // 435
                                                                                                                       // 436
// Options: `parentView`                                                                                               // 437
Blaze._HTMLJSExpander = HTML.TransformingVisitor.extend();                                                             // 438
Blaze._HTMLJSExpander.def({                                                                                            // 439
  visitObject: function (x) {                                                                                          // 440
    if (x instanceof Blaze.Template)                                                                                   // 441
      x = x.constructView();                                                                                           // 442
    if (x instanceof Blaze.View)                                                                                       // 443
      return Blaze._expandView(x, this.parentView);                                                                    // 444
                                                                                                                       // 445
    // this will throw an error; other objects are not allowed!                                                        // 446
    return HTML.TransformingVisitor.prototype.visitObject.call(this, x);                                               // 447
  },                                                                                                                   // 448
  visitAttributes: function (attrs) {                                                                                  // 449
    // expand dynamic attributes                                                                                       // 450
    if (typeof attrs === 'function')                                                                                   // 451
      attrs = Blaze._withCurrentView(this.parentView, attrs);                                                          // 452
                                                                                                                       // 453
    // call super (e.g. for case where `attrs` is an array)                                                            // 454
    return HTML.TransformingVisitor.prototype.visitAttributes.call(this, attrs);                                       // 455
  },                                                                                                                   // 456
  visitAttribute: function (name, value, tag) {                                                                        // 457
    // expand attribute values that are functions.  Any attribute value                                                // 458
    // that contains Views must be wrapped in a function.                                                              // 459
    if (typeof value === 'function')                                                                                   // 460
      value = Blaze._withCurrentView(this.parentView, value);                                                          // 461
                                                                                                                       // 462
    return HTML.TransformingVisitor.prototype.visitAttribute.call(                                                     // 463
      this, name, value, tag);                                                                                         // 464
  }                                                                                                                    // 465
});                                                                                                                    // 466
                                                                                                                       // 467
// Return Blaze.currentView, but only if it is being rendered                                                          // 468
// (i.e. we are in its render() method).                                                                               // 469
var currentViewIfRendering = function () {                                                                             // 470
  var view = Blaze.currentView;                                                                                        // 471
  return (view && view._isInRender) ? view : null;                                                                     // 472
};                                                                                                                     // 473
                                                                                                                       // 474
Blaze._expand = function (htmljs, parentView) {                                                                        // 475
  parentView = parentView || currentViewIfRendering();                                                                 // 476
  return (new Blaze._HTMLJSExpander(                                                                                   // 477
    {parentView: parentView})).visit(htmljs);                                                                          // 478
};                                                                                                                     // 479
                                                                                                                       // 480
Blaze._expandAttributes = function (attrs, parentView) {                                                               // 481
  parentView = parentView || currentViewIfRendering();                                                                 // 482
  return (new Blaze._HTMLJSExpander(                                                                                   // 483
    {parentView: parentView})).visitAttributes(attrs);                                                                 // 484
};                                                                                                                     // 485
                                                                                                                       // 486
Blaze._destroyView = function (view, _skipNodes) {                                                                     // 487
  if (view.isDestroyed)                                                                                                // 488
    return;                                                                                                            // 489
  view.isDestroyed = true;                                                                                             // 490
                                                                                                                       // 491
  Blaze._fireCallbacks(view, 'destroyed');                                                                             // 492
                                                                                                                       // 493
  // Destroy views and elements recursively.  If _skipNodes,                                                           // 494
  // only recurse up to views, not elements, for the case where                                                        // 495
  // the backend (jQuery) is recursing over the elements already.                                                      // 496
                                                                                                                       // 497
  if (view._domrange)                                                                                                  // 498
    view._domrange.destroyMembers(_skipNodes);                                                                         // 499
};                                                                                                                     // 500
                                                                                                                       // 501
Blaze._destroyNode = function (node) {                                                                                 // 502
  if (node.nodeType === 1)                                                                                             // 503
    Blaze._DOMBackend.Teardown.tearDownElement(node);                                                                  // 504
};                                                                                                                     // 505
                                                                                                                       // 506
// Are the HTMLjs entities `a` and `b` the same?  We could be                                                          // 507
// more elaborate here but the point is to catch the most basic                                                        // 508
// cases.                                                                                                              // 509
Blaze._isContentEqual = function (a, b) {                                                                              // 510
  if (a instanceof HTML.Raw) {                                                                                         // 511
    return (b instanceof HTML.Raw) && (a.value === b.value);                                                           // 512
  } else if (a == null) {                                                                                              // 513
    return (b == null);                                                                                                // 514
  } else {                                                                                                             // 515
    return (a === b) &&                                                                                                // 516
      ((typeof a === 'number') || (typeof a === 'boolean') ||                                                          // 517
       (typeof a === 'string'));                                                                                       // 518
  }                                                                                                                    // 519
};                                                                                                                     // 520
                                                                                                                       // 521
/**                                                                                                                    // 522
 * @summary The View corresponding to the current template helper, event handler, callback, or autorun.  If there isn't one, `null`.
 * @locus Client                                                                                                       // 524
 * @type {Blaze.View}                                                                                                  // 525
 */                                                                                                                    // 526
Blaze.currentView = null;                                                                                              // 527
                                                                                                                       // 528
Blaze._withCurrentView = function (view, func) {                                                                       // 529
  var oldView = Blaze.currentView;                                                                                     // 530
  try {                                                                                                                // 531
    Blaze.currentView = view;                                                                                          // 532
    return func();                                                                                                     // 533
  } finally {                                                                                                          // 534
    Blaze.currentView = oldView;                                                                                       // 535
  }                                                                                                                    // 536
};                                                                                                                     // 537
                                                                                                                       // 538
// Blaze.render publicly takes a View or a Template.                                                                   // 539
// Privately, it takes any HTMLJS (extended with Views and Templates)                                                  // 540
// except null or undefined, or a function that returns any extended                                                   // 541
// HTMLJS.                                                                                                             // 542
var checkRenderContent = function (content) {                                                                          // 543
  if (content === null)                                                                                                // 544
    throw new Error("Can't render null");                                                                              // 545
  if (typeof content === 'undefined')                                                                                  // 546
    throw new Error("Can't render undefined");                                                                         // 547
                                                                                                                       // 548
  if ((content instanceof Blaze.View) ||                                                                               // 549
      (content instanceof Blaze.Template) ||                                                                           // 550
      (typeof content === 'function'))                                                                                 // 551
    return;                                                                                                            // 552
                                                                                                                       // 553
  try {                                                                                                                // 554
    // Throw if content doesn't look like HTMLJS at the top level                                                      // 555
    // (i.e. verify that this is an HTML.Tag, or an array,                                                             // 556
    // or a primitive, etc.)                                                                                           // 557
    (new HTML.Visitor).visit(content);                                                                                 // 558
  } catch (e) {                                                                                                        // 559
    // Make error message suitable for public API                                                                      // 560
    throw new Error("Expected Template or View");                                                                      // 561
  }                                                                                                                    // 562
};                                                                                                                     // 563
                                                                                                                       // 564
// For Blaze.render and Blaze.toHTML, take content and                                                                 // 565
// wrap it in a View, unless it's a single View or                                                                     // 566
// Template already.                                                                                                   // 567
var contentAsView = function (content) {                                                                               // 568
  checkRenderContent(content);                                                                                         // 569
                                                                                                                       // 570
  if (content instanceof Blaze.Template) {                                                                             // 571
    return content.constructView();                                                                                    // 572
  } else if (content instanceof Blaze.View) {                                                                          // 573
    return content;                                                                                                    // 574
  } else {                                                                                                             // 575
    var func = content;                                                                                                // 576
    if (typeof func !== 'function') {                                                                                  // 577
      func = function () {                                                                                             // 578
        return content;                                                                                                // 579
      };                                                                                                               // 580
    }                                                                                                                  // 581
    return Blaze.View('render', func);                                                                                 // 582
  }                                                                                                                    // 583
};                                                                                                                     // 584
                                                                                                                       // 585
// For Blaze.renderWithData and Blaze.toHTMLWithData, wrap content                                                     // 586
// in a function, if necessary, so it can be a content arg to                                                          // 587
// a Blaze.With.                                                                                                       // 588
var contentAsFunc = function (content) {                                                                               // 589
  checkRenderContent(content);                                                                                         // 590
                                                                                                                       // 591
  if (typeof content !== 'function') {                                                                                 // 592
    return function () {                                                                                               // 593
      return content;                                                                                                  // 594
    };                                                                                                                 // 595
  } else {                                                                                                             // 596
    return content;                                                                                                    // 597
  }                                                                                                                    // 598
};                                                                                                                     // 599
                                                                                                                       // 600
/**                                                                                                                    // 601
 * @summary Renders a template or View to DOM nodes and inserts it into the DOM, returning a rendered [View](#blaze_view) which can be passed to [`Blaze.remove`](#blaze_remove).
 * @locus Client                                                                                                       // 603
 * @param {Template|Blaze.View} templateOrView The template (e.g. `Template.myTemplate`) or View object to render.  If a template, a View object is [constructed](#template_constructview).  If a View, it must be an unrendered View, which becomes a rendered View and is returned.
 * @param {DOMNode} parentNode The node that will be the parent of the rendered template.  It must be an Element node.
 * @param {DOMNode} [nextNode] Optional. If provided, must be a child of <em>parentNode</em>; the template will be inserted before this node. If not provided, the template will be inserted as the last child of parentNode.
 * @param {Blaze.View} [parentView] Optional. If provided, it will be set as the rendered View's [`parentView`](#view_parentview).
 */                                                                                                                    // 608
Blaze.render = function (content, parentElement, nextNode, parentView) {                                               // 609
  if (! parentElement) {                                                                                               // 610
    Blaze._warn("Blaze.render without a parent element is deprecated. " +                                              // 611
                "You must specify where to insert the rendered content.");                                             // 612
  }                                                                                                                    // 613
                                                                                                                       // 614
  if (nextNode instanceof Blaze.View) {                                                                                // 615
    // handle omitted nextNode                                                                                         // 616
    parentView = nextNode;                                                                                             // 617
    nextNode = null;                                                                                                   // 618
  }                                                                                                                    // 619
                                                                                                                       // 620
  // parentElement must be a DOM node. in particular, can't be the                                                     // 621
  // result of a call to `$`. Can't check if `parentElement instanceof                                                 // 622
  // Node` since 'Node' is undefined in IE8.                                                                           // 623
  if (parentElement && typeof parentElement.nodeType !== 'number')                                                     // 624
    throw new Error("'parentElement' must be a DOM node");                                                             // 625
  if (nextNode && typeof nextNode.nodeType !== 'number') // 'nextNode' is optional                                     // 626
    throw new Error("'nextNode' must be a DOM node");                                                                  // 627
                                                                                                                       // 628
  parentView = parentView || currentViewIfRendering();                                                                 // 629
                                                                                                                       // 630
  var view = contentAsView(content);                                                                                   // 631
  Blaze._materializeView(view, parentView);                                                                            // 632
                                                                                                                       // 633
  if (parentElement) {                                                                                                 // 634
    view._domrange.attach(parentElement, nextNode);                                                                    // 635
  }                                                                                                                    // 636
                                                                                                                       // 637
  return view;                                                                                                         // 638
};                                                                                                                     // 639
                                                                                                                       // 640
Blaze.insert = function (view, parentElement, nextNode) {                                                              // 641
  Blaze._warn("Blaze.insert has been deprecated.  Specify where to insert the " +                                      // 642
              "rendered content in the call to Blaze.render.");                                                        // 643
                                                                                                                       // 644
  if (! (view && (view._domrange instanceof Blaze._DOMRange)))                                                         // 645
    throw new Error("Expected template rendered with Blaze.render");                                                   // 646
                                                                                                                       // 647
  view._domrange.attach(parentElement, nextNode);                                                                      // 648
};                                                                                                                     // 649
                                                                                                                       // 650
/**                                                                                                                    // 651
 * @summary Renders a template or View to DOM nodes with a data context.  Otherwise identical to `Blaze.render`.       // 652
 * @locus Client                                                                                                       // 653
 * @param {Template|Blaze.View} templateOrView The template (e.g. `Template.myTemplate`) or View object to render.     // 654
 * @param {Object|Function} data The data context to use, or a function returning a data context.  If a function is provided, it will be reactively re-run.
 * @param {DOMNode} parentNode The node that will be the parent of the rendered template.  It must be an Element node.
 * @param {DOMNode} [nextNode] Optional. If provided, must be a child of <em>parentNode</em>; the template will be inserted before this node. If not provided, the template will be inserted as the last child of parentNode.
 * @param {Blaze.View} [parentView] Optional. If provided, it will be set as the rendered View's [`parentView`](#view_parentview).
 */                                                                                                                    // 659
Blaze.renderWithData = function (content, data, parentElement, nextNode, parentView) {                                 // 660
  // We defer the handling of optional arguments to Blaze.render.  At this point,                                      // 661
  // `nextNode` may actually be `parentView`.                                                                          // 662
  return Blaze.render(Blaze._TemplateWith(data, contentAsFunc(content)),                                               // 663
                          parentElement, nextNode, parentView);                                                        // 664
};                                                                                                                     // 665
                                                                                                                       // 666
/**                                                                                                                    // 667
 * @summary Removes a rendered View from the DOM, stopping all reactive updates and event listeners on it. Also destroys the Blaze.Template instance associated with the view.
 * @locus Client                                                                                                       // 669
 * @param {Blaze.View} renderedView The return value from `Blaze.render` or `Blaze.renderWithData`, or the `view` property of a Blaze.Template instance. Calling `Blaze.remove(Template.instance().view)` from within a template event handler will destroy the view as well as that template and trigger the template's `onDestroyed` handlers.
 */                                                                                                                    // 671
Blaze.remove = function (view) {                                                                                       // 672
  if (! (view && (view._domrange instanceof Blaze._DOMRange)))                                                         // 673
    throw new Error("Expected template rendered with Blaze.render");                                                   // 674
                                                                                                                       // 675
  while (view) {                                                                                                       // 676
    if (! view.isDestroyed) {                                                                                          // 677
      var range = view._domrange;                                                                                      // 678
      if (range.attached && ! range.parentRange)                                                                       // 679
        range.detach();                                                                                                // 680
      range.destroy();                                                                                                 // 681
    }                                                                                                                  // 682
                                                                                                                       // 683
    view = view._hasGeneratedParent && view.parentView;                                                                // 684
  }                                                                                                                    // 685
};                                                                                                                     // 686
                                                                                                                       // 687
/**                                                                                                                    // 688
 * @summary Renders a template or View to a string of HTML.                                                            // 689
 * @locus Client                                                                                                       // 690
 * @param {Template|Blaze.View} templateOrView The template (e.g. `Template.myTemplate`) or View object from which to generate HTML.
 */                                                                                                                    // 692
Blaze.toHTML = function (content, parentView) {                                                                        // 693
  parentView = parentView || currentViewIfRendering();                                                                 // 694
                                                                                                                       // 695
  return HTML.toHTML(Blaze._expandView(contentAsView(content), parentView));                                           // 696
};                                                                                                                     // 697
                                                                                                                       // 698
/**                                                                                                                    // 699
 * @summary Renders a template or View to HTML with a data context.  Otherwise identical to `Blaze.toHTML`.            // 700
 * @locus Client                                                                                                       // 701
 * @param {Template|Blaze.View} templateOrView The template (e.g. `Template.myTemplate`) or View object from which to generate HTML.
 * @param {Object|Function} data The data context to use, or a function returning a data context.                      // 703
 */                                                                                                                    // 704
Blaze.toHTMLWithData = function (content, data, parentView) {                                                          // 705
  parentView = parentView || currentViewIfRendering();                                                                 // 706
                                                                                                                       // 707
  return HTML.toHTML(Blaze._expandView(Blaze._TemplateWith(                                                            // 708
    data, contentAsFunc(content)), parentView));                                                                       // 709
};                                                                                                                     // 710
                                                                                                                       // 711
Blaze._toText = function (htmljs, parentView, textMode) {                                                              // 712
  if (typeof htmljs === 'function')                                                                                    // 713
    throw new Error("Blaze._toText doesn't take a function, just HTMLjs");                                             // 714
                                                                                                                       // 715
  if ((parentView != null) && ! (parentView instanceof Blaze.View)) {                                                  // 716
    // omitted parentView argument                                                                                     // 717
    textMode = parentView;                                                                                             // 718
    parentView = null;                                                                                                 // 719
  }                                                                                                                    // 720
  parentView = parentView || currentViewIfRendering();                                                                 // 721
                                                                                                                       // 722
  if (! textMode)                                                                                                      // 723
    throw new Error("textMode required");                                                                              // 724
  if (! (textMode === HTML.TEXTMODE.STRING ||                                                                          // 725
         textMode === HTML.TEXTMODE.RCDATA ||                                                                          // 726
         textMode === HTML.TEXTMODE.ATTRIBUTE))                                                                        // 727
    throw new Error("Unknown textMode: " + textMode);                                                                  // 728
                                                                                                                       // 729
  return HTML.toText(Blaze._expand(htmljs, parentView), textMode);                                                     // 730
};                                                                                                                     // 731
                                                                                                                       // 732
/**                                                                                                                    // 733
 * @summary Returns the current data context, or the data context that was used when rendering a particular DOM element or View from a Meteor template.
 * @locus Client                                                                                                       // 735
 * @param {DOMElement|Blaze.View} [elementOrView] Optional.  An element that was rendered by a Meteor, or a View.      // 736
 */                                                                                                                    // 737
Blaze.getData = function (elementOrView) {                                                                             // 738
  var theWith;                                                                                                         // 739
                                                                                                                       // 740
  if (! elementOrView) {                                                                                               // 741
    theWith = Blaze.getView('with');                                                                                   // 742
  } else if (elementOrView instanceof Blaze.View) {                                                                    // 743
    var view = elementOrView;                                                                                          // 744
    theWith = (view.name === 'with' ? view :                                                                           // 745
               Blaze.getView(view, 'with'));                                                                           // 746
  } else if (typeof elementOrView.nodeType === 'number') {                                                             // 747
    if (elementOrView.nodeType !== 1)                                                                                  // 748
      throw new Error("Expected DOM element");                                                                         // 749
    theWith = Blaze.getView(elementOrView, 'with');                                                                    // 750
  } else {                                                                                                             // 751
    throw new Error("Expected DOM element or View");                                                                   // 752
  }                                                                                                                    // 753
                                                                                                                       // 754
  return theWith ? theWith.dataVar.get() : null;                                                                       // 755
};                                                                                                                     // 756
                                                                                                                       // 757
// For back-compat                                                                                                     // 758
Blaze.getElementData = function (element) {                                                                            // 759
  Blaze._warn("Blaze.getElementData has been deprecated.  Use " +                                                      // 760
              "Blaze.getData(element) instead.");                                                                      // 761
                                                                                                                       // 762
  if (element.nodeType !== 1)                                                                                          // 763
    throw new Error("Expected DOM element");                                                                           // 764
                                                                                                                       // 765
  return Blaze.getData(element);                                                                                       // 766
};                                                                                                                     // 767
                                                                                                                       // 768
// Both arguments are optional.                                                                                        // 769
                                                                                                                       // 770
/**                                                                                                                    // 771
 * @summary Gets either the current View, or the View enclosing the given DOM element.                                 // 772
 * @locus Client                                                                                                       // 773
 * @param {DOMElement} [element] Optional.  If specified, the View enclosing `element` is returned.                    // 774
 */                                                                                                                    // 775
Blaze.getView = function (elementOrView, _viewName) {                                                                  // 776
  var viewName = _viewName;                                                                                            // 777
                                                                                                                       // 778
  if ((typeof elementOrView) === 'string') {                                                                           // 779
    // omitted elementOrView; viewName present                                                                         // 780
    viewName = elementOrView;                                                                                          // 781
    elementOrView = null;                                                                                              // 782
  }                                                                                                                    // 783
                                                                                                                       // 784
  // We could eventually shorten the code by folding the logic                                                         // 785
  // from the other methods into this method.                                                                          // 786
  if (! elementOrView) {                                                                                               // 787
    return Blaze._getCurrentView(viewName);                                                                            // 788
  } else if (elementOrView instanceof Blaze.View) {                                                                    // 789
    return Blaze._getParentView(elementOrView, viewName);                                                              // 790
  } else if (typeof elementOrView.nodeType === 'number') {                                                             // 791
    return Blaze._getElementView(elementOrView, viewName);                                                             // 792
  } else {                                                                                                             // 793
    throw new Error("Expected DOM element or View");                                                                   // 794
  }                                                                                                                    // 795
};                                                                                                                     // 796
                                                                                                                       // 797
// Gets the current view or its nearest ancestor of name                                                               // 798
// `name`.                                                                                                             // 799
Blaze._getCurrentView = function (name) {                                                                              // 800
  var view = Blaze.currentView;                                                                                        // 801
  // Better to fail in cases where it doesn't make sense                                                               // 802
  // to use Blaze._getCurrentView().  There will be a current                                                          // 803
  // view anywhere it does.  You can check Blaze.currentView                                                           // 804
  // if you want to know whether there is one or not.                                                                  // 805
  if (! view)                                                                                                          // 806
    throw new Error("There is no current view");                                                                       // 807
                                                                                                                       // 808
  if (name) {                                                                                                          // 809
    while (view && view.name !== name)                                                                                 // 810
      view = view.parentView;                                                                                          // 811
    return view || null;                                                                                               // 812
  } else {                                                                                                             // 813
    // Blaze._getCurrentView() with no arguments just returns                                                          // 814
    // Blaze.currentView.                                                                                              // 815
    return view;                                                                                                       // 816
  }                                                                                                                    // 817
};                                                                                                                     // 818
                                                                                                                       // 819
Blaze._getParentView = function (view, name) {                                                                         // 820
  var v = view.parentView;                                                                                             // 821
                                                                                                                       // 822
  if (name) {                                                                                                          // 823
    while (v && v.name !== name)                                                                                       // 824
      v = v.parentView;                                                                                                // 825
  }                                                                                                                    // 826
                                                                                                                       // 827
  return v || null;                                                                                                    // 828
};                                                                                                                     // 829
                                                                                                                       // 830
Blaze._getElementView = function (elem, name) {                                                                        // 831
  var range = Blaze._DOMRange.forElement(elem);                                                                        // 832
  var view = null;                                                                                                     // 833
  while (range && ! view) {                                                                                            // 834
    view = (range.view || null);                                                                                       // 835
    if (! view) {                                                                                                      // 836
      if (range.parentRange)                                                                                           // 837
        range = range.parentRange;                                                                                     // 838
      else                                                                                                             // 839
        range = Blaze._DOMRange.forElement(range.parentElement);                                                       // 840
    }                                                                                                                  // 841
  }                                                                                                                    // 842
                                                                                                                       // 843
  if (name) {                                                                                                          // 844
    while (view && view.name !== name)                                                                                 // 845
      view = view.parentView;                                                                                          // 846
    return view || null;                                                                                               // 847
  } else {                                                                                                             // 848
    return view;                                                                                                       // 849
  }                                                                                                                    // 850
};                                                                                                                     // 851
                                                                                                                       // 852
Blaze._addEventMap = function (view, eventMap, thisInHandler) {                                                        // 853
  thisInHandler = (thisInHandler || null);                                                                             // 854
  var handles = [];                                                                                                    // 855
                                                                                                                       // 856
  if (! view._domrange)                                                                                                // 857
    throw new Error("View must have a DOMRange");                                                                      // 858
                                                                                                                       // 859
  view._domrange.onAttached(function attached_eventMaps(range, element) {                                              // 860
    _.each(eventMap, function (handler, spec) {                                                                        // 861
      var clauses = spec.split(/,\s+/);                                                                                // 862
      // iterate over clauses of spec, e.g. ['click .foo', 'click .bar']                                               // 863
      _.each(clauses, function (clause) {                                                                              // 864
        var parts = clause.split(/\s+/);                                                                               // 865
        if (parts.length === 0)                                                                                        // 866
          return;                                                                                                      // 867
                                                                                                                       // 868
        var newEvents = parts.shift();                                                                                 // 869
        var selector = parts.join(' ');                                                                                // 870
        handles.push(Blaze._EventSupport.listen(                                                                       // 871
          element, newEvents, selector,                                                                                // 872
          function (evt) {                                                                                             // 873
            if (! range.containsElement(evt.currentTarget))                                                            // 874
              return null;                                                                                             // 875
            var handlerThis = thisInHandler || this;                                                                   // 876
            var handlerArgs = arguments;                                                                               // 877
            return Blaze._withCurrentView(view, function () {                                                          // 878
              return handler.apply(handlerThis, handlerArgs);                                                          // 879
            });                                                                                                        // 880
          },                                                                                                           // 881
          range, function (r) {                                                                                        // 882
            return r.parentRange;                                                                                      // 883
          }));                                                                                                         // 884
      });                                                                                                              // 885
    });                                                                                                                // 886
  });                                                                                                                  // 887
                                                                                                                       // 888
  view.onViewDestroyed(function () {                                                                                   // 889
    _.each(handles, function (h) {                                                                                     // 890
      h.stop();                                                                                                        // 891
    });                                                                                                                // 892
    handles.length = 0;                                                                                                // 893
  });                                                                                                                  // 894
};                                                                                                                     // 895
                                                                                                                       // 896
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/builtins.js                                                                                          //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
Blaze._calculateCondition = function (cond) {                                                                          // 1
  if (cond instanceof Array && cond.length === 0)                                                                      // 2
    cond = false;                                                                                                      // 3
  return !! cond;                                                                                                      // 4
};                                                                                                                     // 5
                                                                                                                       // 6
/**                                                                                                                    // 7
 * @summary Constructs a View that renders content with a data context.                                                // 8
 * @locus Client                                                                                                       // 9
 * @param {Object|Function} data An object to use as the data context, or a function returning such an object.  If a function is provided, it will be reactively re-run.
 * @param {Function} contentFunc A Function that returns [*renderable content*](#renderable_content).                  // 11
 */                                                                                                                    // 12
Blaze.With = function (data, contentFunc) {                                                                            // 13
  var view = Blaze.View('with', contentFunc);                                                                          // 14
                                                                                                                       // 15
  view.dataVar = new ReactiveVar;                                                                                      // 16
                                                                                                                       // 17
  view.onViewCreated(function () {                                                                                     // 18
    if (typeof data === 'function') {                                                                                  // 19
      // `data` is a reactive function                                                                                 // 20
      view.autorun(function () {                                                                                       // 21
        view.dataVar.set(data());                                                                                      // 22
      }, view.parentView, 'setData');                                                                                  // 23
    } else {                                                                                                           // 24
      view.dataVar.set(data);                                                                                          // 25
    }                                                                                                                  // 26
  });                                                                                                                  // 27
                                                                                                                       // 28
  return view;                                                                                                         // 29
};                                                                                                                     // 30
                                                                                                                       // 31
/**                                                                                                                    // 32
 * Attaches bindings to the instantiated view.                                                                         // 33
 * @param {Object} bindings A dictionary of bindings, each binding name                                                // 34
 * corresponds to a value or a function that will be reactively re-run.                                                // 35
 * @param {View} view The target.                                                                                      // 36
 */                                                                                                                    // 37
Blaze._attachBindingsToView = function (bindings, view) {                                                              // 38
  view.onViewCreated(function () {                                                                                     // 39
    _.each(bindings, function (binding, name) {                                                                        // 40
      view._scopeBindings[name] = new ReactiveVar;                                                                     // 41
      if (typeof binding === 'function') {                                                                             // 42
        view.autorun(function () {                                                                                     // 43
          view._scopeBindings[name].set(binding());                                                                    // 44
        }, view.parentView);                                                                                           // 45
      } else {                                                                                                         // 46
        view._scopeBindings[name].set(binding);                                                                        // 47
      }                                                                                                                // 48
    });                                                                                                                // 49
  });                                                                                                                  // 50
};                                                                                                                     // 51
                                                                                                                       // 52
/**                                                                                                                    // 53
 * @summary Constructs a View setting the local lexical scope in the block.                                            // 54
 * @param {Function} bindings Dictionary mapping names of bindings to                                                  // 55
 * values or computations to reactively re-run.                                                                        // 56
 * @param {Function} contentFunc A Function that returns [*renderable content*](#renderable_content).                  // 57
 */                                                                                                                    // 58
Blaze.Let = function (bindings, contentFunc) {                                                                         // 59
  var view = Blaze.View('let', contentFunc);                                                                           // 60
  Blaze._attachBindingsToView(bindings, view);                                                                         // 61
                                                                                                                       // 62
  return view;                                                                                                         // 63
};                                                                                                                     // 64
                                                                                                                       // 65
/**                                                                                                                    // 66
 * @summary Constructs a View that renders content conditionally.                                                      // 67
 * @locus Client                                                                                                       // 68
 * @param {Function} conditionFunc A function to reactively re-run.  Whether the result is truthy or falsy determines whether `contentFunc` or `elseFunc` is shown.  An empty array is considered falsy.
 * @param {Function} contentFunc A Function that returns [*renderable content*](#renderable_content).                  // 70
 * @param {Function} [elseFunc] Optional.  A Function that returns [*renderable content*](#renderable_content).  If no `elseFunc` is supplied, no content is shown in the "else" case.
 */                                                                                                                    // 72
Blaze.If = function (conditionFunc, contentFunc, elseFunc, _not) {                                                     // 73
  var conditionVar = new ReactiveVar;                                                                                  // 74
                                                                                                                       // 75
  var view = Blaze.View(_not ? 'unless' : 'if', function () {                                                          // 76
    return conditionVar.get() ? contentFunc() :                                                                        // 77
      (elseFunc ? elseFunc() : null);                                                                                  // 78
  });                                                                                                                  // 79
  view.__conditionVar = conditionVar;                                                                                  // 80
  view.onViewCreated(function () {                                                                                     // 81
    this.autorun(function () {                                                                                         // 82
      var cond = Blaze._calculateCondition(conditionFunc());                                                           // 83
      conditionVar.set(_not ? (! cond) : cond);                                                                        // 84
    }, this.parentView, 'condition');                                                                                  // 85
  });                                                                                                                  // 86
                                                                                                                       // 87
  return view;                                                                                                         // 88
};                                                                                                                     // 89
                                                                                                                       // 90
/**                                                                                                                    // 91
 * @summary An inverted [`Blaze.If`](#blaze_if).                                                                       // 92
 * @locus Client                                                                                                       // 93
 * @param {Function} conditionFunc A function to reactively re-run.  If the result is falsy, `contentFunc` is shown, otherwise `elseFunc` is shown.  An empty array is considered falsy.
 * @param {Function} contentFunc A Function that returns [*renderable content*](#renderable_content).                  // 95
 * @param {Function} [elseFunc] Optional.  A Function that returns [*renderable content*](#renderable_content).  If no `elseFunc` is supplied, no content is shown in the "else" case.
 */                                                                                                                    // 97
Blaze.Unless = function (conditionFunc, contentFunc, elseFunc) {                                                       // 98
  return Blaze.If(conditionFunc, contentFunc, elseFunc, true /*_not*/);                                                // 99
};                                                                                                                     // 100
                                                                                                                       // 101
/**                                                                                                                    // 102
 * @summary Constructs a View that renders `contentFunc` for each item in a sequence.                                  // 103
 * @locus Client                                                                                                       // 104
 * @param {Function} argFunc A function to reactively re-run. The function can                                         // 105
 * return one of two options:                                                                                          // 106
 *                                                                                                                     // 107
 * 1. An object with two fields: '_variable' and '_sequence'. Each iterates over                                       // 108
 *   '_sequence', it may be a Cursor, an array, null, or undefined. Inside the                                         // 109
 *   Each body you will be able to get the current item from the sequence using                                        // 110
 *   the name specified in the '_variable' field.                                                                      // 111
 *                                                                                                                     // 112
 * 2. Just a sequence (Cursor, array, null, or undefined) not wrapped into an                                          // 113
 *   object. Inside the Each body, the current item will be set as the data                                            // 114
 *   context.                                                                                                          // 115
 * @param {Function} contentFunc A Function that returns  [*renderable                                                 // 116
 * content*](#renderable_content).                                                                                     // 117
 * @param {Function} [elseFunc] A Function that returns [*renderable                                                   // 118
 * content*](#renderable_content) to display in the case when there are no items                                       // 119
 * in the sequence.                                                                                                    // 120
 */                                                                                                                    // 121
Blaze.Each = function (argFunc, contentFunc, elseFunc) {                                                               // 122
  var eachView = Blaze.View('each', function () {                                                                      // 123
    var subviews = this.initialSubviews;                                                                               // 124
    this.initialSubviews = null;                                                                                       // 125
    if (this._isCreatedForExpansion) {                                                                                 // 126
      this.expandedValueDep = new Tracker.Dependency;                                                                  // 127
      this.expandedValueDep.depend();                                                                                  // 128
    }                                                                                                                  // 129
    return subviews;                                                                                                   // 130
  });                                                                                                                  // 131
  eachView.initialSubviews = [];                                                                                       // 132
  eachView.numItems = 0;                                                                                               // 133
  eachView.inElseMode = false;                                                                                         // 134
  eachView.stopHandle = null;                                                                                          // 135
  eachView.contentFunc = contentFunc;                                                                                  // 136
  eachView.elseFunc = elseFunc;                                                                                        // 137
  eachView.argVar = new ReactiveVar;                                                                                   // 138
  eachView.variableName = null;                                                                                        // 139
                                                                                                                       // 140
  // update the @index value in the scope of all subviews in the range                                                 // 141
  var updateIndices = function (from, to) {                                                                            // 142
    if (to === undefined) {                                                                                            // 143
      to = eachView.numItems - 1;                                                                                      // 144
    }                                                                                                                  // 145
                                                                                                                       // 146
    for (var i = from; i <= to; i++) {                                                                                 // 147
      var view = eachView._domrange.members[i].view;                                                                   // 148
      view._scopeBindings['@index'].set(i);                                                                            // 149
    }                                                                                                                  // 150
  };                                                                                                                   // 151
                                                                                                                       // 152
  eachView.onViewCreated(function () {                                                                                 // 153
    // We evaluate argFunc in an autorun to make sure                                                                  // 154
    // Blaze.currentView is always set when it runs (rather than                                                       // 155
    // passing argFunc straight to ObserveSequence).                                                                   // 156
    eachView.autorun(function () {                                                                                     // 157
      // argFunc can return either a sequence as is or a wrapper object with a                                         // 158
      // _sequence and _variable fields set.                                                                           // 159
      var arg = argFunc();                                                                                             // 160
      if (_.isObject(arg) && _.has(arg, '_sequence')) {                                                                // 161
        eachView.variableName = arg._variable || null;                                                                 // 162
        arg = arg._sequence;                                                                                           // 163
      }                                                                                                                // 164
                                                                                                                       // 165
      eachView.argVar.set(arg);                                                                                        // 166
    }, eachView.parentView, 'collection');                                                                             // 167
                                                                                                                       // 168
    eachView.stopHandle = ObserveSequence.observe(function () {                                                        // 169
      return eachView.argVar.get();                                                                                    // 170
    }, {                                                                                                               // 171
      addedAt: function (id, item, index) {                                                                            // 172
        Tracker.nonreactive(function () {                                                                              // 173
          var newItemView;                                                                                             // 174
          if (eachView.variableName) {                                                                                 // 175
            // new-style #each (as in {{#each item in items}})                                                         // 176
            // doesn't create a new data context                                                                       // 177
            newItemView = Blaze.View('item', eachView.contentFunc);                                                    // 178
          } else {                                                                                                     // 179
            newItemView = Blaze.With(item, eachView.contentFunc);                                                      // 180
          }                                                                                                            // 181
                                                                                                                       // 182
          eachView.numItems++;                                                                                         // 183
                                                                                                                       // 184
          var bindings = {};                                                                                           // 185
          bindings['@index'] = index;                                                                                  // 186
          if (eachView.variableName) {                                                                                 // 187
            bindings[eachView.variableName] = item;                                                                    // 188
          }                                                                                                            // 189
          Blaze._attachBindingsToView(bindings, newItemView);                                                          // 190
                                                                                                                       // 191
          if (eachView.expandedValueDep) {                                                                             // 192
            eachView.expandedValueDep.changed();                                                                       // 193
          } else if (eachView._domrange) {                                                                             // 194
            if (eachView.inElseMode) {                                                                                 // 195
              eachView._domrange.removeMember(0);                                                                      // 196
              eachView.inElseMode = false;                                                                             // 197
            }                                                                                                          // 198
                                                                                                                       // 199
            var range = Blaze._materializeView(newItemView, eachView);                                                 // 200
            eachView._domrange.addMember(range, index);                                                                // 201
            updateIndices(index);                                                                                      // 202
          } else {                                                                                                     // 203
            eachView.initialSubviews.splice(index, 0, newItemView);                                                    // 204
          }                                                                                                            // 205
        });                                                                                                            // 206
      },                                                                                                               // 207
      removedAt: function (id, item, index) {                                                                          // 208
        Tracker.nonreactive(function () {                                                                              // 209
          eachView.numItems--;                                                                                         // 210
          if (eachView.expandedValueDep) {                                                                             // 211
            eachView.expandedValueDep.changed();                                                                       // 212
          } else if (eachView._domrange) {                                                                             // 213
            eachView._domrange.removeMember(index);                                                                    // 214
            updateIndices(index);                                                                                      // 215
            if (eachView.elseFunc && eachView.numItems === 0) {                                                        // 216
              eachView.inElseMode = true;                                                                              // 217
              eachView._domrange.addMember(                                                                            // 218
                Blaze._materializeView(                                                                                // 219
                  Blaze.View('each_else',eachView.elseFunc),                                                           // 220
                  eachView), 0);                                                                                       // 221
            }                                                                                                          // 222
          } else {                                                                                                     // 223
            eachView.initialSubviews.splice(index, 1);                                                                 // 224
          }                                                                                                            // 225
        });                                                                                                            // 226
      },                                                                                                               // 227
      changedAt: function (id, newItem, oldItem, index) {                                                              // 228
        Tracker.nonreactive(function () {                                                                              // 229
          if (eachView.expandedValueDep) {                                                                             // 230
            eachView.expandedValueDep.changed();                                                                       // 231
          } else {                                                                                                     // 232
            var itemView;                                                                                              // 233
            if (eachView._domrange) {                                                                                  // 234
              itemView = eachView._domrange.getMember(index).view;                                                     // 235
            } else {                                                                                                   // 236
              itemView = eachView.initialSubviews[index];                                                              // 237
            }                                                                                                          // 238
            if (eachView.variableName) {                                                                               // 239
              itemView._scopeBindings[eachView.variableName].set(newItem);                                             // 240
            } else {                                                                                                   // 241
              itemView.dataVar.set(newItem);                                                                           // 242
            }                                                                                                          // 243
          }                                                                                                            // 244
        });                                                                                                            // 245
      },                                                                                                               // 246
      movedTo: function (id, item, fromIndex, toIndex) {                                                               // 247
        Tracker.nonreactive(function () {                                                                              // 248
          if (eachView.expandedValueDep) {                                                                             // 249
            eachView.expandedValueDep.changed();                                                                       // 250
          } else if (eachView._domrange) {                                                                             // 251
            eachView._domrange.moveMember(fromIndex, toIndex);                                                         // 252
            updateIndices(                                                                                             // 253
              Math.min(fromIndex, toIndex), Math.max(fromIndex, toIndex));                                             // 254
          } else {                                                                                                     // 255
            var subviews = eachView.initialSubviews;                                                                   // 256
            var itemView = subviews[fromIndex];                                                                        // 257
            subviews.splice(fromIndex, 1);                                                                             // 258
            subviews.splice(toIndex, 0, itemView);                                                                     // 259
          }                                                                                                            // 260
        });                                                                                                            // 261
      }                                                                                                                // 262
    });                                                                                                                // 263
                                                                                                                       // 264
    if (eachView.elseFunc && eachView.numItems === 0) {                                                                // 265
      eachView.inElseMode = true;                                                                                      // 266
      eachView.initialSubviews[0] =                                                                                    // 267
        Blaze.View('each_else', eachView.elseFunc);                                                                    // 268
    }                                                                                                                  // 269
  });                                                                                                                  // 270
                                                                                                                       // 271
  eachView.onViewDestroyed(function () {                                                                               // 272
    if (eachView.stopHandle)                                                                                           // 273
      eachView.stopHandle.stop();                                                                                      // 274
  });                                                                                                                  // 275
                                                                                                                       // 276
  return eachView;                                                                                                     // 277
};                                                                                                                     // 278
                                                                                                                       // 279
Blaze._TemplateWith = function (arg, contentFunc) {                                                                    // 280
  var w;                                                                                                               // 281
                                                                                                                       // 282
  var argFunc = arg;                                                                                                   // 283
  if (typeof arg !== 'function') {                                                                                     // 284
    argFunc = function () {                                                                                            // 285
      return arg;                                                                                                      // 286
    };                                                                                                                 // 287
  }                                                                                                                    // 288
                                                                                                                       // 289
  // This is a little messy.  When we compile `{{> Template.contentBlock}}`, we                                        // 290
  // wrap it in Blaze._InOuterTemplateScope in order to skip the intermediate                                          // 291
  // parent Views in the current template.  However, when there's an argument                                          // 292
  // (`{{> Template.contentBlock arg}}`), the argument needs to be evaluated                                           // 293
  // in the original scope.  There's no good order to nest                                                             // 294
  // Blaze._InOuterTemplateScope and Spacebars.TemplateWith to achieve this,                                           // 295
  // so we wrap argFunc to run it in the "original parentView" of the                                                  // 296
  // Blaze._InOuterTemplateScope.                                                                                      // 297
  //                                                                                                                   // 298
  // To make this better, reconsider _InOuterTemplateScope as a primitive.                                             // 299
  // Longer term, evaluate expressions in the proper lexical scope.                                                    // 300
  var wrappedArgFunc = function () {                                                                                   // 301
    var viewToEvaluateArg = null;                                                                                      // 302
    if (w.parentView && w.parentView.name === 'InOuterTemplateScope') {                                                // 303
      viewToEvaluateArg = w.parentView.originalParentView;                                                             // 304
    }                                                                                                                  // 305
    if (viewToEvaluateArg) {                                                                                           // 306
      return Blaze._withCurrentView(viewToEvaluateArg, argFunc);                                                       // 307
    } else {                                                                                                           // 308
      return argFunc();                                                                                                // 309
    }                                                                                                                  // 310
  };                                                                                                                   // 311
                                                                                                                       // 312
  var wrappedContentFunc = function () {                                                                               // 313
    var content = contentFunc.call(this);                                                                              // 314
                                                                                                                       // 315
    // Since we are generating the Blaze._TemplateWith view for the                                                    // 316
    // user, set the flag on the child view.  If `content` is a template,                                              // 317
    // construct the View so that we can set the flag.                                                                 // 318
    if (content instanceof Blaze.Template) {                                                                           // 319
      content = content.constructView();                                                                               // 320
    }                                                                                                                  // 321
    if (content instanceof Blaze.View) {                                                                               // 322
      content._hasGeneratedParent = true;                                                                              // 323
    }                                                                                                                  // 324
                                                                                                                       // 325
    return content;                                                                                                    // 326
  };                                                                                                                   // 327
                                                                                                                       // 328
  w = Blaze.With(wrappedArgFunc, wrappedContentFunc);                                                                  // 329
  w.__isTemplateWith = true;                                                                                           // 330
  return w;                                                                                                            // 331
};                                                                                                                     // 332
                                                                                                                       // 333
Blaze._InOuterTemplateScope = function (templateView, contentFunc) {                                                   // 334
  var view = Blaze.View('InOuterTemplateScope', contentFunc);                                                          // 335
  var parentView = templateView.parentView;                                                                            // 336
                                                                                                                       // 337
  // Hack so that if you call `{{> foo bar}}` and it expands into                                                      // 338
  // `{{#with bar}}{{> foo}}{{/with}}`, and then `foo` is a template                                                   // 339
  // that inserts `{{> Template.contentBlock}}`, the data context for                                                  // 340
  // `Template.contentBlock` is not `bar` but the one enclosing that.                                                  // 341
  if (parentView.__isTemplateWith)                                                                                     // 342
    parentView = parentView.parentView;                                                                                // 343
                                                                                                                       // 344
  view.onViewCreated(function () {                                                                                     // 345
    this.originalParentView = this.parentView;                                                                         // 346
    this.parentView = parentView;                                                                                      // 347
    this.__childDoesntStartNewLexicalScope = true;                                                                     // 348
  });                                                                                                                  // 349
  return view;                                                                                                         // 350
};                                                                                                                     // 351
                                                                                                                       // 352
// XXX COMPAT WITH 0.9.0                                                                                               // 353
Blaze.InOuterTemplateScope = Blaze._InOuterTemplateScope;                                                              // 354
                                                                                                                       // 355
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/lookup.js                                                                                            //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
Blaze._globalHelpers = {};                                                                                             // 1
                                                                                                                       // 2
// Documented as Template.registerHelper.                                                                              // 3
// This definition also provides back-compat for `UI.registerHelper`.                                                  // 4
Blaze.registerHelper = function (name, func) {                                                                         // 5
  Blaze._globalHelpers[name] = func;                                                                                   // 6
};                                                                                                                     // 7
                                                                                                                       // 8
// Also documented as Template.deregisterHelper                                                                        // 9
Blaze.deregisterHelper = function(name) {                                                                              // 10
  delete Blaze._globalHelpers[name];                                                                                   // 11
};                                                                                                                     // 12
                                                                                                                       // 13
var bindIfIsFunction = function (x, target) {                                                                          // 14
  if (typeof x !== 'function')                                                                                         // 15
    return x;                                                                                                          // 16
  return Blaze._bind(x, target);                                                                                       // 17
};                                                                                                                     // 18
                                                                                                                       // 19
// If `x` is a function, binds the value of `this` for that function                                                   // 20
// to the current data context.                                                                                        // 21
var bindDataContext = function (x) {                                                                                   // 22
  if (typeof x === 'function') {                                                                                       // 23
    return function () {                                                                                               // 24
      var data = Blaze.getData();                                                                                      // 25
      if (data == null)                                                                                                // 26
        data = {};                                                                                                     // 27
      return x.apply(data, arguments);                                                                                 // 28
    };                                                                                                                 // 29
  }                                                                                                                    // 30
  return x;                                                                                                            // 31
};                                                                                                                     // 32
                                                                                                                       // 33
Blaze._OLDSTYLE_HELPER = {};                                                                                           // 34
                                                                                                                       // 35
Blaze._getTemplateHelper = function (template, name, tmplInstanceFunc) {                                               // 36
  // XXX COMPAT WITH 0.9.3                                                                                             // 37
  var isKnownOldStyleHelper = false;                                                                                   // 38
                                                                                                                       // 39
  if (template.__helpers.has(name)) {                                                                                  // 40
    var helper = template.__helpers.get(name);                                                                         // 41
    if (helper === Blaze._OLDSTYLE_HELPER) {                                                                           // 42
      isKnownOldStyleHelper = true;                                                                                    // 43
    } else if (helper != null) {                                                                                       // 44
      return wrapHelper(bindDataContext(helper), tmplInstanceFunc);                                                    // 45
    } else {                                                                                                           // 46
      return null;                                                                                                     // 47
    }                                                                                                                  // 48
  }                                                                                                                    // 49
                                                                                                                       // 50
  // old-style helper                                                                                                  // 51
  if (name in template) {                                                                                              // 52
    // Only warn once per helper                                                                                       // 53
    if (! isKnownOldStyleHelper) {                                                                                     // 54
      template.__helpers.set(name, Blaze._OLDSTYLE_HELPER);                                                            // 55
      if (! template._NOWARN_OLDSTYLE_HELPERS) {                                                                       // 56
        Blaze._warn('Assigning helper with `' + template.viewName + '.' +                                              // 57
                    name + ' = ...` is deprecated.  Use `' + template.viewName +                                       // 58
                    '.helpers(...)` instead.');                                                                        // 59
      }                                                                                                                // 60
    }                                                                                                                  // 61
    if (template[name] != null) {                                                                                      // 62
      return wrapHelper(bindDataContext(template[name]), tmplInstanceFunc);                                            // 63
    }                                                                                                                  // 64
  }                                                                                                                    // 65
                                                                                                                       // 66
  return null;                                                                                                         // 67
};                                                                                                                     // 68
                                                                                                                       // 69
var wrapHelper = function (f, templateFunc) {                                                                          // 70
  if (typeof f !== "function") {                                                                                       // 71
    return f;                                                                                                          // 72
  }                                                                                                                    // 73
                                                                                                                       // 74
  return function () {                                                                                                 // 75
    var self = this;                                                                                                   // 76
    var args = arguments;                                                                                              // 77
                                                                                                                       // 78
    return Blaze.Template._withTemplateInstanceFunc(templateFunc, function () {                                        // 79
      return Blaze._wrapCatchingExceptions(f, 'template helper').apply(self, args);                                    // 80
    });                                                                                                                // 81
  };                                                                                                                   // 82
};                                                                                                                     // 83
                                                                                                                       // 84
Blaze._lexicalBindingLookup = function (view, name) {                                                                  // 85
  var currentView = view;                                                                                              // 86
  var blockHelpersStack = [];                                                                                          // 87
                                                                                                                       // 88
  // walk up the views stopping at a Spacebars.include or Template view that                                           // 89
  // doesn't have an InOuterTemplateScope view as a parent                                                             // 90
  do {                                                                                                                 // 91
    // skip block helpers views                                                                                        // 92
    // if we found the binding on the scope, return it                                                                 // 93
    if (_.has(currentView._scopeBindings, name)) {                                                                     // 94
      var bindingReactiveVar = currentView._scopeBindings[name];                                                       // 95
      return function () {                                                                                             // 96
        return bindingReactiveVar.get();                                                                               // 97
      };                                                                                                               // 98
    }                                                                                                                  // 99
  } while (! (currentView.__startsNewLexicalScope &&                                                                   // 100
              ! (currentView.parentView &&                                                                             // 101
                 currentView.parentView.__childDoesntStartNewLexicalScope))                                            // 102
           && (currentView = currentView.parentView));                                                                 // 103
                                                                                                                       // 104
  return null;                                                                                                         // 105
};                                                                                                                     // 106
                                                                                                                       // 107
// templateInstance argument is provided to be available for possible                                                  // 108
// alternative implementations of this function by 3rd party packages.                                                 // 109
Blaze._getTemplate = function (name, templateInstance) {                                                               // 110
  if ((name in Blaze.Template) && (Blaze.Template[name] instanceof Blaze.Template)) {                                  // 111
    return Blaze.Template[name];                                                                                       // 112
  }                                                                                                                    // 113
  return null;                                                                                                         // 114
};                                                                                                                     // 115
                                                                                                                       // 116
Blaze._getGlobalHelper = function (name, templateInstance) {                                                           // 117
  if (Blaze._globalHelpers[name] != null) {                                                                            // 118
    return wrapHelper(bindDataContext(Blaze._globalHelpers[name]), templateInstance);                                  // 119
  }                                                                                                                    // 120
  return null;                                                                                                         // 121
};                                                                                                                     // 122
                                                                                                                       // 123
// Looks up a name, like "foo" or "..", as a helper of the                                                             // 124
// current template; the name of a template; a global helper;                                                          // 125
// or a property of the data context.  Called on the View of                                                           // 126
// a template (i.e. a View with a `.template` property,                                                                // 127
// where the helpers are).  Used for the first name in a                                                               // 128
// "path" in a template tag, like "foo" in `{{foo.bar}}` or                                                            // 129
// ".." in `{{frobulate ../blah}}`.                                                                                    // 130
//                                                                                                                     // 131
// Returns a function, a non-function value, or null.  If                                                              // 132
// a function is found, it is bound appropriately.                                                                     // 133
//                                                                                                                     // 134
// NOTE: This function must not establish any reactive                                                                 // 135
// dependencies itself.  If there is any reactivity in the                                                             // 136
// value, lookup should return a function.                                                                             // 137
Blaze.View.prototype.lookup = function (name, _options) {                                                              // 138
  var template = this.template;                                                                                        // 139
  var lookupTemplate = _options && _options.template;                                                                  // 140
  var helper;                                                                                                          // 141
  var binding;                                                                                                         // 142
  var boundTmplInstance;                                                                                               // 143
  var foundTemplate;                                                                                                   // 144
                                                                                                                       // 145
  if (this.templateInstance) {                                                                                         // 146
    boundTmplInstance = Blaze._bind(this.templateInstance, this);                                                      // 147
  }                                                                                                                    // 148
                                                                                                                       // 149
  // 0. looking up the parent data context with the special "../" syntax                                               // 150
  if (/^\./.test(name)) {                                                                                              // 151
    // starts with a dot. must be a series of dots which maps to an                                                    // 152
    // ancestor of the appropriate height.                                                                             // 153
    if (!/^(\.)+$/.test(name))                                                                                         // 154
      throw new Error("id starting with dot must be a series of dots");                                                // 155
                                                                                                                       // 156
    return Blaze._parentData(name.length - 1, true /*_functionWrapped*/);                                              // 157
                                                                                                                       // 158
  }                                                                                                                    // 159
                                                                                                                       // 160
  // 1. look up a helper on the current template                                                                       // 161
  if (template && ((helper = Blaze._getTemplateHelper(template, name, boundTmplInstance)) != null)) {                  // 162
    return helper;                                                                                                     // 163
  }                                                                                                                    // 164
                                                                                                                       // 165
  // 2. look up a binding by traversing the lexical view hierarchy inside the                                          // 166
  // current template                                                                                                  // 167
  if (template && (binding = Blaze._lexicalBindingLookup(Blaze.currentView, name)) != null) {                          // 168
    return binding;                                                                                                    // 169
  }                                                                                                                    // 170
                                                                                                                       // 171
  // 3. look up a template by name                                                                                     // 172
  if (lookupTemplate && ((foundTemplate = Blaze._getTemplate(name, boundTmplInstance)) != null)) {                     // 173
    return foundTemplate;                                                                                              // 174
  }                                                                                                                    // 175
                                                                                                                       // 176
  // 4. look up a global helper                                                                                        // 177
  if ((helper = Blaze._getGlobalHelper(name, boundTmplInstance)) != null) {                                            // 178
    return helper;                                                                                                     // 179
  }                                                                                                                    // 180
                                                                                                                       // 181
  // 5. look up in a data context                                                                                      // 182
  return function () {                                                                                                 // 183
    var isCalledAsFunction = (arguments.length > 0);                                                                   // 184
    var data = Blaze.getData();                                                                                        // 185
    var x = data && data[name];                                                                                        // 186
    if (! x) {                                                                                                         // 187
      if (lookupTemplate) {                                                                                            // 188
        throw new Error("No such template: " + name);                                                                  // 189
      } else if (isCalledAsFunction) {                                                                                 // 190
        throw new Error("No such function: " + name);                                                                  // 191
      } else if (name.charAt(0) === '@' && ((x === null) ||                                                            // 192
                                            (x === undefined))) {                                                      // 193
        // Throw an error if the user tries to use a `@directive`                                                      // 194
        // that doesn't exist.  We don't implement all directives                                                      // 195
        // from Handlebars, so there's a potential for confusion                                                       // 196
        // if we fail silently.  On the other hand, we want to                                                         // 197
        // throw late in case some app or package wants to provide                                                     // 198
        // a missing directive.                                                                                        // 199
        throw new Error("Unsupported directive: " + name);                                                             // 200
      }                                                                                                                // 201
    }                                                                                                                  // 202
    if (! data) {                                                                                                      // 203
      return null;                                                                                                     // 204
    }                                                                                                                  // 205
    if (typeof x !== 'function') {                                                                                     // 206
      if (isCalledAsFunction) {                                                                                        // 207
        throw new Error("Can't call non-function: " + x);                                                              // 208
      }                                                                                                                // 209
      return x;                                                                                                        // 210
    }                                                                                                                  // 211
    return x.apply(data, arguments);                                                                                   // 212
  };                                                                                                                   // 213
};                                                                                                                     // 214
                                                                                                                       // 215
// Implement Spacebars' {{../..}}.                                                                                     // 216
// @param height {Number} The number of '..'s                                                                          // 217
Blaze._parentData = function (height, _functionWrapped) {                                                              // 218
  // If height is null or undefined, we default to 1, the first parent.                                                // 219
  if (height == null) {                                                                                                // 220
    height = 1;                                                                                                        // 221
  }                                                                                                                    // 222
  var theWith = Blaze.getView('with');                                                                                 // 223
  for (var i = 0; (i < height) && theWith; i++) {                                                                      // 224
    theWith = Blaze.getView(theWith, 'with');                                                                          // 225
  }                                                                                                                    // 226
                                                                                                                       // 227
  if (! theWith)                                                                                                       // 228
    return null;                                                                                                       // 229
  if (_functionWrapped)                                                                                                // 230
    return function () { return theWith.dataVar.get(); };                                                              // 231
  return theWith.dataVar.get();                                                                                        // 232
};                                                                                                                     // 233
                                                                                                                       // 234
                                                                                                                       // 235
Blaze.View.prototype.lookupTemplate = function (name) {                                                                // 236
  return this.lookup(name, {template:true});                                                                           // 237
};                                                                                                                     // 238
                                                                                                                       // 239
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/template.js                                                                                          //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
// [new] Blaze.Template([viewName], renderFunction)                                                                    // 1
//                                                                                                                     // 2
// `Blaze.Template` is the class of templates, like `Template.foo` in                                                  // 3
// Meteor, which is `instanceof Template`.                                                                             // 4
//                                                                                                                     // 5
// `viewKind` is a string that looks like "Template.foo" for templates                                                 // 6
// defined by the compiler.                                                                                            // 7
                                                                                                                       // 8
/**                                                                                                                    // 9
 * @class                                                                                                              // 10
 * @summary Constructor for a Template, which is used to construct Views with particular name and content.             // 11
 * @locus Client                                                                                                       // 12
 * @param {String} [viewName] Optional.  A name for Views constructed by this Template.  See [`view.name`](#view_name).
 * @param {Function} renderFunction A function that returns [*renderable content*](#renderable_content).  This function is used as the `renderFunction` for Views constructed by this Template.
 */                                                                                                                    // 15
Blaze.Template = function (viewName, renderFunction) {                                                                 // 16
  if (! (this instanceof Blaze.Template))                                                                              // 17
    // called without `new`                                                                                            // 18
    return new Blaze.Template(viewName, renderFunction);                                                               // 19
                                                                                                                       // 20
  if (typeof viewName === 'function') {                                                                                // 21
    // omitted "viewName" argument                                                                                     // 22
    renderFunction = viewName;                                                                                         // 23
    viewName = '';                                                                                                     // 24
  }                                                                                                                    // 25
  if (typeof viewName !== 'string')                                                                                    // 26
    throw new Error("viewName must be a String (or omitted)");                                                         // 27
  if (typeof renderFunction !== 'function')                                                                            // 28
    throw new Error("renderFunction must be a function");                                                              // 29
                                                                                                                       // 30
  this.viewName = viewName;                                                                                            // 31
  this.renderFunction = renderFunction;                                                                                // 32
                                                                                                                       // 33
  this.__helpers = new HelperMap;                                                                                      // 34
  this.__eventMaps = [];                                                                                               // 35
                                                                                                                       // 36
  this._callbacks = {                                                                                                  // 37
    created: [],                                                                                                       // 38
    rendered: [],                                                                                                      // 39
    destroyed: []                                                                                                      // 40
  };                                                                                                                   // 41
};                                                                                                                     // 42
var Template = Blaze.Template;                                                                                         // 43
                                                                                                                       // 44
var HelperMap = function () {};                                                                                        // 45
HelperMap.prototype.get = function (name) {                                                                            // 46
  return this[' '+name];                                                                                               // 47
};                                                                                                                     // 48
HelperMap.prototype.set = function (name, helper) {                                                                    // 49
  this[' '+name] = helper;                                                                                             // 50
};                                                                                                                     // 51
HelperMap.prototype.has = function (name) {                                                                            // 52
  return (' '+name) in this;                                                                                           // 53
};                                                                                                                     // 54
                                                                                                                       // 55
/**                                                                                                                    // 56
 * @summary Returns true if `value` is a template object like `Template.myTemplate`.                                   // 57
 * @locus Client                                                                                                       // 58
 * @param {Any} value The value to test.                                                                               // 59
 */                                                                                                                    // 60
Blaze.isTemplate = function (t) {                                                                                      // 61
  return (t instanceof Blaze.Template);                                                                                // 62
};                                                                                                                     // 63
                                                                                                                       // 64
/**                                                                                                                    // 65
 * @name  onCreated                                                                                                    // 66
 * @instance                                                                                                           // 67
 * @memberOf Template                                                                                                  // 68
 * @summary Register a function to be called when an instance of this template is created.                             // 69
 * @param {Function} callback A function to be added as a callback.                                                    // 70
 * @locus Client                                                                                                       // 71
 * @importFromPackage templating                                                                                       // 72
 */                                                                                                                    // 73
Template.prototype.onCreated = function (cb) {                                                                         // 74
  this._callbacks.created.push(cb);                                                                                    // 75
};                                                                                                                     // 76
                                                                                                                       // 77
/**                                                                                                                    // 78
 * @name  onRendered                                                                                                   // 79
 * @instance                                                                                                           // 80
 * @memberOf Template                                                                                                  // 81
 * @summary Register a function to be called when an instance of this template is inserted into the DOM.               // 82
 * @param {Function} callback A function to be added as a callback.                                                    // 83
 * @locus Client                                                                                                       // 84
 * @importFromPackage templating                                                                                       // 85
 */                                                                                                                    // 86
Template.prototype.onRendered = function (cb) {                                                                        // 87
  this._callbacks.rendered.push(cb);                                                                                   // 88
};                                                                                                                     // 89
                                                                                                                       // 90
/**                                                                                                                    // 91
 * @name  onDestroyed                                                                                                  // 92
 * @instance                                                                                                           // 93
 * @memberOf Template                                                                                                  // 94
 * @summary Register a function to be called when an instance of this template is removed from the DOM and destroyed.  // 95
 * @param {Function} callback A function to be added as a callback.                                                    // 96
 * @locus Client                                                                                                       // 97
 * @importFromPackage templating                                                                                       // 98
 */                                                                                                                    // 99
Template.prototype.onDestroyed = function (cb) {                                                                       // 100
  this._callbacks.destroyed.push(cb);                                                                                  // 101
};                                                                                                                     // 102
                                                                                                                       // 103
Template.prototype._getCallbacks = function (which) {                                                                  // 104
  var self = this;                                                                                                     // 105
  var callbacks = self[which] ? [self[which]] : [];                                                                    // 106
  // Fire all callbacks added with the new API (Template.onRendered())                                                 // 107
  // as well as the old-style callback (e.g. Template.rendered) for                                                    // 108
  // backwards-compatibility.                                                                                          // 109
  callbacks = callbacks.concat(self._callbacks[which]);                                                                // 110
  return callbacks;                                                                                                    // 111
};                                                                                                                     // 112
                                                                                                                       // 113
var fireCallbacks = function (callbacks, template) {                                                                   // 114
  Template._withTemplateInstanceFunc(                                                                                  // 115
    function () { return template; },                                                                                  // 116
    function () {                                                                                                      // 117
      for (var i = 0, N = callbacks.length; i < N; i++) {                                                              // 118
        callbacks[i].call(template);                                                                                   // 119
      }                                                                                                                // 120
    });                                                                                                                // 121
};                                                                                                                     // 122
                                                                                                                       // 123
Template.prototype.constructView = function (contentFunc, elseFunc) {                                                  // 124
  var self = this;                                                                                                     // 125
  var view = Blaze.View(self.viewName, self.renderFunction);                                                           // 126
  view.template = self;                                                                                                // 127
                                                                                                                       // 128
  view.templateContentBlock = (                                                                                        // 129
    contentFunc ? new Template('(contentBlock)', contentFunc) : null);                                                 // 130
  view.templateElseBlock = (                                                                                           // 131
    elseFunc ? new Template('(elseBlock)', elseFunc) : null);                                                          // 132
                                                                                                                       // 133
  if (self.__eventMaps || typeof self.events === 'object') {                                                           // 134
    view._onViewRendered(function () {                                                                                 // 135
      if (view.renderCount !== 1)                                                                                      // 136
        return;                                                                                                        // 137
                                                                                                                       // 138
      if (! self.__eventMaps.length && typeof self.events === "object") {                                              // 139
        // Provide limited back-compat support for `.events = {...}`                                                   // 140
        // syntax.  Pass `template.events` to the original `.events(...)`                                              // 141
        // function.  This code must run only once per template, in                                                    // 142
        // order to not bind the handlers more than once, which is                                                     // 143
        // ensured by the fact that we only do this when `__eventMaps`                                                 // 144
        // is falsy, and we cause it to be set now.                                                                    // 145
        Template.prototype.events.call(self, self.events);                                                             // 146
      }                                                                                                                // 147
                                                                                                                       // 148
      _.each(self.__eventMaps, function (m) {                                                                          // 149
        Blaze._addEventMap(view, m, view);                                                                             // 150
      });                                                                                                              // 151
    });                                                                                                                // 152
  }                                                                                                                    // 153
                                                                                                                       // 154
  view._templateInstance = new Blaze.TemplateInstance(view);                                                           // 155
  view.templateInstance = function () {                                                                                // 156
    // Update data, firstNode, and lastNode, and return the TemplateInstance                                           // 157
    // object.                                                                                                         // 158
    var inst = view._templateInstance;                                                                                 // 159
                                                                                                                       // 160
    /**                                                                                                                // 161
     * @instance                                                                                                       // 162
     * @memberOf Blaze.TemplateInstance                                                                                // 163
     * @name  data                                                                                                     // 164
     * @summary The data context of this instance's latest invocation.                                                 // 165
     * @locus Client                                                                                                   // 166
     */                                                                                                                // 167
    inst.data = Blaze.getData(view);                                                                                   // 168
                                                                                                                       // 169
    if (view._domrange && !view.isDestroyed) {                                                                         // 170
      inst.firstNode = view._domrange.firstNode();                                                                     // 171
      inst.lastNode = view._domrange.lastNode();                                                                       // 172
    } else {                                                                                                           // 173
      // on 'created' or 'destroyed' callbacks we don't have a DomRange                                                // 174
      inst.firstNode = null;                                                                                           // 175
      inst.lastNode = null;                                                                                            // 176
    }                                                                                                                  // 177
                                                                                                                       // 178
    return inst;                                                                                                       // 179
  };                                                                                                                   // 180
                                                                                                                       // 181
  /**                                                                                                                  // 182
   * @name  created                                                                                                    // 183
   * @instance                                                                                                         // 184
   * @memberOf Template                                                                                                // 185
   * @summary Provide a callback when an instance of a template is created.                                            // 186
   * @locus Client                                                                                                     // 187
   * @deprecated in 1.1                                                                                                // 188
   */                                                                                                                  // 189
  // To avoid situations when new callbacks are added in between view                                                  // 190
  // instantiation and event being fired, decide on all callbacks to fire                                              // 191
  // immediately and then fire them on the event.                                                                      // 192
  var createdCallbacks = self._getCallbacks('created');                                                                // 193
  view.onViewCreated(function () {                                                                                     // 194
    fireCallbacks(createdCallbacks, view.templateInstance());                                                          // 195
  });                                                                                                                  // 196
                                                                                                                       // 197
  /**                                                                                                                  // 198
   * @name  rendered                                                                                                   // 199
   * @instance                                                                                                         // 200
   * @memberOf Template                                                                                                // 201
   * @summary Provide a callback when an instance of a template is rendered.                                           // 202
   * @locus Client                                                                                                     // 203
   * @deprecated in 1.1                                                                                                // 204
   */                                                                                                                  // 205
  var renderedCallbacks = self._getCallbacks('rendered');                                                              // 206
  view.onViewReady(function () {                                                                                       // 207
    fireCallbacks(renderedCallbacks, view.templateInstance());                                                         // 208
  });                                                                                                                  // 209
                                                                                                                       // 210
  /**                                                                                                                  // 211
   * @name  destroyed                                                                                                  // 212
   * @instance                                                                                                         // 213
   * @memberOf Template                                                                                                // 214
   * @summary Provide a callback when an instance of a template is destroyed.                                          // 215
   * @locus Client                                                                                                     // 216
   * @deprecated in 1.1                                                                                                // 217
   */                                                                                                                  // 218
  var destroyedCallbacks = self._getCallbacks('destroyed');                                                            // 219
  view.onViewDestroyed(function () {                                                                                   // 220
    fireCallbacks(destroyedCallbacks, view.templateInstance());                                                        // 221
  });                                                                                                                  // 222
                                                                                                                       // 223
  return view;                                                                                                         // 224
};                                                                                                                     // 225
                                                                                                                       // 226
/**                                                                                                                    // 227
 * @class                                                                                                              // 228
 * @summary The class for template instances                                                                           // 229
 * @param {Blaze.View} view                                                                                            // 230
 * @instanceName template                                                                                              // 231
 */                                                                                                                    // 232
Blaze.TemplateInstance = function (view) {                                                                             // 233
  if (! (this instanceof Blaze.TemplateInstance))                                                                      // 234
    // called without `new`                                                                                            // 235
    return new Blaze.TemplateInstance(view);                                                                           // 236
                                                                                                                       // 237
  if (! (view instanceof Blaze.View))                                                                                  // 238
    throw new Error("View required");                                                                                  // 239
                                                                                                                       // 240
  view._templateInstance = this;                                                                                       // 241
                                                                                                                       // 242
  /**                                                                                                                  // 243
   * @name view                                                                                                        // 244
   * @memberOf Blaze.TemplateInstance                                                                                  // 245
   * @instance                                                                                                         // 246
   * @summary The [View](#blaze_view) object for this invocation of the template.                                      // 247
   * @locus Client                                                                                                     // 248
   * @type {Blaze.View}                                                                                                // 249
   */                                                                                                                  // 250
  this.view = view;                                                                                                    // 251
  this.data = null;                                                                                                    // 252
                                                                                                                       // 253
  /**                                                                                                                  // 254
   * @name firstNode                                                                                                   // 255
   * @memberOf Blaze.TemplateInstance                                                                                  // 256
   * @instance                                                                                                         // 257
   * @summary The first top-level DOM node in this template instance.                                                  // 258
   * @locus Client                                                                                                     // 259
   * @type {DOMNode}                                                                                                   // 260
   */                                                                                                                  // 261
  this.firstNode = null;                                                                                               // 262
                                                                                                                       // 263
  /**                                                                                                                  // 264
   * @name lastNode                                                                                                    // 265
   * @memberOf Blaze.TemplateInstance                                                                                  // 266
   * @instance                                                                                                         // 267
   * @summary The last top-level DOM node in this template instance.                                                   // 268
   * @locus Client                                                                                                     // 269
   * @type {DOMNode}                                                                                                   // 270
   */                                                                                                                  // 271
  this.lastNode = null;                                                                                                // 272
                                                                                                                       // 273
  // This dependency is used to identify state transitions in                                                          // 274
  // _subscriptionHandles which could cause the result of                                                              // 275
  // TemplateInstance#subscriptionsReady to change. Basically this is triggered                                        // 276
  // whenever a new subscription handle is added or when a subscription handle                                         // 277
  // is removed and they are not ready.                                                                                // 278
  this._allSubsReadyDep = new Tracker.Dependency();                                                                    // 279
  this._allSubsReady = false;                                                                                          // 280
                                                                                                                       // 281
  this._subscriptionHandles = {};                                                                                      // 282
};                                                                                                                     // 283
                                                                                                                       // 284
/**                                                                                                                    // 285
 * @summary Find all elements matching `selector` in this template instance, and return them as a JQuery object.       // 286
 * @locus Client                                                                                                       // 287
 * @param {String} selector The CSS selector to match, scoped to the template contents.                                // 288
 * @returns {DOMNode[]}                                                                                                // 289
 */                                                                                                                    // 290
Blaze.TemplateInstance.prototype.$ = function (selector) {                                                             // 291
  var view = this.view;                                                                                                // 292
  if (! view._domrange)                                                                                                // 293
    throw new Error("Can't use $ on template instance with no DOM");                                                   // 294
  return view._domrange.$(selector);                                                                                   // 295
};                                                                                                                     // 296
                                                                                                                       // 297
/**                                                                                                                    // 298
 * @summary Find all elements matching `selector` in this template instance.                                           // 299
 * @locus Client                                                                                                       // 300
 * @param {String} selector The CSS selector to match, scoped to the template contents.                                // 301
 * @returns {DOMElement[]}                                                                                             // 302
 */                                                                                                                    // 303
Blaze.TemplateInstance.prototype.findAll = function (selector) {                                                       // 304
  return Array.prototype.slice.call(this.$(selector));                                                                 // 305
};                                                                                                                     // 306
                                                                                                                       // 307
/**                                                                                                                    // 308
 * @summary Find one element matching `selector` in this template instance.                                            // 309
 * @locus Client                                                                                                       // 310
 * @param {String} selector The CSS selector to match, scoped to the template contents.                                // 311
 * @returns {DOMElement}                                                                                               // 312
 */                                                                                                                    // 313
Blaze.TemplateInstance.prototype.find = function (selector) {                                                          // 314
  var result = this.$(selector);                                                                                       // 315
  return result[0] || null;                                                                                            // 316
};                                                                                                                     // 317
                                                                                                                       // 318
/**                                                                                                                    // 319
 * @summary A version of [Tracker.autorun](#tracker_autorun) that is stopped when the template is destroyed.           // 320
 * @locus Client                                                                                                       // 321
 * @param {Function} runFunc The function to run. It receives one argument: a Tracker.Computation object.              // 322
 */                                                                                                                    // 323
Blaze.TemplateInstance.prototype.autorun = function (f) {                                                              // 324
  return this.view.autorun(f);                                                                                         // 325
};                                                                                                                     // 326
                                                                                                                       // 327
/**                                                                                                                    // 328
 * @summary A version of [Meteor.subscribe](#meteor_subscribe) that is stopped                                         // 329
 * when the template is destroyed.                                                                                     // 330
 * @return {SubscriptionHandle} The subscription handle to the newly made                                              // 331
 * subscription. Call `handle.stop()` to manually stop the subscription, or                                            // 332
 * `handle.ready()` to find out if this particular subscription has loaded all                                         // 333
 * of its inital data.                                                                                                 // 334
 * @locus Client                                                                                                       // 335
 * @param {String} name Name of the subscription.  Matches the name of the                                             // 336
 * server's `publish()` call.                                                                                          // 337
 * @param {Any} [arg1,arg2...] Optional arguments passed to publisher function                                         // 338
 * on server.                                                                                                          // 339
 * @param {Function|Object} [options] If a function is passed instead of an                                            // 340
 * object, it is interpreted as an `onReady` callback.                                                                 // 341
 * @param {Function} [options.onReady] Passed to [`Meteor.subscribe`](#meteor_subscribe).                              // 342
 * @param {Function} [options.onStop] Passed to [`Meteor.subscribe`](#meteor_subscribe).                               // 343
 * @param {DDP.Connection} [options.connection] The connection on which to make the                                    // 344
 * subscription.                                                                                                       // 345
 */                                                                                                                    // 346
Blaze.TemplateInstance.prototype.subscribe = function (/* arguments */) {                                              // 347
  var self = this;                                                                                                     // 348
                                                                                                                       // 349
  var subHandles = self._subscriptionHandles;                                                                          // 350
  var args = _.toArray(arguments);                                                                                     // 351
                                                                                                                       // 352
  // Duplicate logic from Meteor.subscribe                                                                             // 353
  var options = {};                                                                                                    // 354
  if (args.length) {                                                                                                   // 355
    var lastParam = _.last(args);                                                                                      // 356
                                                                                                                       // 357
    // Match pattern to check if the last arg is an options argument                                                   // 358
    var lastParamOptionsPattern = {                                                                                    // 359
      onReady: Match.Optional(Function),                                                                               // 360
      // XXX COMPAT WITH 1.0.3.1 onError used to exist, but now we use                                                 // 361
      // onStop with an error callback instead.                                                                        // 362
      onError: Match.Optional(Function),                                                                               // 363
      onStop: Match.Optional(Function),                                                                                // 364
      connection: Match.Optional(Match.Any)                                                                            // 365
    };                                                                                                                 // 366
                                                                                                                       // 367
    if (_.isFunction(lastParam)) {                                                                                     // 368
      options.onReady = args.pop();                                                                                    // 369
    } else if (lastParam && ! _.isEmpty(lastParam) && Match.test(lastParam, lastParamOptionsPattern)) {                // 370
      options = args.pop();                                                                                            // 371
    }                                                                                                                  // 372
  }                                                                                                                    // 373
                                                                                                                       // 374
  var subHandle;                                                                                                       // 375
  var oldStopped = options.onStop;                                                                                     // 376
  options.onStop = function (error) {                                                                                  // 377
    // When the subscription is stopped, remove it from the set of tracked                                             // 378
    // subscriptions to avoid this list growing without bound                                                          // 379
    delete subHandles[subHandle.subscriptionId];                                                                       // 380
                                                                                                                       // 381
    // Removing a subscription can only change the result of subscriptionsReady                                        // 382
    // if we are not ready (that subscription could be the one blocking us being                                       // 383
    // ready).                                                                                                         // 384
    if (! self._allSubsReady) {                                                                                        // 385
      self._allSubsReadyDep.changed();                                                                                 // 386
    }                                                                                                                  // 387
                                                                                                                       // 388
    if (oldStopped) {                                                                                                  // 389
      oldStopped(error);                                                                                               // 390
    }                                                                                                                  // 391
  };                                                                                                                   // 392
                                                                                                                       // 393
  var connection = options.connection;                                                                                 // 394
  var callbacks = _.pick(options, ["onReady", "onError", "onStop"]);                                                   // 395
                                                                                                                       // 396
  // The callbacks are passed as the last item in the arguments array passed to                                        // 397
  // View#subscribe                                                                                                    // 398
  args.push(callbacks);                                                                                                // 399
                                                                                                                       // 400
  // View#subscribe takes the connection as one of the options in the last                                             // 401
  // argument                                                                                                          // 402
  subHandle = self.view.subscribe.call(self.view, args, {                                                              // 403
    connection: connection                                                                                             // 404
  });                                                                                                                  // 405
                                                                                                                       // 406
  if (! _.has(subHandles, subHandle.subscriptionId)) {                                                                 // 407
    subHandles[subHandle.subscriptionId] = subHandle;                                                                  // 408
                                                                                                                       // 409
    // Adding a new subscription will always cause us to transition from ready                                         // 410
    // to not ready, but if we are already not ready then this can't make us                                           // 411
    // ready.                                                                                                          // 412
    if (self._allSubsReady) {                                                                                          // 413
      self._allSubsReadyDep.changed();                                                                                 // 414
    }                                                                                                                  // 415
  }                                                                                                                    // 416
                                                                                                                       // 417
  return subHandle;                                                                                                    // 418
};                                                                                                                     // 419
                                                                                                                       // 420
/**                                                                                                                    // 421
 * @summary A reactive function that returns true when all of the subscriptions                                        // 422
 * called with [this.subscribe](#TemplateInstance-subscribe) are ready.                                                // 423
 * @return {Boolean} True if all subscriptions on this template instance are                                           // 424
 * ready.                                                                                                              // 425
 */                                                                                                                    // 426
Blaze.TemplateInstance.prototype.subscriptionsReady = function () {                                                    // 427
  this._allSubsReadyDep.depend();                                                                                      // 428
                                                                                                                       // 429
  this._allSubsReady = _.all(this._subscriptionHandles, function (handle) {                                            // 430
    return handle.ready();                                                                                             // 431
  });                                                                                                                  // 432
                                                                                                                       // 433
  return this._allSubsReady;                                                                                           // 434
};                                                                                                                     // 435
                                                                                                                       // 436
/**                                                                                                                    // 437
 * @summary Specify template helpers available to this template.                                                       // 438
 * @locus Client                                                                                                       // 439
 * @param {Object} helpers Dictionary of helper functions by name.                                                     // 440
 * @importFromPackage templating                                                                                       // 441
 */                                                                                                                    // 442
Template.prototype.helpers = function (dict) {                                                                         // 443
  if (! _.isObject(dict)) {                                                                                            // 444
    throw new Error("Helpers dictionary has to be an object");                                                         // 445
  }                                                                                                                    // 446
                                                                                                                       // 447
  for (var k in dict)                                                                                                  // 448
    this.__helpers.set(k, dict[k]);                                                                                    // 449
};                                                                                                                     // 450
                                                                                                                       // 451
// Kind of like Blaze.currentView but for the template instance.                                                       // 452
// This is a function, not a value -- so that not all helpers                                                          // 453
// are implicitly dependent on the current template instance's `data` property,                                        // 454
// which would make them dependenct on the data context of the template                                                // 455
// inclusion.                                                                                                          // 456
Template._currentTemplateInstanceFunc = null;                                                                          // 457
                                                                                                                       // 458
Template._withTemplateInstanceFunc = function (templateInstanceFunc, func) {                                           // 459
  if (typeof func !== 'function')                                                                                      // 460
    throw new Error("Expected function, got: " + func);                                                                // 461
  var oldTmplInstanceFunc = Template._currentTemplateInstanceFunc;                                                     // 462
  try {                                                                                                                // 463
    Template._currentTemplateInstanceFunc = templateInstanceFunc;                                                      // 464
    return func();                                                                                                     // 465
  } finally {                                                                                                          // 466
    Template._currentTemplateInstanceFunc = oldTmplInstanceFunc;                                                       // 467
  }                                                                                                                    // 468
};                                                                                                                     // 469
                                                                                                                       // 470
/**                                                                                                                    // 471
 * @summary Specify event handlers for this template.                                                                  // 472
 * @locus Client                                                                                                       // 473
 * @param {EventMap} eventMap Event handlers to associate with this template.                                          // 474
 * @importFromPackage templating                                                                                       // 475
 */                                                                                                                    // 476
Template.prototype.events = function (eventMap) {                                                                      // 477
  if (! _.isObject(eventMap)) {                                                                                        // 478
    throw new Error("Event map has to be an object");                                                                  // 479
  }                                                                                                                    // 480
                                                                                                                       // 481
  var template = this;                                                                                                 // 482
  var eventMap2 = {};                                                                                                  // 483
  for (var k in eventMap) {                                                                                            // 484
    eventMap2[k] = (function (k, v) {                                                                                  // 485
      return function (event/*, ...*/) {                                                                               // 486
        var view = this; // passed by EventAugmenter                                                                   // 487
        var data = Blaze.getData(event.currentTarget);                                                                 // 488
        if (data == null)                                                                                              // 489
          data = {};                                                                                                   // 490
        var args = Array.prototype.slice.call(arguments);                                                              // 491
        var tmplInstanceFunc = Blaze._bind(view.templateInstance, view);                                               // 492
        args.splice(1, 0, tmplInstanceFunc());                                                                         // 493
                                                                                                                       // 494
        return Template._withTemplateInstanceFunc(tmplInstanceFunc, function () {                                      // 495
          return v.apply(data, args);                                                                                  // 496
        });                                                                                                            // 497
      };                                                                                                               // 498
    })(k, eventMap[k]);                                                                                                // 499
  }                                                                                                                    // 500
                                                                                                                       // 501
  template.__eventMaps.push(eventMap2);                                                                                // 502
};                                                                                                                     // 503
                                                                                                                       // 504
/**                                                                                                                    // 505
 * @function                                                                                                           // 506
 * @name instance                                                                                                      // 507
 * @memberOf Template                                                                                                  // 508
 * @summary The [template instance](#template_inst) corresponding to the current template helper, event handler, callback, or autorun.  If there isn't one, `null`.
 * @locus Client                                                                                                       // 510
 * @returns {Blaze.TemplateInstance}                                                                                   // 511
 * @importFromPackage templating                                                                                       // 512
 */                                                                                                                    // 513
Template.instance = function () {                                                                                      // 514
  return Template._currentTemplateInstanceFunc                                                                         // 515
    && Template._currentTemplateInstanceFunc();                                                                        // 516
};                                                                                                                     // 517
                                                                                                                       // 518
// Note: Template.currentData() is documented to take zero arguments,                                                  // 519
// while Blaze.getData takes up to one.                                                                                // 520
                                                                                                                       // 521
/**                                                                                                                    // 522
 * @summary                                                                                                            // 523
 *                                                                                                                     // 524
 * - Inside an `onCreated`, `onRendered`, or `onDestroyed` callback, returns                                           // 525
 * the data context of the template.                                                                                   // 526
 * - Inside an event handler, returns the data context of the template on which                                        // 527
 * this event handler was defined.                                                                                     // 528
 * - Inside a helper, returns the data context of the DOM node where the helper                                        // 529
 * was used.                                                                                                           // 530
 *                                                                                                                     // 531
 * Establishes a reactive dependency on the result.                                                                    // 532
 * @locus Client                                                                                                       // 533
 * @function                                                                                                           // 534
 * @importFromPackage templating                                                                                       // 535
 */                                                                                                                    // 536
Template.currentData = Blaze.getData;                                                                                  // 537
                                                                                                                       // 538
/**                                                                                                                    // 539
 * @summary Accesses other data contexts that enclose the current data context.                                        // 540
 * @locus Client                                                                                                       // 541
 * @function                                                                                                           // 542
 * @param {Integer} [numLevels] The number of levels beyond the current data context to look. Defaults to 1.           // 543
 * @importFromPackage templating                                                                                       // 544
 */                                                                                                                    // 545
Template.parentData = Blaze._parentData;                                                                               // 546
                                                                                                                       // 547
/**                                                                                                                    // 548
 * @summary Defines a [helper function](#template_helpers) which can be used from all templates.                       // 549
 * @locus Client                                                                                                       // 550
 * @function                                                                                                           // 551
 * @param {String} name The name of the helper function you are defining.                                              // 552
 * @param {Function} function The helper function itself.                                                              // 553
 * @importFromPackage templating                                                                                       // 554
 */                                                                                                                    // 555
Template.registerHelper = Blaze.registerHelper;                                                                        // 556
                                                                                                                       // 557
/**                                                                                                                    // 558
 * @summary Removes a global [helper function](#template_helpers).                                                     // 559
 * @locus Client                                                                                                       // 560
 * @function                                                                                                           // 561
 * @param {String} name The name of the helper function you are defining.                                              // 562
 * @importFromPackage templating                                                                                       // 563
 */                                                                                                                    // 564
Template.deregisterHelper = Blaze.deregisterHelper;                                                                    // 565
                                                                                                                       // 566
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);






(function(){

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                                                                                                     //
// packages/blaze/backcompat.js                                                                                        //
//                                                                                                                     //
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                                                                                                                       //
UI = Blaze;                                                                                                            // 1
                                                                                                                       // 2
Blaze.ReactiveVar = ReactiveVar;                                                                                       // 3
UI._templateInstance = Blaze.Template.instance;                                                                        // 4
                                                                                                                       // 5
Handlebars = {};                                                                                                       // 6
Handlebars.registerHelper = Blaze.registerHelper;                                                                      // 7
                                                                                                                       // 8
Handlebars._escape = Blaze._escape;                                                                                    // 9
                                                                                                                       // 10
// Return these from {{...}} helpers to achieve the same as returning                                                  // 11
// strings from {{{...}}} helpers                                                                                      // 12
Handlebars.SafeString = function(string) {                                                                             // 13
  this.string = string;                                                                                                // 14
};                                                                                                                     // 15
Handlebars.SafeString.prototype.toString = function() {                                                                // 16
  return this.string.toString();                                                                                       // 17
};                                                                                                                     // 18
                                                                                                                       // 19
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

}).call(this);
