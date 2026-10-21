/* Inference equivalent for HeatShift's frozen sklearn HistGradientBoosting model. */
(function (root) {
  "use strict";

  function lowerBound(values, x) {
    let lo = 0;
    let hi = values.length;
    while (lo < hi) {
      const mid = (lo + hi) >>> 1;
      if (x <= values[mid]) hi = mid;
      else lo = mid + 1;
    }
    return lo;
  }

  function predictResidual(row, model) {
    if (model.format !== "heatshift-hgb-js-v1") throw new Error("Unsupported model file.");
    const values = [];
    model.numeric_features.forEach((name, i) => {
      const raw = row[name];
      let value = raw === null || raw === undefined || raw === "" ? NaN : Number(raw);
      if (!Number.isFinite(value)) value = model.medians[i];
      values.push((value - model.means[i]) / model.scales[i]);
    });
    model.categorical_features.forEach((name, categoryIndex) => {
      const categories = model.categories[categoryIndex];
      const wanted = String(row[name]);
      categories.forEach((category) => values.push(category === wanted ? 1 : 0));
    });

    if (values.length !== model.bin_thresholds.length) throw new Error("Model feature count mismatch.");
    const bins = values.map((value, i) => lowerBound(model.bin_thresholds[i], value));
    let prediction = model.baseline;
    model.trees.forEach((nodes) => {
      let index = 0;
      while (!nodes[index].leaf) {
        const node = nodes[index];
        index = bins[node.feature] <= node.bin ? node.left : node.right;
      }
      prediction += nodes[index].value;
    });
    return prediction;
  }

  root.HeatShiftModel = { predictResidual };
  if (typeof module !== "undefined" && module.exports) module.exports = root.HeatShiftModel;
})(typeof globalThis !== "undefined" ? globalThis : this);

