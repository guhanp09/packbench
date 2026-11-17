# Review findings

17 November 2026, after the first executed study and telemetry build.

The two archives contain different specimens. The initial-capacity record is
SP20-1; dynamic tests are SP20-2. The report identifies both and never calls the
first cell's measured capacity the second cell's capacity. The pack screen
combines their energy/resistance only as an assumed representative cell.

The DST spreadsheets have `.xls` names but OOXML contents, and an information
sheet precedes the measurement sheet. Import explicitly selects the channel
sheet and engine; it checks time ordering before reduction. Current is inverted
once at import to a discharge-positive convention.

Time-constant and parameter selection use only the 80% run. The 50% file stays
separate. Its 16 mV RMS error coexists with a 310 mV largest error near the low-SOC
tail, which remains in the plot and metrics. The first 2.7 V crossing is a declared
analysis boundary, not a test-data choice made to improve the result. Excluded
tails are counted and raw data remain unchanged.

The integration/cycler disagreement is small but nonzero. The first available
discharge sample omits an initial interval the cycler may have counted. No
endpoint or calibration factor is inserted to force agreement.

The C packet is encoded explicitly by bytes, without relying on struct packing,
endianness or signed C overflow. An independent Python CRC/struct decoder checks
the emitted bytes. Timer and sequence wrap are exercised. Manifest checks cover
frame loss at the edges; CRC and sequence alone cannot establish full recording
completeness. Fresh, biased calibration can still pass every integrity test.

An ARM object is a compilation result, not an installed board firmware image.
Host sanitizers do not establish MCU timing. The evidence register records those
physical integration/protection requirements as open, and class approval as
outside scope. No unchecked item is converted into a pass to improve a headline.

The pack example makes no thermal claim and does not close aircraft mass/drag.
Its 24S40P point is the lightest passing member of a declared coarse enumeration;
it is neither a continuous optimum nor a constructible pack design. The assumed
4 A current ceiling is a screening choice rather than a qualified cell rating.

The initial Linux/GCC build rejected an implicit signedness change in the CRC
shift expression under `-Werror`. The expression now shifts through an explicit
uint32_t temporary before truncating to uint16_t. The standard CRC vector and
independent Python decoder exercise the unchanged byte-level result. CI now
prints command diagnostics and retains failed-run artifacts instead of obscuring
failures behind the evidence runner.
