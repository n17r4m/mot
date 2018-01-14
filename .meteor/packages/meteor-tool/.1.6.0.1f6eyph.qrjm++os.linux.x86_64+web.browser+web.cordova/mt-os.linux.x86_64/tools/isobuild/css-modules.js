const module1 = module;
module1.export({
  cssToCommonJS: () => cssToCommonJS
});

function cssToCommonJS(css) {
  return ['module.exports = require("meteor/modules").addStyles(', "  " + JSON.stringify(css), ");", ""].join("\n");
}
//# sourceMappingURL=css-modules.js.map