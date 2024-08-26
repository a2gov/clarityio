# Changelog

<!--next-version-placeholder-->

## v0.3.0 (2024-08-26)

- `scale_raw_to_aqi()` function converts raw pollutant measurements to EPA AQI values.  Cutoff values come from https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf,
    except for PM2.5 values which changed in 2024: https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf.

This package implemented the more strict values of PM2.5 in August 2024.  The EPA notes, "Many areas can expect to see more days in the Moderate (Code Yellow) category because of the changes in the AQI breakpoints. The Moderate category now begins when fine particle pollution concentrations reach 9 micrograms per cubic meter of air (the level of the updated annual air quality standard). Previously, the Moderate category began at 12 micrograms per cubic meter."

Thus users might see an apparent decrease in air quality with respect to PM2.5 occurring after updating to clarityio v0.3.0.

## v0.2.0 (2024-07-22)

- Can retrieve data in `csv-wide` format

## v0.1.0 (2024-07-07)

- Initial release