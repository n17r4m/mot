module.export({
  eachline: () => eachline,
  transform: () => transform
});
let split;
module.watch(require("split2"), {
  default(v) {
    split = v;
  }

}, 0);
let pipe;
module.watch(require("multipipe"), {
  default(v) {
    pipe = v;
  }

}, 1);
let Transform;
module.watch(require("stream"), {
  Transform(v) {
    Transform = v;
  }

}, 2);

function eachline(stream, callback) {
  stream.pipe(transform(callback));
}

function transform(callback) {
  const splitStream = split(/\r?\n/, null, {
    trailing: false
  });
  const transform = new Transform();

  transform._transform = function (chunk, encoding, done) {
    return Promise.asyncApply(() => {
      let line = chunk.toString("utf8");

      try {
        line = Promise.await(callback(line));
      } catch (error) {
        done(error);
        return;
      }

      done(null, line);
    });
  };

  return pipe(splitStream, transform);
}
//# sourceMappingURL=eachline.js.map