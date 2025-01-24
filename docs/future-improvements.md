## Future improvements:

### Wifi

- Should be able to test only Wifi connection, without displaying the serial printout directly from test board.

### UI
- Scrollable listboxes for output to handle expected output that is more than one line.

- UI for test status and progress is not updated if connection is lost and then reestablished.

- Checkbox and ports should not be changeable when connection is established.
    - Include total reset/disconnect button in the UI?

- Port selection fault when connecting Wifi board:
    - Sometimes a popup is triggered, saying that the test board cannot be connected to the same port as the control board.
    - Most likely has to do with config.py that saves the previously selected ports,

### Firmware
- Instead of a hardcoded definition of ROOM_TEMP (22) one could have an environment variable that may be accessed via the python app.

- Implement timeout or fallback mechanism in runCurrentSequence in the check of (!isTemepratureReached) in case of not being able to reach a temperature because the threshold between the current temperature and the goal temperature is too low when heating.
    - If one want to make a test where temperatures are very close to eachother, you might want to cool down to room temp between temperatures, or cool down to a high enough threshold to increase the odds that the next temperature will be reached
