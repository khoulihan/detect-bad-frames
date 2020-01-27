# detect-bad-frames

A script to detect and remove bad frames from a sequence of timelapse screenshots.

Copyright (c) 2020 by Kevin Houlihan

License: MIT, see LICENSE for more details.

## Prerequisites

The script depends on Python 3.6 (though possibly earlier versions of Python 3 will work fine), and [Pillow](https://python-pillow.org/).

## Usage

The script requires at least on specification file to define what a "good" frame is, and a target directory with the timelapse sequence to check.

```
detectbadframes.py specs/pyxel_edit.json timelapse/01
```

If multiple applications were expected to be captured by the timelapse, multiple specification files can be listed. If a frame passes according to at least one of the specifications, it will not be rejected.

```
detectbadframes.py specs/pyxel_edit.json specs/godot.json timelapse/01
```

### Destination

By default, any bad frames detected will be moved to a directory called "rejected" in the current working directory.

The specify a different destination, use the `--destination` flag.

```
detectbadframes.py --destination rejected/01 specs/pyxel_edit.json timelapse/01
```

### Delete Immediately

To delete frames immediately instead of moving them, add the `--delete` flag. This is not recommended unless you're sure your specification files work exactly as you want.

```
detectbadframes.py --delete specs/pyxel_edit.json timelapse/01
```

### Test

To only perform the checks, but not move or delete the detected bad frames, use the `--test` flag. A list of detected bad frames will be output to the terminal.

```
detectbadframes.py --test specs/pyxel_edit.json timelapse/01
```

### Debug

The `--debug` or `-d` flags can be used to print debugging information to the terminal. This is quite verbose, but may be useful in determining why frames are or are not being rejected.

## Specification Format

Specification files contain a json formatted set of rules to match each frame against. If any rule is broken then the frame is deemed to be "bad" according to the specification.

The root of the file should be a json object with keys "name", which is the name of the specification, and "rules", which is an array of rule objects to apply.

```json
{
    "name": "Pyxel Edit",
    "rules": [
    		...
    ]
}
```

Rule objects must always contain "name" and "type" keys. The name can be anything, but is used in debugging output to indicate broken rules, while the type must be one of `size`, `pixel_colour`, `pixel_not_colour`, or `or`. The remaining required keys differs for each type.

### size

This rule type checks that the dimensions of the screenshot match what was expected. If a dialog box was captured instead of the main application window, it will be rejected based on this rule.

```json
{
    "name": "Size",
    "type": "size",
    "width": 2560,
    "height": 1356
}
```

### pixel_colour

This rule type checks that a specific pixel in the image is a particular colour. Select an invariant location on the target application's window to detect frames where the window has just been minimized or where another application has been captured accidentally. Also can be useful for detecting when dropdown menus were open.

```json
{
    "name": "Window normal",
    "type": "pixel_colour",
    "x": 3,
    "y": 1353,
    "colour": "#555555"
}
```

### pixel_not_colour

This rule is the inverse of `pixel_colour`, and is passed as long as the specified pixel is *not* the specified colour.

```json
{
    "name": "Edit menu",
    "type": "pixel_not_colour",
    "x": 34,
    "y": 2,
    "colour": "#ebe9ed"
}
```

### or

This rule type takes a set of sub-rules. If any one of the sub-rules is passed then the rule as a whole will pass. This is useful where a pixel can be one of several colours without indicating a bad frame.

```json
{
    "name": "Window normal",
    "type": "or",
    "rules": [
        {
            "name": "Window normal",
            "type": "pixel_colour",
            "x": 3,
            "y": 1353,
            "colour": "#1f2531"
        },
        {
            "name": "Window occluded",
            "type": "pixel_colour",
            "x": 3,
            "y": 1353,
            "colour": "#0c0f14"
        }
    ]
}
```