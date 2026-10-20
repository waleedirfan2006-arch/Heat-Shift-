# History-input model experiment

Uses only the uploaded warehouse's current, 24-hour-lag and 48-hour-lag station temperatures plus known calendar features. No agent code is imported or changed.

Four Ridge, eight HistGradientBoosting and two ExtraTrees configurations were each compared at four fixed residual weights on three expanding training folds (56 comparisons). The selection rule used training-fold MAE before scoring fixed validation.

The selected ExtraTrees model scored 1.247286 C validation MAE versus persistence 1.235165 C. It is not promoted. Missing-history performance is a software robustness stress test, not an official contest accuracy metric. Validation has previously been examined; no fresh final-test claim is made.

Run `python HeatShift_Training/train_history_model.py` to rebuild the fitted artifact and results from the uploaded warehouse. No downloads are performed. The large fitted model is generated locally rather than checked into GitHub; metrics and per-row validation predictions are included.
