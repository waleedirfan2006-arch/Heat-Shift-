const fs = require("fs");
const model = require("./model.js");
const frozen = JSON.parse(fs.readFileSync(`${__dirname}/model.json`, "utf8"));
const vectors = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let maxError = 0;
for (const vector of vectors) {
  const actual = model.predictResidual(vector.row, frozen);
  const error = Math.abs(actual - vector.expected);
  maxError = Math.max(maxError, error);
  if (error > 1e-10) throw new Error(`Prediction mismatch: ${actual} vs ${vector.expected} (error ${error})`);
}
console.log(`JavaScript inference matches sklearn on ${vectors.length} feature rows; max difference ${maxError}.`);

