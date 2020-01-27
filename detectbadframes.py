#!/usr/bin/env python3

import sys
import argparse
from PIL import Image, ImageColor
from pathlib import Path
import json


_debug = False
_test = False


def _parse_arguments():
    parser = argparse.ArgumentParser(description="Detect and remove bad frames from a timelapse image sequence.")
    parser.add_argument("specification", type=str, action="store", nargs="+", help="specification of what to check for in the images")
    parser.add_argument("source", type=str, action="store", help="source directory for image sequences")
    parser.add_argument("--destination", dest="destination", metavar='D', type=str, action="store", default="rejected", help="destination directory for bad frames")
    parser.add_argument("--delete", action="store_true", dest="delete_immediately", help="delete detected frames immediately instead of moving them to a rejection directory")
    parser.add_argument("-d", "--debug", action="store_true", dest="debug", help="print debugging information")
    parser.add_argument("--test", action="store_true", dest="test", help="check the rules but do not move or delete the frames")
    
    args = parser.parse_args()
    return args


def _verify_source(destination):
    p = Path(destination)
    if not p.exists():
        raise FileNotFoundError()
    else:
        if p.is_file():
            raise NotADirectoryError()


def _verify_destination(destination, source):
    p = Path(destination)
    if not p.exists():
        p.mkdir()
    else:
        if p.is_file():
            raise NotADirectoryError()


def _check_rule(frame, rule):
    rule_type = rule['type']
    if rule_type == 'size':
        match = frame.width == rule['width'] and frame.height == rule['height']
        if not match and _debug:
            print("Size rule broken (%s) (image is (%d, %d), rule requires (%d, %d))" % (rule['name'], frame.width, frame.height, rule['width'], rule['height']))
        return match
    elif rule_type == 'pixel_colour' or rule_type == 'pixel_not_colour':
        pixel = None
        try:
            pixel = frame.getpixel((rule['x'], rule['y']))
        except IndexError:
            # This occurs if the frame is smaller than expected
            return False
        rule_color = ImageColor.getrgb(rule['colour'])
        match = rule_color == pixel
        if rule_type == 'pixel_colour' and not match and _debug:
            print("Colour rule broken (%s)" % rule['name'])
        if rule_type == 'pixel_not_colour' and match and _debug:
            print("Inverse colour rule broken (%s)" % rule['name'])
        if rule_type == 'pixel_colour':
            return match
        else:
            return not match
    elif rule_type == 'or':
        sub_rules = rule["rules"]
        match = any(map(lambda sub_rule: _check_rule(frame, sub_rule), sub_rules))
        if not match and _debug:
            print("Or rule broken (%s)" % rule['name'])
        return match


def _check_rules(frame, specification):
    passed = all(map(lambda rule: _check_rule(frame, rule), specification['rules']))
    if not passed:
        if _debug:
            print('Frame broke rules for specification "%s"' % specification['name'])
    return passed


def _process_frame(frame_path, destination, delete_immediately, specifications):
    passed = None
    with Image.open(frame_path) as frame:
        passed = any(map(lambda spec: _check_rules(frame, spec), specifications))
    if not passed:
        if _debug:
            print('Bad frame detected (%s)' % frame_path)
        if not _test:
            if delete_immediately:
                frame_path.unlink()
            else:
                frame_path.rename(Path(destination) / frame_path.name)

    return passed


def _process_source(source, destination, delete_immediately, specifications):
    rejected = []
    processed = 0
    for frame in Path(source).iterdir():
        processed += 1
        if not _process_frame(frame, destination, delete_immediately, specifications):
            rejected.append(frame)
    return processed, rejected


if __name__ == "__main__":
    args = _parse_arguments()
    _debug = args.debug
    _test = args.test
    parsed_specifications = []
    try:
        try:
            _verify_source(args.source)
        except FileNotFoundError:
            print ("The specified source does not exist.")
            sys.exit(1)
        except NotAFileError:
            print ("The specified source is not a file.")
            sys.exit(1)

        try:
            if not args.delete_immediately:
                _verify_destination(args.destination, args.source)
        except NotADirectoryError:
            print ("The specified destination is not a directory.")
            sys.exit(1)
        except FileNotFoundError:
            print ("The specified destination directory could not be created because of missing parents.")
            sys.exit(1)
        except PermissionError:
            print ("The destination directory could not be created due to inadequate permissions.")
            sys.exit(1)

        try:
            for spec in args.specification:
                with Path(spec).open() as spec_file:
                    parsed_specifications.append(json.load(spec_file))
        except FileNotFoundError as e:
            print ("The specification file does not exist (%s)." % e.filename)
            sys.exit(1)

        # TODO: Validate specifications

        if _debug:
            print("Parsed specifications:")
            for spec in parsed_specifications:
                print(spec)

        processed, rejected = _process_source(args.source, args.destination, args.delete_immediately, parsed_specifications)
        
        print("%d frame(s) rejected of %d processed" % (len(rejected), processed))
        if _test:
            for r in rejected:
                print (r)
    except KeyboardInterrupt:
        # TODO: Maybe track some statistics and print them on exit.
        print()
        sys.exit(0)
