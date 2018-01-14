module.export({
  execFileSync: () => execFileSync,
  execFileAsync: () => execFileAsync
});

let _;

module.watch(require("underscore"), {
  default(v) {
    _ = v;
  }

}, 0);
let child_process;
module.watch(require("child_process"), {
  default(v) {
    child_process = v;
  }

}, 1);
let files;
module.watch(require("../fs/mini-files"), {
  default(v) {
    files = v;
  }

}, 2);

function execFileSync(command, args, options) {
  return Promise.await(execFileAsync(command, args, options));
}

function execFileAsync(command, args, options = {
  waitForClose: true
}) {
  // args is optional, so if it's not an array we interpret it as options
  if (!Array.isArray(args)) {
    options = _.extend(options, args);
    args = [];
  }

  if (options.cwd) {
    options.cwd = files.convertToOSPath(options.cwd);
  } // The child process close event is emitted when the stdio streams
  // have all terminated. If those streams are shared with other
  // processes, that means we won't receive a 'close' until all processes
  // have exited, so we may want to respond to 'exit' instead.
  // (The downside of responding to 'exit' is that the streams may not be
  // fully flushed, so we could miss captured output. Only use this
  // option when needed.)


  const exitEvent = options.waitForClose ? 'close' : 'exit';
  return new Promise((resolve, reject) => {
    var child;

    if (process.platform !== 'win32') {
      child = child_process.spawn(command, args, ({
        cwd,
        env,
        stdio
      } = options));
    } else {
      // https://github.com/nodejs/node-v0.x-archive/issues/2318
      args.forEach(arg => {
        command += ' ' + arg;
      });
      child = child_process.exec(command, ({
        cwd,
        env,
        stdio
      } = options));
    }

    let capturedStdout = '';

    if (child.stdout) {
      if (options.destination) {
        child.stdout.pipe(options.destination);
      } else {
        child.stdout.setEncoding('utf8');
        child.stdout.on('data', data => {
          capturedStdout += data;
        });
      }
    }

    let capturedStderr = '';

    if (child.stderr) {
      child.stderr.setEncoding('utf8');
      child.stderr.on('data', data => {
        capturedStderr += data;
      });
    }

    const errorCallback = error => {
      // Make sure we only receive one type of callback
      child.removeListener(exitEvent, exitCallback); // Trim captured output to get rid of excess whitespace

      capturedStdout = capturedStdout.trim();
      capturedStderr = capturedStderr.trim();

      _.extend(error, {
        pid: child.pid,
        stdout: capturedStdout,
        stderr: capturedStderr
      }); // Set a more informative error message on ENOENT, that includes the
      // command we attempted to execute


      if (error.code === 'ENOENT') {
        error.message = `Could not find command '${command}'`;
      }

      reject(error);
    };

    child.on('error', errorCallback);

    const exitCallback = (code, signal) => {
      // Make sure we only receive one type of callback
      child.removeListener('error', errorCallback); // Trim captured output to get rid of excess whitespace

      capturedStdout = capturedStdout.trim();
      capturedStderr = capturedStderr.trim();

      if (code === 0) {
        resolve(capturedStdout);
      } else {
        let errorMessage = `Command failed: ${command}`;

        if (args) {
          errorMessage += ` ${args.join(' ')}`;
        }

        errorMessage += `\n${capturedStderr}`;
        const error = new Error(errorMessage);

        _.extend(error, {
          pid: child.pid,
          stdout: capturedStdout,
          stderr: capturedStderr,
          status: code,
          signal: signal
        });

        reject(error);
      }
    };

    child.on(exitEvent, exitCallback);
  });
}
//# sourceMappingURL=processes.js.map