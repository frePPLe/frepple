=========================
Machine Learning Forecast
=========================

This app is using the Orbit library to generate a machine learning forecast.
See https://orbit-ml.readthedocs.io/en/stable/
When installed, for each forecast record, this app will train the model using the demand history
and then will predict the future for the length of the future horizon defined in the parameters.

If a forecast record has not enough demand history, then frePPLe will revert to the statistical
forecast methods.